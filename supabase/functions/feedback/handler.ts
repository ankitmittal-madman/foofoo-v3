/**
 * POST /v1/feedback — business handler (WP-15).
 *
 * THIN handler, same shape as consent/handler.ts: parse → authorize (the feedback is always
 * about the CALLER's own recommendation, so the JWT user_id IS the profile_id — there is no
 * separate body field to check ownership against, unlike consent/recommendations) → delegate to
 * the DB writer → envelope the response.
 *
 * This is the "instrument real feedback" step WP-14 identified as the actual prerequisite for the
 * Core Spine's `w_pref·S_pref` term (pinned to 0 in v1) — no scoring/ML change here, purely
 * capturing accept/edit/swap/like/dislike signals against already-served recommendation_events
 * rows so that history exists to learn from later.
 */
import { requireAuth } from "../_shared/auth/authorize.ts";
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

    const requestContext: RequestContext = {
      ...ctx,
      logger: ctx.logger.child({ service: "feedback" }),
    };

    const result = await recordEvent(requestContext, {
      profileId: claims.userId,
      requestId: feedbackReq.requestId,
      eventType: feedbackReq.eventType,
      dishName: feedbackReq.dishName,
      slot: feedbackReq.slot,
      detail: feedbackReq.detail,
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
