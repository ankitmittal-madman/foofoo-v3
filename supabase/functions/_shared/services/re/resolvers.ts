/**
 * Recommendation Engine — resolvers (WP-8D).
 *
 * The "which persona / which cohort / which class plan" lookups (DOC-P3-03 §03 LF-A09, §04
 * LF-B01/B02/B03). Thin orchestration over the CohortResolutionRepository port — no scoring, no
 * SQL here. Persona/cohort resolution is a DB lookup, not a computed function (LF-A09).
 */
import type { ClassAssignment, MealSlot } from "./types.ts";
import type { CohortResolutionRepository } from "./ports.ts";

export interface PersonaResolution {
  readonly personaId: string;
  readonly overlayPersonaIds: string[];
  readonly cohortId: string;
  /** True when the Option-B fallback was applied (no exact assignment-rule match). */
  readonly fallbackApplied: boolean;
}

/**
 * LF-A09 + LF-B02 — resolve persona then cohort. Applies the CONFIRMED Option-B fallback (broadest
 * state coverage for the main cohort) when no assignment rule matches (DOC-P3-03 §03 LF-A09).
 * `dietMode` is the cohort diet dimension (veg / non_veg per §04); caller maps diet_type→diet_mode.
 */
export async function resolvePersonaAndCohort(
  repo: CohortResolutionRepository,
  input: {
    mainCohortCode: string;
    subCohortTag: string;
    homeState: string;
    dietType: string;
    dietMode: string;
  },
): Promise<PersonaResolution> {
  const persona = await repo.assignPersona(
    input.mainCohortCode,
    input.subCohortTag,
    input.homeState,
    input.dietType,
  );

  if (persona) {
    const cohortId = await repo.resolveCohort(persona.personaId, input.homeState, input.dietMode);
    if (cohortId) {
      return { ...persona, cohortId, fallbackApplied: false };
    }
  }

  // Option-B fallback (CONFIRMED, founder-approved): broadest-coverage cohort for the main cohort.
  const fb = await repo.assignPersonaFallback(input.mainCohortCode);
  return {
    personaId: fb.personaId,
    overlayPersonaIds: fb.overlayPersonaIds,
    cohortId: fb.cohortId,
    fallbackApplied: true,
  };
}

/**
 * LF-B02 + LF-B03 — fetch the 21 class assignments for the cohort's week and apply the non-veg
 * cadence overlay for non_veg/egg households (replace N slots with a non-veg main class).
 * Weekday/weekend selection is baked into the seeded rows (no runtime calculation, §04).
 */
export async function resolveWeeklyClassPlan(
  repo: CohortResolutionRepository,
  cohortId: string,
  weekStartDate: string,
  opts: { dietType: string; homeState: string; nonVegMainClass: string },
): Promise<ClassAssignment[]> {
  const base = await repo.getWeeklyClassPlan(cohortId, weekStartDate);
  if (opts.dietType !== "non_veg" && opts.dietType !== "egg") return base;

  const overlay = await repo.getNonVegOverlay(opts.homeState);
  if (overlay.weeklySlots <= 0) return base;

  // Replace up to `weeklySlots` assignments in the preferred slots with the non-veg main class.
  const preferred = new Set(overlay.preferredSlots);
  let replaced = 0;
  return base.map((a) => {
    if (replaced < overlay.weeklySlots && preferred.has(a.mealSlot)) {
      replaced++;
      return { ...a, classCode: opts.nonVegMainClass };
    }
    return a;
  });
}

/** Group class assignments by (slotDate, mealSlot) → classCode for slate generation. */
export function classForSlot(
  assignments: ClassAssignment[],
  slotDate: string,
  mealSlot: MealSlot,
): string | null {
  const hit = assignments.find((a) => a.slotDate === slotDate && a.mealSlot === mealSlot);
  return hit ? hit.classCode : null;
}
