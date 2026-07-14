/**
 * Invariant helpers (WP-8B foundation). Framework-level guards only — no business rules.
 */
import { AppError } from "../errors/app-error.ts";
import { ERROR_CATALOGUE } from "../errors/catalogue.ts";

/** Assert an internal invariant; failure is a 500 (programmer error, not user input). */
export function invariant(condition: unknown, message: string): asserts condition {
  if (!condition) {
    throw new AppError(ERROR_CATALOGUE.INTERNAL, { detail: message });
  }
}
