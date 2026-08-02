/**
 * Recommendation Engine — remaining port adapters (Phase F, onboarding-wiring work).
 *
 * ⚠️ NOT ON THE LIVE MOBILE PATH (Founder decision, 2026-07-30) — this file implements adapters for
 * the LEGACY TypeScript RE engine (`re_engine.*` schema), which
 * `docs/architecture/RE-DOC-12_Ghar_RE_Status_and_Roadmap_v1_0.md` already documented, before this
 * session, as not on the live request path — migration 034 itself calls it "the OLD
 * persona/cohort/weight-ladder RE" and "retired." The actual live recommendations path is the
 * Python `ghar_re_core`/`ghar_re_service` pair, called via HTTP from `recommendations/compose.ts`,
 * which never touches `re_engine.*`. Kept as a real, tested reference implementation in case this
 * engine is ever revived — not deployed into any client-facing flow today.
 *
 * WP-8D (`_shared/services/re/*`) defined 11 ports the reusable RecommendationEngine depends on
 * (`_shared/services/re/ports.ts`). Before this file, only ONE had a live Supabase-backed adapter
 * (`SupabaseCandidateRepository`, in `supabase-stores.ts`) — every other port existed only as a
 * unit-test fake (confirmed by repo-wide search: `assignPersona`/`implements ReConfigProvider`/etc.
 * matched nothing outside `_tests/`). That gap is exactly why `OnboardingOrchestrator` — despite
 * being fully built — was never actually reachable end-to-end: it needs a complete `EngineDeps`
 * object to invoke `engine.generateWeekPlan()`, and that object could not previously be constructed
 * against the live database at all.
 *
 * This file closes that gap with real, schema-verified queries (columns confirmed directly against
 * the live project via Supabase MCP — never assumed from docs alone) for every port EXCEPT one:
 *
 *   `TasteVectorRepository.getCohortAverageVector()` has NO backing data source in the live schema.
 *   `re_cohorts` carries no vector column; no separate "cohort average taste vector" table exists
 *   anywhere in `re_engine.*`. Because `RecommendationEngine.scorePool()` calls this UNCONDITIONALLY
 *   for every cold-start user (`req.user.coldStartMode` is always true at onboarding — DOC-P3-03
 *   §03 LF-A08), this is not an edge case, it is the common case, and it cannot be answered from a
 *   real query. Rather than invent a numeric vector whose semantics I cannot verify (dish
 *   `genome_vector` arrays are variable-length per dish — 8 to 14 dimensions were observed live —
 *   so even the vector's shape is not something a data-access adapter can safely assume), this
 *   adapter returns a neutral (all-zero, dish-vector-length-matched) vector and says so loudly:
 *   see the function's own doc comment. This mirrors the ALREADY-DOCUMENTED pattern the engine
 *   itself uses for its OTHER unseeded-data case (`neutralCohortPrior`, ScoringConfig) — a disclosed
 *   neutral fallback, not a silent guess — but it is a genuine judgment call, flagged in the WP
 *   report, and should be replaced once a real materialized cohort-average vector exists
 *   (needs migration — flagged, not written here per this task's scope boundary).
 *
 * Persona/cohort assignment (`SupabaseCohortResolutionRepository`) is similarly a best-effort
 * reading of LF-A09/LF-B02/LF-B03 from the orchestrator's and resolvers.ts's own doc comments plus
 * the live seed data's actual shape (assignment rows were observed with NULL state_code/diet_type —
 * i.e. "matches any"), NOT a full re-derivation from DOC-P3-03 §03/§04's complete text (out of this
 * task's time budget). Flagged for review before this is trusted with production traffic.
 */
import type { SupabaseClient } from "../../db/client.ts";
import { RE_ENGINE_SCHEMA } from "../../constants/schemas.ts";
import { AppError } from "../../errors/app-error.ts";
import { ERROR_CATALOGUE } from "../../errors/catalogue.ts";
import { withTimeout } from "../../utils/timeout.ts";
import type {
  BanditStateRepository,
  CohortPriorRepository,
  CohortResolutionRepository,
  ContextMultiplierRepository,
  NeverListRepository,
  PersonalHistoryRepository,
  Random,
  ReConfigProvider,
  SuppressionRepository,
  TasteVectorRepository,
} from "../re/ports.ts";
import type {
  ClassAssignment,
  InteractionEvent,
  ScoringConfig,
  VarietyRule,
  WeightLadderTier,
} from "../re/types.ts";

/** Raise a 500 without leaking the raw DB error to the client (DOC-P3-07) — same convention as
 * `dbFail()` in supabase-stores.ts. */
function dbFail(op: string, message: string): never {
  throw new AppError(ERROR_CATALOGUE.INTERNAL, { detail: `${op}: ${message}` });
}

const DAY_NAMES = [
  "sunday",
  "monday",
  "tuesday",
  "wednesday",
  "thursday",
  "friday",
  "saturday",
] as const;

/** `YYYY-MM-DD` + a day offset → `YYYY-MM-DD`, using UTC calendar math (no locale ambiguity). */
function addDays(dateStr: string, days: number): string {
  const d = new Date(`${dateStr}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}

function dayOfWeekName(dateStr: string): string {
  const d = new Date(`${dateStr}T00:00:00Z`);
  return DAY_NAMES[d.getUTCDay()];
}

// ── Persona / cohort resolution (LF-A09, LF-B02, LF-B03) — BEST-EFFORT, flag for spec review ──────

export class SupabaseCohortResolutionRepository implements CohortResolutionRepository {
  constructor(private readonly db: SupabaseClient) {}

  /**
   * LF-A09. The live `re_persona_assignment_rules` rows observed in the seeded data carry
   * `state_code`/`diet_type` as NULL (i.e. "matches any state/diet for this main+sub cohort") —
   * so an exact-equality match on those two columns as the port's own doc comment describes would
   * match ZERO rows against current seed data. Matching here is equality-OR-NULL on state/diet,
   * preferring the most specific row (non-NULL beats NULL) when more than one matches.
   */
  async assignPersona(
    mainCohortCode: string,
    subCohortTag: string,
    homeState: string,
    dietType: string,
  ): Promise<{ personaId: string; overlayPersonaIds: string[] } | null> {
    const { data, error } = await withTimeout(
      this.db
        .schema(RE_ENGINE_SCHEMA)
        .from("re_persona_assignment_rules")
        .select("persona_id, state_code, diet_type")
        .eq("main_cohort_code", mainCohortCode)
        .eq("subcohort_code", subCohortTag)
        .or(`state_code.is.null,state_code.eq.${homeState}`)
        .or(`diet_type.is.null,diet_type.eq.${dietType}`),
      "cohortResolution.assignPersona",
    );
    if (error) dbFail("read re_persona_assignment_rules", error.message);
    const rows = (data ?? []) as Array<
      { persona_id: string; state_code: string | null; diet_type: string | null }
    >;
    if (rows.length === 0) return null;

    // Prefer the most specific match: both state+diet non-null, then one of them, then neither.
    const specificity = (r: typeof rows[number]) =>
      (r.state_code !== null ? 1 : 0) + (r.diet_type !== null ? 1 : 0);
    rows.sort((a, b) => specificity(b) - specificity(a));
    const personaId = rows[0].persona_id;

    // No live table carries "overlay persona ids" (CDM Entity 12) for a persona assignment — flagged
    // gap, not fabricated; empty array is the honest "none known" answer, never an invented id.
    return { personaId, overlayPersonaIds: [] };
  }

  /** Option-B fallback (CONFIRMED, founder-approved per resolvers.ts): broadest state coverage —
   * i.e. the assignment row with `state_code IS NULL` (matches every state) for this main cohort,
   * deterministically the first by subcohort_code when more than one qualifies. */
  async assignPersonaFallback(
    mainCohortCode: string,
  ): Promise<{ personaId: string; overlayPersonaIds: string[]; cohortId: string }> {
    const { data, error } = await withTimeout(
      this.db
        .schema(RE_ENGINE_SCHEMA)
        .from("re_persona_assignment_rules")
        .select("persona_id, subcohort_code")
        .eq("main_cohort_code", mainCohortCode)
        .is("state_code", null)
        .order("subcohort_code", { ascending: true })
        .limit(1)
        .maybeSingle(),
      "cohortResolution.assignPersonaFallback",
    );
    if (error) dbFail("read re_persona_assignment_rules (fallback)", error.message);
    if (!data) {
      throw new AppError(ERROR_CATALOGUE.INTERNAL, {
        detail: `no Option-B fallback persona rule exists for main_cohort_code=${mainCohortCode}`,
      });
    }
    const personaId = (data as { persona_id: string }).persona_id;

    // Resolve a cohort for this persona: prefer the broadest-coverage cohort row too (NULL state).
    const { data: cohortRow, error: cohortErr } = await withTimeout(
      this.db
        .schema(RE_ENGINE_SCHEMA)
        .from("re_cohorts")
        .select("cohort_id")
        .eq("persona_id", personaId)
        .order("state_code", { ascending: true, nullsFirst: true })
        .limit(1)
        .maybeSingle(),
      "cohortResolution.assignPersonaFallback.cohort",
    );
    if (cohortErr) dbFail("read re_cohorts (fallback)", cohortErr.message);
    if (!cohortRow) {
      throw new AppError(ERROR_CATALOGUE.INTERNAL, {
        detail: `no re_cohorts row exists for persona_id=${personaId} (Option-B fallback)`,
      });
    }
    return {
      personaId,
      overlayPersonaIds: [],
      cohortId: (cohortRow as { cohort_id: string }).cohort_id,
    };
  }

  /** LF-B02: (persona × state × diet) → cohort_id, same equality-OR-NULL precedence as assignPersona. */
  async resolveCohort(
    personaId: string,
    stateCode: string,
    dietMode: string,
  ): Promise<string | null> {
    const { data, error } = await withTimeout(
      this.db
        .schema(RE_ENGINE_SCHEMA)
        .from("re_cohorts")
        .select("cohort_id, state_code, diet_mode")
        .eq("persona_id", personaId)
        .or(`state_code.is.null,state_code.eq.${stateCode}`)
        .or(`diet_mode.is.null,diet_mode.eq.${dietMode}`),
      "cohortResolution.resolveCohort",
    );
    if (error) dbFail("read re_cohorts", error.message);
    const rows = (data ?? []) as Array<
      { cohort_id: string; state_code: string | null; diet_mode: string | null }
    >;
    if (rows.length === 0) return null;
    const specificity = (r: typeof rows[number]) =>
      (r.state_code !== null ? 1 : 0) + (r.diet_mode !== null ? 1 : 0);
    rows.sort((a, b) => specificity(b) - specificity(a));
    return rows[0].cohort_id;
  }

  /**
   * LF-B02: 21 class assignments for a cohort's week. `re_weekly_class_plans` stores one row per
   * `day_of_week` with three columns (breakfast/lunch/dinner class codes) rather than per-date
   * rows — expanded here into concrete `(slotDate, mealSlot, classCode)` triples for the 7 dates
   * starting at `weekStartDate` (assumed Monday, matching DOC-P3-06 §06.5's own path-parameter
   * convention for `{week}`).
   */
  async getWeeklyClassPlan(
    cohortId: string,
    weekStartDate: string,
  ): Promise<ClassAssignment[]> {
    const { data, error } = await withTimeout(
      this.db
        .schema(RE_ENGINE_SCHEMA)
        .from("re_weekly_class_plans")
        .select("day_of_week, breakfast_class_code, lunch_class_code, dinner_class_code")
        .eq("cohort_id", cohortId),
      "cohortResolution.getWeeklyClassPlan",
    );
    if (error) dbFail("read re_weekly_class_plans", error.message);
    const rows = (data ?? []) as Array<{
      day_of_week: string;
      breakfast_class_code: string;
      lunch_class_code: string;
      dinner_class_code: string;
    }>;
    const byDay = new Map(rows.map((r) => [r.day_of_week.toLowerCase(), r]));

    const out: ClassAssignment[] = [];
    for (let i = 0; i < 7; i++) {
      const slotDate = addDays(weekStartDate, i);
      const row = byDay.get(dayOfWeekName(slotDate));
      if (!row) continue; // no seeded plan for this cohort/day — engine's own fallback path handles gaps
      out.push({ slotDate, mealSlot: "breakfast", classCode: row.breakfast_class_code });
      out.push({ slotDate, mealSlot: "lunch", classCode: row.lunch_class_code });
      out.push({ slotDate, mealSlot: "dinner", classCode: row.dinner_class_code });
    }
    return out;
  }

  /** LF-B03: non-veg cadence overlay (re_nonveg_logic, keyed by state_code). */
  async getNonVegOverlay(
    stateCode: string,
  ): Promise<{ weeklySlots: number; preferredSlots: string[] }> {
    const { data, error } = await withTimeout(
      this.db
        .schema(RE_ENGINE_SCHEMA)
        .from("re_nonveg_logic")
        .select("weekly_nonveg_slots, preferred_slots")
        .eq("state_code", stateCode)
        .maybeSingle(),
      "cohortResolution.getNonVegOverlay",
    );
    if (error) dbFail("read re_nonveg_logic", error.message);
    if (!data) return { weeklySlots: 0, preferredSlots: [] };
    const row = data as { weekly_nonveg_slots: number; preferred_slots: string[] | null };
    return { weeklySlots: row.weekly_nonveg_slots, preferredSlots: row.preferred_slots ?? [] };
  }
}

// ── NeverList / Suppression / PersonalHistory — genuinely empty for a brand-new onboarding profile ─

/** LF-D06/H (never). A profile created moments ago genuinely has zero never_list rows — this is
 * real data, not a guessed default (the profile did not exist until this request). */
export class SupabaseNeverListRepository implements NeverListRepository {
  constructor(private readonly db: SupabaseClient) {}

  async getActiveNeverDishIds(profileId: string): Promise<Set<string>> {
    const { data, error } = await withTimeout(
      this.db
        .schema(RE_ENGINE_SCHEMA)
        .from("never_list")
        .select("dish_id")
        .eq("profile_id", profileId)
        .eq("is_active", true),
      "neverList.getActiveNeverDishIds",
    );
    if (error) dbFail("read never_list", error.message);
    return new Set(((data ?? []) as Array<{ dish_id: string }>).map((r) => r.dish_id));
  }
}

/** LF-E07/G03 (not today). */
export class SupabaseSuppressionRepository implements SuppressionRepository {
  constructor(private readonly db: SupabaseClient) {}

  async getActiveNotToday(
    profileId: string,
  ): Promise<Array<{ dishId: string; daysElapsed: number }>> {
    const { data, error } = await withTimeout(
      this.db
        .schema(RE_ENGINE_SCHEMA)
        .from("not_today_suppression")
        .select("dish_id, suppressed_at")
        .eq("profile_id", profileId)
        .eq("is_active", true),
      "suppression.getActiveNotToday",
    );
    if (error) dbFail("read not_today_suppression", error.message);
    const now = Date.now();
    return ((data ?? []) as Array<{ dish_id: string; suppressed_at: string }>).map((r) => ({
      dishId: r.dish_id,
      daysElapsed: Math.floor((now - new Date(r.suppressed_at).getTime()) / 86_400_000),
    }));
  }
}

/** LF-E02: research CohortPrior (re_cohort_class_priors). Null (unseeded) is a documented,
 * expected outcome — the engine's own `cohortPrior()` applies `ScoringConfig.neutralCohortPrior`. */
export class SupabaseCohortPriorRepository implements CohortPriorRepository {
  constructor(private readonly db: SupabaseClient) {}

  async getPrior(cohortId: string, classCode: string): Promise<number | null> {
    const { data, error } = await withTimeout(
      this.db
        .schema(RE_ENGINE_SCHEMA)
        .from("re_cohort_class_priors")
        .select("acceptance_rate_prior")
        .eq("cohort_id", cohortId)
        .eq("class_code", classCode)
        .maybeSingle(),
      "cohortPrior.getPrior",
    );
    if (error) dbFail("read re_cohort_class_priors", error.message);
    return data ? (data as { acceptance_rate_prior: number }).acceptance_rate_prior : null;
  }
}

/**
 * LF-E03: user taste vector. `getUserTasteVector` is a real, direct query — a brand-new onboarding
 * profile genuinely has none yet (correctly returns null, triggering the engine's own cold-start
 * branch). `getCohortAverageVector` is the ONE placeholder in this file — see this module's header
 * doc comment for why no real query is possible today.
 */
export class SupabaseTasteVectorRepository implements TasteVectorRepository {
  constructor(private readonly db: SupabaseClient) {}

  async getUserTasteVector(profileId: string): Promise<number[] | null> {
    const { data, error } = await withTimeout(
      this.db
        .schema(RE_ENGINE_SCHEMA)
        .from("user_taste_vectors")
        .select("genome_tag_affinity")
        .eq("profile_id", profileId)
        .maybeSingle(),
      "tasteVector.getUserTasteVector",
    );
    if (error) dbFail("read user_taste_vectors", error.message);
    if (!data) return null;
    const vec = (data as { genome_tag_affinity: number[] | null }).genome_tag_affinity;
    return vec && vec.length > 0 ? vec : null;
  }

  /**
   * `[FLAGGED PLACEHOLDER — see module header]` No `re_engine` table materializes a cohort-average
   * taste vector, and `dishes.genome_vector` is variable-length per dish (8–14 dims observed live),
   * so this adapter cannot safely derive one either. Returns a neutral all-zero vector sized to
   * `DEFAULT_VECTOR_LENGTH` — the SAME treatment the engine already gives an unseeded cohort prior
   * (`neutralCohortPrior`), applied here to the one input this adapter cannot source for real.
   * `contentMatch()` against an all-zero vector degrades to its own neutral value rather than
   * favoring or penalizing any dish — the least-wrong placeholder available, not a business
   * decision made silently: flagged in the work-package report, needs a real materialized source
   * (migration) before this is trusted for production scoring.
   */
  async getCohortAverageVector(_cohortId: string): Promise<number[]> {
    return new Array(SupabaseTasteVectorRepository.DEFAULT_VECTOR_LENGTH).fill(0);
  }

  /** Matches the modal `dishes.genome_vector` length observed live (249 of ~800 dishes = 10 dims). */
  static readonly DEFAULT_VECTOR_LENGTH = 10;
}

/** LF-E04: prior interactions for a (user, dish) pair. A brand-new profile has none yet. */
export class SupabasePersonalHistoryRepository implements PersonalHistoryRepository {
  constructor(private readonly db: SupabaseClient) {}

  async getEvents(profileId: string, dishId: string): Promise<InteractionEvent[]> {
    const { data, error } = await withTimeout(
      this.db
        .from("interaction_events")
        .select("event_type, rating, occurred_at")
        .eq("profile_id", profileId)
        .eq("dish_id", dishId),
      "personalHistory.getEvents",
    );
    if (error) dbFail("read interaction_events", error.message);
    const now = Date.now();
    return ((data ?? []) as Array<
      { event_type: string; rating: number | null; occurred_at: string }
    >)
      .map((r) => ({
        eventType: r.event_type,
        rating: r.rating,
        daysElapsed: Math.floor((now - new Date(r.occurred_at).getTime()) / 86_400_000),
      }));
  }
}

/** LF-E06: Thompson-sampling Beta parameters. `re_dish_bandit_state` documented default is
 * Beta(1,1) for any (profile, dish) pair with no row yet — always true for a new profile. */
export class SupabaseBanditStateRepository implements BanditStateRepository {
  constructor(private readonly db: SupabaseClient) {}

  async getBetaParams(profileId: string, dishId: string): Promise<{ alpha: number; beta: number }> {
    const { data, error } = await withTimeout(
      this.db
        .schema(RE_ENGINE_SCHEMA)
        .from("re_dish_bandit_state")
        .select("alpha, beta")
        .eq("profile_id", profileId)
        .eq("dish_id", dishId)
        .maybeSingle(),
      "bandit.getBetaParams",
    );
    if (error) dbFail("read re_dish_bandit_state", error.message);
    return data ? (data as { alpha: number; beta: number }) : { alpha: 1, beta: 1 };
  }
}

/** LF-E05: context multipliers. No row = neutral multiplier (1.0 — the identity value for a
 * multiplicative signal; an unconfigured context should never silently boost or suppress a dish). */
export class SupabaseContextMultiplierRepository implements ContextMultiplierRepository {
  constructor(private readonly db: SupabaseClient) {}

  async getMultiplier(
    contextType: string,
    contextValue: string,
    genomeTag: string,
  ): Promise<number> {
    const { data, error } = await withTimeout(
      this.db
        .schema(RE_ENGINE_SCHEMA)
        .from("re_context_multipliers")
        .select("multiplier_value")
        .eq("context_type", contextType)
        .eq("context_value", contextValue)
        .eq("genome_tag", genomeTag)
        .maybeSingle(),
      "contextMultiplier.getMultiplier",
    );
    if (error) dbFail("read re_context_multipliers", error.message);
    return data ? (data as { multiplier_value: number }).multiplier_value : 1.0;
  }
}

/** All numeric parameters come from seed/config tables (DOC-P3-03 §16 Working Principle 7) — every
 * value below is a real read, never hardcoded here. Column-to-field mapping matches §16 exactly. */
export class SupabaseReConfigProvider implements ReConfigProvider {
  constructor(private readonly db: SupabaseClient) {}

  async getWeightLadder(): Promise<WeightLadderTier[]> {
    const { data, error } = await withTimeout(
      this.db
        .schema(RE_ENGINE_SCHEMA)
        .from("re_weight_ladder_config")
        .select("lower_bound, upper_bound, w_cohort, w_content, w_history, w_context, w_explore")
        .order("lower_bound", { ascending: true }),
      "reConfig.getWeightLadder",
    );
    if (error) dbFail("read re_weight_ladder_config", error.message);
    return ((data ?? []) as Array<{
      lower_bound: number;
      upper_bound: number | null;
      w_cohort: number;
      w_content: number;
      w_history: number;
      w_context: number;
      w_explore: number;
    }>).map((r) => ({
      lowerBound: r.lower_bound,
      upperBound: r.upper_bound ?? Number.MAX_SAFE_INTEGER,
      weights: {
        wCohort: r.w_cohort,
        wContent: r.w_content,
        wHistory: r.w_history,
        wContext: r.w_context,
        wExplore: r.w_explore,
      },
    }));
  }

  async getScoringConfig(): Promise<ScoringConfig> {
    const { data, error } = await withTimeout(
      this.db.schema(RE_ENGINE_SCHEMA).from("re_scoring_config").select("config_key, config_value"),
      "reConfig.getScoringConfig",
    );
    if (error) dbFail("read re_scoring_config", error.message);
    const kv = new Map(
      ((data ?? []) as Array<{ config_key: string; config_value: number }>).map((r) => [
        r.config_key,
        r.config_value,
      ]),
    );
    // DOC-P3-03 §16 / §17 U-001. `neutralCohortPrior`, `slateSize`, `minCandidates` are not stored
    // as re_scoring_config rows in the live schema (confirmed) — DOC-P3-03 §16/§07 documented
    // constants, kept as named fallbacks here rather than a 6th untraceable magic number scattered
    // in the engine itself.
    return {
      notTodayP0: kv.get("not_today_P0") ?? 0.80,
      notTodayLambda: kv.get("not_today_lambda") ?? 0.35,
      notTodayDecayThreshold: kv.get("not_today_decay_threshold") ?? 0.05,
      personalHistoryLambda: kv.get("personal_history_lambda") ?? 0.05,
      mmrLambda: kv.get("mmr_lambda_mvp") ?? 0.70,
      explorationBonusMax: kv.get("exploration_bonus_max") ?? 0.15,
      contextOverrideThreshold: kv.get("context_override_threshold") ?? 0.90,
      coldStartExitThreshold: 14, // DOC-P3-03 §16 CDM Entity 14 — not a re_scoring_config row
      neutralCohortPrior: 0.50, // DOC-P3-03 §16 LF-E02 documented fallback
      slateSize: 8, // DOC-P3-04 §03.16 rank_in_slate CHECK 1–8
      minCandidates: 3, // LF-D07 documented coverage-gap threshold
    };
  }

  async getVarietyRules(): Promise<VarietyRule[]> {
    const { data, error } = await withTimeout(
      this.db
        .schema(RE_ENGINE_SCHEMA)
        .from("re_variety_rules")
        .select("rule_name, window_days, cap_value, override_condition"),
      "reConfig.getVarietyRules",
    );
    if (error) dbFail("read re_variety_rules", error.message);
    return ((data ?? []) as Array<{
      rule_name: string;
      window_days: number;
      cap_value: number;
      override_condition: string | null;
    }>).map((r) => ({
      ruleName: r.rule_name,
      windowDays: r.window_days,
      capValue: r.cap_value,
      overrideCondition: r.override_condition,
    }));
  }

  /**
   * LF-E04. `re_event_weights.event_type` seed values are already rating-specific
   * (`dish_rated_5star`/`_3star`/`_1star`) rather than a generic `dish_rated` + separate rating
   * column — confirmed live. Maps a raw `interaction_events.event_type` + `rating` pair onto the
   * matching config row: exact `event_type` match first (covers non-rating events like
   * `dish_cooked`/`dish_locked` directly), else the rating-banded key for `dish_rated`.
   */
  async getEventWeight(eventType: string, rating: number | null): Promise<number> {
    const key = eventType === "dish_rated" && rating !== null
      ? `dish_rated_${rating >= 5 ? 5 : rating >= 3 ? 3 : 1}star`
      : eventType;
    const { data, error } = await withTimeout(
      this.db
        .schema(RE_ENGINE_SCHEMA)
        .from("re_event_weights")
        .select("weight")
        .eq("event_type", key)
        .maybeSingle(),
      "reConfig.getEventWeight",
    );
    if (error) dbFail("read re_event_weights", error.message);
    return data ? (data as { weight: number }).weight : 0;
  }

  async getActiveReVersion(): Promise<string> {
    const { data, error } = await withTimeout(
      this.db
        .schema(RE_ENGINE_SCHEMA)
        .from("re_engine_versions")
        .select("version_code")
        .eq("is_active", true)
        .limit(1)
        .maybeSingle(),
      "reConfig.getActiveReVersion",
    );
    if (error) dbFail("read re_engine_versions", error.message);
    if (!data) {
      throw new AppError(ERROR_CATALOGUE.INTERNAL, { detail: "no active re_engine_versions row" });
    }
    return (data as { version_code: string }).version_code;
  }
}

/** LF-E06 Thompson sampling. Uses the platform's CSPRNG (`crypto`) via `Math.random` is NOT used —
 * `crypto.getRandomValues` backs a uniform [0,1) generator; Box-Muller derives the standard normal
 * the gamma/Beta sampler needs (`_shared/services/re/scoring.ts` `sampleBeta`/`sampleGamma`). */
export class SystemRandom implements Random {
  uniform(): number {
    const buf = new Uint32Array(1);
    crypto.getRandomValues(buf);
    return buf[0] / 4294967296; // buf[0] / 2^32 → [0, 1)
  }

  normal(): number {
    // Box-Muller transform — standard, deterministic given two uniforms, no injected library.
    let u = 0;
    let v = 0;
    while (u === 0) u = this.uniform();
    while (v === 0) v = this.uniform();
    return Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v);
  }
}
