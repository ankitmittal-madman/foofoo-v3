/**
 * OnboardingAnswers -> POST /v1/household screens[] — the field-name/vocabulary mapping this
 * repo's own backend actually expects (household/schema.ts), NOT scareme21-create/NewFoo's
 * ghar_api/app/onboarding.py shape (that source repo's toProfile.ts targets a different service
 * entirely and was not reusable — see docs/architecture DOC-P4-03 §3/§4 addendum).
 *
 * Every mapping below was checked against schema.ts's HOUSEHOLD_ANSWERS_SCHEMAS/PROFILE_SCHEMAS,
 * not assumed from the source repo's own naming.
 */
import type { ScreenAnswer, MemberWrite } from "@/api/types";
import type { OnboardingAnswers } from "./OnboardingContext";

// Source's 'eggetarian' UI token has no matching value in our profiles.diet_type CHECK
// constraint (veg/non_veg/egg/vegan/jain) — 'egg' is the equivalent.
const DIET_MAP: Record<string, string> = {
  veg: "veg",
  eggetarian: "egg",
  non_veg: "non_veg",
  jain: "jain",
  vegan: "vegan",
};

// Source's 'order_in' has no match in q13_who_cooks's CHECK constraint (self/family/
// hired_cook/order_tiffin) — 'order_tiffin' is the equivalent.
const WHO_COOKS_MAP: Record<string, string> = {
  self: "self",
  family: "family",
  hired_cook: "hired_cook",
  order_in: "order_tiffin",
};

// Source derived a fractional eat_out_per_week (e.g. 0.5); q14_eat_out_per_week is
// z.number().int().min(0) — integers only, so cadence maps straight to a whole number.
const EAT_OUT_PER_WEEK: Record<string, number> = {
  rarely: 0,
  weekly: 1,
  few_weekly: 3,
  daily: 7,
};

const OBJECTIVE_MAP: Record<string, string> = {
  tasty: "awesome_taste",
  healthy: "healthy_living",
  discover: "awesome_taste", // source's collect-only wants_discovery flag has no destination here
  into_fitness: "into_fitness",
};

// compose.ts's ALLERGEN_BITS (the frozen 7-bit model) — 'others' has no bit; it is
// collect-only, carried through allergensOther/q10_allergy_other instead.
const ALLERGEN_BITS: Record<string, number> = {
  peanuts: 1, // the live catalogue's plural spelling maps to the engine's 'nuts' bit
  dairy: 2,
  gluten: 4,
  shellfish: 8,
  soy: 32,
  sesame: 64,
};

/**
 * allergenFlags — packs the user's selected allergen chips into the single bitmask integer
 * profiles.allergen_flags expects (ALLERGEN_BITS above), OR-ing together each selected
 * allergen's bit. Any allergen not in ALLERGEN_BITS (currently just "others", which is
 * collect-only and carried separately as free text) contributes no bit.
 * @param allergens - the allergen chip values the user selected on Screen 4 (e.g. ["dairy", "soy"]).
 * @returns the combined bitmask to send as profiles.allergen_flags.
 */
function allergenFlags(allergens: string[]): number {
  return allergens.reduce((bits, a) => bits | (ALLERGEN_BITS[a] ?? 0), 0);
}

// Age token -> household_members.conditions (MEMBER_CONDITIONS vocab, household/schema.ts).
// A lossy but honest approximation: source's age RANGES don't map 1:1 onto our per-member
// CONDITION flags, so only the bands with a clear condition equivalent produce a member row.
const AGE_TO_CONDITION: Record<string, string> = {
  "0-2": "baby_6_18m",
  "2-5": "toddler",
  "5-12": "school_child",
  "12-18": "teen_high_appetite",
  "60+": "elderly_member",
};

export interface HouseholdWritePayload {
  screens: ScreenAnswer[];
  members: MemberWrite[];
}

/** Screen 1 answers -> household_answers q1/q2. */
export function step1ToScreens(a: OnboardingAnswers): ScreenAnswer[] {
  const screens: ScreenAnswer[] = [];
  if (a.householdType) {
    screens.push({ screen_id: "onboarding-step-1", question_key: "q1_household_type", answer_value: a.householdType });
  }
  if (a.workingProfessionals != null) {
    screens.push({
      screen_id: "onboarding-step-1",
      question_key: "q2_working_professionals",
      answer_value: a.workingProfessionals,
    });
  }
  return screens;
}

// indianStates.ts's INDIAN_STATES is the full display name ("Madhya Pradesh"), but
// profiles.home_state REFERENCES re_engine.re_states(state_code) — the 2-letter code ("MP"), not
// the name. Verified 1:1 against the live re_states table (36 states/UTs, exact name match).
const STATE_NAME_TO_CODE: Record<string, string> = {
  "Andaman & Nicobar Islands": "AN",
  "Andhra Pradesh": "AP",
  "Arunachal Pradesh": "AR",
  "Assam": "AS",
  "Bihar": "BR",
  "Chandigarh": "CH",
  "Chhattisgarh": "CT",
  "Dadra & Nagar Haveli and Daman & Diu": "DN",
  "Delhi": "DL",
  "Goa": "GA",
  "Gujarat": "GJ",
  "Haryana": "HR",
  "Himachal Pradesh": "HP",
  "Jammu & Kashmir": "JK",
  "Jharkhand": "JH",
  "Karnataka": "KA",
  "Kerala": "KL",
  "Ladakh": "LA",
  "Lakshadweep": "LD",
  "Madhya Pradesh": "MP",
  "Maharashtra": "MH",
  "Manipur": "MN",
  "Meghalaya": "ML",
  "Mizoram": "MZ",
  "Nagaland": "NL",
  "Odisha": "OD",
  "Puducherry": "PY",
  "Punjab": "PB",
  "Rajasthan": "RJ",
  "Sikkim": "SK",
  "Tamil Nadu": "TN",
  "Telangana": "TS",
  "Tripura": "TR",
  "Uttar Pradesh": "UP",
  "Uttarakhand": "UK",
  "West Bengal": "WB",
};

/** Screen 2 answers -> profiles.home_state/current_city (2 of the 5 profile-required fields). */
export function step2ToScreens(a: OnboardingAnswers): ScreenAnswer[] {
  const screens: ScreenAnswer[] = [];
  if (a.homeState) {
    screens.push({
      screen_id: "onboarding-step-2",
      question_key: "home_state",
      answer_value: STATE_NAME_TO_CODE[a.homeState] ?? a.homeState,
    });
  }
  if (a.currentCity) {
    screens.push({ screen_id: "onboarding-step-2", question_key: "current_city", answer_value: a.currentCity });
  }
  return screens;
}

/** Screen 3 answers -> profiles.diet_type (required) + household_answers q6/q7. */
export function step3ToScreens(a: OnboardingAnswers): ScreenAnswer[] {
  const screens: ScreenAnswer[] = [];
  if (a.diet) screens.push({ screen_id: "onboarding-step-3", question_key: "diet_type", answer_value: DIET_MAP[a.diet] });
  if (a.meatPreferences.length) {
    screens.push({ screen_id: "onboarding-step-3", question_key: "q6_nonveg_types", answer_value: a.meatPreferences });
  }
  if (a.vegDays.length) {
    screens.push({ screen_id: "onboarding-step-3", question_key: "q7_veg_days", answer_value: a.vegDays });
  }
  return screens;
}

/** Screen 4 answers -> profiles.allergen_flags + household_answers q10/q11. */
export function step4ToScreens(a: OnboardingAnswers): ScreenAnswer[] {
  const screens: ScreenAnswer[] = [];
  const flags = allergenFlags(a.allergens);
  if (flags > 0) {
    screens.push({ screen_id: "onboarding-step-4", question_key: "allergen_flags", answer_value: flags });
  }
  if (a.allergensOther.trim()) {
    screens.push({ screen_id: "onboarding-step-4", question_key: "q10_allergy_other", answer_value: a.allergensOther.trim() });
  }
  const conditions = [...a.medicalConditions.filter((c) => c !== "others"), ...(a.medicalConditionsOther.trim() ? [a.medicalConditionsOther.trim()] : [])];
  if (conditions.length) {
    screens.push({ screen_id: "onboarding-step-4", question_key: "q11_conditions", answer_value: conditions });
  }
  return screens;
}

/**
 * Screen 5 answers -> profiles.cook_capability (required) + household_answers q13/q14/q15,
 * plus a best-effort household_members row when an age band maps to a condition token.
 */
export function step5ToPayload(a: OnboardingAnswers): HouseholdWritePayload {
  const screens: ScreenAnswer[] = [];
  if (a.cookCapability) {
    screens.push({ screen_id: "onboarding-step-5", question_key: "cook_capability", answer_value: a.cookCapability });
  }
  if (a.whoCooks) {
    screens.push({ screen_id: "onboarding-step-5", question_key: "q13_who_cooks", answer_value: WHO_COOKS_MAP[a.whoCooks] });
  }
  if (a.eatOutFrequency && a.eatOutFrequency in EAT_OUT_PER_WEEK) {
    screens.push({
      screen_id: "onboarding-step-5",
      question_key: "q14_eat_out_per_week",
      answer_value: EAT_OUT_PER_WEEK[a.eatOutFrequency],
    });
  }
  const objective = a.cookingObjective ? OBJECTIVE_MAP[a.cookingObjective] : "awesome_taste";
  screens.push({ screen_id: "onboarding-step-5", question_key: "q15_objective", answer_value: objective });

  const members: MemberWrite[] = [];
  const ageTokens = isSplitAge(a) ? [a.ageEldest, a.ageYoungest] : [a.ageSingle];
  for (const token of ageTokens) {
    if (token && AGE_TO_CONDITION[token]) {
      members.push({ conditions: [AGE_TO_CONDITION[token]] });
    }
  }

  return { screens, members };
}

/**
 * isSplitAge — whether this household answered Screen 5's age question with two separate
 * bands (eldest/youngest) rather than one, so step5ToPayload knows which age field(s) to read
 * when building the best-effort household_members condition row(s).
 * @param a - the full onboarding answer bag.
 * @returns true if householdType is one of the multi-generation types (kids and/or parents/joint).
 */
function isSplitAge(a: OnboardingAnswers): boolean {
  return a.householdType === "couple_kids" || a.householdType === "couple_kids_parents" || a.householdType === "joint";
}
