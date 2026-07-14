/**
 * Consent request validation (WP-8C — POST /v1/consent).
 *
 * Mirrors the frozen contract (DOC-P3-06 §06.1) and the DB CHECK constraint on
 * `public.consent_records.consent_type` (DOC-P3-04 §03.4). Validation is split deliberately to
 * honor the contract's 400-vs-422 distinction (DOC-P3-06 §07 / §21.1):
 *   - structural problems (missing/malformed fields)      → ERR_VALIDATION_FAILED (400)
 *   - well-formed but consent_type not in the CHECK set    → ERR_CONSENT_TYPE_INVALID (422)
 *
 * That is why consent_type is validated as a plain string by Zod (structure) and its enum
 * membership is checked separately — a Zod z.enum would collapse both into a single 400.
 */
import { z } from "./validate.ts";
import { AppError } from "../errors/app-error.ts";
import { API_ERRORS } from "../errors/api-catalogue.ts";

/** The exact 4 values in the consent_records.consent_type CHECK constraint (DOC-P3-04 §03.4). */
export const CONSENT_TYPES = [
  "personalization",
  "analytics",
  "push_notifications",
  "data_retention",
] as const;

export type ConsentType = typeof CONSENT_TYPES[number];

export interface ConsentInput {
  readonly consentType: ConsentType;
  readonly granted: boolean;
}

export interface ConsentRequest {
  readonly profileId: string;
  readonly consents: ConsentInput[];
  readonly privacyPolicyVersion: string;
}

/** Structural schema only — semantic enum membership is checked afterwards (see above). */
const consentEnvelope = z.object({
  profile_id: z.string().uuid(),
  consents: z
    .array(
      z.object({
        consent_type: z.string(),
        granted: z.boolean(),
      }),
    )
    .min(1),
  privacy_policy_version: z.string().min(1),
});

function isConsentType(value: string): value is ConsentType {
  return (CONSENT_TYPES as readonly string[]).includes(value);
}

/**
 * Parse + validate a raw request body into a typed ConsentRequest.
 * @throws AppError ERR_VALIDATION_FAILED (400) on structural failure.
 * @throws AppError ERR_CONSENT_TYPE_INVALID (422) on an unrecognized consent_type.
 */
export function parseConsentRequest(body: unknown): ConsentRequest {
  const parsed = consentEnvelope.safeParse(body);
  if (!parsed.success) {
    const issues = parsed.error.issues.map((i) => ({
      path: i.path.join("."),
      message: i.message,
    }));
    throw new AppError(API_ERRORS.ERR_VALIDATION_FAILED, {
      detail: JSON.stringify(issues),
      context: { issues },
    });
  }

  for (const c of parsed.data.consents) {
    if (!isConsentType(c.consent_type)) {
      throw new AppError(API_ERRORS.ERR_CONSENT_TYPE_INVALID, {
        context: { invalid_consent_type: c.consent_type, allowed: CONSENT_TYPES },
      });
    }
  }

  return {
    profileId: parsed.data.profile_id,
    consents: parsed.data.consents.map((c) => ({
      consentType: c.consent_type as ConsentType,
      granted: c.granted,
    })),
    privacyPolicyVersion: parsed.data.privacy_policy_version,
  };
}
