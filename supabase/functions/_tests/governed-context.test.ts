import { assertEquals, assertFalse } from "@std/assert";
import { deriveGovernedContextSignals } from "../recommendations/governed-context.ts";
import type { HouseholdRaw } from "../recommendations/compose.ts";

function household(overrides: Partial<HouseholdRaw> = {}): HouseholdRaw {
  return {
    q1_household_type: "couple_kids",
    q2_working_professionals: 2,
    q3_home_state: "MP",
    q4_current_city: "Mumbai",
    q5_diet: "veg",
    q6_nonveg_types: [], q7_veg_days: [], q8_is_jain: false, q9_allergies: [],
    q10_allergy_other: null, q11_conditions: [],
    q12_member_ages: [{ role: "adult", age: 34 }, { role: "adult", age: 33 }, { role: "child", age: 5 }],
    q13_who_cooks: "self", q14_eat_out_per_week: 1, q15_objective: "into_fitness",
    cook_capability: "intermediate",
    ...overrides,
  };
}

Deno.test("explicit health goal and working count retain full authority", () => {
  const signals = deriveGovernedContextSignals(household());
  assertEquals(signals[0], {
    feature_code: "health_objective", value: "into_fitness", authority: "explicit",
    confidence: 1, sources: ["q15_objective"], allowed_use: "strong_rank",
    correction_state: "active", feature_version: "governed-context-v1",
  });
  assertEquals(signals[1].value, 2);
  assertEquals(signals[1].allowed_use, "context_input");
});

Deno.test("time pressure is bounded, expiring-policy inference and never uses geography", () => {
  const signal = deriveGovernedContextSignals(household())[2];
  assertEquals(signal.feature_code, "weekday_time_pressure");
  assertEquals(signal.authority, "inferred");
  assertEquals(signal.confidence, 0.65);
  assertEquals(signal.allowed_use, "soft_rank");
  assertFalse(signal.sources.includes("q3_home_state"));
  assertFalse(signal.sources.includes("q4_current_city"));
  assertEquals(signal.value, 0.85);
});

Deno.test("a teen or child never creates a medical, diet, income, or profession feature", () => {
  const signals = deriveGovernedContextSignals(household({ q2_working_professionals: 0 }));
  assertEquals(signals.map((signal) => signal.feature_code), [
    "health_objective", "working_professionals", "weekday_time_pressure",
  ]);
});
