/**
 * Validation framework (WP-8B foundation).
 *
 * Thin wrapper over Zod. Endpoint request/response SCHEMAS are added per-endpoint in later WPs
 * (they must mirror the DB CHECK constraints — DOC-P3-07 §26). This module only provides the
 * reusable `validate()` that converts a schema failure into a typed VALIDATION_FAILED AppError.
 */
import { z, type ZodType } from "zod";
import { AppError } from "../errors/app-error.ts";
import { ERROR_CATALOGUE } from "../errors/catalogue.ts";

/** Validate `data` against `schema`; return the typed value or throw VALIDATION_FAILED. */
export function validate<T>(schema: ZodType<T>, data: unknown): T {
  const result = schema.safeParse(data);
  if (!result.success) {
    const issues = result.error.issues.map((i) => ({
      path: i.path.join("."),
      message: i.message,
    }));
    throw new AppError(ERROR_CATALOGUE.VALIDATION_FAILED, {
      detail: JSON.stringify(issues),
      context: { issues },
    });
  }
  return result.data;
}

export { z };
export type { ZodType };
