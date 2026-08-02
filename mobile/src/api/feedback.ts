import { apiPost } from "./client";
import type { FeedbackRequest, FeedbackResponse } from "./types";

/**
 * POST /v1/feedback (WP-15) — records what the caller actually did with a served plate/dish
 * against the recommendation identified by `request_id` (the id echoed back in
 * RecommendationsResponse, NOT any id the client would have to look up separately). This is the
 * instrumentation WP-14 identified as the prerequisite for the Core Spine's `w_pref·S_pref` term
 * (pinned to 0 in v1 for lack of real interaction data) — recording here has no scoring effect
 * yet, it only starts building the history a future version can learn from.
 */
export function postFeedback(body: FeedbackRequest): Promise<FeedbackResponse> {
  return apiPost<FeedbackResponse>("/feedback", body);
}
