/**
 * Result type (WP-8B foundation) — explicit success/failure without throwing, for internal
 * service boundaries that prefer values over exceptions. HTTP-facing code uses AppError.
 */
import type { AppError } from "../errors/app-error.ts";

export type Result<T> = { ok: true; value: T } | { ok: false; error: AppError };

export const ok = <T>(value: T): Result<T> => ({ ok: true, value });
export const err = <T = never>(error: AppError): Result<T> => ({ ok: false, error });
