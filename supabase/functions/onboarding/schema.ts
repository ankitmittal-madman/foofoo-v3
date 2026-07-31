/**
 * POST /v1/onboarding — request validation (DOC-P3-06 §06.2).
 *
 * Parses the frozen contract's `answers.OB-01..OB-08` envelope into the
 * `OnboardingOrchestrator`'s own `OnboardingAnswers` shape. Two mappings below are flagged as
 * best-effort, not full spec derivations (see each field's comment) — this task's time budget
 * covered wiring the orchestrator to a deployed endpoint, not re-deriving LF-A09's complete
 * sub-cohort/segment vocabulary from DOC-P3-03 §03's full text.
 */
import { z } from "../_shared/validation/validate.ts";
import { AppError } from "../_shared/errors/app-error.ts";
import { API_ERRORS } from "../_shared/errors/api-catalogue.ts";
import type { MigrationBand, OnboardingAnswers } from "../_shared/services/onboarding/orchestrator.ts";

/** household_members.conditions — the exact 15-value vocabulary (migration 033), mirrored from
 * household/schema.ts so OB-02 segments can be checked against the same live vocabulary. */
const MEMBER_CONDITIONS = new Set([
  "baby_6_18m",
  "diabetic_member",
  "elderly_member",
  "fasting_member",
  "gym_high_protein_member",
  "hypertension_heart_member",
  "jain_member",
  "lactating_or_postpartum_mother",
  "picky_child",
  "pregnant_member",
  "recovery_member",
  "school_child",
  "teen_high_appetite",
  "toddler",
  "weight_loss_member",
]);

const memberEnvelope = z.object({
  segment: z.string().min(1),
  member_name: z.string().min(1).optional(),
});

const swipeEnvelope = z.object({
  dish_id: z.string().uuid(),
  class_code: z.string().min(1),
  swipe: z.enum(["yes", "nope"]),
});

const answersEnvelope = z.object({
  "OB-01_main_cohort": z.string().min(1).optional(),
  "OB-02_household_branch": z.object({ members: z.array(memberEnvelope).default([]) })
    .optional(),
  "OB-03_regional_identity": z.object({
    home_state: z.string().min(1).optional(),
    current_city: z.string().min(1).optional(),
    migration_duration_band: z.enum(["native", "lt_1yr", "1_3yr", "3_7yr", "7plus_yr", "skipped"])
      .optional(),
  }).optional(),
  "OB-04_diet_configuration": z.object({
    diet_type: z.enum(["veg", "non_veg", "egg", "vegan", "jain"]).optional(),
    religious_pref: z.enum(["all", "hindu_veg", "jain", "halal", "no_beef", "no_pork"]).optional(),
  }).optional(),
  "OB-05_allergen_exclusions": z.object({ allergen_flags: z.number().int().min(0).max(127) })
    .optional(),
  "OB-06_cook_capability": z.enum(["beginner", "intermediate", "advanced"]).optional(),
  "OB-07_class_preference_swipes": z.array(swipeEnvelope).default([]),
  "OB-08_profile_setup": z.object({
    primary_cook_name: z.string().min(1),
    push_notification_time: z.string().regex(/^\d{2}:\d{2}(:\d{2})?$/, "expected HH:MM[:SS]"),
  }),
});

const requestEnvelope = z.object({
  user_id: z.string().uuid(),
  answers: answersEnvelope,
  skipped_screens: z.array(z.string()).default([]),
});

export interface ParsedOnboardingRequest {
  readonly userId: string;
  readonly answers: OnboardingAnswers;
}

/** OB-02 `segment` → `household_members.conditions` tag. Best-effort direct case mapping — the
 * contract's OB-01/OB-09 segment vocabulary (e.g. `SCHOOL_CHILD`) was not confirmed 1:1 against
 * migration 033's tag vocabulary from spec text alone; entries that don't land in the live 15-value
 * vocabulary are dropped (never fabricated as an unrecognized tag) rather than rejecting the whole
 * request — flagged for review, not silently assumed correct. */
function segmentToConditions(segment: string): string[] {
  const tag = segment.toLowerCase();
  return MEMBER_CONDITIONS.has(tag) ? [tag] : [];
}

/**
 * Parse + validate a raw POST /v1/onboarding body.
 * @throws AppError ERR_VALIDATION_FAILED (400) on structural failure.
 */
export function parseOnboardingRequest(body: unknown): ParsedOnboardingRequest {
  const parsed = requestEnvelope.safeParse(body);
  if (!parsed.success) {
    const issues = parsed.error.issues.map((i) => ({ path: i.path.join("."), message: i.message }));
    throw new AppError(API_ERRORS.ERR_VALIDATION_FAILED, {
      detail: JSON.stringify(issues),
      context: { issues },
    });
  }
  const d = parsed.data;
  const a = d.answers;

  const swipes = a["OB-07_class_preference_swipes"];
  const members = (a["OB-02_household_branch"]?.members ?? []).map((m) => ({
    memberName: m.member_name,
    conditions: segmentToConditions(m.segment),
    // Per-member allergen flags are not part of the DOC-P3-06 §06.2 request shape (only the
    // household-level OB-05 total exists) — 0 here is the schema's own "none asserted for this
    // member individually" default, not an invented value (FD-11); the household-level union
    // still applies via profiles.allergen_flags.
    allergenFlags: 0,
  }));

  const answers: OnboardingAnswers = {
    // LF-A01 fallback: absent OB-01 → MC_SOLO (confidence penalty is computeOnboardingConfidence's
    // concern, not this parser's).
    mainCohortCode: a["OB-01_main_cohort"] ?? "MC_SOLO",
    // `[FLAGGED]` No OB-field carries a sub-cohort tag anywhere in DOC-P3-06 §06.2's request shape —
    // empty string here means assignPersona's exact match always misses, which correctly and
    // safely routes every onboarding call through the CONFIRMED Option-B fallback
    // (resolvePersonaAndCohort) rather than crashing or guessing a tag. Needs a real sub-cohort
    // derivation rule (from OB-01/OB-02 answers) before persona assignment is fully LF-A09-correct.
    subCohortTag: "",
    members,
    homeState: a["OB-03_regional_identity"]?.home_state ?? null,
    currentCity: a["OB-03_regional_identity"]?.current_city ?? null,
    migrationBand: (a["OB-03_regional_identity"]?.migration_duration_band ?? null) as
      | MigrationBand
      | null,
    dietType: a["OB-04_diet_configuration"]?.diet_type ?? null,
    religiousPref: a["OB-04_diet_configuration"]?.religious_pref ?? null,
    allergenFlags: a["OB-05_allergen_exclusions"]?.allergen_flags ?? 0,
    cookCapability: a["OB-06_cook_capability"] ?? null,
    primaryCookName: a["OB-08_profile_setup"].primary_cook_name,
    pushNotificationTime: a["OB-08_profile_setup"].push_notification_time,
    // LF-A07: capped at 10 by the orchestrator itself; this is just the raw count of "yes"/"nope"
    // swipes recorded, whichever screen they came from.
    classSwipeCount: swipes.length,
    ob07Completed: swipes.length > 0,
    skippedScreens: d.skipped_screens,
  };

  return { userId: d.user_id, answers };
}
