/**
 * Household/onboarding writes — the live `public` schema (household/ — onboarding write path).
 *
 * Data ownership (RE-DOC-10 §1, same discipline as recommendations/compose.ts): this file is the
 * ONLY place that writes public.profiles / public.household_members / public.household_answers /
 * public.onboarding_sessions. It never touches `ghar_re.*` (the RE's offline golden-sample schema)
 * or `re_engine.*` (the retired reference tier).
 *
 * Style/pattern deliberately mirrors recommendations/compose.ts and events.ts (direct
 * createServiceRoleClient calls, `if (error) throw error` — no repository/DI layer): those are the
 * established Phase C.5 convention for new `public`-schema write surfaces, not the older
 * repository-based pattern under `_shared/services/adapters/` (which backs the retired legacy RE
 * and is not the precedent to extend — S40 ground-truth audit).
 */
import { createServiceRoleClient } from "../_shared/db/client.ts";
import type { RequestContext } from "../_shared/types/context.ts";
import { type MemberWrite, PROFILE_REQUIRED_FIELDS, type ScreenAnswer } from "./schema.ts";

// ---------------------------------------------------------------------------
// Pure helpers (no I/O) — exported for direct unit testing, same convention as compose.ts's
// composeHouseholdRaw/memberRole/toMemberAge.
// ---------------------------------------------------------------------------

/**
 * Reduce this call's non-skipped, household_answers-targeted screens into the partial column set
 * to UPSERT. Last write wins if the same question_key appears twice in one call. Skipped answers
 * and profiles-targeted answers are excluded — the former recorded no value, the latter belongs to
 * a different table (see accumulatedProfileFields).
 */
export function buildHouseholdAnswersPatch(screens: ScreenAnswer[]): Record<string, unknown> {
  const patch: Record<string, unknown> = {};
  for (const s of screens) {
    if (s.target === "household_answers" && !s.skipped) {
      patch[s.questionKey] = s.answerValue;
    }
  }
  return patch;
}

/** Which of the five required profile fields are still unknown, given an accumulated field set. */
export function missingRequiredProfileFields(accumulated: Record<string, unknown>): string[] {
  return PROFILE_REQUIRED_FIELDS.filter((f) => accumulated[f] === undefined);
}

// ---------------------------------------------------------------------------
// Writes
// ---------------------------------------------------------------------------

/**
 * Log every screen this call covers to the append-only onboarding_sessions history — including
 * skipped ones (skipped=true rows ARE the record of "asked, not answered"; they matter for resume
 * logic even though they carry no value). This is the source of truth accumulatedProfileFields
 * reduces over, so it MUST run before that function is called for the same request.
 */
export async function insertOnboardingSessionRows(
  ctx: RequestContext,
  profileId: string,
  screens: ScreenAnswer[],
): Promise<void> {
  if (screens.length === 0) return;
  const db = createServiceRoleClient(ctx.config);
  const { error } = await db.from("onboarding_sessions").insert(
    screens.map((s) => ({
      profile_id: profileId,
      screen_id: s.screenId,
      question_key: s.questionKey,
      answer_value: s.answerValue ?? null,
      skipped: s.skipped,
    })),
  );
  // Unlike recommendations/events.ts's best-effort recommendation_events write, this one is NOT
  // best-effort: onboarding_sessions is the accumulation source of truth profile creation reads
  // from, so a silently-lost write here would silently strand a household's answers. Propagate.
  if (error) throw error;
}

/**
 * Incremental UPSERT of only the columns present in `patch` — every household_answers column is
 * nullable except the PK/timestamps/data_source (migration 038), so a partial payload genuinely
 * merges into the existing row rather than nulling out unmentioned columns. Skipped entirely when
 * `patch` is empty (this call touched no household_answers-bound fields).
 */
export async function upsertHouseholdAnswers(
  ctx: RequestContext,
  profileId: string,
  patch: Record<string, unknown>,
): Promise<void> {
  if (Object.keys(patch).length === 0) return;
  const db = createServiceRoleClient(ctx.config);
  const { error } = await db.from("household_answers").upsert(
    { profile_id: profileId, updated_at: new Date().toISOString(), ...patch },
    { onConflict: "profile_id" },
  );
  if (error) throw error;
}

/**
 * The accumulated value of every profiles-targeted question_key ever answered (non-skipped) for
 * this household, latest write wins. This is where a not-yet-created profile's fields live in the
 * meantime — public.profiles cannot hold them until all five required columns are known, so
 * onboarding_sessions (already an append-only per-answer log, migration 006) is the accumulation
 * substrate rather than a new staging table.
 *
 * Called AFTER insertOnboardingSessionRows for the same request, so this call's own new answers
 * are included in the reduction, not just prior calls' history.
 */
export async function accumulatedProfileFields(
  ctx: RequestContext,
  profileId: string,
): Promise<Record<string, unknown>> {
  const db = createServiceRoleClient(ctx.config);
  const { data, error } = await db
    .from("onboarding_sessions")
    .select("question_key, answer_value, skipped, answered_at")
    .eq("profile_id", profileId)
    .eq("skipped", false)
    .order("answered_at", { ascending: true });
  if (error) throw error;

  const rows = (data ?? []) as {
    question_key: string;
    answer_value: unknown;
    skipped: boolean;
  }[];

  const accumulated: Record<string, unknown> = {};
  for (const row of rows) {
    if ((PROFILE_REQUIRED_FIELDS as readonly string[]).includes(row.question_key)) {
      accumulated[row.question_key] = row.answer_value;
    }
  }
  return accumulated;
}

/** Does a profiles row already exist for this household? */
export async function profileExists(ctx: RequestContext, profileId: string): Promise<boolean> {
  const db = createServiceRoleClient(ctx.config);
  const { data, error } = await db
    .from("profiles")
    .select("id")
    .eq("id", profileId)
    .maybeSingle();
  if (error) throw error;
  return data !== null;
}

/**
 * Create the profiles row — ONCE. `callerUserId` is a SEPARATE parameter from any request-supplied
 * id, and this function always inserts `id: callerUserId` — never a value threaded from the
 * request body. This is the "enforce profiles.id = claims.userId at the query level, not a
 * post-hoc check" requirement: even if the ownership check earlier in the handler had a bug, this
 * INSERT is structurally incapable of creating a profile for anyone but the authenticated caller.
 *
 * `fields` must already contain all five PROFILE_REQUIRED_FIELDS — the caller (handler.ts) gates
 * this. Optional profiles columns not present in `fields` are simply omitted from the INSERT, so
 * Postgres applies the column's own DEFAULT (religious_pref='all', allergen_flags=0,
 * city_overlay_weight=0.50, push_notification_time='07:00:00') rather than a value invented here —
 * that DEFAULT is the schema's own mechanism for "not yet asked", not a fabrication (FD-11).
 */
export async function createProfile(
  ctx: RequestContext,
  callerUserId: string,
  fields: Record<string, unknown>,
): Promise<void> {
  const db = createServiceRoleClient(ctx.config);
  const { error } = await db.from("profiles").insert({ id: callerUserId, ...fields });
  if (error) throw error;
}

/**
 * Insert/update household_members rows. Requires a profiles row to already exist — enforced by
 * the FK (household_members.profile_id → profiles.id) and re-checked by the caller (handler.ts)
 * before this runs, so a caller-facing 422 is raised instead of a raw FK-violation 500.
 *
 * An update is scoped to BOTH `id` AND `profile_id` (defense in depth beyond the handler's
 * requireOwnership check): even if a member id from another household were somehow submitted, the
 * .eq("profile_id", profileId) means the UPDATE simply matches zero rows rather than touching a
 * row it has no business touching.
 */
export async function upsertHouseholdMembers(
  ctx: RequestContext,
  profileId: string,
  members: MemberWrite[],
): Promise<number> {
  if (members.length === 0) return 0;
  const db = createServiceRoleClient(ctx.config);

  const toInsert = members.filter((m) => !m.id);
  const toUpdate = members.filter((m) => m.id);

  if (toInsert.length > 0) {
    const { error } = await db.from("household_members").insert(
      toInsert.map((m) => ({
        profile_id: profileId,
        member_name: m.memberName ?? null,
        conditions: m.conditions ?? [],
        allergen_flags: m.allergenFlags ?? 0,
        diet_type: m.dietType ?? null,
        is_active: m.isActive ?? true,
      })),
    );
    if (error) throw error;
  }

  for (const m of toUpdate) {
    const patch: Record<string, unknown> = {};
    if (m.memberName !== undefined) patch.member_name = m.memberName;
    if (m.conditions !== undefined) patch.conditions = m.conditions;
    if (m.allergenFlags !== undefined) patch.allergen_flags = m.allergenFlags;
    if (m.dietType !== undefined) patch.diet_type = m.dietType;
    if (m.isActive !== undefined) patch.is_active = m.isActive;
    if (Object.keys(patch).length === 0) continue;

    const { error } = await db
      .from("household_members")
      .update(patch)
      .eq("id", m.id as string)
      .eq("profile_id", profileId);
    if (error) throw error;
  }

  return members.length;
}
