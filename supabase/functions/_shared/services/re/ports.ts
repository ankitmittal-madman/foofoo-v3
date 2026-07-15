/**
 * Recommendation Engine — repository & config PORTS (WP-8D).
 *
 * The RE core depends only on these interfaces, never on a concrete DB client (DDD / hexagonal;
 * DOC-P4-00 §4 repository pattern, §20 DI). Concrete Supabase-backed adapters are a later WP; unit
 * tests inject in-memory fakes. This keeps the engine pure, reusable, and independently testable
 * (the WP-8D requirement). Every method maps to a DOC-P3-03 logical function / DOC-P3-04 table.
 */
import type {
  ClassAssignment,
  DishCandidate,
  InteractionEvent,
  ScoringConfig,
  VarietyRule,
  WeightLadderTier,
} from "./types.ts";

/** LF-D01: candidate dishes for a meal class (re_class_dish_options ⨝ dishes; ICD-1 scope). */
export interface CandidateRepository {
  getClassCandidates(classCode: string): Promise<DishCandidate[]>;
  /** LF-D07 fallback: 8 most-popular dishes filtered by diet_type only. */
  getPopularFallback(dietType: string, limit: number): Promise<DishCandidate[]>;
}

/** LF-D06 / LF-H (never): active Never-listed dish ids (re_engine.never_list). */
export interface NeverListRepository {
  getActiveNeverDishIds(profileId: string): Promise<Set<string>>;
}

/** LF-E07 / LF-G03: active Not-Today suppression rows (re_engine.not_today_suppression). */
export interface SuppressionRepository {
  getActiveNotToday(profileId: string): Promise<Array<{ dishId: string; daysElapsed: number }>>;
}

/** LF-E02: research CohortPrior (re_cohort_class_priors). Returns null when unseeded → caller
 * applies the documented neutral fallback (see ScoringConfig.neutralCohortPrior). */
export interface CohortPriorRepository {
  getPrior(cohortId: string, classCode: string): Promise<number | null>;
}

/** LF-E03: user taste vector (re_engine.user_taste_vectors); cold-start → cohort average. */
export interface TasteVectorRepository {
  getUserTasteVector(profileId: string): Promise<number[] | null>;
  getCohortAverageVector(cohortId: string): Promise<number[]>;
}

/** LF-E04: prior interactions for a (user, dish) pair (interaction_events). */
export interface PersonalHistoryRepository {
  getEvents(profileId: string, dishId: string): Promise<InteractionEvent[]>;
}

/** LF-E06: Thompson-sampling Beta parameters (re_engine.re_dish_bandit_state); default Beta(1,1). */
export interface BanditStateRepository {
  getBetaParams(profileId: string, dishId: string): Promise<{ alpha: number; beta: number }>;
}

/** LF-E05: context multipliers (re_context_multipliers). */
export interface ContextMultiplierRepository {
  getMultiplier(contextType: string, contextValue: string, genomeTag: string): Promise<number>;
}

/** LF-A09/B01/B02 resolution: persona → cohort → weekly class plan. */
export interface CohortResolutionRepository {
  /** LF-A09: (main_cohort, sub_cohort, home_state, diet) → persona (re_persona_assignment_rules);
   * null triggers Option-B fallback (broadest state coverage for the main cohort). */
  assignPersona(
    mainCohortCode: string,
    subCohortTag: string,
    homeState: string,
    dietType: string,
  ): Promise<{ personaId: string; overlayPersonaIds: string[] } | null>;
  assignPersonaFallback(
    mainCohortCode: string,
  ): Promise<{ personaId: string; overlayPersonaIds: string[]; cohortId: string }>;
  /** LF-B02: (persona × state × diet) → cohort_id (re_cohorts, tier-aware SER-001). */
  resolveCohort(personaId: string, stateCode: string, dietMode: string): Promise<string | null>;
  /** LF-B02: 21 class assignments for a cohort (re_weekly_class_plans, 20,664 rows). */
  getWeeklyClassPlan(
    cohortId: string,
    weekStartDate: string,
  ): Promise<ClassAssignment[]>;
  /** LF-B03: non-veg cadence overlay (re_nonveg_logic). */
  getNonVegOverlay(stateCode: string): Promise<{ weeklySlots: number; preferredSlots: string[] }>;
}

/** Config provider — all numeric parameters come from seed/config tables, never hardcoded
 * (DOC-P3-03 §16 Working Principle 7). Fakes supply the §16 values in tests. */
export interface ReConfigProvider {
  getWeightLadder(): Promise<WeightLadderTier[]>;
  getScoringConfig(): Promise<ScoringConfig>;
  getVarietyRules(): Promise<VarietyRule[]>;
  /** LF-E04 event weights (re_event_weights). */
  getEventWeight(eventType: string, rating: number | null): Promise<number>;
  getActiveReVersion(): Promise<string>;
}

/** Injectable randomness for the Thompson-sampling bandit (LF-E06) — deterministic in tests. */
export interface Random {
  /** Uniform [0,1). */
  uniform(): number;
  /** Standard normal (for the gamma/Beta sampler). */
  normal(): number;
}
