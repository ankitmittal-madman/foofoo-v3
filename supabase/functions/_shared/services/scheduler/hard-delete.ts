/**
 * Hard-delete scheduler (Phase F) — LF-M03 `executeDataDeletion()`'s CRON half (DOC-P3-06 §06.8 /
 * DOC-P3-03 §15): "Hard-delete all personal data within 72h via CRON."
 *
 * Convention note: `nightly-plan.ts` (LF-L01's CRON) was the only existing scheduler in this
 * codebase at the time this file was written, and it was ITSELF never given a deployed Edge
 * Function entrypoint (confirmed by repo-wide search — only exercised by its own tests). It and
 * its test were deleted this session as confirmed dead code, unreachable from any live handler.
 * This file follows the SAME shape it did (a pure, DI'd, unit-testable class + a separate deployed
 * entrypoint in `supabase/functions/cron-hard-delete/`) for consistency, per this task's own
 * instruction that "consistency between the two matters more than which exact mechanism you pick."
 * Registering the actual `pg_cron` schedule (`SELECT cron.schedule(...)`) is a `database/`-scoped
 * change and is deliberately NOT done here — flagged in the WP report as a coordination item for
 * the next available migration number.
 *
 * Style: direct `SupabaseClient` queries, no repository/DI port layer — matching household/store.ts
 * and compose.ts's own documented Phase C.5 convention for a straightforward, single-purpose write
 * surface (as opposed to the RE engine's port-based DI, which exists because the engine itself is
 * unit-tested with fakes; a purge job has no equivalent need to swap implementations).
 */
import type { SupabaseClient } from "../../db/client.ts";
import { PUBLIC_SCHEMA, RE_ENGINE_SCHEMA } from "../../constants/schemas.ts";
import type { Logger } from "../../logging/logger.ts";

const HARD_DELETE_WINDOW_MS = 72 * 60 * 60 * 1000;

export interface HardDeleteResult {
  readonly processed: number;
  readonly succeeded: number;
  readonly failed: number;
}

export class HardDeleteScheduler {
  constructor(private readonly db: SupabaseClient, private readonly logger: Logger) {}

  /**
   * Hard-delete every profile whose 72h soft-delete window has elapsed. `audit_log` is
   * DELIBERATELY never touched here — DPDP retains it 3 years (DOC-P3-03 §15's one named exception;
   * DCR-P3-07-004 — a SEPARATE policy/table from the 2-year interaction_events retention purge,
   * see `retention-purge.ts`). Every other personal-data table LF-M03 names is purged, scoped
   * strictly to each due profile's own id, in FK-safe (children-before-parents) order.
   */
  async run(): Promise<HardDeleteResult> {
    const cutoff = new Date(Date.now() - HARD_DELETE_WINDOW_MS).toISOString();
    const { data, error } = await this.db
      .schema(PUBLIC_SCHEMA)
      .from("profiles")
      .select("id")
      .not("deleted_at", "is", null)
      .lte("deleted_at", cutoff);
    if (error) {
      this.logger.error("hard_delete.load_due_profiles_failed", { detail: error.message });
      return { processed: 0, succeeded: 0, failed: 0 };
    }

    const due = ((data ?? []) as Array<{ id: string }>).map((r) => r.id);
    let succeeded = 0;
    let failed = 0;
    for (const profileId of due) {
      try {
        await this.purgeProfile(profileId);
        succeeded++;
      } catch (err) {
        failed++;
        this.logger.error("hard_delete.purge_failed", {
          profile_id: profileId,
          error: err instanceof Error ? err.message : String(err),
        });
      }
    }

    this.logger.info("hard_delete.complete", { processed: due.length, succeeded, failed });
    return { processed: due.length, succeeded, failed };
  }

  /** Purge every LF-M03-scoped table for one profile, children before parents, then the profile
   * row itself. `audit_log` is never included (see class doc comment). */
  private async purgeProfile(profileId: string): Promise<void> {
    // plan_slots has no profile_id column — delete via the profile's own week_plans ids first.
    const { data: weekPlans, error: wpErr } = await this.db
      .schema(PUBLIC_SCHEMA)
      .from("week_plans")
      .select("id")
      .eq("profile_id", profileId);
    if (wpErr) throw wpErr;
    const weekPlanIds = ((weekPlans ?? []) as Array<{ id: string }>).map((r) => r.id);
    if (weekPlanIds.length > 0) {
      const { error } = await this.db.schema(PUBLIC_SCHEMA).from("plan_slots").delete().in(
        "week_plan_id",
        weekPlanIds,
      );
      if (error) throw error;
    }

    const publicTables = [
      "week_plans",
      "interaction_events",
      "household_members",
      "onboarding_sessions",
      "consent_records",
    ] as const;
    for (const table of publicTables) {
      const { error } = await this.db.schema(PUBLIC_SCHEMA).from(table).delete().eq(
        "profile_id",
        profileId,
      );
      if (error) throw error;
    }

    const reEngineTables = [
      "never_list",
      "not_today_suppression",
      "user_re_state",
      "user_taste_vectors",
      "re_dish_bandit_state",
    ] as const;
    for (const table of reEngineTables) {
      const { error } = await this.db.schema(RE_ENGINE_SCHEMA).from(table).delete().eq(
        "profile_id",
        profileId,
      );
      if (error) throw error;
    }

    // The profile row itself, last — every FK child above is already gone.
    const { error: profileErr } = await this.db
      .schema(PUBLIC_SCHEMA)
      .from("profiles")
      .delete()
      .eq("id", profileId);
    if (profileErr) throw profileErr;
  }
}
