/**
 * Recommendation Engine — variety re-ranking (WP-8D).
 *
 * DOC-P3-03 §08 (LF-F01 MMR, LF-F02 variety-window rules, LF-F03 edge cases). Pure functions.
 * MMR balances relevance against diversity across variety-relevant genome dimensions (RE-DOC-04 §02).
 */
import type { ScoredCandidate, VarietyRule } from "./types.ts";

/** Similarity across the 4 variety-relevant dimensions (LF-F01): fraction of dimensions that match. */
export function varietySimilarity(a: ScoredCandidate, b: ScoredCandidate): number {
  const dims: Array<keyof typeof a.candidate> = [
    "cuisineFamily",
    "cookingMethod",
    "mainIngredientClass",
    "texture",
  ];
  let matches = 0;
  for (const d of dims) {
    if (a.candidate[d] === b.candidate[d]) matches++;
  }
  return matches / dims.length;
}

/**
 * LF-F01 — Maximal Marginal Relevance selection.
 * MMR(i) = λ·relevance(i) − (1−λ)·max_{j∈selected} sim(i,j). Iteratively picks the highest-MMR
 * remaining candidate until `slateSize` is reached or candidates are exhausted. The (1−λ)·sim term
 * IS the variety penalty referenced by the FinalScore formula.
 */
export function applyMmr(
  scored: ScoredCandidate[],
  lambda: number,
  slateSize: number,
): ScoredCandidate[] {
  const remaining = [...scored].sort((a, b) => b.score - a.score);
  const selected: ScoredCandidate[] = [];

  while (selected.length < slateSize && remaining.length > 0) {
    let bestIdx = 0;
    let bestMmr = -Infinity;
    for (let i = 0; i < remaining.length; i++) {
      const cand = remaining[i];
      const maxSim = selected.length === 0
        ? 0
        : Math.max(...selected.map((s) => varietySimilarity(cand, s)));
      const mmr = lambda * cand.score - (1 - lambda) * maxSim;
      if (mmr > bestMmr) {
        bestMmr = mmr;
        bestIdx = i;
      }
    }
    selected.push(remaining.splice(bestIdx, 1)[0]);
  }
  return selected;
}

/**
 * LF-F02 — validate a 7-day plan against the rolling variety-window rules. Returns the list of
 * violations (empty = compliant). Rules and caps are config (re_variety_rules); the monsoon override
 * raises the fried cap. `slots` are the chosen dishes in slot order with their variety dimensions.
 */
export interface PlannedSlot {
  readonly slotDate: string;
  readonly mealSlot: string;
  readonly cuisineFamily: string;
  readonly cookingMethod: string;
  readonly mainIngredientClass: string;
  readonly dishId: string;
  readonly breakfastClassCode?: string;
}

export interface VarietyViolation {
  readonly ruleName: string;
  readonly detail: string;
}

export function checkVarietyWindow(
  slots: PlannedSlot[],
  rules: VarietyRule[],
  isMonsoon: boolean,
): VarietyViolation[] {
  const violations: VarietyViolation[] = [];
  const ruleBy = (name: string) => rules.find((r) => r.ruleName === name);

  // Rule 2 — fried method per week (monsoon override raises the cap).
  const fried = ruleBy("fried_method");
  if (fried) {
    const cap = isMonsoon && fried.overrideCondition ? Math.max(fried.capValue, 4) : fried.capValue;
    const friedCount = slots.filter((s) => s.cookingMethod === "fried").length;
    if (friedCount > cap) {
      violations.push({ ruleName: "fried_method", detail: `${friedCount} fried > cap ${cap}` });
    }
  }

  // Rule 3 — same main ingredient on back-to-back days (rice forms treated distinct upstream).
  const sameIngr = ruleBy("same_main_ingredient");
  if (sameIngr) {
    const byDate = [...slots].sort((a, b) => a.slotDate.localeCompare(b.slotDate));
    for (let i = 1; i < byDate.length; i++) {
      if (
        byDate[i].mealSlot === byDate[i - 1].mealSlot &&
        byDate[i].mainIngredientClass === byDate[i - 1].mainIngredientClass
      ) {
        violations.push({
          ruleName: "same_main_ingredient",
          detail: `${byDate[i].mainIngredientClass} back-to-back in ${byDate[i].mealSlot}`,
        });
      }
    }
  }

  // Rule 4 — same exact dish within the window (default 30 days; within one week = any repeat).
  const sameDish = ruleBy("same_dish");
  if (sameDish) {
    const seen = new Set<string>();
    for (const s of slots) {
      if (seen.has(s.dishId)) {
        violations.push({ ruleName: "same_dish", detail: `dish ${s.dishId} repeats` });
      }
      seen.add(s.dishId);
    }
  }

  return violations;
}
