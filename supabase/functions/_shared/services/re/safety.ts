/**
 * Recommendation Engine — safety gates (WP-8D).
 *
 * DOC-P3-03 §10 (LF-H01–H04; RE-DOC-05 §04; CDM Invariant 11). ALL gates must return zero
 * violations before a slate/plan is served; any violation is a P0. In the live system these run as
 * SQL over suggestion_logs/plan_slots (validation 902); here they are pure predicates over the
 * in-memory proposed slate so the engine can self-check BEFORE persistence (defense in depth — the
 * hard-constraint filters should already guarantee zero, but the gate is never skipped).
 */
import type { DietType, DishCandidate, ReligiousPref } from "./types.ts";

export interface SafetyViolation {
  readonly gate: "diet" | "allergen" | "jain" | "planning_role";
  readonly dishId: string;
  readonly detail: string;
}

export interface SafetyProfile {
  readonly dietType: DietType;
  readonly religiousPref: ReligiousPref;
  readonly combinedAllergenFlags: number;
}

/** LF-H01 — diet violations. */
function dietViolation(dish: DishCandidate, p: SafetyProfile): boolean {
  switch (p.dietType) {
    case "veg":
      return !["veg", "vegan", "jain"].includes(dish.dietType);
    case "jain":
      return dish.isJain === false;
    case "vegan":
      return dish.dietType !== "vegan";
    case "egg":
      return !["veg", "vegan", "jain", "egg"].includes(dish.dietType);
    case "non_veg":
      return false;
  }
}

/**
 * Run gates 1–3 (diet, allergen ingredient-level, Jain) over the proposed dishes. Gate 4
 * (planning-role) is checked separately over class assignments (checkPlanningRoleGate).
 */
export function runSafetyGates(dishes: DishCandidate[], p: SafetyProfile): SafetyViolation[] {
  const v: SafetyViolation[] = [];
  for (const dish of dishes) {
    if (dietViolation(dish, p)) {
      v.push({
        gate: "diet",
        dishId: dish.dishId,
        detail: `diet ${p.dietType} vs ${dish.dietType}`,
      });
    }
    if ((dish.ingredientAllergenUnion & p.combinedAllergenFlags) > 0) {
      v.push({ gate: "allergen", dishId: dish.dishId, detail: "ingredient allergen overlap" });
    }
    if (p.religiousPref === "jain" && dish.isJain === false) {
      v.push({ gate: "jain", dishId: dish.dishId, detail: "non-jain dish for jain household" });
    }
  }
  return v;
}

/**
 * LF-H04 — planning-role gate: every non-addon plan slot's class must have planning_role
 * MAIN_PRIMARY. `classes` supplies each chosen class's planning role (from re_meal_classes).
 */
export function checkPlanningRoleGate(
  slots: Array<{ classCode: string; planningRole: string; isAddon: boolean }>,
): SafetyViolation[] {
  return slots
    .filter((s) => !s.isAddon && s.planningRole !== "MAIN_PRIMARY")
    .map((s) => ({
      gate: "planning_role" as const,
      dishId: s.classCode,
      detail: `class ${s.classCode} role ${s.planningRole} != MAIN_PRIMARY`,
    }));
}
