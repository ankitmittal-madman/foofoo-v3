/**
 * Nightly plan scheduler (WP-8E) — LF-L01 generateWeekPlan CRON (DOC-P3-03 §14; 23:30 UTC).
 *
 * The third engine caller. For every eligible user (last_active_at within 7 days, §14) it invokes
 * the SAME reusable RE Engine (WP-8D) and persists the week plan — identical to onboarding's plan
 * step, just batched and scheduled. ZERO recommendation logic here; the engine owns it all
 * (DCR-P3-06-007: the CRON calls the shared service, never the public HTTP endpoint).
 */
import type { RecommendationEngine } from "../re/engine.ts";
import type {
  HouseholdConstraints,
  HouseholdMember,
  MealSlot,
  RecommendationContext,
  UserReState,
} from "../re/types.ts";
import { toPersistable, type WeekPlanStore } from "../planning/persistence.ts";
import type { Logger } from "../../logging/logger.ts";

/** An eligible user's RE inputs for scheduled generation (§14). */
export interface EligibleUser {
  readonly user: UserReState;
  readonly constraints: HouseholdConstraints;
  readonly members: HouseholdMember[];
  readonly weekStartDate: string;
}

/** Source of users eligible for nightly regeneration (active within 7 days). */
export interface EligibleUsersStore {
  getEligibleUsers(): Promise<EligibleUser[]>;
}

export interface SchedulerResult {
  readonly processed: number;
  readonly succeeded: number;
  readonly failed: number;
}

export class NightlyPlanScheduler {
  constructor(
    private readonly users: EligibleUsersStore,
    private readonly engine: RecommendationEngine,
    private readonly weekPlanStore: WeekPlanStore,
    private readonly logger: Logger,
    private readonly nonVegMainClass: string,
    private readonly contextForSlot: (
      slotDate: string,
      mealSlot: MealSlot,
    ) => RecommendationContext,
  ) {}

  /** Generate + persist a fresh week plan for every eligible user. A single user's failure is
   * isolated (logged) and does not abort the batch. */
  async run(): Promise<SchedulerResult> {
    const eligible = await this.users.getEligibleUsers();
    let succeeded = 0;
    let failed = 0;

    for (const e of eligible) {
      try {
        const plan = await this.engine.generateWeekPlan(
          e.user,
          e.constraints,
          e.members,
          e.weekStartDate,
          this.contextForSlot,
          { nonVegMainClass: this.nonVegMainClass },
        );
        const { header, slots } = toPersistable(plan);
        await this.weekPlanStore.persistWeekPlan(header, slots);
        succeeded++;
      } catch (err) {
        failed++;
        // No PII: profile id is a pseudonymous key; log the failure for the ops dashboard.
        this.logger.error("nightly_plan_failed", {
          profile_id: e.user.profileId,
          error: err instanceof Error ? err.message : String(err),
        });
      }
    }

    this.logger.info("nightly_plan_complete", {
      processed: eligible.length,
      succeeded,
      failed,
    });
    return { processed: eligible.length, succeeded, failed };
  }
}
