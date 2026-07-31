/**
 * Maps an ApiError's `code` to a distinct, user-facing message (api-contract-audit-2026-07-30.md
 * MEDIUM finding: "the client never reads error.code — every non-2xx response is rendered
 * identically"). Codes are the backend's real `app-error.ts`/`api-catalogue.ts` taxonomy plus the
 * two client-only transport codes added alongside the apiPost() timeout fix (client.ts's
 * CLIENT_ERROR_CODES). Not every code below is necessarily reachable from every call site today —
 * this is a single shared mapping so future call sites don't have to reinvent it, matching the
 * catalogue's own "codes are immutable once published" discipline (DOC-P3-06 §21.0).
 */
import { ApiError } from "./client";

const MESSAGES: Record<string, string> = {
  TIMEOUT: "Request timed out — check your connection and try again.",
  NETWORK_ERROR: "Network error — check your connection and try again.",
  ERR_VALIDATION_FAILED: "Something about that answer wasn't recognized — please try again.",
  ERR_UNAUTHENTICATED: "Your session has expired — please sign in again.",
  ERR_OWNERSHIP_MISMATCH: "You don't have permission to do that — please sign in again.",
  ERR_CONSENT_TYPE_INVALID: "That consent option isn't recognized — please try again.",
  ERR_CONSENT_REQUIRED: "Personalization consent is required before we can continue.",
  ERR_PLAN_NOT_FOUND: "We couldn't find a plan for that week yet.",
  ERR_ONBOARDING_ALREADY_COMPLETE: "Your onboarding is already complete.",
  ERR_HOUSEHOLD_FIELD_INVALID: "One of your answers isn't valid — please review and try again.",
  ERR_HOUSEHOLD_INCOMPLETE: "A few required details are still missing from earlier steps.",
};

/** Returns a distinct message for a known `error.code`, falling back to the error's own message
 * (or a generic string for non-ApiError failures). */
export function describeApiError(error: unknown): string {
  if (!(error instanceof ApiError)) {
    return "Something went wrong. Please try again.";
  }
  if (error.code && MESSAGES[error.code]) {
    return MESSAGES[error.code];
  }
  return error.message || "Something went wrong. Please try again.";
}
