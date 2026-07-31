/**
 * Retention/purge scheduler (Phase F) — DOC-P3-03 §15 / DOC-09 §03, `DCR-P3-07-004`.
 *
 * TWO SEPARATE policies, two separate tables — deliberately not conflated (per DCR-P3-07-004's own
 * note): `interaction_events` rows older than 2 years are purged (RE-learning data has no DPDP
 * retention floor beyond operational usefulness); `audit_log` rows older than 3 years are purged
 * (the DPDP-mandated compliance-record retention period — this is the SAME `audit_log` that
 * `HardDeleteScheduler` deliberately never touches, because a soft-deleted user's compliance trail
 * must survive their own account deletion for exactly this long).
 *
 * Same convention as `hard-delete.ts`: a plain `SupabaseClient`-backed class (no port/DI layer —
 * see that file's doc comment for why) + a separate deployed entrypoint
 * (`supabase/functions/cron-retention-purge/`), consistent with `nightly-plan.ts`'s own
 * never-deployed shape. Registering the `pg_cron` schedule itself is a `database/`-scoped change,
 * flagged for the next available migration number, not done here.
 */
import type { SupabaseClient } from "../../db/client.ts";
import { PUBLIC_SCHEMA } from "../../constants/schemas.ts";
import type { Logger } from "../../logging/logger.ts";

const TWO_YEARS_MS = 2 * 365 * 24 * 60 * 60 * 1000;
const THREE_YEARS_MS = 3 * 365 * 24 * 60 * 60 * 1000;

export interface RetentionPurgeResult {
  readonly interactionEventsPurged: number;
  readonly auditLogPurged: number;
}

export class RetentionPurgeScheduler {
  constructor(private readonly db: SupabaseClient, private readonly logger: Logger) {}

  async run(): Promise<RetentionPurgeResult> {
    const interactionEventsPurged = await this.purgeOlderThan(
      "interaction_events",
      "occurred_at",
      TWO_YEARS_MS,
    );
    const auditLogPurged = await this.purgeOlderThan("audit_log", "occurred_at", THREE_YEARS_MS);

    this.logger.info("retention_purge.complete", { interactionEventsPurged, auditLogPurged });
    return { interactionEventsPurged, auditLogPurged };
  }

  private async purgeOlderThan(
    table: "interaction_events" | "audit_log",
    dateColumn: string,
    windowMs: number,
  ): Promise<number> {
    const cutoff = new Date(Date.now() - windowMs).toISOString();
    const { data, error } = await this.db
      .schema(PUBLIC_SCHEMA)
      .from(table)
      .delete()
      .lt(dateColumn, cutoff)
      .select("id");
    if (error) {
      this.logger.error("retention_purge.table_failed", { table, detail: error.message });
      return 0;
    }
    return (data ?? []).length;
  }
}
