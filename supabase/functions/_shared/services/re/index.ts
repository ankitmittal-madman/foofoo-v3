/**
 * Recommendation Engine — public barrel (WP-8D).
 *
 * Single import surface for the reusable RE core. Callers (/v1/recommendations, nightly plan job,
 * onboarding orchestrator) import the engine + types from here; concrete Supabase-backed port
 * adapters are wired in their own WP. Pure domain logic only — no DB, no HTTP.
 */
export { RecommendationEngine } from "./engine.ts";
export type { EngineDeps, SlotRequest } from "./engine.ts";

export * from "./types.ts";
export type {
  BanditStateRepository,
  CandidateRepository,
  CohortPriorRepository,
  CohortResolutionRepository,
  ContextMultiplierRepository,
  NeverListRepository,
  PersonalHistoryRepository,
  Random,
  ReConfigProvider,
  SuppressionRepository,
  TasteVectorRepository,
} from "./ports.ts";

export {
  applyHardConstraints,
  combinedAllergenFlags,
  passesAllergen,
  passesDietType,
  passesMealOccasion,
  passesNeverList,
  passesReligious,
} from "./constraints.ts";

export {
  cohortPrior,
  contentMatch,
  contextFit,
  explorationBonus,
  finalScore,
  interpolateWeightLadder,
  notTodayPenalty,
  personalHistory,
  sampleBeta,
  sampleGamma,
  updateBanditParams,
} from "./scoring.ts";

export { applyMmr, checkVarietyWindow, varietySimilarity } from "./variety.ts";
export type { PlannedSlot, VarietyViolation } from "./variety.ts";

export { checkPlanningRoleGate, runSafetyGates } from "./safety.ts";
export type { SafetyProfile, SafetyViolation } from "./safety.ts";

export { classForSlot, resolvePersonaAndCohort, resolveWeeklyClassPlan } from "./resolvers.ts";
export type { PersonaResolution } from "./resolvers.ts";
