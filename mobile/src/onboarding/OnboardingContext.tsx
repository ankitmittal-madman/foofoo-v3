/**
 * Onboarding state — the shared answer bag for the 5-screen flow. Adapted from
 * scareme21-create/NewFoo's OnboardingContext.tsx, which targeted a different backend
 * (ghar_api's /v1/onboarding). Two fields that source's flow never collected were added
 * here because foofoo-v3's household/handler.ts hard-requires all five profiles columns
 * before it will create a profile at all (schema.ts's PROFILE_REQUIRED_FIELDS):
 *   - currentCity (source only collected an optional GPS-derived city; foofoo-v3 has no
 *     GPS integration, so Screen 2 asks for it directly, same as home state)
 *   - cookCapability (source never asked this at all; added to Screen 5 as the one
 *     required field on an otherwise fully-skippable screen)
 * `primaryCookName` is asked on Create ID, same as source, but here it is submitted to
 * POST /v1/household (source only saved it to Supabase Auth user_metadata).
 *
 * Persistence (audit-onboarding-funnel HIGH finding: "no persisted resume logic" — every reopen
 * forced a full restart from step 1 with a blank form). This is a client-side stopgap, not a
 * server-side resume feature: there is no `onboarding_step`/draft column anywhere in the schema
 * (household/store.ts's onboarding_sessions is an append-only per-answer log, not a resumable
 * draft), so the answer bag + current step + local consent decision are mirrored into a single
 * JSON blob in AsyncStorage, keyed per signed-in user where a user id is available (falls back to
 * a single device-local key otherwise — acceptable per this fix's own scope: this is a single-user
 * mobile client, not a shared/multi-account device). Restored on mount; cleared on successful
 * final submission (step-5's onSuccess calls reset()).
 */
import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import AsyncStorage from "@react-native-async-storage/async-storage";

import { logger } from "@/lib/logger";

export type HouseholdType = "single" | "couple" | "couple_kids" | "couple_kids_parents" | "joint" | "flatmates";

// The 5 diet choices shown to the user. 'eggetarian' is UI-only — mapped to our
// schema's 'egg' at submit time (toHouseholdWrite.ts), never stored under this name.
export type DietChoice = "veg" | "eggetarian" | "non_veg" | "jain" | "vegan";

export type CookCapability = "beginner" | "intermediate" | "advanced";

export type OnboardingAnswers = {
  // Screen 1 — "Who lives in your home?"
  householdType: HouseholdType | null;
  workingProfessionals: number | null;

  // Screen 2 — "Where are you based?"
  homeState: string | null;
  currentCity: string | null;

  // Screen 3 — "What kind of meals do you enjoy?"
  diet: DietChoice | null;
  jainExclusions: string[]; // collect-only: no destination in foofoo-v3's schema, kept for parity, not submitted
  meatPreferences: string[];
  vegDays: string[];

  // Screen 4 — health
  allergens: string[];
  allergensOther: string;
  medicalConditions: string[];
  medicalConditionsOther: string;

  // Screen 5 — last details (all skippable except cookCapability)
  ageSingle: string | null;
  ageEldest: string | null;
  ageYoungest: string | null;
  whoCooks: string | null; // self | family | hired_cook | order_in (mapped to order_tiffin at submit)
  eatOutFrequency: string | null;
  cookingObjective: string | null;
  cookCapability: CookCapability | null; // required — see header note
};

const INITIAL_ANSWERS: OnboardingAnswers = {
  householdType: null,
  workingProfessionals: null,
  homeState: null,
  currentCity: null,
  diet: null,
  jainExclusions: [],
  meatPreferences: [],
  vegDays: [],
  allergens: [],
  allergensOther: "",
  medicalConditions: [],
  medicalConditionsOther: "",
  ageSingle: null,
  ageEldest: null,
  ageYoungest: null,
  whoCooks: null,
  eatOutFrequency: null,
  cookingObjective: null,
  cookCapability: null,
};

const SPLIT_AGE_HOUSEHOLDS: HouseholdType[] = ["couple_kids", "couple_kids_parents", "joint"];

/**
 * isSplitAgeHousehold — whether Screen 5 should ask for two separate age bands (eldest +
 * youngest) instead of one, based on the household type chosen on Screen 1. True for any
 * household that plausibly spans generations (kids and/or grandparents); false for single,
 * couple, or flatmate households where one age band covers everyone relevant.
 * @param household - the household type answered on Screen 1, or null if not yet answered.
 * @returns true if Screen 5's age question should show the eldest/youngest split.
 */
export function isSplitAgeHousehold(household: HouseholdType | null): boolean {
  return household != null && SPLIT_AGE_HOUSEHOLDS.includes(household);
}

/**
 * earliestIncompleteStep — the lowest-numbered step (1-4) whose own required field(s) are still
 * unanswered, mirroring each step screen's own `canContinue` gate (step-1's household type,
 * step-2's home state + city, step-3's diet). Step 5's only required field (cookCapability) is
 * excluded — its own screen already gates Continue on that. Returns null when steps 1-3 are all
 * satisfied, meaning any step 1-5 route can safely render.
 *
 * Needed because a step screen only guards ITS OWN required field, not earlier ones — landing
 * directly on step-5 via a deep link/hard refresh (bypassing steps 1-4 entirely) previously fell
 * through every screen's local check and only surfaced as a cryptic ERR_HOUSEHOLD_INCOMPLETE
 * after submitting on step 5.
 * @param answers - the current onboarding answer bag.
 * @returns the step number to redirect to, or null if steps 1-3's required fields are all set.
 */
export function earliestIncompleteStep(answers: OnboardingAnswers): number | null {
  if (answers.householdType === null) return 1;
  if (answers.homeState === null || !answers.currentCity?.trim()) return 2;
  if (answers.diet === null) return 3;
  return null;
}

// ---- Consent (DOC-P3-06 §06.1 — POST /v1/consent) ---------------------------
//
// Captured on a dedicated screen before Screen 1 (api-contract-audit-2026-07-30.md HIGH finding —
// /v1/consent had zero mobile callers, and DOC-09 §03 requires personalization consent be granted
// before any dietary/preference data collection). `decided` flips true the moment the user makes a
// local choice on the consent screen (gates re-showing that screen on resume); `submitted` flips
// true only once the POST /v1/consent call has actually succeeded — see step-5.tsx's header
// comment for why that call is deferred until profile creation rather than fired immediately.
export type ConsentAnswers = {
  personalization: boolean | null;
  analytics: boolean | null;
  pushNotifications: boolean | null;
  dataRetention: boolean | null;
  privacyPolicyVersion: string | null;
  decided: boolean;
  submitted: boolean;
};

const INITIAL_CONSENT: ConsentAnswers = {
  personalization: true,
  analytics: true,
  pushNotifications: false,
  dataRetention: true,
  privacyPolicyVersion: null,
  decided: false,
  submitted: false,
};

interface PersistedProgress {
  answers: OnboardingAnswers;
  consent: ConsentAnswers;
  currentStep: number;
}

const STORAGE_PREFIX = "@foofoo/onboarding-progress";

type OnboardingContextValue = {
  answers: OnboardingAnswers;
  setAnswers: (patch: Partial<OnboardingAnswers>) => void;
  consent: ConsentAnswers;
  setConsent: (patch: Partial<ConsentAnswers>) => void;
  /** Which step screen ("/(onboarding)/step-N") a returning user should resume at. */
  currentStep: number;
  setCurrentStep: (step: number) => void;
  /** True once the AsyncStorage read on mount has completed (hit or miss) — screens that decide
   * whether to redirect-to-resume vs render fresh should wait for this to avoid a flash. */
  restored: boolean;
  reset: () => void;
};

const OnboardingContext = createContext<OnboardingContextValue | null>(null);

/**
 * OnboardingProvider — wraps the 5-step onboarding flow (mounted once in the onboarding group
 * layout) and holds the in-memory answer bag every step screen reads from and writes to via
 * useOnboarding(). Answers live only in memory for the duration of the flow — each step also
 * submits its own slice to the backend immediately via postHousehold, so this context is not
 * the durable source of truth, just the shared scratch pad the UI reads while the user is
 * mid-flow. Progress is also persisted to AsyncStorage (see below) so a killed/reopened app
 * resumes instead of restarting from step 1.
 * @param children - the onboarding step screens, rendered once this provider is mounted.
 * @param userId - keys the persisted blob per signed-in user when available. Falls back to a
 * single device-local key if no id is supplied — the onboarding flow is only ever reachable
 * while signed in (see (onboarding)/_layout.tsx's guard), so callers should generally pass the
 * session's user id.
 */
export function OnboardingProvider({
  children,
  userId,
}: {
  children: React.ReactNode;
  userId?: string | null;
}) {
  const storageKey = userId ? `${STORAGE_PREFIX}:${userId}` : STORAGE_PREFIX;

  const [answers, setAnswersState] = useState<OnboardingAnswers>(INITIAL_ANSWERS);
  const [consent, setConsentState] = useState<ConsentAnswers>(INITIAL_CONSENT);
  const [currentStep, setCurrentStepState] = useState<number>(1);
  const [restored, setRestored] = useState(false);

  // Guards the persist-effect below from firing (and clobbering AsyncStorage with the initial
  // defaults) before the restore read for the CURRENT storageKey has actually completed.
  const restoredKeyRef = useRef<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setRestored(false);
    AsyncStorage.getItem(storageKey)
      .then((raw) => {
        if (cancelled) return;
        if (raw) {
          const parsed = JSON.parse(raw) as Partial<PersistedProgress>;
          if (parsed.answers) setAnswersState({ ...INITIAL_ANSWERS, ...parsed.answers });
          if (parsed.consent) setConsentState({ ...INITIAL_CONSENT, ...parsed.consent });
          if (typeof parsed.currentStep === "number") setCurrentStepState(parsed.currentStep);
        } else {
          setAnswersState(INITIAL_ANSWERS);
          setConsentState(INITIAL_CONSENT);
          setCurrentStepState(1);
        }
      })
      .catch((e) => {
        logger.warn("onboarding.restore_failed", { detail: e instanceof Error ? e.message : String(e) });
      })
      .finally(() => {
        if (!cancelled) {
          restoredKeyRef.current = storageKey;
          setRestored(true);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [storageKey]);

  // Persist on every change, once the restore for this exact key has completed.
  useEffect(() => {
    if (!restored || restoredKeyRef.current !== storageKey) return;
    const blob: PersistedProgress = { answers, consent, currentStep };
    AsyncStorage.setItem(storageKey, JSON.stringify(blob)).catch((e) => {
      logger.warn("onboarding.persist_failed", { detail: e instanceof Error ? e.message : String(e) });
    });
  }, [answers, consent, currentStep, restored, storageKey]);

  const setAnswers = useCallback((patch: Partial<OnboardingAnswers>) => {
    setAnswersState((prev) => ({ ...prev, ...patch }));
  }, []);

  const setConsent = useCallback((patch: Partial<ConsentAnswers>) => {
    setConsentState((prev) => ({ ...prev, ...patch }));
  }, []);

  const setCurrentStep = useCallback((step: number) => {
    setCurrentStepState(step);
  }, []);

  const reset = useCallback(() => {
    setAnswersState(INITIAL_ANSWERS);
    setConsentState(INITIAL_CONSENT);
    setCurrentStepState(1);
    AsyncStorage.removeItem(storageKey).catch((e) => {
      logger.warn("onboarding.reset_failed", { detail: e instanceof Error ? e.message : String(e) });
    });
  }, [storageKey]);

  const value = useMemo(
    () => ({ answers, setAnswers, consent, setConsent, currentStep, setCurrentStep, restored, reset }),
    [answers, setAnswers, consent, setConsent, currentStep, setCurrentStep, restored, reset],
  );

  return <OnboardingContext.Provider value={value}>{children}</OnboardingContext.Provider>;
}

/**
 * useOnboarding — reads the current answer bag and the setAnswers/reset actions from
 * OnboardingProvider. Every onboarding step screen (step-1..step-5) calls this to read the
 * user's prior answers and patch in new ones as they're made. Throws if called outside the
 * provider, since that indicates a screen was rendered outside the onboarding flow.
 * @returns the current answers, a patch function (`setAnswers`), and a full `reset`.
 */
export function useOnboarding(): OnboardingContextValue {
  const ctx = useContext(OnboardingContext);
  if (!ctx) {
    throw new Error("useOnboarding must be used within an OnboardingProvider");
  }
  return ctx;
}
