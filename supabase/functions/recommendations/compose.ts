/**
 * Request composition (Phase C, wired to live tables in Phase C.5) — build the ghar-re-v1 request
 * from the household's raw Q1–Q15 answers + today's context. The RE runs D1–D7 itself (frozen
 * decision), so we send RAW inputs and never derived θ.
 *
 * Data ownership (RE-DOC-10 §1): Edge Functions own 100% of database access. Everything below
 * reads `public` — the LIVE application schema — never `ghar_re.*` (the engine's offline
 * golden-sample schema) and never `re_engine.*` (the retired reference tier). The RE itself gains
 * nothing from this file: it still receives only JSON and has no idea Postgres exists.
 *
 * Q1–Q15 is assembled from three live sources (migration 038 documents the full map):
 *   public.profiles          — q3, q4, q5, q8 (derived), q9 (derived from the allergen bitfield)
 *   public.household_answers — q1, q2, q6, q7, q10, q11, q13, q14, q15
 *   public.household_members — q12 (age + role derived from the conditions[] vocabulary)
 *
 * A household with no profiles row is a genuinely NEW user, not an error — see loadHouseholdRaw.
 */
import { createServiceRoleClient } from "../_shared/db/client.ts";
import type { RequestContext } from "../_shared/types/context.ts";

export interface MemberAge {
  role?: string;
  age: number;
}

export interface HouseholdRaw {
  label?: string;
  q1_household_type: string;
  q2_working_professionals: number;
  q3_home_state: string;
  q4_current_city: string;
  q5_diet: string;
  q6_nonveg_types: string[];
  q7_veg_days: string[];
  q8_is_jain: boolean;
  q9_allergies: string[];
  q10_allergy_other: string | null;
  q11_conditions: string[];
  q12_member_ages: MemberAge[];
  q13_who_cooks: string;
  q14_eat_out_per_week: number;
  q15_objective: string;
}

/**
 * Allergen bitfield → RE allergen tokens (DOC-P3-02 §Allergen, the frozen 7-bit model).
 * profiles.allergen_flags already holds the household-wide union (members are OR-ed into it by the
 * fn_sync_profile_allergen_union trigger from migration 010), so reading the profile alone is
 * sufficient here — no separate member allergen pass is needed.
 */
const ALLERGEN_BITS: ReadonlyArray<readonly [number, string]> = [
  [1, "nuts"],
  [2, "dairy"],
  [4, "gluten"],
  [8, "shellfish"],
  [16, "egg"],
  [32, "soy"],
  [64, "sesame"],
];

export function allergenTokens(flags: number): string[] {
  return ALLERGEN_BITS.filter(([bit]) => (flags & bit) !== 0).map(([, name]) => name);
}

/**
 * household_members.conditions[] → the RE's member `role`, plus a representative age when the
 * age column is NULL (it is nullable — the current onboarding flow does not collect it, and
 * migration 038 deliberately does not fabricate one in the database).
 *
 * The age defaults below exist ONLY because contracts/ghar-re-v1.schema.json marks MemberAge.age
 * required. They are safe precisely because they never *create* a safety condition that the
 * conditions[] vocabulary didn't already assert: the RE's weaning floor triggers on age < 2 OR
 * role === "weaning", and its senior ceiling on age >= 65 OR role === "senior", so the role — which
 * comes from real user data — is what actually drives every safety-critical filter. The number is
 * only there to satisfy the contract's type.
 */
const ROLE_DEFAULT_AGE: Readonly<Record<string, number>> = {
  weaning: 1,
  toddler: 3,
  child: 9,
  teen: 15,
  senior: 70,
  adult: 32,
};

export function memberRole(conditions: string[]): string {
  const c = new Set(conditions);
  // Ordered most-constraining first: a member tagged both baby_6_18m and picky_child must be
  // treated as weaning, since that is the stricter food-safety floor.
  if (c.has("baby_6_18m")) return "weaning";
  if (c.has("toddler")) return "toddler";
  if (c.has("elderly_member")) return "senior";
  if (c.has("school_child") || c.has("picky_child")) return "child";
  if (c.has("teen_high_appetite")) return "teen";
  return "adult";
}

export function toMemberAge(row: { age: number | null; conditions: string[] | null }): MemberAge {
  const role = memberRole(row.conditions ?? []);
  return { role, age: row.age ?? ROLE_DEFAULT_AGE[role] ?? ROLE_DEFAULT_AGE.adult };
}

/**
 * Defaults for a household that exists but hasn't finished onboarding (no household_answers row).
 * These are the neutral answers — deliberately NOT a persona — so a half-onboarded user still gets
 * a real recommendation rather than an error screen.
 */
const NEW_HOUSEHOLD_ANSWER_DEFAULTS = {
  q1_household_type: "couple",
  q2_working_professionals: 1,
  q6_nonveg_types: [] as string[],
  q7_veg_days: [] as string[],
  q10_allergy_other: null as string | null,
  q11_conditions: [] as string[],
  q13_who_cooks: "self",
  q14_eat_out_per_week: 2,
  q15_objective: "awesome_taste",
};

/**
 * The whole-household fallback, used only when there is no profiles row at all — i.e. a genuinely
 * NEW user whose onboarding hasn't written anything yet. This is a valid state, not a failure:
 * the caller still gets a real 7-plate recommendation instead of an error.
 */
const NEW_HOUSEHOLD: HouseholdRaw = {
  label: "new household (no profile yet) — neutral defaults",
  ...NEW_HOUSEHOLD_ANSWER_DEFAULTS,
  q3_home_state: "Delhi",
  q4_current_city: "Delhi",
  q5_diet: "veg",
  q8_is_jain: false,
  q9_allergies: [],
  q12_member_ages: [{ role: "adult", age: 32 }],
};

interface ProfileRow {
  id: string;
  home_state: string | null;
  current_city: string | null;
  diet_type: string | null;
  religious_pref: string | null;
  allergen_flags: number | null;
}

interface AnswersRow {
  q1_household_type: string | null;
  q2_working_professionals: number | null;
  q6_nonveg_types: string[] | null;
  q7_veg_days: string[] | null;
  q10_allergy_other: string | null;
  q11_conditions: string[] | null;
  q13_who_cooks: string | null;
  q14_eat_out_per_week: number | null;
  q15_objective: string | null;
}

interface MemberRow {
  age: number | null;
  conditions: string[] | null;
}

/** Assemble HouseholdRaw from the three live row sets. Exported for direct unit testing. */
export function composeHouseholdRaw(
  profile: ProfileRow,
  answers: AnswersRow | null,
  members: MemberRow[],
): HouseholdRaw {
  const a = answers ?? {} as AnswersRow;
  const memberAges = members.map(toMemberAge);
  return {
    // q8: either signal means Jain — religious_pref is the primary field, but diet_type='jain' is
    // permitted by the profiles CHECK constraint too, so both are honoured (fail-safe direction).
    q8_is_jain: profile.religious_pref === "jain" || profile.diet_type === "jain",
    q3_home_state: profile.home_state ?? NEW_HOUSEHOLD.q3_home_state,
    q4_current_city: profile.current_city ?? NEW_HOUSEHOLD.q4_current_city,
    q5_diet: profile.diet_type ?? NEW_HOUSEHOLD.q5_diet,
    q9_allergies: allergenTokens(profile.allergen_flags ?? 0),
    q1_household_type: a.q1_household_type ?? NEW_HOUSEHOLD_ANSWER_DEFAULTS.q1_household_type,
    q2_working_professionals: a.q2_working_professionals ??
      NEW_HOUSEHOLD_ANSWER_DEFAULTS.q2_working_professionals,
    q6_nonveg_types: a.q6_nonveg_types ?? [],
    q7_veg_days: a.q7_veg_days ?? [],
    q10_allergy_other: a.q10_allergy_other ?? null,
    q11_conditions: a.q11_conditions ?? [],
    q13_who_cooks: a.q13_who_cooks ?? NEW_HOUSEHOLD_ANSWER_DEFAULTS.q13_who_cooks,
    q14_eat_out_per_week: a.q14_eat_out_per_week ??
      NEW_HOUSEHOLD_ANSWER_DEFAULTS.q14_eat_out_per_week,
    q15_objective: a.q15_objective ?? NEW_HOUSEHOLD_ANSWER_DEFAULTS.q15_objective,
    // A household with a profile but zero member rows still needs one member for the RE's
    // household-size maths — treat it as a single adult rather than sending an empty array.
    q12_member_ages: memberAges.length > 0 ? memberAges : [{ role: "adult", age: 32 }],
  };
}

/**
 * Load the household's raw Q1–Q15 answers from the live `public` schema.
 *
 * `stubbed` is true only when no profiles row exists (new user served neutral defaults) — it is
 * the signal the handler logs, so a recommendation built on defaults is never silently
 * indistinguishable from one built on the user's real answers.
 */
export async function loadHouseholdRaw(
  ctx: RequestContext,
  householdId: string | null,
): Promise<{ household: HouseholdRaw; householdId: string; stubbed: boolean }> {
  const profileId = householdId ?? ctx.claims?.userId ?? null;
  if (!profileId) {
    return { household: NEW_HOUSEHOLD, householdId: "new-household", stubbed: true };
  }

  const db = createServiceRoleClient(ctx.config);

  // Three independent reads, issued concurrently — none depends on another's result.
  const [profileRes, answersRes, membersRes] = await Promise.all([
    db.from("profiles")
      .select("id, home_state, current_city, diet_type, religious_pref, allergen_flags")
      .eq("id", profileId).maybeSingle(),
    db.from("household_answers")
      .select(
        "q1_household_type, q2_working_professionals, q6_nonveg_types, q7_veg_days, " +
          "q10_allergy_other, q11_conditions, q13_who_cooks, q14_eat_out_per_week, q15_objective",
      )
      .eq("profile_id", profileId).maybeSingle(),
    db.from("household_members")
      .select("age, conditions").eq("profile_id", profileId).eq("is_active", true),
  ]);

  // A read ERROR is not the same as "no rows" — surface it rather than silently serving defaults,
  // which would make a broken database look like a brand-new user.
  if (profileRes.error) throw profileRes.error;
  if (answersRes.error) throw answersRes.error;
  if (membersRes.error) throw membersRes.error;

  if (!profileRes.data) {
    // Genuinely new user: onboarding hasn't written a profile yet. Valid state, not an error.
    ctx.logger.info("household.new_user_defaults", { profile_id: profileId });
    return { household: NEW_HOUSEHOLD, householdId: profileId, stubbed: true };
  }

  const household = composeHouseholdRaw(
    profileRes.data as ProfileRow,
    (answersRes.data ?? null) as AnswersRow | null,
    (membersRes.data ?? []) as MemberRow[],
  );
  return { household, householdId: profileId, stubbed: false };
}

/** Default context when the caller supplies none (weather is mocked in v1 — no live API). */
const DEFAULT_CONTEXT = {
  slot: "dinner",
  season: "monsoon",
  weekday: "Thursday",
  weather: { is_raining: true, temp_c: 27 },
  active_modes: [] as string[],
  calorie_target: null as number | null,
};

/**
 * Load the household's most recent stored context, if any. Returns undefined when the household
 * has none — the caller then falls back to DEFAULT_CONTEXT, so a household that has never had a
 * context row still gets a recommendation.
 */
export async function loadLatestContext(
  ctx: RequestContext,
  profileId: string,
): Promise<Record<string, unknown> | undefined> {
  const db = createServiceRoleClient(ctx.config);
  const { data, error } = await db.from("household_context")
    .select(
      "slot, season, weekday, weather_condition, temp_c, is_raining, humidity, " +
        "active_modes, calorie_target",
    )
    .eq("profile_id", profileId)
    .order("created_at", { ascending: false })
    .limit(1)
    .maybeSingle();

  if (error) throw error;
  if (!data) return undefined;

  // Reshape the flat row into the contract's nested `weather` object. The double assertion is
  // needed because supabase-js types `data` as a union that includes its own error shape; the
  // `error` branch is already returned above, so only the row shape can reach here.
  const row = data as unknown as Record<string, unknown>;
  return {
    slot: row.slot ?? DEFAULT_CONTEXT.slot,
    season: row.season ?? DEFAULT_CONTEXT.season,
    weekday: row.weekday ?? DEFAULT_CONTEXT.weekday,
    weather: {
      is_raining: row.is_raining ?? false,
      temp_c: row.temp_c ?? null,
      humidity: row.humidity ?? null,
      condition: row.weather_condition ?? null,
    },
    active_modes: row.active_modes ?? [],
    calorie_target: row.calorie_target ?? null,
  };
}

/** Assemble the ghar-re-v1 request. `contextOverride` (from the request body) wins over defaults. */
export function buildRequest(
  household: HouseholdRaw,
  contextOverride: Record<string, unknown> | undefined,
  requestId: string,
): Record<string, unknown> {
  const context = { ...DEFAULT_CONTEXT, ...(contextOverride ?? {}) };
  return { request_id: requestId, household, context };
}
