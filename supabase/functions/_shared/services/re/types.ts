/**
 * Recommendation Engine — domain types / DTOs (WP-8D).
 *
 * Pure domain model for the reusable RE core. These types carry exactly the fields the frozen
 * business logic (DOC-P3-03 §02–11) and schema (DOC-P3-04) define — no invented fields. The engine
 * is caller-agnostic (RE-DOC-01 isolation; DOC-P4-00 §3/§14): the same core is invoked by
 * /v1/recommendations, the nightly plan job, and (per DOC-P3-02 Domain Events "PlanPreviewGenerated",
 * actor = RE Engine) the onboarding orchestrator. Nothing here reads HTTP or the database directly.
 */

/** Diet vocabulary (DOC-P3-03 §03 LF-A04; dishes.diet_type CHECK). */
export type DietType = "veg" | "non_veg" | "egg" | "vegan" | "jain";

/** Religious preference vocabulary (DOC-P3-03 §03 LF-A04). */
export type ReligiousPref = "all" | "hindu_veg" | "jain" | "halal" | "no_beef" | "no_pork";

/** Meal slot (DOC-P3-04 plan_slots.meal_slot). */
export type MealSlot = "breakfast" | "lunch" | "dinner" | "snack";

/** Household constraints resolved during onboarding (DOC-P3-03 §03; DOC-P3-02 Entities 5–8). */
export interface HouseholdConstraints {
  readonly profileId: string;
  readonly dietType: DietType;
  readonly religiousPref: ReligiousPref;
  /** Bitfield union base (user); members merged separately (LF-A05, CDM Invariant 3). */
  readonly allergenFlags: number;
  readonly cookCapability: "beginner" | "intermediate" | "advanced";
  readonly homeState: string;
}

/** Active household member (DOC-P3-02 Entity 3; LF-A05 allergen union). */
export interface HouseholdMember {
  readonly segment: string;
  readonly allergenFlags: number;
  readonly isActive: boolean;
}

/** User RE state (DOC-P3-04 re_engine.user_re_state; DOC-P3-02 Entities 11–14). */
export interface UserReState {
  readonly profileId: string;
  readonly personaId: string;
  readonly overlayPersonaIds: string[];
  readonly cohortId: string;
  readonly confidenceScore: number;
  readonly coldStartMode: boolean;
  readonly interactionCount: number;
  readonly reEngineVersion: string;
}

/** Situational context assembled per request (DOC-P3-03 §11 LF-I01; DOC-P3-02 Entity 43). */
export interface RecommendationContext {
  readonly mealSlot: MealSlot;
  readonly slotDate: string; // YYYY-MM-DD
  readonly dayType: "weekday" | "weekend";
  readonly weather?: "rainy" | "hot" | "cold" | "mild";
  readonly season?: string;
  readonly isMonsoon: boolean;
}

/**
 * A candidate dish for a class, materialised by the CandidateRepository (LF-D01). Carries the
 * fields the hard-constraint filters (§06) and scoring (§07) need. `ingredientAllergenUnion` is the
 * ingredient-level allergen OR (LF-D03 / Safety Gate 2 — never the dish-level cache, GR-06).
 */
export interface DishCandidate {
  readonly dishId: string;
  readonly baseScore: number;
  readonly dietType: DietType;
  readonly isJain: boolean;
  readonly ingredientAllergenUnion: number;
  readonly mealOccasions: string[];
  readonly classCode: string;
  readonly genomeVector: number[];
  readonly cookTimeBandMinutes: number;
  readonly seasonalAffinity: string[];
  /** Variety-relevant genome dimensions (LF-F01 similarity). */
  readonly cuisineFamily: string;
  readonly cookingMethod: string;
  readonly mainIngredientClass: string;
  readonly texture: string;
  /** Religious ingredient markers (LF-D04 ingredient-level; true if the dish contains the item). */
  readonly hasNonHalalMeat: boolean;
  readonly hasBeef: boolean;
  readonly hasPork: boolean;
}

/** A candidate after FinalScore assembly (LF-E08). */
export interface ScoredCandidate {
  readonly candidate: DishCandidate;
  readonly score: number;
  readonly signals: ScoreSignals;
}

/** The five FinalScore signals + penalty, retained for auditability (DOC-P3-03A §08). */
export interface ScoreSignals {
  readonly cohortPrior: number;
  readonly contentMatch: number;
  readonly personalHistory: number;
  readonly contextFit: number;
  readonly explorationBonus: number;
  readonly penalty: number;
}

/** Scoring weights (LF-E01 weight ladder). */
export interface ScoringWeights {
  readonly wCohort: number;
  readonly wContent: number;
  readonly wHistory: number;
  readonly wContext: number;
  readonly wExplore: number;
}

/** One ranked dish in a slate (surfaces the already-computed FinalScore for DOC-P3-06 §06.4). */
export interface RankedDish {
  readonly dishId: string;
  readonly rank: number;
  readonly score: number;
  readonly reasonTags: string[];
}

/** A generated slate for one plan slot (DOC-P3-02 Entity 25; ≤8 dishes). */
export interface Slate {
  readonly mealSlot: MealSlot;
  readonly slotDate: string;
  readonly classCode: string;
  /** Ranked dishes (rank 1 = headline). Surfaces engine output; no logic added here. */
  readonly ranked: RankedDish[];
  readonly dishIds: string[];
  readonly reasonTags: Record<string, string[]>;
  readonly confidence: number;
  readonly coldStartMode: boolean;
  readonly reVersion: string;
  /** True when the static popular-dish fallback was used (LF-D07). */
  readonly fallbackUsed: boolean;
}

/** One class assignment in the weekly class plan (LF-B02). */
export interface ClassAssignment {
  readonly slotDate: string;
  readonly mealSlot: MealSlot;
  readonly classCode: string;
}

/** The engine's week-plan output — an in-memory plan object; persistence is the caller's concern
 * (DOC-P3-02 Domain Events: RE Engine generates Week Plan / Plan Slots; a repository persists). */
export interface GeneratedWeekPlan {
  readonly profileId: string;
  readonly weekStartDate: string;
  readonly reVersion: string;
  readonly coldStartMode: boolean;
  readonly slots: Slate[];
}

/** An interaction event relevant to PersonalHistory (LF-E04; DOC-P3-04 interaction_events). */
export interface InteractionEvent {
  readonly eventType: string;
  readonly rating: number | null;
  readonly daysElapsed: number;
}

/** Weight-ladder tier row (DOC-P3-03 §07 LF-E01 / §16). */
export interface WeightLadderTier {
  readonly lowerBound: number;
  readonly upperBound: number;
  readonly weights: ScoringWeights;
}

/** A variety-window rule (DOC-P3-03 §08 LF-F02 / §16 re_variety_rules). */
export interface VarietyRule {
  readonly ruleName: string;
  readonly windowDays: number;
  readonly capValue: number;
  readonly overrideCondition: string | null;
}

/** Scoring scalar config (DOC-P3-03 §07/§16 re_scoring_config). */
export interface ScoringConfig {
  readonly notTodayP0: number; // 0.80
  readonly notTodayLambda: number; // 0.35
  readonly notTodayDecayThreshold: number; // 0.05
  readonly personalHistoryLambda: number; // 0.05
  readonly mmrLambda: number; // 0.70 MVP
  readonly explorationBonusMax: number; // 0.15
  readonly contextOverrideThreshold: number; // U-001 suggested 0.90
  readonly coldStartExitThreshold: number; // 14
  readonly neutralCohortPrior: number; // 0.50 fallback (LF-E02)
  readonly slateSize: number; // 8
  readonly minCandidates: number; // 3 (LF-D07)
}
