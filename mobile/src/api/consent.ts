import { apiPost } from "./client";
import type { ConsentRequest, ConsentResponse } from "./types";

/**
 * POST /v1/consent (DOC-P3-06 §06.1). Previously fully built and tested server-side with zero
 * mobile callers (api-contract-audit-2026-07-30.md HIGH finding — "orphaned handler").
 *
 * `profile_id` must equal the caller's own JWT `user_id` (requireOwnership in consent/handler.ts)
 * — callers pass the signed-in user's id explicitly rather than this module guessing it, so the
 * call site stays honest about which id it's using.
 */
export function postConsent(request: ConsentRequest): Promise<ConsentResponse> {
  return apiPost<ConsentResponse>("/consent", request);
}
