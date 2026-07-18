/**
 * Onboarding orchestrator (WP-8E).
 *
 * Owns ONBOARDING logic only (DOC-P3-03 §03 LF-A01–A09: answer processing, confidence, city-overlay,
 * persona resolution) and ORCHESTRATES the reusable RE Engine (WP-8D) for the first week plan. It
 * contains ZERO recommendation logic — candidate/score/rank/safety all live in the engine. Per
 * DOC-P3-02 Domain Events (`PersonaAssigned`, `PlanPreviewGenerated`, actor = RE Engine) the engine
 * generates the plan; this orchestrator persists it (via WeekPlanStore) and returns the handle
 * (DOC-P3-06 §06.2). Idempotent per household (§06.2/§08).
 */
import type { RecommendationEngine } from "../re/engine.ts";
import type { CohortResolutionRepository } from "../re/ports.ts";
import type {
  DietType,
  HouseholdConstraints,
  HouseholdMember,
  MealSlot,
  RecommendationContext,
  ReligiousPref,
  UserReState,
} from "../re/types.ts";
import { resolvePersonaAndCohort } from "../re/resolvers.ts";
import { toPersistable, type WeekPlanStore } from "../planning/persistence.ts";
import { AppError } from "../../errors/app-error.ts";
import { API_ERRORS } from "../../errors/api-catalogue.ts";

/** Parsed onboarding answers (from DOC-P3-06 §06.2 request `answers`; parsing is the endpoint's job). */
export interface OnboardingAnswers {
  readonly mainCohortCode: string;
  readonly subCohortTag: string;
  /** FD-15 Phase 2 (SER-004): each member carries zero or more independent condition tags. */
  readonly members: Array<{ conditions: string[]; memberName?: string; allergenFlags: number }>;
  readonly homeState: string | null;
  readonly currentCity: string | null;
  readonly migrationBand: MigrationBand | null;
  readonly dietType: DietType | null;
  readonly religiousPref: ReligiousPref | null;
  readonly allergenFlags: number;
  readonly cookCapability: "beginner" | "intermediate" | "advanced" | null;
  readonly primaryCookName: string;
  readonly pushNotificationTime: string;
  /** OB-07 class-preference swipes → count toward interaction_count (capped 10, LF-A07). */
  readonly classSwipeCount: number;
  readonly ob07Completed: boolean;
  readonly skippedScreens: string[];
}

export type MigrationBand = "native" | "lt_1yr" | "1_3yr" | "3_7yr" | "7plus_yr" | "skipped";

/** DOC-P3-06 §06.2 response. */
export interface OnboardingResult {
  readonly profile_id: string;
  readonly persona_id: string;
  readonly overlay_persona_ids: string[];
  readonly confidence_score: number;
  readonly cold_start_mode: boolean;
  readonly onboarding_completed: boolean;
  readonly first_week_plan: { week_plan_id: string; week_start_date: string };
}

/** Persistence port for onboarding's OWN writes (never plan tables — those are WeekPlanStore). */
export interface OnboardingStore {
  /** DOC-P3-06 §06.1 / DOC-09 §03: personalization consent must precede onboarding. */
  isPersonalizationGranted(profileId: string): Promise<boolean>;
  isOnboardingComplete(profileId: string): Promise<boolean>;
  persistProfile(row: ProfileRow): Promise<void>;
  persistHouseholdMembers(profileId: string, members: HouseholdMemberRow[]): Promise<void>;
  persistOnboardingSessions(profileId: string, sessions: OnboardingSessionRow[]): Promise<void>;
  persistUserReState(row: UserReStateRow): Promise<void>;
  persistTasteVector(profileId: string, classAffinity: Record<string, number>): Promise<void>;
}

export interface ProfileRow {
  readonly id: string;
  readonly primary_cook_name: string;
  readonly home_state: string;
  readonly current_city: string;
  readonly migration_duration_band: MigrationBand | null;
  readonly city_overlay_weight: number;
  readonly diet_type: DietType;
  readonly religious_pref: ReligiousPref;
  readonly allergen_flags: number;
  readonly cook_capability: "beginner" | "intermediate" | "advanced";
  readonly push_notification_time: string;
  readonly onboarding_completed: boolean;
}
export interface HouseholdMemberRow {
  readonly member_name: string | null;
  /** FD-15 Phase 2 (SER-004): household_members.conditions (text[]), not the old scalar segment. */
  readonly conditions: string[];
  readonly allergen_flags: number;
}
export interface OnboardingSessionRow {
  readonly screen_id: string;
  readonly question_key: string;
  readonly answer_value: unknown;
  readonly skipped: boolean;
}
export interface UserReStateRow {
  readonly profile_id: string;
  readonly persona_id: string;
  readonly overlay_persona_ids: string[];
  readonly confidence_score: number;
  readonly interaction_count: number;
  readonly cold_start_mode: boolean;
  readonly re_engine_version: string;
  readonly city_overlay_weight: number;
}

/** LF-A03 city-overlay weight from migration band (DOC-P3-03 §03; DOC-06 C-11). */
export function cityOverlayWeight(band: MigrationBand | null): number {
  switch (band) {
    case "native":
      return 0.0;
    case "lt_1yr":
      return 0.15;
    case "1_3yr":
      return 0.30;
    case "3_7yr":
      return 0.50;
    case "7plus_yr":
      return 0.70;
    case "skipped":
    case null:
      return 0.50; // 3-year default (LF-A03)
  }
}

/** LF-A08 onboarding confidence (DOC-P3-03 §03; RE-DOC-04 §01). Clamped to the schema CHECK 0.35–1.0. */
export function computeOnboardingConfidence(a: OnboardingAnswers): number {
  const dietSkipped = a.dietType === null;
  const ob03Skipped = a.homeState === null && a.currentCity === null;
  const everythingSkipped = dietSkipped && ob03Skipped && !a.ob07Completed &&
    a.cookCapability === null;
  if (everythingSkipped) return 0.35;

  let c = 0.40; // base floor, all users
  if (a.homeState !== null) c += 0.15;
  if (a.dietType !== null) c += 0.10;
  if (a.currentCity !== null) c += 0.08; // city overlay found
  if (a.cookCapability !== null) c += 0.07;
  if (a.ob07Completed) c += 0.12;
  c += 0.08; // contextual signals, always
  if (dietSkipped) c -= 0.15;
  if (ob03Skipped) c -= 0.08;
  // DOC-P3-03 §03 LF-A08: "Maximum at Day 0 completion: 0.65" (Range Day 0: 0.40–0.65). The 1.0
  // schema ceiling is for later warm-state evolution as interaction_count grows, not onboarding.
  return Math.max(0.35, Math.min(0.65, c));
}

/**
 * Mutually-exclusive age-band life-stage tags (SER-004 §11 implementation risk: the
 * household_members.conditions CHECK validates vocabulary membership only, not business-rule
 * exclusivity — enforced here at the application layer instead, per this repository's existing
 * pattern of keeping business-rule validation in code, not DB triggers). Scoped narrowly to
 * values that represent sequential, non-overlapping age bands for the same growing child — NOT
 * every condition that happens to correlate with age (e.g. `picky_child`, `elderly_member`, and
 * `recovery_member` are deliberately excluded: the research evidence (Canonical Planning Model
 * §7 stress test — "Elderly couple + Recovery") shows those legitimately co-occur with an age
 * band or with each other on the same member).
 */
const EXCLUSIVE_LIFE_STAGE_TAGS: ReadonlySet<string> = new Set([
  "baby_6_18m",
  "toddler",
  "school_child",
  "teen_high_appetite",
]);

/** LF-A05 area, application-layer only (SER-004 §11) — a member may carry at most one age-band tag. */
export function assertNoConflictingLifeStageTags(conditions: readonly string[]): void {
  const present = conditions.filter((c) => EXCLUSIVE_LIFE_STAGE_TAGS.has(c));
  if (present.length > 1) {
    throw new AppError(API_ERRORS.ERR_VALIDATION_FAILED, {
      detail: `household member carries mutually-exclusive life-stage tags: ${present.join(", ")}`,
      context: { conflictingConditions: present },
    });
  }
}

export class OnboardingOrchestrator {
  constructor(
    private readonly store: OnboardingStore,
    private readonly cohortRepo: CohortResolutionRepository,
    private readonly engine: RecommendationEngine,
    private readonly weekPlanStore: WeekPlanStore,
    private readonly reVersion: string,
    private readonly nonVegMainClass: string,
  ) {}

  /**
   * Complete onboarding: capture (LF-A01–A08) → resolve persona/cohort (LF-A09) → invoke the RE
   * Engine for the first week plan → persist → return the §06.2 response. Idempotent: a completed
   * household re-submitting gets 409.
   */
  async completeOnboarding(
    userId: string,
    answers: OnboardingAnswers,
    weekStartDate: string,
    contextForSlot: (slotDate: string, mealSlot: MealSlot) => RecommendationContext,
  ): Promise<OnboardingResult> {
    // Consent gate (DOC-P3-06 §06.1 / DOC-09 §03): personalization must be granted first.
    if (!(await this.store.isPersonalizationGranted(userId))) {
      throw new AppError(API_ERRORS.ERR_CONSENT_REQUIRED, {
        detail: "personalization consent not granted",
      });
    }
    if (await this.store.isOnboardingComplete(userId)) {
      throw new AppError(API_ERRORS.ERR_ONBOARDING_ALREADY_COMPLETE, {
        detail: "onboarding already completed for this profile",
      });
    }

    const dietType: DietType = answers.dietType ?? "veg"; // LF-A04 skip → veg base, penalty in confidence
    // Jain rule (LF-A04 / CDM Entity 5): jain diet forces jain religious pref.
    const religiousPref: ReligiousPref = dietType === "jain"
      ? "jain"
      : (answers.religiousPref ?? "all");
    const overlayWeight = cityOverlayWeight(answers.migrationBand);
    const confidence = computeOnboardingConfidence(answers);
    const interactionCount = Math.min(answers.classSwipeCount, 10); // LF-A07 cap
    const cookCapability = answers.cookCapability ?? "beginner"; // LF-A06 skip default

    // SER-004 §11: application-layer business rule, not a DB constraint — reject conflicting
    // age-band tags on any single member before persisting anything.
    for (const m of answers.members) {
      assertNoConflictingLifeStageTags(m.conditions);
    }

    // LF-A09 — resolve persona then cohort (Option-B fallback inside the resolver).
    const dietMode = dietType === "non_veg" || dietType === "egg" ? "non_veg" : "veg";
    const persona = await resolvePersonaAndCohort(this.cohortRepo, {
      mainCohortCode: answers.mainCohortCode,
      subCohortTag: answers.subCohortTag,
      homeState: answers.homeState ?? "",
      dietType,
      dietMode,
    });

    // Persist onboarding's OWN writes (never plan tables).
    await this.store.persistProfile({
      id: userId,
      primary_cook_name: answers.primaryCookName,
      home_state: answers.homeState ?? "",
      current_city: answers.currentCity ?? "",
      migration_duration_band: answers.migrationBand,
      city_overlay_weight: overlayWeight,
      diet_type: dietType,
      religious_pref: religiousPref,
      allergen_flags: answers.allergenFlags,
      cook_capability: cookCapability,
      push_notification_time: answers.pushNotificationTime,
      onboarding_completed: true,
    });
    await this.store.persistHouseholdMembers(
      userId,
      answers.members.map((m) => ({
        member_name: m.memberName ?? null,
        conditions: m.conditions,
        allergen_flags: m.allergenFlags,
      })),
    );
    await this.store.persistOnboardingSessions(
      userId,
      answers.skippedScreens.map((s) => ({
        screen_id: s,
        question_key: s,
        answer_value: null,
        skipped: true,
      })),
    );
    await this.store.persistUserReState({
      profile_id: userId,
      persona_id: persona.personaId,
      overlay_persona_ids: persona.overlayPersonaIds,
      confidence_score: confidence,
      interaction_count: interactionCount,
      cold_start_mode: true,
      re_engine_version: this.reVersion,
      city_overlay_weight: overlayWeight,
    });
    await this.store.persistTasteVector(userId, {}); // class_affinity seeded empty; OB-07 events feed it later

    // Invoke the reusable RE Engine for the first week plan (engine owns ALL recommendation logic).
    const user: UserReState = {
      profileId: userId,
      personaId: persona.personaId,
      overlayPersonaIds: persona.overlayPersonaIds,
      cohortId: persona.cohortId,
      confidenceScore: confidence,
      coldStartMode: true,
      interactionCount,
      reEngineVersion: this.reVersion,
    };
    const constraints: HouseholdConstraints = {
      profileId: userId,
      dietType,
      religiousPref,
      allergenFlags: answers.allergenFlags,
      cookCapability,
      homeState: answers.homeState ?? "",
    };
    const members: HouseholdMember[] = answers.members.map((m) => ({
      conditions: m.conditions,
      allergenFlags: m.allergenFlags,
      isActive: true,
    }));

    const plan = await this.engine.generateWeekPlan(
      user,
      constraints,
      members,
      weekStartDate,
      contextForSlot,
      { nonVegMainClass: this.nonVegMainClass },
    );

    // Persist the plan (Plan Assembly → Persistence responsibility) and return the handle.
    const { header, slots } = toPersistable(plan);
    const persisted = await this.weekPlanStore.persistWeekPlan(header, slots);

    return {
      profile_id: userId,
      persona_id: persona.personaId,
      overlay_persona_ids: persona.overlayPersonaIds,
      confidence_score: confidence,
      cold_start_mode: true,
      onboarding_completed: true,
      first_week_plan: {
        week_plan_id: persisted.weekPlanId,
        week_start_date: persisted.weekStartDate,
      },
    };
  }
}
