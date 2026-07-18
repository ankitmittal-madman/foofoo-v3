/**
 * WP-8E integration-layer tests (fakes only; no live DB, no live Supabase).
 *
 * Proves the WP-8E mission: the ONE reusable RE Engine (WP-8D) is shared by all three callers —
 * onboarding orchestrator, /v1/recommendations service, nightly scheduler — and that onboarding
 * orchestrates (persona resolve → invoke engine → persist → return handle) without duplicating any
 * recommendation logic. Every port is an in-memory fake.
 */
import { assertEquals, assertRejects } from "@std/assert";
import { AppError, createLogger } from "../_shared/mod.ts";
import { RecommendationEngine } from "../_shared/services/re/engine.ts";
import type { EngineDeps } from "../_shared/services/re/engine.ts";
import type {
  DishCandidate,
  ScoringConfig,
  WeightLadderTier,
} from "../_shared/services/re/index.ts";
import {
  cityOverlayWeight,
  computeOnboardingConfidence,
  type OnboardingAnswers,
  OnboardingOrchestrator,
  type OnboardingStore,
} from "../_shared/services/onboarding/orchestrator.ts";
import {
  type PlanSlotRow,
  type WeekPlanRow,
  type WeekPlanStore,
} from "../_shared/services/planning/persistence.ts";
import {
  type PlanSlotStore,
  RecommendationService,
  type ReStateStore,
} from "../_shared/services/recommendations/service.ts";
import {
  type EligibleUser,
  NightlyPlanScheduler,
} from "../_shared/services/scheduler/nightly-plan.ts";

// ── engine fakes (compact) ──────────────────────────────────────────────────────────────────────

const LADDER: WeightLadderTier[] = [
  {
    lowerBound: 0,
    upperBound: 0,
    weights: { wCohort: 0.55, wContent: 0.20, wHistory: 0.00, wContext: 0.15, wExplore: 0.10 },
  },
  {
    lowerBound: 150,
    upperBound: 100000,
    weights: { wCohort: 0.05, wContent: 0.15, wHistory: 0.65, wContext: 0.15, wExplore: 0.00 },
  },
];
const CFG: ScoringConfig = {
  notTodayP0: 0.80,
  notTodayLambda: 0.35,
  notTodayDecayThreshold: 0.05,
  personalHistoryLambda: 0.05,
  mmrLambda: 0.70,
  explorationBonusMax: 0.15,
  contextOverrideThreshold: 0.90,
  coldStartExitThreshold: 14,
  neutralCohortPrior: 0.50,
  slateSize: 8,
  minCandidates: 3,
};
function dish(id: string): DishCandidate {
  return {
    dishId: id,
    baseScore: 0.5,
    dietType: "veg",
    isJain: true,
    ingredientAllergenUnion: 0,
    mealOccasions: ["breakfast", "lunch", "dinner", "any"],
    classCode: "BF_LIGHT_GRAIN",
    genomeVector: [1, 0, 0],
    cookTimeBandMinutes: 20,
    seasonalAffinity: [],
    cuisineFamily: "south",
    cookingMethod: "steamed",
    mainIngredientClass: "rice",
    texture: "soft",
    hasNonHalalMeat: false,
    hasBeef: false,
    hasPork: false,
  };
}
function makeEngineDeps(): EngineDeps {
  const cands = [dish("a"), dish("b"), dish("c"), dish("d")];
  return {
    candidates: {
      getClassCandidates: () => Promise.resolve(cands),
      getPopularFallback: () => Promise.resolve(cands),
    },
    neverList: { getActiveNeverDishIds: () => Promise.resolve(new Set<string>()) },
    suppression: { getActiveNotToday: () => Promise.resolve([]) },
    cohortPriors: { getPrior: () => Promise.resolve(null) },
    tasteVectors: {
      getUserTasteVector: () => Promise.resolve(null),
      getCohortAverageVector: () => Promise.resolve([1, 0, 0]),
    },
    personalHistory: { getEvents: () => Promise.resolve([]) },
    bandit: { getBetaParams: () => Promise.resolve({ alpha: 1, beta: 1 }) },
    contextMultipliers: { getMultiplier: () => Promise.resolve(0.5) },
    cohortResolution: {
      assignPersona: () => Promise.resolve({ personaId: "P1", overlayPersonaIds: [] }),
      assignPersonaFallback: () =>
        Promise.resolve({ personaId: "P1", overlayPersonaIds: [], cohortId: "C1" }),
      resolveCohort: () => Promise.resolve("C1"),
      getWeeklyClassPlan: (_c, wsd) =>
        Promise.resolve([{ slotDate: wsd, mealSlot: "breakfast", classCode: "BF_LIGHT_GRAIN" }]),
      getNonVegOverlay: () => Promise.resolve({ weeklySlots: 0, preferredSlots: [] }),
    },
    config: {
      getWeightLadder: () => Promise.resolve(LADDER),
      getScoringConfig: () => Promise.resolve(CFG),
      getVarietyRules: () => Promise.resolve([]),
      getEventWeight: () => Promise.resolve(0),
      getActiveReVersion: () => Promise.resolve("classfirst_v1"),
    },
    rng: { uniform: () => 0.5, normal: () => 0.5 },
  };
}

const ctxFactory = (slotDate: string, mealSlot: "breakfast" | "lunch" | "dinner" | "snack") => ({
  mealSlot,
  slotDate,
  dayType: "weekday" as const,
  weather: "mild" as const,
  isMonsoon: false,
});

// ── fake stores ─────────────────────────────────────────────────────────────────────────────────

function fakeWeekPlanStore() {
  const persisted: Array<{ header: WeekPlanRow; slots: PlanSlotRow[] }> = [];
  const updated: PlanSlotRow[] = [];
  const store: WeekPlanStore = {
    persistWeekPlan: (header, slots) => {
      persisted.push({ header, slots });
      return Promise.resolve({ weekPlanId: "WP1", weekStartDate: header.week_start_date });
    },
    updateSlotSlate: (_wp, slot) => {
      updated.push(slot);
      return Promise.resolve({ slotId: "SLOT1" });
    },
  };
  return { store, persisted, updated };
}

function fakeOnboardingStore(alreadyComplete = false, personalizationGranted = true) {
  const calls: Record<string, unknown[]> = {
    profile: [],
    members: [],
    sessions: [],
    reState: [],
    taste: [],
  };
  const store: OnboardingStore = {
    isPersonalizationGranted: () => Promise.resolve(personalizationGranted),
    isOnboardingComplete: () => Promise.resolve(alreadyComplete),
    persistProfile: (r) => {
      calls.profile.push(r);
      return Promise.resolve();
    },
    persistHouseholdMembers: (_p, m) => {
      calls.members.push(m);
      return Promise.resolve();
    },
    persistOnboardingSessions: (_p, s) => {
      calls.sessions.push(s);
      return Promise.resolve();
    },
    persistUserReState: (r) => {
      calls.reState.push(r);
      return Promise.resolve();
    },
    persistTasteVector: (_p, c) => {
      calls.taste.push(c);
      return Promise.resolve();
    },
  };
  return { store, calls };
}

function answers(over: Partial<OnboardingAnswers> = {}): OnboardingAnswers {
  return {
    mainCohortCode: "MC_NUCLEAR_FAMILY",
    subCohortTag: "SC_WITH_SCHOOL_CHILD",
    members: [{ conditions: ["school_child"], allergenFlags: 0 }],
    homeState: "MH",
    currentCity: "Mumbai",
    migrationBand: "3_7yr",
    dietType: "veg",
    religiousPref: "hindu_veg",
    allergenFlags: 0,
    cookCapability: "intermediate",
    primaryCookName: "Meera",
    pushNotificationTime: "07:00:00",
    classSwipeCount: 8,
    ob07Completed: true,
    skippedScreens: [],
    ...over,
  };
}

// ── onboarding orchestration ──────────────────────────────────────────────────────────────────

Deno.test("onboarding — orchestrates engine, persists plan, returns §06.2 handle", async () => {
  const engine = new RecommendationEngine(makeEngineDeps());
  const ob = fakeOnboardingStore();
  const wp = fakeWeekPlanStore();
  const orch = new OnboardingOrchestrator(
    ob.store,
    makeEngineDeps().cohortResolution,
    engine,
    wp.store,
    "classfirst_v1",
    "DIN_NON_VEG_MAIN",
  );

  const res = await orch.completeOnboarding("u1", answers(), "2026-07-20", ctxFactory);

  assertEquals(res.profile_id, "u1");
  assertEquals(res.onboarding_completed, true);
  assertEquals(res.cold_start_mode, true);
  assertEquals(res.first_week_plan.week_plan_id, "WP1");
  assertEquals(res.first_week_plan.week_start_date, "2026-07-20");
  // plan was persisted exactly once, via the store (engine generated it)
  assertEquals(wp.persisted.length, 1);
  assertEquals(wp.persisted[0].slots.length, 1); // 1 primary slot from the fake weekly plan
  // onboarding persisted its OWN writes with onboarding_completed=true
  assertEquals(
    (ob.calls.profile[0] as { onboarding_completed: boolean }).onboarding_completed,
    true,
  );
  assertEquals(ob.calls.reState.length, 1);
});

Deno.test("onboarding — Jain diet forces jain religious pref (LF-A04)", async () => {
  const engine = new RecommendationEngine(makeEngineDeps());
  const ob = fakeOnboardingStore();
  const wp = fakeWeekPlanStore();
  const orch = new OnboardingOrchestrator(
    ob.store,
    makeEngineDeps().cohortResolution,
    engine,
    wp.store,
    "classfirst_v1",
    "DIN_NON_VEG_MAIN",
  );
  await orch.completeOnboarding(
    "u2",
    answers({ dietType: "jain", religiousPref: "all" }),
    "2026-07-20",
    ctxFactory,
  );
  assertEquals((ob.calls.profile[0] as { religious_pref: string }).religious_pref, "jain");
});

Deno.test("onboarding — idempotent: already-complete profile → 409 ERR_ONBOARDING_ALREADY_COMPLETE", async () => {
  const engine = new RecommendationEngine(makeEngineDeps());
  const ob = fakeOnboardingStore(/* alreadyComplete */ true);
  const wp = fakeWeekPlanStore();
  const orch = new OnboardingOrchestrator(
    ob.store,
    makeEngineDeps().cohortResolution,
    engine,
    wp.store,
    "classfirst_v1",
    "DIN_NON_VEG_MAIN",
  );
  const e = await assertRejects(
    () => orch.completeOnboarding("u3", answers(), "2026-07-20", ctxFactory),
    AppError,
  );
  assertEquals(e.httpStatus, 409);
  assertEquals(wp.persisted.length, 0); // no plan generated on the idempotent short-circuit
});

Deno.test("onboarding — personalization consent not granted → 403 ERR_CONSENT_REQUIRED", async () => {
  const engine = new RecommendationEngine(makeEngineDeps());
  const ob = fakeOnboardingStore(false, /* personalizationGranted */ false);
  const wp = fakeWeekPlanStore();
  const orch = new OnboardingOrchestrator(
    ob.store,
    makeEngineDeps().cohortResolution,
    engine,
    wp.store,
    "classfirst_v1",
    "DIN_NON_VEG_MAIN",
  );
  const e = await assertRejects(
    () => orch.completeOnboarding("u4", answers(), "2026-07-20", ctxFactory),
    AppError,
  );
  assertEquals(e.httpStatus, 403);
  assertEquals(wp.persisted.length, 0);
});

Deno.test("computeOnboardingConfidence — full answers ~0.65; all-skipped floor 0.35", () => {
  const full = computeOnboardingConfidence(answers());
  assertEquals(full >= 0.60 && full <= 0.65, true);
  const none = computeOnboardingConfidence(answers({
    homeState: null,
    currentCity: null,
    migrationBand: null,
    dietType: null,
    cookCapability: null,
    ob07Completed: false,
    classSwipeCount: 0,
  }));
  assertEquals(none, 0.35);
});

Deno.test("cityOverlayWeight — matches LF-A03 bands", () => {
  assertEquals(cityOverlayWeight("native"), 0.0);
  assertEquals(cityOverlayWeight("3_7yr"), 0.50);
  assertEquals(cityOverlayWeight("7plus_yr"), 0.70);
  assertEquals(cityOverlayWeight(null), 0.50);
});

// ── recommendations service ─────────────────────────────────────────────────────────────────────

function reStateStore(): ReStateStore {
  return {
    loadUser: (profileId) =>
      Promise.resolve({
        user: {
          profileId,
          personaId: "P1",
          overlayPersonaIds: [],
          cohortId: "C1",
          confidenceScore: 0.58,
          coldStartMode: true,
          interactionCount: 0,
          reEngineVersion: "classfirst_v1",
        },
        constraints: {
          profileId,
          dietType: "veg",
          religiousPref: "all",
          allergenFlags: 0,
          cookCapability: "intermediate",
          homeState: "MH",
        },
        members: [],
      }),
  };
}

Deno.test("recommendations — reuses engine, persists fresh slate, returns §06.4 dishes with score", async () => {
  const engine = new RecommendationEngine(makeEngineDeps());
  const wp = fakeWeekPlanStore();
  const planSlots: PlanSlotStore = {
    getSlotClass: () => Promise.resolve({ weekPlanId: "WP1", classCode: "BF_LIGHT_GRAIN" }),
  };
  const svc = new RecommendationService(reStateStore(), planSlots, engine, wp.store);
  const res = await svc.recommend({
    userId: "u1",
    mealSlot: "breakfast",
    date: "2026-07-20",
    context: ctxFactory("2026-07-20", "breakfast"),
    excludeDishIds: ["a"],
  });
  assertEquals(res.class_code, "BF_LIGHT_GRAIN");
  assertEquals(res.re_version, "classfirst_v1");
  assertEquals(res.dishes.length >= 3, true);
  assertEquals(res.dishes[0].rank, 1);
  assertEquals(typeof res.dishes[0].score, "number");
  assertEquals(res.dishes.some((d) => d.dish_id === "a"), false); // excluded dish absent
  assertEquals(wp.updated.length, 1); // slate persisted to the slot
});

Deno.test("recommendations — no existing slot → ERR_PLAN_NOT_FOUND (404)", async () => {
  const engine = new RecommendationEngine(makeEngineDeps());
  const wp = fakeWeekPlanStore();
  const planSlots: PlanSlotStore = { getSlotClass: () => Promise.resolve(null) };
  const svc = new RecommendationService(reStateStore(), planSlots, engine, wp.store);
  const e = await assertRejects(
    () =>
      svc.recommend({
        userId: "u1",
        mealSlot: "breakfast",
        date: "2026-07-20",
        context: ctxFactory("2026-07-20", "breakfast"),
        excludeDishIds: [],
      }),
    AppError,
  );
  assertEquals(e.httpStatus, 404);
});

// ── nightly scheduler ───────────────────────────────────────────────────────────────────────────

Deno.test("scheduler — reuses engine for every eligible user, persists each, isolates failures", async () => {
  const engine = new RecommendationEngine(makeEngineDeps());
  const wp = fakeWeekPlanStore();
  const eligible: EligibleUser[] = ["u1", "u2"].map((id) => ({
    user: {
      profileId: id,
      personaId: "P1",
      overlayPersonaIds: [],
      cohortId: "C1",
      confidenceScore: 0.58,
      coldStartMode: true,
      interactionCount: 0,
      reEngineVersion: "classfirst_v1",
    },
    constraints: {
      profileId: id,
      dietType: "veg",
      religiousPref: "all",
      allergenFlags: 0,
      cookCapability: "intermediate",
      homeState: "MH",
    },
    members: [],
    weekStartDate: "2026-07-27",
  }));
  const scheduler = new NightlyPlanScheduler(
    { getEligibleUsers: () => Promise.resolve(eligible) },
    engine,
    wp.store,
    createLogger("error"),
    "DIN_NON_VEG_MAIN",
    ctxFactory,
  );
  const result = await scheduler.run();
  assertEquals(result.processed, 2);
  assertEquals(result.succeeded, 2);
  assertEquals(result.failed, 0);
  assertEquals(wp.persisted.length, 2); // one week plan persisted per user, same engine
});

Deno.test("scheduler — a single user's failure does not abort the batch", async () => {
  const deps = makeEngineDeps();
  // Make the engine throw for the second user by failing the candidate load once.
  let calls = 0;
  deps.candidates.getClassCandidates = () => {
    calls++;
    if (calls === 2) return Promise.reject(new Error("boom"));
    return Promise.resolve([dish("a"), dish("b"), dish("c")]);
  };
  const engine = new RecommendationEngine(deps);
  const wp = fakeWeekPlanStore();
  const eligible: EligibleUser[] = ["u1", "u2"].map((id) => ({
    user: {
      profileId: id,
      personaId: "P1",
      overlayPersonaIds: [],
      cohortId: "C1",
      confidenceScore: 0.58,
      coldStartMode: true,
      interactionCount: 0,
      reEngineVersion: "classfirst_v1",
    },
    constraints: {
      profileId: id,
      dietType: "veg",
      religiousPref: "all",
      allergenFlags: 0,
      cookCapability: "intermediate",
      homeState: "MH",
    },
    members: [],
    weekStartDate: "2026-07-27",
  }));
  const scheduler = new NightlyPlanScheduler(
    { getEligibleUsers: () => Promise.resolve(eligible) },
    engine,
    wp.store,
    createLogger("error"),
    "DIN_NON_VEG_MAIN",
    ctxFactory,
  );
  const result = await scheduler.run();
  assertEquals(result.processed, 2);
  assertEquals(result.succeeded, 1);
  assertEquals(result.failed, 1);
});
