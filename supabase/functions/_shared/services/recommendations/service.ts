/**
 * Recommendations service (WP-8E) — POST /v1/recommendations (DOC-P3-06 §06.4).
 *
 * Loads the caller's RE inputs, invokes the SAME reusable RE Engine (WP-8D) for a single slot, and
 * persists the fresh slate. Contains ZERO recommendation logic. This is the second of the three
 * engine callers (onboarding, this endpoint, nightly job) — all share one engine implementation
 * (DOC-P4-00 §5/§14; DCR-P3-06-007).
 */
import type { RecommendationEngine } from "../re/engine.ts";
import type {
  HouseholdConstraints,
  HouseholdMember,
  MealSlot,
  RecommendationContext,
  UserReState,
} from "../re/types.ts";
import type { WeekPlanStore } from "../planning/persistence.ts";
import { slateToRow } from "../planning/persistence.ts";
import { AppError } from "../../errors/app-error.ts";
import { API_ERRORS } from "../../errors/api-catalogue.ts";

/** Loads a user's RE inputs (user_re_state + profile constraints + members). */
export interface ReStateStore {
  loadUser(profileId: string): Promise<
    { user: UserReState; constraints: HouseholdConstraints; members: HouseholdMember[] } | null
  >;
}

/** Reads the fixed class for an existing plan slot (LF-L03: class does not change on refresh). */
export interface PlanSlotStore {
  getSlotClass(
    profileId: string,
    slotDate: string,
    mealSlot: MealSlot,
  ): Promise<{ weekPlanId: string; classCode: string } | null>;
}

/** DOC-P3-06 §06.4 request. */
export interface RecommendationsRequest {
  readonly userId: string;
  readonly mealSlot: MealSlot;
  readonly date: string;
  readonly context: RecommendationContext;
  readonly excludeDishIds: string[];
}

/** DOC-P3-06 §06.4 response. */
export interface RecommendationsResponse {
  readonly slate_id: string;
  readonly confidence: number;
  readonly cold_start_mode: boolean;
  readonly re_version: string;
  readonly class_code: string;
  readonly dishes: Array<{ dish_id: string; rank: number; score: number; reason_tags: string[] }>;
}

export class RecommendationService {
  constructor(
    private readonly reState: ReStateStore,
    private readonly planSlots: PlanSlotStore,
    private readonly engine: RecommendationEngine,
    private readonly weekPlanStore: WeekPlanStore,
  ) {}

  async recommend(req: RecommendationsRequest): Promise<RecommendationsResponse> {
    const loaded = await this.reState.loadUser(req.userId);
    if (!loaded) {
      throw new AppError(API_ERRORS.ERR_VALIDATION_FAILED, { detail: "no RE state for user" });
    }

    const slot = await this.planSlots.getSlotClass(req.userId, req.date, req.mealSlot);
    if (!slot) {
      throw new AppError(API_ERRORS.ERR_PLAN_NOT_FOUND, { detail: "plan_not_yet_generated" });
    }

    // Same engine as onboarding and the nightly job — single source of recommendation logic.
    const slate = await this.engine.generateSlate({
      user: loaded.user,
      constraints: loaded.constraints,
      members: loaded.members,
      context: req.context,
      classCode: slot.classCode,
      excludeDishIds: new Set(req.excludeDishIds),
    });

    const persisted = await this.weekPlanStore.updateSlotSlate(slot.weekPlanId, slateToRow(slate));

    return {
      slate_id: persisted.slotId,
      confidence: slate.confidence,
      cold_start_mode: slate.coldStartMode,
      re_version: slate.reVersion,
      class_code: slate.classCode,
      dishes: slate.ranked.map((r) => ({
        dish_id: r.dishId,
        rank: r.rank,
        score: r.score,
        reason_tags: r.reasonTags,
      })),
    };
  }
}
