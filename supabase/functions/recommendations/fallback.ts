/**
 * Fallback response (Phase C, RE-DOC-10 §11).
 *
 * When the RE is unreachable / times out / returns a bad body, we no longer guess a "safe" plate
 * on the household's behalf — a single hardcoded dish (Moong Dal Khichdi) ignores each household's
 * actual allergies/diet beyond jain/weaning-safety, which is a real safety risk, not just a UX gap.
 * Until a real per-zone cached default plate set exists (RE-DOC-10 §11), the caller gets a real
 * error surfaced to the user ("couldn't load your recommendations, try again") instead of a plate
 * that may not respect their restrictions.
 */
import { API_VERSION } from "./meta.ts";

export class RecommendationEngineUnavailableError extends Error {
  constructor(public readonly reason: string) {
    super(
      `RE unavailable (${reason}); no safe default plate can be served without per-household diet/allergy data`,
    );
    this.name = "RecommendationEngineUnavailableError";
  }
}

/**
 * Build the error response used whenever the RE cannot be used.
 * @param requestId - correlation id, echoed into `request_id`
 * @param reason - short machine string describing why the RE result was rejected (timeout/network/
 *   http/bad_body/etc.)
 * @returns a contract-conformant error body (no plates) the client renders as a retryable failure
 */
export function buildFallbackResponse(requestId: string, reason: string): Record<string, unknown> {
  return {
    request_id: requestId,
    api_version: API_VERSION,
    engine_version: "fallback",
    config_version: "fallback",
    error: {
      code: "recommendation_engine_unavailable",
      message: "We couldn't load your recommendations right now. Please try again.",
      reason,
    },
  };
}
