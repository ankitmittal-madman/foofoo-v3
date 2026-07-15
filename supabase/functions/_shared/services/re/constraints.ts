/**
 * Recommendation Engine — hard constraint (ICD) filters (WP-8D).
 *
 * The 6 hard constraints of DOC-P3-03 §06 (RE-DOC-03 §03; CDM Invariant 12). ALL run BEFORE any
 * scoring; a dish failing ANY constraint is permanently excluded for this request. These are pure
 * predicates over an already-materialised candidate (allergen checks use the ingredient-level union
 * carried on the candidate, never the dish-level cache — GR-06 / Safety Gate 2).
 */
import type { DietType, DishCandidate, HouseholdMember, ReligiousPref } from "./types.ts";

/** LF-A05 / CDM Invariant 3: bitwise-OR of the user's and all active members' allergen flags. */
export function combinedAllergenFlags(userFlags: number, members: HouseholdMember[]): number {
  return members.reduce((acc, m) => (m.isActive ? acc | m.allergenFlags : acc), userFlags);
}

/** Hard Constraint 1 — diet type (LF-D02). Returns true if the dish is ELIGIBLE. */
export function passesDietType(dish: DishCandidate, dietType: DietType): boolean {
  switch (dietType) {
    case "veg":
      return ["veg", "vegan", "jain"].includes(dish.dietType);
    case "jain":
      return dish.isJain === true;
    case "vegan":
      return dish.dietType === "vegan";
    case "egg":
      return ["veg", "vegan", "jain", "egg"].includes(dish.dietType);
    case "non_veg":
      return true; // no diet exclusions
  }
}

/** Hard Constraint 2 — allergen (LF-D03), ingredient-level. Eligible iff no overlapping flags. */
export function passesAllergen(dish: DishCandidate, combinedFlags: number): boolean {
  return (dish.ingredientAllergenUnion & combinedFlags) === 0;
}

/** Hard Constraint 3 — religious preference (LF-D04). Returns true if ELIGIBLE. */
export function passesReligious(dish: DishCandidate, pref: ReligiousPref): boolean {
  switch (pref) {
    case "jain":
      return dish.isJain === true;
    case "halal":
      return !dish.hasNonHalalMeat;
    case "no_beef":
      return !dish.hasBeef;
    case "no_pork":
      return !dish.hasPork;
    case "all":
    case "hindu_veg":
      return true; // diet_type handles these
  }
}

/** Hard Constraint 4 — meal occasion (LF-D05). Eligible iff the dish serves this slot or 'any'. */
export function passesMealOccasion(dish: DishCandidate, mealSlot: string): boolean {
  return dish.mealOccasions.includes(mealSlot) || dish.mealOccasions.includes("any");
}

/** Hard Constraint 5 — Never list (LF-D06). Eligible iff the dish is NOT on the active Never list. */
export function passesNeverList(dish: DishCandidate, activeNeverIds: Set<string>): boolean {
  return !activeNeverIds.has(dish.dishId);
}

export interface HardConstraintInputs {
  readonly dietType: DietType;
  readonly religiousPref: ReligiousPref;
  readonly combinedAllergenFlags: number;
  readonly mealSlot: string;
  readonly activeNeverIds: Set<string>;
}

/**
 * Apply all 6 hard constraints (LF-D02–D06) to a candidate pool. Order is irrelevant to the result
 * (all must pass); diet/allergen/religious/occasion/never are each hard. Returns survivors only.
 */
export function applyHardConstraints(
  candidates: DishCandidate[],
  c: HardConstraintInputs,
): DishCandidate[] {
  return candidates.filter((dish) =>
    passesDietType(dish, c.dietType) &&
    passesAllergen(dish, c.combinedAllergenFlags) &&
    passesReligious(dish, c.religiousPref) &&
    passesMealOccasion(dish, c.mealSlot) &&
    passesNeverList(dish, c.activeNeverIds)
  );
}
