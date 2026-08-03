/**
 * GET /v1/user/export — data access (DOC-P3-06 §06.7, LF-M02 `executeDataExport()`).
 *
 * Reads EXACTLY the 8 tables DOC-P3-03 §15 LF-M02 names, every query explicitly scoped to the
 * caller's own `profile_id`/`user_id` (never relying on RLS — this runs under service_role, which
 * bypasses RLS entirely, same discipline as every other adapter in this codebase). `plan_slots` has
 * no direct `profile_id` column — it is scoped via its owning `week_plans` row instead.
 */
import type { SupabaseClient } from "../_shared/db/client.ts";
import { PUBLIC_SCHEMA } from "../_shared/constants/schemas.ts";
import { withTimeout } from "../_shared/utils/timeout.ts";
import { AppError } from "../_shared/errors/app-error.ts";
import { ERROR_CATALOGUE } from "../_shared/errors/catalogue.ts";

function dbFail(op: string, message: string): never {
  throw new AppError(ERROR_CATALOGUE.INTERNAL, { detail: `${op}: ${message}` });
}

/** The exact LF-M02 data scope, one key per table, keyed by table name for the export payload. */
export interface UserExportBundle {
  readonly profiles: unknown;
  readonly household_members: unknown[];
  readonly interaction_events: unknown[];
  readonly week_plans: unknown[];
  readonly plan_slots: unknown[];
  readonly never_list: unknown[];
  readonly onboarding_sessions: unknown[];
  readonly consent_records: unknown[];
  readonly exported_at: string;
}

/** Load every LF-M02-scoped row for exactly one profile_id — never a broader query. */
export async function loadUserExportBundle(
  db: SupabaseClient,
  profileId: string,
): Promise<UserExportBundle> {
  const [
    profileRes,
    membersRes,
    eventsRes,
    weekPlansRes,
    neverListRes,
    sessionsRes,
    consentRes,
  ] = await Promise.all([
    withTimeout(
      db.schema(PUBLIC_SCHEMA).from("profiles").select("*").eq("id", profileId).maybeSingle(),
      "userExport.profiles",
    ),
    withTimeout(
      db.schema(PUBLIC_SCHEMA).from("household_members").select("*").eq("profile_id", profileId),
      "userExport.household_members",
    ),
    withTimeout(
      db.schema(PUBLIC_SCHEMA).from("interaction_events").select("*").eq("profile_id", profileId),
      "userExport.interaction_events",
    ),
    withTimeout(
      db.schema(PUBLIC_SCHEMA).from("week_plans").select("*").eq("profile_id", profileId),
      "userExport.week_plans",
    ),
    withTimeout(
      // WP-20: never_list moved re_engine -> public (migration 046) ahead of the re_engine schema drop.
      db.schema(PUBLIC_SCHEMA).from("never_list").select("*").eq("profile_id", profileId),
      "userExport.never_list",
    ),
    withTimeout(
      db.schema(PUBLIC_SCHEMA).from("onboarding_sessions").select("*").eq("profile_id", profileId),
      "userExport.onboarding_sessions",
    ),
    withTimeout(
      db.schema(PUBLIC_SCHEMA).from("consent_records").select("*").eq("profile_id", profileId),
      "userExport.consent_records",
    ),
  ]);

  if (profileRes.error) dbFail("read profiles", profileRes.error.message);
  if (membersRes.error) dbFail("read household_members", membersRes.error.message);
  if (eventsRes.error) dbFail("read interaction_events", eventsRes.error.message);
  if (weekPlansRes.error) dbFail("read week_plans", weekPlansRes.error.message);
  if (neverListRes.error) dbFail("read never_list", neverListRes.error.message);
  if (sessionsRes.error) dbFail("read onboarding_sessions", sessionsRes.error.message);
  if (consentRes.error) dbFail("read consent_records", consentRes.error.message);

  // plan_slots has no profile_id column — scope via the profile's own week_plans ids only.
  const weekPlanIds = ((weekPlansRes.data ?? []) as Array<{ id: string }>).map((r) => r.id);
  let planSlots: unknown[] = [];
  if (weekPlanIds.length > 0) {
    const { data, error } = await withTimeout(
      db.schema(PUBLIC_SCHEMA).from("plan_slots").select("*").in("week_plan_id", weekPlanIds),
      "userExport.plan_slots",
    );
    if (error) dbFail("read plan_slots", error.message);
    planSlots = data ?? [];
  }

  return {
    profiles: profileRes.data,
    household_members: membersRes.data ?? [],
    interaction_events: eventsRes.data ?? [],
    week_plans: weekPlansRes.data ?? [],
    plan_slots: planSlots,
    never_list: neverListRes.data ?? [],
    onboarding_sessions: sessionsRes.data ?? [],
    consent_records: consentRes.data ?? [],
    exported_at: new Date().toISOString(),
  };
}
