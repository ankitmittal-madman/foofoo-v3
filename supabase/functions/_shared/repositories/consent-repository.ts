/**
 * Consent repository (WP-8C).
 *
 * The ONLY place SQL/data-access for `public.consent_records` lives (DOC-P4-00 §4). The table is
 * append-only (DOC-P3-04 §03.4 / GR-05): every consent action inserts a new row; nothing is ever
 * updated or deleted here (erasure is the DPDP job's privileged concern, not this path). No
 * business logic — the service layer owns LF-M01.
 *
 * NOTE: types are hand-declared to mirror DOC-P3-04 §03.4 exactly. When `supabase gen types`
 * output is wired (scripts/gen-types.sh), these should be replaced by the generated row type so
 * schema drift breaks the build (DOC-P4-00 §4).
 */
import { BaseRepository } from "./base-repository.ts";
import { AppError } from "../errors/app-error.ts";
import { ERROR_CATALOGUE } from "../errors/catalogue.ts";
import type { ConsentType } from "../validation/consent-schema.ts";

/** A row to be inserted into public.consent_records (columns per DOC-P3-04 §03.4). */
export interface ConsentInsertRow {
  readonly profile_id: string;
  readonly consent_type: ConsentType;
  readonly granted: boolean;
  readonly privacy_policy_version: string;
  /** Nullable in the schema; populated by a later WP once an IP-hash salt secret exists. */
  readonly ip_address_hash: string | null;
}

/** The subset of columns returned to the caller (DOC-P3-06 §06.1 response). */
export interface RecordedConsent {
  readonly consent_type: ConsentType;
  readonly granted: boolean;
  readonly granted_at: string;
}

/** Repository contract — services depend on this, not the concrete class (testability, DI). */
export interface IConsentRepository {
  insertConsents(rows: ConsentInsertRow[]): Promise<RecordedConsent[]>;
}

export class ConsentRepository extends BaseRepository implements IConsentRepository {
  /**
   * Append consent rows and return the recorded (consent_type, granted, granted_at) triples.
   * `granted_at` is the DB DEFAULT now() value, selected back per the contract.
   */
  async insertConsents(rows: ConsentInsertRow[]): Promise<RecordedConsent[]> {
    const { data, error } = await this.db
      .from("consent_records")
      .insert(rows)
      .select("consent_type, granted, granted_at");

    if (error) {
      // Never leak the raw DB error to the client (DOC-P3-07); log the code, throw a 500.
      this.logger.error("consent_insert_failed", { pg_code: error.code });
      throw new AppError(ERROR_CATALOGUE.INTERNAL, {
        detail: `consent insert failed: ${error.message}`,
      });
    }
    return (data ?? []) as unknown as RecordedConsent[];
  }
}
