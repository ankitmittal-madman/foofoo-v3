/**
 * Request composition (Phase C) — build the ghar-re-v1 request from the household's raw Q1–Q15
 * answers + today's context. The RE runs D1–D7 itself (frozen decision), so we send RAW inputs.
 *
 * ⚠️ STUB (TODO — founder decision needed): the live app Postgres has NO household / household_context
 * tables yet. They exist only in the golden-sample `ghar_re` schema from the RE-build session, which
 * is NOT the live application schema. Until those tables (and where they live) are decided, this
 * loads a HARDCODED sample household matching ghar_re_core/fixtures.py (`couple_delhi_north`) rather
 * than inventing a live schema silently. Replace `loadHouseholdRaw` with a real Postgres read
 * (Edge Functions own DB access) once the schema lands.
 */
import type { RequestContext } from "../_shared/types/context.ts";

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
  q12_member_ages: Array<{ role?: string; age: number }>;
  q13_who_cooks: string;
  q14_eat_out_per_week: number;
  q15_objective: string;
}

/** STUB sample household (mirrors ghar_re_core/fixtures.py `couple_delhi_north`, a North veg couple). */
const SAMPLE_HOUSEHOLD: HouseholdRaw = {
  label: "STUB: couple_delhi_north (fixtures.py) — replace with Postgres read",
  q1_household_type: "couple",
  q2_working_professionals: 2,
  q3_home_state: "Delhi",
  q4_current_city: "Delhi",
  q5_diet: "veg",
  q6_nonveg_types: [],
  q7_veg_days: [],
  q8_is_jain: false,
  q9_allergies: [],
  q10_allergy_other: null,
  q11_conditions: [],
  q12_member_ages: [{ role: "adult", age: 32 }, { role: "adult", age: 30 }],
  q13_who_cooks: "self",
  q14_eat_out_per_week: 2,
  q15_objective: "awesome_taste",
};

/**
 * Load the household's raw Q1–Q15 answers.
 * TODO(founder-decision): read from the live `households` table once it exists + verify ownership
 * (household.profile_id == claims.userId). For now returns the stub sample regardless of household_id.
 */
export function loadHouseholdRaw(
  _ctx: RequestContext,
  _householdId: string | null,
): Promise<{ household: HouseholdRaw; householdId: string; stubbed: boolean }> {
  return Promise.resolve({
    household: SAMPLE_HOUSEHOLD,
    householdId: _householdId ?? "stub-household",
    stubbed: true,
  });
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

/** Assemble the ghar-re-v1 request. `contextOverride` (from the request body) wins over defaults. */
export function buildRequest(
  household: HouseholdRaw,
  contextOverride: Record<string, unknown> | undefined,
  requestId: string,
): Record<string, unknown> {
  const context = { ...DEFAULT_CONTEXT, ...(contextOverride ?? {}) };
  return { request_id: requestId, household, context };
}
