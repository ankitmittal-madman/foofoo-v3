/**
 * POST /v1/user/delete — request validation (DOC-P3-06 §06.8 / DCR-P3-06-005).
 */
import { z } from "../_shared/validation/validate.ts";
import { AppError } from "../_shared/errors/app-error.ts";
import { API_ERRORS } from "../_shared/errors/api-catalogue.ts";

/** The exact, case-sensitive safety-gate phrase (DOC-P3-06 §06.8) — not a stored column, a
 * request-only confirmation gate. */
export const REQUIRED_CONFIRMATION_PHRASE = "DELETE MY ACCOUNT";

const requestEnvelope = z.object({
  user_id: z.string().uuid(),
  confirmation_phrase: z.string(),
});

export interface ParsedDeleteRequest {
  readonly userId: string;
  readonly confirmationPhrase: string;
}

/** Parse + validate; does NOT check the confirmation phrase value itself (the handler does that,
 * since a mismatch is its own specific error code, not a generic 400). */
export function parseDeleteRequest(body: unknown): ParsedDeleteRequest {
  const parsed = requestEnvelope.safeParse(body);
  if (!parsed.success) {
    const issues = parsed.error.issues.map((i) => ({ path: i.path.join("."), message: i.message }));
    throw new AppError(API_ERRORS.ERR_VALIDATION_FAILED, {
      detail: JSON.stringify(issues),
      context: { issues },
    });
  }
  return { userId: parsed.data.user_id, confirmationPhrase: parsed.data.confirmation_phrase };
}
