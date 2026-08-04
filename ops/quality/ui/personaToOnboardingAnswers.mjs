/**
 * personaToOnboardingAnswers.mjs — WP-22 reverse mapper: persona household q1..q15 fields ->
 * mobile/src/onboarding/OnboardingContext.tsx's OnboardingAnswers shape, so the Playwright
 * journey driver (run_persona_journeys.mjs) can fill in the real onboarding UI exactly as a
 * human answering that persona's household would.
 *
 * This is the field-by-field INVERSE of mobile/src/onboarding/toHouseholdWrite.ts's forward
 * maps. Every function/table here is named and ordered to mirror its toHouseholdWrite.ts
 * counterpart 1:1 (mapQ5ToDiet <-> DIET_MAP, mapQ13ToWhoCooks <-> WHO_COOKS_MAP, etc.) so future
 * drift between the two directions is easy to spot in a diff.
 *
 * IMPORTANT — this mapping is LOSSY/AMBIGUOUS in several places because personas.py's household
 * dict (ops/quality/personas/personas.py) and toHouseholdWrite.ts's UI answer bag were built for
 * different purposes (a request-contract fixture vs. a UI form) and don't line up 1:1. Every such
 * spot is called out in a comment at the point it happens; see also this file's header note THIS
 * COMMENT continues in the final report handed back to the caller of the WP-22 build task.
 */

// ---- Screen 1 (mirrors toHouseholdWrite.ts's step1ToScreens) --------------------------------

/**
 * mapQ1ToHouseholdType — inverse of step1ToScreens's plain passthrough of a.householdType.
 * personas.py's q1_household_type vocabulary (single/couple/couple_kids/couple_kids_parents/
 * joint/flatmates) is already identical to OnboardingContext's HouseholdType union, so this is a
 * lossless passthrough, not a real remap.
 * @param household - the persona's household dict.
 * @returns the UI householdType token, or null if q1_household_type is missing/unrecognized.
 */
export function mapQ1ToHouseholdType(household) {
  const v = household.q1_household_type;
  const valid = ["single", "couple", "couple_kids", "couple_kids_parents", "joint", "flatmates"];
  return valid.includes(v) ? v : null;
}

/** mapQ2ToWorkingProfessionals — inverse passthrough of step1ToScreens's a.workingProfessionals. */
export function mapQ2ToWorkingProfessionals(household) {
  return typeof household.q2_working_professionals === "number" ? household.q2_working_professionals : null;
}

// ---- Screen 2 (mirrors toHouseholdWrite.ts's step2ToScreens + STATE_NAME_TO_CODE) ------------

// Inverse of toHouseholdWrite.ts's STATE_NAME_TO_CODE (name -> 2-letter code). personas.py's
// q3_home_state already carries the full state NAME (e.g. "Maharashtra"), not the code, so in
// the common case no lookup is even needed — this table only matters if a persona ever supplied
// a bare code directly (none currently do, kept for symmetry/future-proofing).
const CODE_TO_STATE_NAME = {
  AN: "Andaman & Nicobar Islands", AP: "Andhra Pradesh", AR: "Arunachal Pradesh", AS: "Assam",
  BR: "Bihar", CH: "Chandigarh", CT: "Chhattisgarh", DN: "Dadra & Nagar Haveli and Daman & Diu",
  DL: "Delhi", GA: "Goa", GJ: "Gujarat", HR: "Haryana", HP: "Himachal Pradesh", JK: "Jammu & Kashmir",
  JH: "Jharkhand", KA: "Karnataka", KL: "Kerala", LA: "Ladakh", LD: "Lakshadweep", MP: "Madhya Pradesh",
  MH: "Maharashtra", MN: "Manipur", ML: "Meghalaya", MZ: "Mizoram", NL: "Nagaland", OD: "Odisha",
  PY: "Puducherry", PB: "Punjab", RJ: "Rajasthan", SK: "Sikkim", TN: "Tamil Nadu", TS: "Telangana",
  TR: "Tripura", UP: "Uttar Pradesh", UK: "Uttarakhand", WB: "West Bengal",
};

/**
 * mapQ3ToHomeState — inverse of step2ToScreens's STATE_NAME_TO_CODE lookup. personas.py already
 * stores the full state name, so this passes it through directly; a 2-letter code (if one were
 * ever supplied) is expanded back via CODE_TO_STATE_NAME. Falls back to the raw value so the UI
 * search field still gets *something* typeable rather than silently going blank.
 */
export function mapQ3ToHomeState(household) {
  const v = household.q3_home_state;
  if (!v) return null;
  return CODE_TO_STATE_NAME[v] ?? v;
}

/** mapQ4ToCurrentCity — inverse passthrough of step2ToScreens's a.currentCity. */
export function mapQ4ToCurrentCity(household) {
  return household.q4_current_city ?? null;
}

// ---- Screen 3 (mirrors toHouseholdWrite.ts's step3ToScreens + DIET_MAP) ----------------------

// Inverse of toHouseholdWrite.ts's DIET_MAP (UI token -> profiles.diet_type). AMBIGUOUS: DIET_MAP
// is many-to-one — both "eggetarian" and "egg" would forward-map differently, but personas.py
// never emits "egg" as q5_diet (it isn't in the engine's own diet vocabulary either), so this
// inverse only needs to handle the straightforward veg/non_veg/jain/vegan cases 1:1. q8_is_jain
// is handled as an override below since personas.py sometimes signals Jain via q8 rather than
// q5_diet="jain" directly (see jain_strict_derived: q5_diet="veg", q8_is_jain=True).
const DIET_MAP_INVERSE = { veg: "veg", non_veg: "non_veg", vegan: "vegan", jain: "jain" };

/**
 * mapQ5ToDiet — inverse of step3ToScreens's DIET_MAP application. If q8_is_jain is true, the UI
 * diet choice is forced to "jain" regardless of q5_diet's own value (personas.py sometimes
 * expresses Jain-ness only via q8_is_jain on top of q5_diet="veg" — see personas.py's
 * jain_strict_derived persona). Otherwise passes q5_diet through DIET_MAP_INVERSE.
 * @param household - the persona's household dict.
 * @returns the UI DietChoice token, or null if q5_diet is missing/unrecognized.
 */
export function mapQ5ToDiet(household) {
  if (household.q8_is_jain === true) return "jain";
  return DIET_MAP_INVERSE[household.q5_diet] ?? null;
}

// Inverse of the engine's meat-type vocabulary (q6_nonveg_types) -> Screen 3's MEATS chip values.
// AMBIGUOUS: personas.py's q6_nonveg_types uses tokens like "egg" (see nonveg_family persona)
// that have NO matching chip on Screen 3 (MEATS is chicken/mutton/fish/other_seafood/pork/any) —
// Screen 3's egg-adjacent case is actually the SEPARATE "eggetarian" diet choice, not a meat chip.
// Any q6 token with no chip match is simply dropped (best-effort, not fabricated).
const MEAT_TOKEN_MAP = {
  chicken: "chicken", mutton: "mutton", fish: "fish", pork: "pork",
  seafood: "other_seafood", other_seafood: "other_seafood",
};

/** mapQ6ToMeatPreferences — inverse of step3ToScreens's plain q6_nonveg_types passthrough. */
export function mapQ6ToMeatPreferences(household) {
  const list = Array.isArray(household.q6_nonveg_types) ? household.q6_nonveg_types : [];
  return list.map((tok) => MEAT_TOKEN_MAP[tok]).filter(Boolean);
}

/** mapQ7ToVegDays — inverse passthrough of step3ToScreens's a.vegDays (day-name tokens match). */
export function mapQ7ToVegDays(household) {
  return Array.isArray(household.q7_veg_days) ? household.q7_veg_days : [];
}

// ---- Screen 4 (mirrors toHouseholdWrite.ts's step4ToScreens + ALLERGEN_BITS) ------------------

// Inverse of toHouseholdWrite.ts's ALLERGEN_BITS. AMBIGUOUS/LOSSY spelling mismatch: personas.py's
// q9_allergies uses the SINGULAR "peanut" (see nut_allergy_derived), while ALLERGEN_BITS'S own key
// (and Screen 4's chip value) is the PLURAL "peanuts" — the toHouseholdWrite.ts header comment
// itself flags this exact singular/plural drift ("the live catalogue's plural spelling maps to
// the engine's 'nuts' bit"). This table absorbs that mismatch so the reverse mapper still finds
// the right chip; a persona using any other un-mapped token is simply dropped, not guessed at.
const ALLERGEN_TOKEN_MAP = {
  peanut: "peanuts", peanuts: "peanuts", dairy: "dairy", gluten: "gluten",
  shellfish: "shellfish", soy: "soy", sesame: "sesame", fish: "fish", mustard: "mustard",
};

/** mapQ9ToAllergens — inverse of step4ToScreens's allergenFlags() bitmask packer. */
export function mapQ9ToAllergens(household) {
  const list = Array.isArray(household.q9_allergies) ? household.q9_allergies : [];
  return list.map((tok) => ALLERGEN_TOKEN_MAP[tok]).filter(Boolean);
}

/**
 * mapQ10ToAllergensOther — GUESS: personas.py's household dict has no q10_allergy_other field at
 * all (q10 is collect-only free text with no behavioural expectation any persona asserts on), so
 * there is nothing to invert. Always returns "" — the "Others" chip is never selected by this
 * mapper (see mapQ9ToAllergens: an unmapped token is dropped, never coerced into "others").
 */
export function mapQ10ToAllergensOther(_household) {
  return "";
}

// Inverse of step4ToScreens's q11_conditions passthrough. personas.py's condition tokens
// (diabetes, hypertension, ...) already match Screen 4's MEDICAL_CONDITIONS chip values 1:1.
export function mapQ11ToMedicalConditions(household) {
  const KNOWN = new Set(["diabetes", "hypertension", "high_cholesterol", "thyroid", "pcos", "acidity", "heart", "kidney"]);
  const list = Array.isArray(household.q11_conditions) ? household.q11_conditions : [];
  const known = list.filter((c) => KNOWN.has(c));
  const unknown = list.filter((c) => !KNOWN.has(c));
  // AMBIGUOUS: any condition token personas.py supplies that ISN'T one of Screen 4's 8 preset
  // chips has no destination except the catch-all "others" chip + its free-text box — same
  // many-to-one shape as toHouseholdWrite.ts's own forward q11_conditions handling (which folds
  // "others" plus free text back into one flat list on submit). Best-effort, not fabricated.
  return { medicalConditions: unknown.length ? [...known, "others"] : known, medicalConditionsOther: unknown.join(", ") };
}

// ---- Screen 5 (mirrors toHouseholdWrite.ts's step5ToPayload + WHO_COOKS_MAP/EAT_OUT_PER_WEEK/OBJECTIVE_MAP) ----

// Inverse of toHouseholdWrite.ts's WHO_COOKS_MAP ("order_in" UI token -> "order_tiffin" API token).
const WHO_COOKS_MAP_INVERSE = { self: "self", family: "family", hired_cook: "hired_cook", order_tiffin: "order_in" };

/** mapQ13ToWhoCooks — inverse of step5ToPayload's WHO_COOKS_MAP application. */
export function mapQ13ToWhoCooks(household) {
  return WHO_COOKS_MAP_INVERSE[household.q13_who_cooks] ?? null;
}

// Inverse of toHouseholdWrite.ts's EAT_OUT_PER_WEEK (UI cadence token -> integer count).
// AMBIGUOUS/LOSSY: EAT_OUT_PER_WEEK is a 4-value -> integer map (rarely=0, weekly=1,
// few_weekly=3, daily=7); personas.py's q14_eat_out_per_week is a free integer 0-7+, so values
// that were never a forward-map OUTPUT (2, 4, 5, 6, or anything >7) have no exact inverse. This
// picks the nearest EAT_OUT_PER_WEEK bucket by absolute distance rather than inventing a 5th UI
// option that doesn't exist on Screen 5.
const EAT_OUT_BUCKETS = [["rarely", 0], ["weekly", 1], ["few_weekly", 3], ["daily", 7]];

/**
 * mapQ14ToEatOutFrequency — nearest-bucket inverse of EAT_OUT_PER_WEEK; see the ambiguity note
 * above the EAT_OUT_BUCKETS table for exactly which integer values this cannot invert exactly.
 */
export function mapQ14ToEatOutFrequency(household) {
  const n = household.q14_eat_out_per_week;
  if (typeof n !== "number") return null;
  let best = EAT_OUT_BUCKETS[0];
  for (const bucket of EAT_OUT_BUCKETS) {
    if (Math.abs(bucket[1] - n) < Math.abs(best[1] - n)) best = bucket;
  }
  return best[0];
}

// Inverse of toHouseholdWrite.ts's OBJECTIVE_MAP. AMBIGUOUS/LOSSY: OBJECTIVE_MAP is many-to-one
// — both "tasty" and "discover" forward-map to the same API value "awesome_taste" (the header
// comment on OBJECTIVE_MAP admits "discover" has no destination of its own). There is therefore
// no way to tell, from "awesome_taste" alone, whether the original UI answer was "tasty" or
// "discover" — this inverse always picks "tasty" as the representative choice, which is a genuine
// guess this mapper cannot avoid without more information than the API payload carries.
const OBJECTIVE_MAP_INVERSE = { awesome_taste: "tasty", healthy_living: "healthy", into_fitness: "into_fitness" };

/** mapQ15ToCookingObjective — lossy inverse of OBJECTIVE_MAP; see ambiguity note above. */
export function mapQ15ToCookingObjective(household) {
  return OBJECTIVE_MAP_INVERSE[household.q15_objective] ?? null;
}

/**
 * mapQ12ToAges — inverse of step5ToPayload's AGE_TO_CONDITION table (age BAND -> per-member
 * condition token), run backwards from q12_member_ages (a list of {role, age} numbers) to the UI's
 * age-BAND chip tokens. GUESS/LOSSY: AGE_TO_CONDITION only covers 5 of many possible bands
 * (baby_6_18m, toddler, school_child, teen_high_appetite, elderly_member) and was built to go
 * age-band -> condition, not age-in-years -> band, so this reimplements the band boundaries
 * from Screen 5's own AGE_RANGES/AGE_YOUNGEST chip definitions (18-25/25-35/35-45/45-60/60+ for
 * adults, plus 0-2/2-5/5-12/12-18 for the youngest-in-home question) rather than reusing
 * AGE_TO_CONDITION, since that table is one-directional by design (condition is a superset
 * concept, not a strict inverse of a band).
 * @param household - the persona's household dict.
 * @param isSplit - whether this household type asks for eldest+youngest (see isSplitAge below).
 * @returns { ageSingle, ageEldest, ageYoungest } — whichever the screen actually needs is filled.
 */
export function mapQ12ToAges(household, isSplit) {
  const ages = Array.isArray(household.q12_member_ages) ? household.q12_member_ages.map((m) => m.age).filter((a) => typeof a === "number") : [];
  if (!ages.length) return { ageSingle: null, ageEldest: null, ageYoungest: null };

  const bandAdult = (age) => (age < 25 ? "18-25" : age < 35 ? "25-35" : age < 45 ? "35-45" : age < 60 ? "45-60" : "60+");
  const bandYoungest = (age) => (age < 2 ? "0-2" : age < 5 ? "2-5" : age < 12 ? "5-12" : age < 18 ? "12-18" : bandAdult(age));

  if (!isSplit) {
    return { ageSingle: bandAdult(Math.max(...ages)), ageEldest: null, ageYoungest: null };
  }
  return {
    ageSingle: null,
    ageEldest: bandAdult(Math.max(...ages)),
    ageYoungest: bandYoungest(Math.min(...ages)),
  };
}

/** isSplitAge — mirrors OnboardingContext.tsx's isSplitAgeHousehold exactly (same 3 household types). */
export function isSplitAge(householdType) {
  return householdType === "couple_kids" || householdType === "couple_kids_parents" || householdType === "joint";
}

/**
 * mapCookCapability — GUESS: personas.py's household dict has NO field corresponding to
 * profiles.cook_capability at all (toHouseholdWrite.ts's own header note flags this — "source
 * never asked this at all"). Since Screen 5 hard-requires this field to submit, this mapper
 * fills a fixed default ("intermediate") rather than leaving it null and dead-ending the journey.
 * This is a fabricated answer with no persona-driven basis — flagged explicitly in the WP-22
 * build report as a known gap, not a real signal read from any persona field.
 */
export function mapCookCapability(_household) {
  return "intermediate";
}

/**
 * personaToOnboardingAnswers — top-level entry point: turns one persona's household dict into
 * the full OnboardingAnswers-shaped patch the journey driver applies across step-1..step-5.
 * Field order below matches OnboardingContext.tsx's own OnboardingAnswers type declaration order.
 * @param household - persona.household (q1..q15 dict) from export_personas.py's JSON dump.
 * @returns a plain object matching (a subset of) OnboardingAnswers.
 */
export function personaToOnboardingAnswers(household) {
  const householdType = mapQ1ToHouseholdType(household);
  const split = isSplitAge(householdType);
  const ages = mapQ12ToAges(household, split);
  const conditions = mapQ11ToMedicalConditions(household);

  return {
    householdType,
    workingProfessionals: mapQ2ToWorkingProfessionals(household),
    homeState: mapQ3ToHomeState(household),
    currentCity: mapQ4ToCurrentCity(household),
    diet: mapQ5ToDiet(household),
    jainExclusions: [], // collect-only in the UI itself; never submitted, never worth reverse-mapping
    meatPreferences: mapQ6ToMeatPreferences(household),
    vegDays: mapQ7ToVegDays(household),
    allergens: mapQ9ToAllergens(household),
    allergensOther: mapQ10ToAllergensOther(household),
    medicalConditions: conditions.medicalConditions,
    medicalConditionsOther: conditions.medicalConditionsOther,
    ageSingle: ages.ageSingle,
    ageEldest: ages.ageEldest,
    ageYoungest: ages.ageYoungest,
    whoCooks: mapQ13ToWhoCooks(household),
    eatOutFrequency: mapQ14ToEatOutFrequency(household),
    cookingObjective: mapQ15ToCookingObjective(household),
    cookCapability: mapCookCapability(household),
  };
}
