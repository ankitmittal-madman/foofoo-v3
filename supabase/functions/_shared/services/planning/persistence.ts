/**
 * Plan persistence (WP-8E).
 *
 * Converts the engine's in-memory GeneratedWeekPlan (WP-8D) into `week_plans` + `plan_slots` rows
 * and persists them. This is the "Plan Assembly → Persistence" responsibility (CPTO separation;
 * DOC-P3-02 Domain Events: the RE Engine generates, a repository persists). NO recommendation logic
 * lives here — it only maps and writes. Columns match DOC-P3-04 §03.12/§03.13 (migration 011)
 * exactly. Persisted slots are the 3 primary meal slots only, because `plan_slots.meal_slot` CHECK
 * is ('breakfast','lunch','dinner') — snack/addon are separate structures.
 */
import type { GeneratedWeekPlan, Slate } from "../re/types.ts";

/** A `week_plans` insert row (DOC-P3-04 §03.12). */
export interface WeekPlanRow {
  readonly profile_id: string;
  readonly week_start_date: string;
  readonly re_version: string;
}

/** A `plan_slots` insert row (DOC-P3-04 §03.13). */
export interface PlanSlotRow {
  readonly slot_date: string;
  readonly meal_slot: "breakfast" | "lunch" | "dinner";
  readonly class_code: string;
  readonly selected_dish_id: string | null;
  readonly slate_dish_ids: string[];
  readonly slate_reasons: Record<string, string[]>;
  readonly slate_confidence: number;
  readonly cold_start_mode: boolean;
}

const PRIMARY_SLOTS = new Set(["breakfast", "lunch", "dinner"]);

/** True if a slate targets a persistable primary meal slot (plan_slots CHECK). */
export function isPrimarySlate(slate: Slate): boolean {
  return PRIMARY_SLOTS.has(slate.mealSlot);
}

/** Map one engine Slate to a plan_slots row. The headline dish (rank 1) is the selected dish. */
export function slateToRow(slate: Slate): PlanSlotRow {
  return {
    slot_date: slate.slotDate,
    meal_slot: slate.mealSlot as PlanSlotRow["meal_slot"],
    class_code: slate.classCode,
    selected_dish_id: slate.dishIds[0] ?? null,
    slate_dish_ids: slate.dishIds,
    slate_reasons: slate.reasonTags,
    slate_confidence: slate.confidence,
    cold_start_mode: slate.coldStartMode,
  };
}

/** Persistence port — the only place plan rows are written. Concrete adapter in re/adapters. */
export interface WeekPlanStore {
  /**
   * Persist a generated week plan atomically: upsert the `week_plans` header, then its `plan_slots`.
   * Returns the persisted week_plan id + start date (the handle onboarding/recommendations return).
   */
  persistWeekPlan(
    header: WeekPlanRow,
    slots: PlanSlotRow[],
  ): Promise<{ weekPlanId: string; weekStartDate: string }>;

  /** Update a single slot's slate (used by /v1/recommendations single-slot refresh). */
  updateSlotSlate(weekPlanId: string, slot: PlanSlotRow): Promise<{ slotId: string }>;
}

/** Split a GeneratedWeekPlan into a header row + primary-slot rows for persistence. */
export function toPersistable(
  plan: GeneratedWeekPlan,
): { header: WeekPlanRow; slots: PlanSlotRow[] } {
  return {
    header: {
      profile_id: plan.profileId,
      week_start_date: plan.weekStartDate,
      re_version: plan.reVersion,
    },
    slots: plan.slots.filter(isPrimarySlate).map(slateToRow),
  };
}
