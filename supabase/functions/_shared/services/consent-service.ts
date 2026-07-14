/**
 * Consent service (WP-8C) — implements LF-M01 captureConsent() (DOC-P3-03 §15).
 *
 * Records granular DPDP consent (DOC-09 §03) as append-only rows and resolves whether
 * personalization was granted — the flag that gates whether /v1/onboarding may proceed
 * (DOC-P3-06 §06.1 / §15 dependency). Orchestration only; all I/O is delegated to the
 * repository (DOC-P4-00 §5). Stateless — per-request state arrives via RequestContext.
 */
import { BaseService } from "./base-service.ts";
import type {
  ConsentInsertRow,
  IConsentRepository,
  RecordedConsent,
} from "../repositories/consent-repository.ts";
import type { ConsentRequest } from "../validation/consent-schema.ts";
import type { RequestContext } from "../types/context.ts";

/** Response body for POST /v1/consent (DOC-P3-06 §06.1). */
export interface ConsentResponse {
  readonly recorded: RecordedConsent[];
  readonly personalization_granted: boolean;
}

export class ConsentService extends BaseService {
  private readonly repo: IConsentRepository;

  constructor(ctx: RequestContext, repo: IConsentRepository) {
    super(ctx);
    this.repo = repo;
  }

  /**
   * LF-M01: persist one append-only row per consent action and return the recorded triples plus
   * the resolved personalization flag.
   *
   * @param req            the validated consent request (owner already asserted by the handler).
   * @param ipAddressHash  hashed IP at time of action (DOC-P3-04 §13.10); null until the IP-hash
   *                       salt secret is provisioned in a later WP — the column is nullable.
   */
  async captureConsent(
    req: ConsentRequest,
    ipAddressHash: string | null,
  ): Promise<ConsentResponse> {
    const rows: ConsentInsertRow[] = req.consents.map((c) => ({
      profile_id: req.profileId,
      consent_type: c.consentType,
      granted: c.granted,
      privacy_policy_version: req.privacyPolicyVersion,
      ip_address_hash: ipAddressHash,
    }));

    const recorded = await this.repo.insertConsents(rows);

    // Resolve personalization from the recorded rows; last occurrence wins if a client sent the
    // type more than once (append-only permits it). Absent → treated as not granted.
    const personalization = [...recorded]
      .reverse()
      .find((r) => r.consent_type === "personalization");
    const personalizationGranted = personalization?.granted ?? false;

    // No PII in logs (DOC-P3-07 §16): count + flag only, never profile_id.
    this.logger.info("consent_captured", {
      count: recorded.length,
      personalization_granted: personalizationGranted,
    });

    return { recorded, personalization_granted: personalizationGranted };
  }
}
