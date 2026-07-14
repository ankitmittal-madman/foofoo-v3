/**
 * Base error catalogue (WP-8B foundation).
 *
 * FOUNDATION-LEVEL codes only (auth, validation, rate-limit, internal). The full business/API
 * error catalogue is owned by DOC-P3-06 §21 and is added per-endpoint in later WPs — NOT here.
 * Each entry maps a stable code to an HTTP status and whether the caller may retry.
 */
export interface ErrorSpec {
  readonly code: string;
  readonly httpStatus: number;
  readonly retriable: boolean;
  readonly message: string;
}

export const ERROR_CATALOGUE = {
  AUTH_REQUIRED: {
    code: "AUTH_REQUIRED",
    httpStatus: 401,
    retriable: false,
    message: "Authentication required.",
  },
  FORBIDDEN: {
    code: "FORBIDDEN",
    httpStatus: 403,
    retriable: false,
    message: "Not permitted to access this resource.",
  },
  VALIDATION_FAILED: {
    code: "VALIDATION_FAILED",
    httpStatus: 422,
    retriable: false,
    message: "Request failed validation.",
  },
  NOT_FOUND: {
    code: "NOT_FOUND",
    httpStatus: 404,
    retriable: false,
    message: "Resource not found.",
  },
  RATE_LIMITED: {
    code: "RATE_LIMITED",
    httpStatus: 429,
    retriable: true,
    message: "Too many requests.",
  },
  METHOD_NOT_ALLOWED: {
    code: "METHOD_NOT_ALLOWED",
    httpStatus: 405,
    retriable: false,
    message: "HTTP method not allowed for this endpoint.",
  },
  INTERNAL: {
    code: "INTERNAL",
    httpStatus: 500,
    retriable: false,
    message: "Internal server error.",
  },
} as const satisfies Record<string, ErrorSpec>;

export type ErrorCode = keyof typeof ERROR_CATALOGUE;
