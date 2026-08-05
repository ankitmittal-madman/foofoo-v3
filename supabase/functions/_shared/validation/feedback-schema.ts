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
] as const;

export type FeedbackEventType = typeof FEEDBACK_EVENT_TYPES[number];

export interface FeedbackRequest {
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
}

const feedbackEnvelope = z.object({
  request_id: z.string().min(1),
  event_type: z.string(),
  dish_name: z.string().min(1).optional(),
  slot: z.string().optional(),
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

  return {
    requestId: parsed.data.request_id,
    eventType: parsed.data.event_type,
    dishName: parsed.data.dish_name,
    slot: parsed.data.slot,
    detail: parsed.data.detail,
  };
}
