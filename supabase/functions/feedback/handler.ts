/**
 * POST /v1/feedback — business handler (WP-15).
 *
 * THIN handler, same shape as consent/handler.ts: parse → authorize (the feedback is always
 * about an explicitly selected household recommendation. JWT identity remains the actor while
 * active membership plus the event-specific role matrix authorizes the household target →
 * delegate to the DB writer → envelope the response.
 *
 * This is the "instrument real feedback" step WP-14 identified as the actual prerequisite for the
 * Core Spine's `w_pref·S_pref` term (pinned to 0 in v1) — no scoring/ML change here, purely
 * capturing accept/edit/swap/like/dislike signals against already-served recommendation_events
 * rows so that history exists to learn from later.
 */
import { requireAuth } from "../_shared/auth/authorize.ts";
import {
  type HouseholdRole,
  type HouseholdRoleLookup,
  requireHouseholdRole,
} from "../_shared/auth/household.ts";
import { jsonContract } from "../_shared/api/response.ts";
import { AppError } from "../_shared/errors/app-error.ts";
import { API_ERRORS } from "../_shared/errors/api-catalogue.ts";
import { ERROR_CATALOGUE } from "../_shared/errors/catalogue.ts";
import { UserJourney } from "../_shared/logging/userJourney.ts";
import type { Handler } from "../_shared/middleware/types.ts";
import type { RequestContext } from "../_shared/types/context.ts";
import { parseFeedbackRequest } from "../_shared/validation/feedback-schema.ts";

import { recordFeedbackEvent } from "./events.ts";

export interface FeedbackDeps {
  recordEvent?: typeof recordFeedbackEvent;
  authorizeHousehold?: HouseholdRoleLookup;
}

const PLAN_CONTROL_EVENTS = new Set([
  "accept",
  "edit",
  "swap",
  "lock",
  "unlock",
  "add_to_date",
  "make_this",
  "replaced",
  "selected",
  "never",
  "not_today",
]);
const COOK_EXECUTION_EVENTS = new Set(["cooked", "missing_ingredient"]);

/** Role matrix from the canonical PRD: viewers never write; planners control the shared plan;
 * cooks may additionally record execution/pantry facts; members may record attributable feedback. */
export function feedbackAllowedRoles(eventType: string): readonly HouseholdRole[] {
  if (PLAN_CONTROL_EVENTS.has(eventType)) return ["owner", "planner"];
  if (COOK_EXECUTION_EVENTS.has(eventType)) return ["owner", "planner", "cook"];
  return ["owner", "planner", "cook", "member"];
}

/** Build the POST /v1/feedback handler. */
export function makeFeedbackHandler(deps: FeedbackDeps = {}): Handler {
  const recordEvent = deps.recordEvent ?? recordFeedbackEvent;

  return async (req, ctx) => {
    if (req.method !== "POST") {
      throw new AppError(ERROR_CATALOGUE.METHOD_NOT_ALLOWED);
    }

    // Auth middleware populated claims; requireAuth is the defensive backstop.
    const claims = requireAuth(ctx.claims);

    let body: unknown;
    try {
      body = await req.json();
    } catch {
      throw new AppError(API_ERRORS.ERR_VALIDATION_FAILED, {
        detail: "request body is not valid JSON",
      });
    }

    const feedbackReq = parseFeedbackRequest(body);
    const householdId = feedbackReq.householdId ?? claims.userId;
    await requireHouseholdRole(
      ctx,
      claims,
      householdId,
      feedbackAllowedRoles(feedbackReq.eventType),
      deps.authorizeHousehold,
    );

    const requestContext: RequestContext = {
      ...ctx,
      logger: ctx.logger.child({ service: "feedback" }),
    };

    const result = await recordEvent(requestContext, {
      actorProfileId: claims.userId,
      householdId,
      requestId: feedbackReq.requestId,
      eventType: feedbackReq.eventType,
      dishName: feedbackReq.dishName,
      slot: feedbackReq.slot,
      detail: feedbackReq.detail,
      schemaVersion: feedbackReq.schemaVersion,
      idempotencyKey: feedbackReq.idempotencyKey,
      target: feedbackReq.target,
      replacement: feedbackReq.replacement,
      moment: feedbackReq.moment,
      evidence: feedbackReq.evidence,
      reasonCode: feedbackReq.reasonCode,
      versions: feedbackReq.versions,
    });

    UserJourney.logFeedbackRecorded(claims.userId, feedbackReq.eventType, result.dishResolved);

    // 201 Created — mirrors consent/handler.ts's convention for a new row.
    return jsonContract(
      { id: result.id, event_type: feedbackReq.eventType, recorded_at: result.createdAt },
      ctx.traceId,
      201,
    );
  };
}
