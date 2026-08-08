/**
 * Feedback request validation (WP-15 — POST /v1/feedback).
 *
 * This is the instrumentation WP-14 identified as the actual prerequisite for the Core Spine's
 * `w_pref·S_pref` term (pinned to 0 in v1 for lack of real interaction data): a caller records
 * what they actually did with a served plate — accepted it, edited/swapped a dish, or explicitly
 * liked/disliked one. Mirrors the consent-schema.ts split (structural 400 vs. semantic-enum 422 —
 * DOC-P3-06 §07 / §21.1): event_type is validated as a plain string by Zod (structure) and its
 * CHECK-constraint membership (feedback_events.event_type, migration 038) is checked separately.
 */
import { z } from "./validate.ts";
import { AppError } from "../errors/app-error.ts";
import { API_ERRORS } from "../errors/api-catalogue.ts";

/** The exact 6 values in feedback_events.event_type's CHECK constraint (migration 038). */
export const FEEDBACK_EVENT_TYPES = [
  "accept",
  "edit",
  "swap",
  "like",
  "dislike",
  "shown_not_tapped",
  "never",
  "not_today",
  "lock",
  "unlock",
  "add_to_date",
  "make_this",
  "too_much_work",
  "missing_ingredient",
  "member_objection",
  "cooked",
  "ordered",
  "replaced",
  "completed",
  "regretted",
  "opened",
  "search",
  "selected",
] as const;

export type FeedbackEventType = typeof FEEDBACK_EVENT_TYPES[number];

export const INTERACTION_TARGET_TYPES = [
  "dish",
  "meal_episode",
  "meal_class",
  "ingredient",
  "query",
  "plan_slot",
] as const;
export type InteractionTargetType = typeof INTERACTION_TARGET_TYPES[number];
export interface InteractionTarget {
  readonly type: InteractionTargetType;
  readonly id: string;
  readonly identityStatus: "resolved" | "unresolved";
  readonly displayName?: string;
  readonly snapshot?: Record<string, unknown>;
}
export interface InteractionMoment {
  readonly occurredAt: string;
  readonly localTimezone: string;
  readonly intendedMealDate?: string;
  readonly mealSlot: "breakfast" | "lunch" | "dinner" | "snacks";
  readonly weekday?: string;
  readonly dayType?: "weekday" | "weekend";
}
export interface InteractionEvidence {
  readonly kind: "explicit" | "inferred" | "integration" | "operator";
  readonly sourceSurface: string;
  readonly shownRank?: number;
  readonly selectionPropensity?: number;
}

export interface FeedbackRequest {
  /** Household whose served recommendation is being acted on. Defaults to the caller's
   * compatibility household for older clients. Actor identity always comes from the JWT. */
  readonly householdId?: string;
  /** The `request_id` echoed in a POST /v1/recommendations response (RecommendationsResponse.
   * request_id, mobile/src/api/types.ts) — deliberately NOT recommendation_events.id (the DB row's
   * uuid PK), which the client is never given. events.ts resolves this to the matching
   * recommendation_events row server-side. */
  readonly requestId: string;
  readonly eventType: FeedbackEventType;
  /** The dish's catalogue name (what the client actually has — plate.hero_dish_names — not a
   * public.dishes uuid the mobile app never sees). Resolved to dish_id server-side; see events.ts. */
  readonly dishName?: string;
  readonly slot?: string;
  readonly detail?: Record<string, unknown>;
  readonly schemaVersion: "1" | "2";
  readonly idempotencyKey?: string;
  readonly target?: InteractionTarget;
  readonly replacement?: { readonly from: InteractionTarget; readonly to: InteractionTarget };
  readonly moment?: InteractionMoment;
  readonly evidence?: InteractionEvidence;
  readonly reasonCode?: string;
  readonly versions?: {
    readonly catalog?: string;
    readonly config?: string;
    readonly feature?: string;
    readonly policy?: string;
    readonly model?: string;
  };
}

const targetSchema = z.object({
  type: z.enum(INTERACTION_TARGET_TYPES),
  id: z.string().min(1).max(300),
  identity_status: z.enum(["resolved", "unresolved"]),
  display_name: z.string().min(1).max(300).optional(),
  snapshot: z.record(z.unknown()).optional(),
});
const momentSchema = z.object({
  occurred_at: z.string().datetime(),
  local_timezone: z.string().min(1).max(100),
  intended_meal_date: z.string().date().optional(),
  meal_slot: z.enum(["breakfast", "lunch", "dinner", "snacks"]),
  weekday: z.enum(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
    .optional(),
  day_type: z.enum(["weekday", "weekend"]).optional(),
});
const evidenceSchema = z.object({
  kind: z.enum(["explicit", "inferred", "integration", "operator"]),
  source_surface: z.string().min(1).max(100),
  shown_rank: z.number().int().positive().optional(),
  selection_propensity: z.number().positive().max(1).optional(),
});

const feedbackEnvelope = z.object({
  household_id: z.string().uuid().optional(),
  request_id: z.string().min(1),
  event_type: z.string(),
  dish_name: z.string().min(1).optional(),
  slot: z.string().optional(),
  schema_version: z.enum(["1", "2"]).optional(),
  idempotency_key: z.string().min(1).max(200).optional(),
  target: targetSchema.optional(),
  replacement: z.object({ from: targetSchema, to: targetSchema }).optional(),
  moment: momentSchema.optional(),
  evidence: evidenceSchema.optional(),
  reason: z.object({
    code: z.string().min(1).max(100).optional(),
    detail: z.record(z.unknown()).optional(),
  }).optional(),
  versions: z.object({
    catalog: z.string().max(200).optional(),
    config: z.string().max(200).optional(),
    feature: z.string().max(200).optional(),
    policy: z.string().max(200).optional(),
    model: z.string().max(200).optional(),
  }).optional(),
  detail: z.record(z.unknown()).optional(),
});

function isFeedbackEventType(value: string): value is FeedbackEventType {
  return (FEEDBACK_EVENT_TYPES as readonly string[]).includes(value);
}

/**
 * Parse + validate a raw request body into a typed FeedbackRequest.
 * @throws AppError ERR_VALIDATION_FAILED (400) on structural failure.
 * @throws AppError ERR_FEEDBACK_EVENT_TYPE_INVALID (422) on an unrecognized event_type.
 */
export function parseFeedbackRequest(body: unknown): FeedbackRequest {
  const parsed = feedbackEnvelope.safeParse(body);
  if (!parsed.success) {
    const issues = parsed.error.issues.map((i) => ({
      path: i.path.join("."),
      message: i.message,
    }));
    throw new AppError(API_ERRORS.ERR_VALIDATION_FAILED, {
      detail: JSON.stringify(issues),
      context: { issues },
    });
  }

  if (!isFeedbackEventType(parsed.data.event_type)) {
    throw new AppError(API_ERRORS.ERR_FEEDBACK_EVENT_TYPE_INVALID, {
      context: { invalid_event_type: parsed.data.event_type, allowed: FEEDBACK_EVENT_TYPES },
    });
  }

  const schemaVersion = parsed.data.schema_version ?? "1";
  if (
    schemaVersion === "2" && (!parsed.data.idempotency_key || !parsed.data.target ||
      !parsed.data.moment || !parsed.data.evidence)
  ) {
    throw new AppError(API_ERRORS.ERR_VALIDATION_FAILED, {
      detail: "schema_version 2 requires idempotency_key, target, moment, and evidence",
    });
  }
  if (parsed.data.evidence && parsed.data.evidence.kind !== "explicit") {
    throw new AppError(API_ERRORS.ERR_VALIDATION_FAILED, {
      detail: "POST /feedback accepts explicit evidence only",
    });
  }
  const toTarget = (target: z.infer<typeof targetSchema>): InteractionTarget => ({
    type: target.type,
    id: target.id,
    identityStatus: target.identity_status,
    displayName: target.display_name,
    snapshot: target.snapshot,
  });

  return {
    householdId: parsed.data.household_id,
    requestId: parsed.data.request_id,
    eventType: parsed.data.event_type,
    dishName: parsed.data.dish_name ??
      (parsed.data.target?.type === "dish" ? parsed.data.target.display_name : undefined),
    slot: parsed.data.slot ?? parsed.data.moment?.meal_slot,
    detail: { ...(parsed.data.detail ?? {}), ...(parsed.data.reason?.detail ?? {}) },
    schemaVersion,
    idempotencyKey: parsed.data.idempotency_key,
    target: parsed.data.target ? toTarget(parsed.data.target) : undefined,
    replacement: parsed.data.replacement
      ? { from: toTarget(parsed.data.replacement.from), to: toTarget(parsed.data.replacement.to) }
      : undefined,
    moment: parsed.data.moment
      ? {
        occurredAt: parsed.data.moment.occurred_at,
        localTimezone: parsed.data.moment.local_timezone,
        intendedMealDate: parsed.data.moment.intended_meal_date,
        mealSlot: parsed.data.moment.meal_slot,
        weekday: parsed.data.moment.weekday,
        dayType: parsed.data.moment.day_type,
      }
      : undefined,
    evidence: parsed.data.evidence
      ? {
        kind: parsed.data.evidence.kind,
        sourceSurface: parsed.data.evidence.source_surface,
        shownRank: parsed.data.evidence.shown_rank,
        selectionPropensity: parsed.data.evidence.selection_propensity,
      }
      : undefined,
    reasonCode: parsed.data.reason?.code,
    versions: parsed.data.versions,
  };
}
