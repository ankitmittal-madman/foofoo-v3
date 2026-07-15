/**
 * WP-8D Recommendation Engine core tests.
 *
 * Unit tests for the pure algorithm functions (constraints §06, scoring §07, variety §08, safety
 * §10) plus fake-repository integration tests for the RecommendationEngine orchestrator (§02
 * pipeline). No live DB and no live RE dependency — every port is an in-memory fake (the WP-8D
 * "integration tests (fakes)" requirement). Config fakes carry the exact DOC-P3-03 §16 values.
 */
import { assertAlmostEquals, assertEquals, assertFalse } from "@std/assert";
import {
  applyHardConstraints,
  applyMmr,
  checkPlanningRoleGate,
  checkVarietyWindow,
  cohortPrior,
  combinedAllergenFlags,
  contentMatch,
  contextFit,
  explorationBonus,
  finalScore,
  interpolateWeightLadder,
  notTodayPenalty,
  passesAllergen,
  passesDietType,
  passesReligious,
  personalHistory,
  RecommendationEngine,
  resolvePersonaAndCohort,
  runSafetyGates,
  updateBanditParams,
  varietySimilarity,
} from "../_shared/services/re/index.ts";
import type {
  DishCandidate,
  ScoredCandidate,
  ScoringConfig,
  WeightLadderTier,
} from "../_shared/services/re/index.ts";
import type { EngineDeps } from "../_shared/services/re/engine.ts";
import type { CohortResolutionRepository, Random } from "../_shared/services/re/ports.ts";

// ── Fixtures ────────────────────────────────────────────────────────────────────────────────────

const LADDER: WeightLadderTier[] = [
  {
    lowerBound: 0,
    upperBound: 0,
    weights: { wCohort: 0.55, wContent: 0.20, wHistory: 0.00, wContext: 0.15, wExplore: 0.10 },
  },
  {
    lowerBound: 1,
    upperBound: 10,
    weights: { wCohort: 0.35, wContent: 0.25, wHistory: 0.15, wContext: 0.15, wExplore: 0.10 },
  },
  {
    lowerBound: 11,
    upperBound: 50,
    weights: { wCohort: 0.20, wContent: 0.25, wHistory: 0.35, wContext: 0.15, wExplore: 0.05 },
  },
  {
    lowerBound: 51,
    upperBound: 150,
    weights: { wCohort: 0.10, wContent: 0.20, wHistory: 0.50, wContext: 0.15, wExplore: 0.05 },
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

const EVENT_WEIGHTS: Record<string, number> = {
  dish_cooked: 0.80,
  dish_locked: 0.60,
  dish_accepted: 0.40,
  dish_swiped_past: -0.10,
  "dish_rated|5": 0.60,
  "dish_rated|3": 0.00,
  "dish_rated|1": -0.30,
};
const eventWeightOf = (t: string, r: number | null) =>
  t === "dish_rated" ? EVENT_WEIGHTS[`dish_rated|${r}`] ?? 0 : EVENT_WEIGHTS[t] ?? 0;

const fixedRng: Random = { uniform: () => 0.5, normal: () => 0.5 };

function dish(over: Partial<DishCandidate> = {}): DishCandidate {
  return {
    dishId: over.dishId ?? "d1",
    baseScore: over.baseScore ?? 0.5,
    dietType: over.dietType ?? "veg",
    isJain: over.isJain ?? true,
    ingredientAllergenUnion: over.ingredientAllergenUnion ?? 0,
    mealOccasions: over.mealOccasions ?? ["breakfast", "any"],
    classCode: over.classCode ?? "BF_LIGHT_GRAIN",
    genomeVector: over.genomeVector ?? [1, 0, 0],
    cookTimeBandMinutes: over.cookTimeBandMinutes ?? 20,
    seasonalAffinity: over.seasonalAffinity ?? [],
    cuisineFamily: over.cuisineFamily ?? "south",
    cookingMethod: over.cookingMethod ?? "steamed",
    mainIngredientClass: over.mainIngredientClass ?? "rice",
    texture: over.texture ?? "soft",
    hasNonHalalMeat: over.hasNonHalalMeat ?? false,
    hasBeef: over.hasBeef ?? false,
    hasPork: over.hasPork ?? false,
  };
}

// ── §06 hard constraints ────────────────────────────────────────────────────────────────────────

Deno.test("passesDietType — veg excludes non_veg/egg dishes", () => {
  assertEquals(passesDietType(dish({ dietType: "veg" }), "veg"), true);
  assertEquals(passesDietType(dish({ dietType: "non_veg" }), "veg"), false);
  assertEquals(passesDietType(dish({ dietType: "egg" }), "veg"), false);
});

Deno.test("passesDietType — non_veg admits all; jain requires is_jain", () => {
  assertEquals(passesDietType(dish({ dietType: "non_veg" }), "non_veg"), true);
  assertEquals(passesDietType(dish({ isJain: false }), "jain"), false);
  assertEquals(passesDietType(dish({ isJain: true, dietType: "veg" }), "jain"), true);
});

Deno.test("passesAllergen — ingredient-level bitwise overlap excludes", () => {
  // nut=1, dairy=2. Household avoids nuts (1). Dish with dairy(2) OK; dish with nut(1) excluded.
  assertEquals(passesAllergen(dish({ ingredientAllergenUnion: 2 }), 1), true);
  assertEquals(passesAllergen(dish({ ingredientAllergenUnion: 3 }), 1), false);
});

Deno.test("combinedAllergenFlags — OR of user + active members only", () => {
  const flags = combinedAllergenFlags(1, [
    { segment: "TODDLER", allergenFlags: 2, isActive: true },
    { segment: "X", allergenFlags: 4, isActive: false },
  ]);
  assertEquals(flags, 3); // 1 | 2 ; inactive member's 4 ignored
});

Deno.test("passesReligious — halal excludes non-halal meat; no_beef excludes beef", () => {
  assertEquals(passesReligious(dish({ hasNonHalalMeat: true }), "halal"), false);
  assertEquals(passesReligious(dish({ hasBeef: true }), "no_beef"), false);
  assertEquals(passesReligious(dish(), "all"), true);
});

Deno.test("applyHardConstraints — a nut-allergen dish is removed for a veg+nut-free household", () => {
  const pool = [
    dish({ dishId: "ok", dietType: "veg", ingredientAllergenUnion: 0 }),
    dish({ dishId: "nutty", dietType: "veg", ingredientAllergenUnion: 1 }),
    dish({ dishId: "meat", dietType: "non_veg", ingredientAllergenUnion: 0 }),
  ];
  const survivors = applyHardConstraints(pool, {
    dietType: "veg",
    religiousPref: "all",
    combinedAllergenFlags: 1,
    mealSlot: "breakfast",
    activeNeverIds: new Set<string>(),
  });
  assertEquals(survivors.map((s) => s.dishId), ["ok"]);
});

Deno.test("applyHardConstraints — never-listed dish is excluded", () => {
  const pool = [dish({ dishId: "a" }), dish({ dishId: "b" })];
  const survivors = applyHardConstraints(pool, {
    dietType: "veg",
    religiousPref: "all",
    combinedAllergenFlags: 0,
    mealSlot: "breakfast",
    activeNeverIds: new Set(["a"]),
  });
  assertEquals(survivors.map((s) => s.dishId), ["b"]);
});

// ── §07 scoring ─────────────────────────────────────────────────────────────────────────────────

Deno.test("interpolateWeightLadder — endpoints return exact tier weights", () => {
  assertEquals(interpolateWeightLadder(0, LADDER).wCohort, 0.55);
  assertEquals(interpolateWeightLadder(200, LADDER).wHistory, 0.65);
});

Deno.test("interpolateWeightLadder — interpolated weights stay a partition of unity", () => {
  for (const count of [5, 25, 100]) {
    const w = interpolateWeightLadder(count, LADDER);
    const sum = w.wCohort + w.wContent + w.wHistory + w.wContext + w.wExplore;
    assertAlmostEquals(sum, 1.0, 1e-9);
    for (const v of Object.values(w)) {
      assertEquals(v >= 0 && v <= 1, true);
    }
  }
});

Deno.test("cohortPrior — null (unseeded re_cohort_class_priors) falls back to neutral 0.50", () => {
  assertEquals(cohortPrior(null, CFG), 0.50);
  assertEquals(cohortPrior(0.82, CFG), 0.82);
});

Deno.test("contentMatch — cosine of identical direction = 1, orthogonal = 0", () => {
  assertAlmostEquals(contentMatch([1, 2, 2], [2, 4, 4]), 1.0, 1e-9);
  assertAlmostEquals(contentMatch([1, 0], [0, 1]), 0.0, 1e-9);
});

Deno.test("personalHistory — decays with elapsed days; positive events raise, swipes lower", () => {
  const recent = personalHistory(
    [{ eventType: "dish_cooked", rating: null, daysElapsed: 0 }],
    eventWeightOf,
    CFG,
  );
  const old = personalHistory(
    [{ eventType: "dish_cooked", rating: null, daysElapsed: 60 }],
    eventWeightOf,
    CFG,
  );
  assertAlmostEquals(recent, 0.80, 1e-9);
  assertEquals(old < recent && old > 0, true); // ~5% retained at 60d
  const neg = personalHistory(
    [{ eventType: "dish_swiped_past", rating: null, daysElapsed: 0 }],
    eventWeightOf,
    CFG,
  );
  assertAlmostEquals(neg, -0.10, 1e-9);
});

Deno.test("notTodayPenalty — 0.80 at day 0, ~0 past day 7, halved on strong-context override", () => {
  assertAlmostEquals(notTodayPenalty(0, 0.0, CFG), 0.80, 1e-9);
  assertEquals(notTodayPenalty(8, 0.0, CFG), 0); // below decay threshold → expired
  const day4 = notTodayPenalty(4, 0.0, CFG);
  const day4override = notTodayPenalty(4, 0.95, CFG);
  assertAlmostEquals(day4override, day4 * 0.5, 1e-9);
});

Deno.test("finalScore — weighted signal sum minus penalty", () => {
  const w = { wCohort: 0.5, wContent: 0.2, wHistory: 0.1, wContext: 0.1, wExplore: 0.1 };
  const s = finalScore(w, {
    cohortPrior: 1,
    contentMatch: 1,
    personalHistory: 1,
    contextFit: 1,
    explorationBonus: 1,
    penalty: 0.3,
  });
  assertAlmostEquals(s, 1.0 - 0.3, 1e-9);
});

Deno.test("contextFit — clamped to 1.2; weekday adds cook-time boost", () => {
  assertAlmostEquals(contextFit(dish({ cookTimeBandMinutes: 20 }), [0.6], "weekday"), 0.7, 1e-9);
  assertEquals(contextFit(dish(), [1.0, 0.9], "weekend") <= 1.2, true);
});

Deno.test("explorationBonus — bounded to [0, exploration_bonus_max]", () => {
  const eb = explorationBonus(1, 1, CFG, fixedRng);
  assertEquals(eb >= 0 && eb <= CFG.explorationBonusMax, true);
});

Deno.test("updateBanditParams — accepts raise alpha, rejections raise beta", () => {
  assertEquals(updateBanditParams(1, 1, "dish_cooked"), { alpha: 2, beta: 1 });
  assertEquals(updateBanditParams(1, 1, "dish_not_today"), { alpha: 1, beta: 2 });
  assertEquals(updateBanditParams(1, 1, "plan_opened"), { alpha: 1, beta: 1 });
});

// ── §08 variety ─────────────────────────────────────────────────────────────────────────────────

Deno.test("varietySimilarity — identical dimensions = 1, all-different = 0", () => {
  const a: ScoredCandidate = { candidate: dish(), score: 1, signals: zeroSignals() };
  const b: ScoredCandidate = {
    candidate: dish({
      cuisineFamily: "north",
      cookingMethod: "fried",
      mainIngredientClass: "wheat",
      texture: "crisp",
    }),
    score: 1,
    signals: zeroSignals(),
  };
  assertEquals(varietySimilarity(a, a), 1);
  assertEquals(varietySimilarity(a, b), 0);
});

Deno.test("applyMmr — prefers a diverse dish over a near-duplicate of higher raw score", () => {
  const head: ScoredCandidate = {
    candidate: dish({ dishId: "head" }),
    score: 1.0,
    signals: zeroSignals(),
  };
  const dup: ScoredCandidate = {
    candidate: dish({ dishId: "dup" }),
    score: 0.95,
    signals: zeroSignals(),
  }; // same dims → sim 1
  const diverse: ScoredCandidate = {
    candidate: dish({
      dishId: "div",
      cuisineFamily: "north",
      cookingMethod: "fried",
      mainIngredientClass: "wheat",
      texture: "crisp",
    }),
    score: 0.9,
    signals: zeroSignals(),
  };
  const slate = applyMmr([head, dup, diverse], 0.7, 2);
  assertEquals(slate[0].candidate.dishId, "head");
  assertEquals(slate[1].candidate.dishId, "div"); // diverse beats higher-scoring duplicate
});

Deno.test("checkVarietyWindow — flags fried over cap and exact dish repeat", () => {
  const rules = [
    { ruleName: "fried_method", windowDays: 7, capValue: 3, overrideCondition: "monsoon" },
    { ruleName: "same_dish", windowDays: 30, capValue: 1, overrideCondition: null },
  ];
  const fried = (id: string) => ({
    slotDate: id,
    mealSlot: "lunch",
    cuisineFamily: "x",
    cookingMethod: "fried",
    mainIngredientClass: "y",
    dishId: id,
  });
  const v = checkVarietyWindow([fried("1"), fried("2"), fried("3"), fried("4")], rules, false);
  assertEquals(v.some((x) => x.ruleName === "fried_method"), true);
  const repeat = checkVarietyWindow(
    [{
      slotDate: "1",
      mealSlot: "lunch",
      cuisineFamily: "x",
      cookingMethod: "steamed",
      mainIngredientClass: "y",
      dishId: "same",
    }, {
      slotDate: "2",
      mealSlot: "dinner",
      cuisineFamily: "x",
      cookingMethod: "steamed",
      mainIngredientClass: "z",
      dishId: "same",
    }],
    rules,
    false,
  );
  assertEquals(repeat.some((x) => x.ruleName === "same_dish"), true);
});

Deno.test("checkVarietyWindow — monsoon override raises the fried cap to 4", () => {
  const rules = [{
    ruleName: "fried_method",
    windowDays: 7,
    capValue: 3,
    overrideCondition: "monsoon",
  }];
  const fried = (id: string) => ({
    slotDate: id,
    mealSlot: "lunch",
    cuisineFamily: "x",
    cookingMethod: "fried",
    mainIngredientClass: "y",
    dishId: id,
  });
  assertEquals(
    checkVarietyWindow([fried("1"), fried("2"), fried("3"), fried("4")], rules, true).length,
    0,
  );
});

// ── §10 safety gates ────────────────────────────────────────────────────────────────────────────

Deno.test("runSafetyGates — flags a diet, allergen, and jain violation", () => {
  const p = { dietType: "jain" as const, religiousPref: "jain" as const, combinedAllergenFlags: 1 };
  const v = runSafetyGates([
    dish({ dishId: "ok", isJain: true, dietType: "veg", ingredientAllergenUnion: 0 }),
    dish({ dishId: "nonjain", isJain: false, dietType: "veg" }),
    dish({ dishId: "nut", isJain: true, ingredientAllergenUnion: 1 }),
  ], p);
  assertEquals(v.some((x) => x.gate === "jain" && x.dishId === "nonjain"), true);
  assertEquals(v.some((x) => x.gate === "diet" && x.dishId === "nonjain"), true);
  assertEquals(v.some((x) => x.gate === "allergen" && x.dishId === "nut"), true);
  assertFalse(v.some((x) => x.dishId === "ok"));
});

Deno.test("checkPlanningRoleGate — flags a non-MAIN_PRIMARY class in a primary slot", () => {
  const v = checkPlanningRoleGate([
    { classCode: "BF_LIGHT_GRAIN", planningRole: "MAIN_PRIMARY", isAddon: false },
    { classCode: "ADDON_INFANT", planningRole: "ADDON", isAddon: true },
    { classCode: "SIDE_ONLY", planningRole: "SIDE", isAddon: false },
  ]);
  assertEquals(v.length, 1);
  assertEquals(v[0].dishId, "SIDE_ONLY");
});

// ── resolvers ─────────────────────────────────────────────────────────────────────────────────

Deno.test("resolvePersonaAndCohort — Option-B fallback when no assignment rule matches", async () => {
  const repo: CohortResolutionRepository = {
    assignPersona: () => Promise.resolve(null),
    assignPersonaFallback: () =>
      Promise.resolve({ personaId: "P_FB", overlayPersonaIds: [], cohortId: "C_FB" }),
    resolveCohort: () => Promise.resolve(null),
    getWeeklyClassPlan: () => Promise.resolve([]),
    getNonVegOverlay: () => Promise.resolve({ weeklySlots: 0, preferredSlots: [] }),
  };
  const r = await resolvePersonaAndCohort(repo, {
    mainCohortCode: "MC_SOLO",
    subCohortTag: "SC_SOLO_STANDARD",
    homeState: "MH",
    dietType: "veg",
    dietMode: "veg",
  });
  assertEquals(r.fallbackApplied, true);
  assertEquals(r.personaId, "P_FB");
  assertEquals(r.cohortId, "C_FB");
});

// ── engine integration (fakes) ──────────────────────────────────────────────────────────────────

function zeroSignals() {
  return {
    cohortPrior: 0,
    contentMatch: 0,
    personalHistory: 0,
    contextFit: 0,
    explorationBonus: 0,
    penalty: 0,
  };
}

function makeDeps(candidates: DishCandidate[], priorNull = true): EngineDeps {
  return {
    candidates: {
      getClassCandidates: () => Promise.resolve(candidates),
      getPopularFallback: (dietType) =>
        Promise.resolve(
          candidates.filter((c) => c.dietType === dietType || dietType === "non_veg"),
        ),
    },
    neverList: { getActiveNeverDishIds: () => Promise.resolve(new Set<string>()) },
    suppression: { getActiveNotToday: () => Promise.resolve([]) },
    cohortPriors: { getPrior: () => Promise.resolve(priorNull ? null : 0.7) },
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
      getEventWeight: (t, r) => Promise.resolve(eventWeightOf(t, r)),
      getActiveReVersion: () => Promise.resolve("classfirst_v1"),
    },
    rng: fixedRng,
  };
}

const USER = {
  profileId: "u1",
  personaId: "P1",
  overlayPersonaIds: [],
  cohortId: "C1",
  confidenceScore: 0.58,
  coldStartMode: true,
  interactionCount: 0,
  reEngineVersion: "classfirst_v1",
};
const CONSTRAINTS = {
  profileId: "u1",
  dietType: "veg" as const,
  religiousPref: "all" as const,
  allergenFlags: 0,
  cookCapability: "intermediate" as const,
  homeState: "MH",
};
const CTX = {
  mealSlot: "breakfast" as const,
  slotDate: "2026-07-20",
  dayType: "weekday" as const,
  weather: "rainy" as const,
  isMonsoon: true,
};

Deno.test("engine.generateSlate — returns a safe, non-empty, correctly-sized slate", async () => {
  const cands = [
    dish({ dishId: "a", dietType: "veg", cuisineFamily: "south" }),
    dish({
      dishId: "b",
      dietType: "veg",
      cuisineFamily: "north",
      cookingMethod: "fried",
      mainIngredientClass: "wheat",
    }),
    dish({ dishId: "c", dietType: "veg", cuisineFamily: "east", texture: "crisp" }),
    dish({ dishId: "meat", dietType: "non_veg" }), // must be filtered out for veg household
  ];
  const engine = new RecommendationEngine(makeDeps(cands));
  const slate = await engine.generateSlate({
    user: USER,
    constraints: CONSTRAINTS,
    members: [],
    context: CTX,
    classCode: "BF_LIGHT_GRAIN",
  });
  assertEquals(slate.dishIds.includes("meat"), false);
  assertEquals(slate.dishIds.length >= 3, true);
  assertEquals(slate.reVersion, "classfirst_v1");
  assertEquals(slate.coldStartMode, true);
  // every returned dish is diet-safe
  const gates = runSafetyGates(cands.filter((c) => slate.dishIds.includes(c.dishId)), {
    dietType: "veg",
    religiousPref: "all",
    combinedAllergenFlags: 0,
  });
  assertEquals(gates.length, 0);
});

Deno.test("engine.generateSlate — unseeded cohort prior does not crash (neutral fallback path)", async () => {
  const cands = [dish({ dishId: "a" }), dish({ dishId: "b" }), dish({ dishId: "c" })];
  const engine = new RecommendationEngine(makeDeps(cands, /* priorNull */ true));
  const slate = await engine.generateSlate({
    user: USER,
    constraints: CONSTRAINTS,
    members: [],
    context: CTX,
    classCode: "BF_LIGHT_GRAIN",
  });
  assertEquals(slate.dishIds.length, 3);
});

Deno.test("engine.generateSlate — falls back to popular dishes when <3 candidates survive (LF-D07)", async () => {
  // Only 1 in-class candidate survives; popular fallback (same list, diet-filtered) fills the slate.
  const cands = [
    dish({ dishId: "only", dietType: "veg" }),
    dish({ dishId: "p2", dietType: "veg" }),
    dish({ dishId: "p3", dietType: "veg" }),
  ];
  const deps = makeDeps(cands);
  // class query returns just 1; popular fallback returns all 3
  deps.candidates.getClassCandidates = () => Promise.resolve([cands[0]]);
  const engine = new RecommendationEngine(deps);
  const slate = await engine.generateSlate({
    user: USER,
    constraints: CONSTRAINTS,
    members: [],
    context: CTX,
    classCode: "BF_LIGHT_GRAIN",
  });
  assertEquals(slate.fallbackUsed, true);
  assertEquals(slate.dishIds.length, 3);
});

Deno.test("engine.generateWeekPlan — produces one slate per class assignment", async () => {
  const cands = [dish({ dishId: "a" }), dish({ dishId: "b" }), dish({ dishId: "c" })];
  const engine = new RecommendationEngine(makeDeps(cands));
  const plan = await engine.generateWeekPlan(
    USER,
    CONSTRAINTS,
    [],
    "2026-07-20",
    (slotDate, mealSlot) => ({
      mealSlot,
      slotDate,
      dayType: "weekday",
      weather: "mild",
      isMonsoon: false,
    }),
    { nonVegMainClass: "DIN_NON_VEG_MAIN" },
  );
  assertEquals(plan.slots.length, 1);
  assertEquals(plan.slots[0].mealSlot, "breakfast");
  assertEquals(plan.weekStartDate, "2026-07-20");
});
