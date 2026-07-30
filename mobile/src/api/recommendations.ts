import { apiPost } from "./client";
import type { RecommendationsRequest, RecommendationsResponse } from "./types";

/**
 * POST /v1/recommendations. No `household`/`context` payload is required from the client —
 * compose.ts fetches the household's own profiles/household_answers/household_members rows
 * server-side and falls back to DEFAULT_CONTEXT (dinner, monsoon, Thursday) when the caller
 * supplies none. Phase 1 relies entirely on those server-side defaults.
 */
export function postRecommendations(
  overrides: RecommendationsRequest = {},
): Promise<RecommendationsResponse> {
  return apiPost<RecommendationsResponse>("/recommendations", overrides);
}
