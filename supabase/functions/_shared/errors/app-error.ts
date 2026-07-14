/**
 * Typed application error (WP-8B foundation).
 *
 * The single error type thrown across the backend. Carries a catalogue spec (code + HTTP status
 * + retriable) plus an optional internal `detail` (logged, never returned to the client) and
 * safe `context` fields. Client-facing serialization is handled by the error-boundary middleware
 * (never leaks stack traces / DB errors — DOC-P3-07; DOC-P3-06 §21).
 */
import type { ErrorSpec } from "./catalogue.ts";

export class AppError extends Error {
  readonly code: string;
  readonly httpStatus: number;
  readonly retriable: boolean;
  /** Internal-only detail for logs (never serialized to the client). */
  readonly detail?: string;
  /** Safe, client-shareable context (e.g. which field failed validation). */
  readonly context?: Record<string, unknown>;

  constructor(spec: ErrorSpec, opts: { detail?: string; context?: Record<string, unknown> } = {}) {
    super(spec.message);
    this.name = "AppError";
    this.code = spec.code;
    this.httpStatus = spec.httpStatus;
    this.retriable = spec.retriable;
    this.detail = opts.detail;
    this.context = opts.context;
  }

  /** Client-safe representation (no internal detail, no stack). */
  toClientJSON(traceId: string): { error: Record<string, unknown> } {
    return {
      error: {
        code: this.code,
        message: this.message,
        retriable: this.retriable,
        trace_id: traceId,
        ...(this.context ? { context: this.context } : {}),
      },
    };
  }

  static isAppError(e: unknown): e is AppError {
    return e instanceof AppError;
  }
}
