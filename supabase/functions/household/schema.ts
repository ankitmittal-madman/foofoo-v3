/**
 * Household/onboarding write validation (household/ — the onboarding write path).
 *
 * Mirrors consent-schema.ts's split (DOC-P3-06 §07/§21.1 stage distinction): structural problems
 * (wrong type/shape) → ERR_VALIDATION_FAILED (400); a well-formed request whose question_key or
 * answer_value is semantically invalid → ERR_HOUSEHOLD_FIELD_INVALID (422).
 *
 * QUESTION_KEY VOCABULARY — a deliberate choice, not an oversight: migration 038's own header
 * mentions "seeds 101/111"'s question_key examples (children_ages, elder_members_present, ...),
 * but those belong to `re_engine.re_routing_rules` — the LEGACY TypeScript RE's own onboarding
 * flow, confirmed by direct inspection (S40 ground-truth audit) to be retired and off the live
 * request path, with no defined mapping onto this schema. Reusing it here would import a dead
 * system's vocabulary into a live write path. Instead, `question_key` IS the destination column's
 * own name — either a `public.household_answers` column or one of the five `public.profiles`
 * columns this endpoint can populate. This is the one vocabulary the LIVE schema actually defines:
 * it is exactly compose.ts's own documented "Q1–Q15 SOURCE MAP", read in the write direction.
 *
 * Two Q-numbers are deliberately absent from HOUSEHOLD_ANSWERS_SCHEMAS: q8_is_jain and
 * q9_allergies are DERIVED (from profiles.religious_pref/diet_type and profiles.allergen_flags
 * respectively — compose.ts's own source map), never raw input; q12_member_ages has no scalar
 * answer at all — member data arrives through this request's own `members[]`, matching
 * household_members' own row shape rather than a single answer_value.
 */
import { z } from "../_shared/validation/validate.ts";
import { AppError } from "../_shared/errors/app-error.ts";
import { API_ERRORS } from "../_shared/errors/api-catalogue.ts";

// ---------------------------------------------------------------------------
// Per-field schemas, keyed by question_key == destination column name.
// Values are the EXACT CHECK-constraint vocabularies from the live migrations (038 for
// household_answers, 005 for profiles) — read from the .sql files directly, not invented.
// ---------------------------------------------------------------------------

/** public.household_answers columns this endpoint can write (migration 038). */
const HOUSEHOLD_ANSWERS_SCHEMAS = {
  q1_household_type: z.enum([
    "single",
    "couple",
    "couple_kids",
    "couple_kids_parents",
    "joint",
    "flatmates",
  ]),
  q2_working_professionals: z.number().int().min(0),
  q6_nonveg_types: z.array(z.string()),
  q7_veg_days: z.array(z.string()),
  q10_allergy_other: z.string(),
  q11_conditions: z.array(z.string()),
  q13_who_cooks: z.enum(["self", "family", "hired_cook", "order_tiffin"]),
  q14_eat_out_per_week: z.number().int().min(0),
  q15_objective: z.enum([
    "awesome_taste",
    "healthy_living",
    "into_fitness",
    "protein_calculator",
  ]),
} as const;

/**
 * public.profiles columns this endpoint can populate (migration 005). The first five are exactly
 * the required (NOT NULL, no DEFAULT) columns that gate profile creation — PROFILE_REQUIRED_FIELDS
 * below. The rest are optional (nullable or DEFAULTed) and, if never supplied, are simply omitted
 * from the INSERT so Postgres applies its own column DEFAULT — never a value invented in code
 * (FD-11's standing rule: no fabricated defaults).
 */
const PROFILE_SCHEMAS = {
  primary_cook_name: z.string().min(1),
  home_state: z.string().min(1), // FK to re_engine.re_states — validated by the DB, not duplicated
  current_city: z.string().min(1),
  diet_type: z.enum(["veg", "non_veg", "egg", "vegan", "jain"]),
  cook_capability: z.enum(["beginner", "intermediate", "advanced"]),
  religious_pref: z.enum(["all", "hindu_veg", "jain", "halal", "no_beef", "no_pork"]),
  allergen_flags: z.number().int().min(0).max(127), // 7-bit model, DOC-P3-02 §Allergen
  migration_duration_band: z.enum(["native", "lt_1yr", "1_3yr", "3_7yr", "7plus_yr", "skipped"]),
  city_overlay_weight: z.number().min(0).max(1),
  push_notification_time: z.string().regex(/^\d{2}:\d{2}(:\d{2})?$/, "expected HH:MM[:SS]"),
} as const;

/** The five NOT NULL, no-DEFAULT public.profiles columns — profile creation is gated on all five
 * being known (accumulated across calls; see store.ts's accumulatedProfileFields). */
export const PROFILE_REQUIRED_FIELDS = [
  "primary_cook_name",
  "home_state",
  "current_city",
  "diet_type",
  "cook_capability",
] as const;

/** household_members.conditions — the exact 15-value vocabulary from migration 033. */
const MEMBER_CONDITIONS = [
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
] as const;

export type Target = "household_answers" | "profiles";

/** Which table a question_key targets, or null if it is not a recognized key. */
export function targetFor(questionKey: string): Target | null {
  if (questionKey in HOUSEHOLD_ANSWERS_SCHEMAS) return "household_answers";
  if (questionKey in PROFILE_SCHEMAS) return "profiles";
  return null;
}

/** Validate one answer_value against its field's schema. Throws on failure (caller wraps as 422). */
function validateAnswerValue(questionKey: string, value: unknown): void {
  const schema = (HOUSEHOLD_ANSWERS_SCHEMAS as Record<string, z.ZodTypeAny>)[questionKey] ??
    (PROFILE_SCHEMAS as Record<string, z.ZodTypeAny>)[questionKey];
  // targetFor() already confirmed questionKey is one of the two maps, so schema is always defined
  // here — this is a parse, not a presence check.
  const result = schema.safeParse(value);
  if (!result.success) {
    throw new AppError(API_ERRORS.ERR_HOUSEHOLD_FIELD_INVALID, {
      detail: JSON.stringify(result.error.issues),
      context: { question_key: questionKey },
    });
  }
}

// ---------------------------------------------------------------------------
// Request envelope
// ---------------------------------------------------------------------------

const screenAnswerEnvelope = z.object({
  screen_id: z.string().min(1),
  question_key: z.string().min(1),
  answer_value: z.unknown(),
  skipped: z.boolean().optional().default(false),
});

const memberEnvelope = z.object({
  id: z.string().uuid().optional(),
  member_name: z.string().min(1).optional(),
  conditions: z.array(z.string()).optional(),
  allergen_flags: z.number().int().min(0).max(127).optional(),
  diet_type: z.enum(["veg", "non_veg", "egg", "vegan", "jain"]).optional(),
  is_active: z.boolean().optional(),
});

const householdWriteEnvelope = z.object({
  household_id: z.string().uuid().optional(),
  screens: z.array(screenAnswerEnvelope).default([]),
  members: z.array(memberEnvelope).default([]),
});

export interface ScreenAnswer {
  readonly screenId: string;
  readonly questionKey: string;
  readonly answerValue: unknown;
  readonly skipped: boolean;
  /** Populated by parseHouseholdWriteRequest — which table this key targets, once validated. */
  readonly target: Target;
}

export interface MemberWrite {
  readonly id?: string;
  readonly memberName?: string;
  readonly conditions?: string[];
  readonly allergenFlags?: number;
  readonly dietType?: string;
  readonly isActive?: boolean;
}

export interface HouseholdWriteRequest {
  readonly householdId?: string;
  readonly screens: ScreenAnswer[];
  readonly members: MemberWrite[];
}

/**
 * Parse + validate a raw request body.
 * @throws AppError ERR_VALIDATION_FAILED (400) on structural failure (wrong shape/type).
 * @throws AppError ERR_HOUSEHOLD_FIELD_INVALID (422) on an unrecognized question_key, an
 *   answer_value outside its field's vocabulary, or a member's conditions[] outside the 15-value
 *   household_members vocabulary.
 */
export function parseHouseholdWriteRequest(body: unknown): HouseholdWriteRequest {
  const parsed = householdWriteEnvelope.safeParse(body);
  if (!parsed.success) {
    const issues = parsed.error.issues.map((i) => ({ path: i.path.join("."), message: i.message }));
    throw new AppError(API_ERRORS.ERR_VALIDATION_FAILED, {
      detail: JSON.stringify(issues),
      context: { issues },
    });
  }

  const screens: ScreenAnswer[] = parsed.data.screens.map((s) => {
    const target = targetFor(s.question_key);
    if (target === null) {
      throw new AppError(API_ERRORS.ERR_HOUSEHOLD_FIELD_INVALID, {
        context: { unknown_question_key: s.question_key },
      });
    }
    // A skipped screen carries no answer to validate — the caller is recording "asked, not
    // answered", not submitting a value for the field.
    if (!s.skipped) validateAnswerValue(s.question_key, s.answer_value);
    return {
      screenId: s.screen_id,
      questionKey: s.question_key,
      answerValue: s.answer_value,
      skipped: s.skipped,
      target,
    };
  });

  const members: MemberWrite[] = parsed.data.members.map((m) => {
    if (m.conditions) {
      for (const c of m.conditions) {
        if (!(MEMBER_CONDITIONS as readonly string[]).includes(c)) {
          throw new AppError(API_ERRORS.ERR_HOUSEHOLD_FIELD_INVALID, {
            context: { invalid_condition: c, allowed: MEMBER_CONDITIONS },
          });
        }
      }
    }
    return {
      id: m.id,
      memberName: m.member_name,
      conditions: m.conditions,
      allergenFlags: m.allergen_flags,
      dietType: m.diet_type,
      isActive: m.is_active,
    };
  });

  return { householdId: parsed.data.household_id, screens, members };
}
