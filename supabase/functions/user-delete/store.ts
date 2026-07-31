/**
 * POST /v1/user/delete — data access (DOC-P3-06 §06.8, LF-M03 `executeDataDeletion()`).
 *
 * This function performs ONLY the immediate soft-delete (`profiles.deleted_at`) — the actual
 * hard-delete-within-72h is a separate scheduled job
 * (`_shared/services/scheduler/hard-delete.ts`), matching DOC-P3-06 §06.8's own framing ("the
 * CRON-based hard-delete itself remains, correctly, an internal scheduled job").
 */
import type { SupabaseClient } from "../_shared/db/client.ts";
import { PUBLIC_SCHEMA } from "../_shared/constants/schemas.ts";
import { withTimeout } from "../_shared/utils/timeout.ts";
import { AppError } from "../_shared/errors/app-error.ts";
import { ERROR_CATALOGUE } from "../_shared/errors/catalogue.ts";

function dbFail(op: string, message: string): never {
  throw new AppError(ERROR_CATALOGUE.INTERNAL, { detail: `${op}: ${message}` });
}

/** Read the profile's existence + current `deleted_at`. `exists: false` is distinct from
 * `deletedAt: null` — the former means there is no profiles row at all for this id. */
export async function getProfileDeletionState(
  db: SupabaseClient,
  profileId: string,
): Promise<{ exists: boolean; deletedAt: string | null }> {
  const { data, error } = await withTimeout(
    db.schema(PUBLIC_SCHEMA).from("profiles").select("deleted_at").eq("id", profileId)
      .maybeSingle(),
    "userDelete.getProfileDeletionState",
  );
  if (error) dbFail("read profiles.deleted_at", error.message);
  if (!data) return { exists: false, deletedAt: null };
  return { exists: true, deletedAt: (data as { deleted_at: string | null }).deleted_at };
}

/**
 * Set `deleted_at = now()` — ONLY if it is not already set (`.is("deleted_at", null)`), so a
 * concurrent retry can't push the 72h hard-delete clock forward by re-stamping it. Returns the
 * timestamp that ended up stored (either the one this call just set, or — if a concurrent call won
 * the race — whatever is there now, re-read).
 */
export async function softDeleteIfNotAlready(
  db: SupabaseClient,
  profileId: string,
): Promise<string> {
  const now = new Date().toISOString();
  const { data, error } = await withTimeout(
    db
      .schema(PUBLIC_SCHEMA)
      .from("profiles")
      .update({ deleted_at: now })
      .eq("id", profileId)
      .is("deleted_at", null)
      .select("deleted_at"),
    "userDelete.softDelete",
  );
  if (error) dbFail("soft-delete profile", error.message);
  if ((data ?? []).length > 0) {
    return (data as Array<{ deleted_at: string }>)[0].deleted_at;
  }
  // Row count 0 means deleted_at was already non-null (a concurrent/earlier call won) — re-read
  // the existing value rather than assume `now`, so hard_delete_estimated_by stays anchored to the
  // ORIGINAL soft-delete time, never reset by a retry.
  const existing = await getProfileDeletionState(db, profileId);
  if (existing.deletedAt === null) {
    // Should be unreachable (the row existed a moment ago, per the caller's own pre-check); fail
    // loudly rather than fabricate a timestamp.
    throw new AppError(ERROR_CATALOGUE.INTERNAL, {
      detail: "profiles.deleted_at unexpectedly null immediately after a no-op soft-delete update",
    });
  }
  return existing.deletedAt;
}
