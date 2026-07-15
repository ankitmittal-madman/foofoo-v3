/**
 * API error catalogue (WP-8C).
 *
 * These are the CLIENT-FACING `error.code` values defined by the frozen API contract
 * (DOC-P3-06 §21.1). They are distinct from the foundation catalogue (errors/catalogue.ts),
 * which carries infrastructure-level codes only. Per DOC-P3-06 §21.0 these codes are IMMUTABLE
 * once published — a code's meaning may never change; only its human-readable message may be
 * reworded (message text is not a compatibility-relevant field, §17.2).
 *
 * Only the codes actually used by shipped endpoints are added here (avoids dead entries); the
 * remaining §21.1 codes land with their endpoints in later WPs.
 */
import type { ErrorSpec } from "./catalogue.ts";

export const API_ERRORS = {
  /** 400 — request is malformed / fails structural validation (DOC-P3-06 §21.1, §07 Stage 1). */
  ERR_VALIDATION_FAILED: {
    code: "ERR_VALIDATION_FAILED",
    httpStatus: 400,
    retriable: false,
    message: "Request validation failed.",
  },
  /** 401 — missing/expired/invalid JWT (DOC-P3-06 §04, §05.1). Deliberately generic (§05.1). */
  ERR_UNAUTHENTICATED: {
    code: "ERR_UNAUTHENTICATED",
    httpStatus: 401,
    retriable: false,
    message: "Authentication required.",
  },
  /** 403 — JWT user_id does not match the target resource owner (DOC-P3-06 §05, §05.1). */
  ERR_OWNERSHIP_MISMATCH: {
    code: "ERR_OWNERSHIP_MISMATCH",
    httpStatus: 403,
    retriable: false,
    message: "Not permitted to access this resource.",
  },
  /** 422 — well-formed request but consent_type not one of the 4 CHECK values (DOC-P3-04 §03.4). */
  ERR_CONSENT_TYPE_INVALID: {
    code: "ERR_CONSENT_TYPE_INVALID",
    httpStatus: 422,
    retriable: false,
    message: "consent_type is not a recognized value.",
  },
  /** 403 — personalization consent not granted before onboarding (DOC-P3-06 §06.1; DOC-09 §03). */
  ERR_CONSENT_REQUIRED: {
    code: "ERR_CONSENT_REQUIRED",
    httpStatus: 403,
    retriable: false,
    message: "Personalization consent is required before onboarding.",
  },
  /** 404 — no week_plans row for the requested slot/week (DOC-P3-06 §06.5). */
  ERR_PLAN_NOT_FOUND: {
    code: "ERR_PLAN_NOT_FOUND",
    httpStatus: 404,
    retriable: false,
    message: "Plan not found for the requested week.",
  },
  /** 409 — onboarding retried after onboarding_completed=true (DOC-P3-06 §06.2/§08). */
  ERR_ONBOARDING_ALREADY_COMPLETE: {
    code: "ERR_ONBOARDING_ALREADY_COMPLETE",
    httpStatus: 409,
    retriable: false,
    message: "Onboarding is already complete for this profile.",
  },
} as const satisfies Record<string, ErrorSpec>;

export type ApiErrorCode = keyof typeof API_ERRORS;
