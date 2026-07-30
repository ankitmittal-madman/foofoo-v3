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
 */
import React, { createContext, useCallback, useContext, useMemo, useState } from "react";

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

export function isSplitAgeHousehold(household: HouseholdType | null): boolean {
  return household != null && SPLIT_AGE_HOUSEHOLDS.includes(household);
}

type OnboardingContextValue = {
  answers: OnboardingAnswers;
  setAnswers: (patch: Partial<OnboardingAnswers>) => void;
  reset: () => void;
};

const OnboardingContext = createContext<OnboardingContextValue | null>(null);

export function OnboardingProvider({ children }: { children: React.ReactNode }) {
  const [answers, setAnswersState] = useState<OnboardingAnswers>(INITIAL_ANSWERS);

  const setAnswers = useCallback((patch: Partial<OnboardingAnswers>) => {
    setAnswersState((prev) => ({ ...prev, ...patch }));
  }, []);

  const reset = useCallback(() => setAnswersState(INITIAL_ANSWERS), []);

  const value = useMemo(() => ({ answers, setAnswers, reset }), [answers, setAnswers, reset]);

  return <OnboardingContext.Provider value={value}>{children}</OnboardingContext.Provider>;
}

export function useOnboarding(): OnboardingContextValue {
  const ctx = useContext(OnboardingContext);
  if (!ctx) {
    throw new Error("useOnboarding must be used within an OnboardingProvider");
  }
  return ctx;
}
