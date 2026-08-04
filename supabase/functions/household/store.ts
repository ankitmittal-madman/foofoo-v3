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
 * repository-based pattern that backed the retired legacy local RE (deleted this session — S40
 * ground-truth audit confirmed it dead, unreachable from any live handler).
 */
import { createServiceRoleClient } from "../_shared/db/client.ts";
import type { RequestContext } from "../_shared/types/context.ts";
import { type MemberWrite, PROFILE_REQUIRED_FIELDS, type ScreenAnswer } from "./schema.ts";
import { withTimeout } from "../_shared/utils/timeout.ts";

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

/**
 * Reduce this call's non-skipped, profiles-targeted screens into the partial column set to
 * UPDATE (P1-4, 2026-08). Mirrors buildHouseholdAnswersPatch's shape exactly, targeting
 * "profiles" instead of "household_answers" -- added because handler.ts previously had NO path
 * that ever updated an EXISTING profile's diet_type/allergen_flags/etc.: upsertProfileIfAbsent's
 * ON CONFLICT DO NOTHING makes profile creation correctly idempotent, but that also means it
 * silently no-ops for every field on a repeat call, including an intentional edit. This patch is
 * for updateProfileFields below, an explicit UPDATE, never used for the create path.
 */
export function buildProfilePatch(screens: ScreenAnswer[]): Record<string, unknown> {
  const patch: Record<string, unknown> = {};
  for (const s of screens) {
    if (s.target === "profiles" && !s.skipped) {
      patch[s.questionKey] = s.answerValue;
    }
  }
  return patch;
}

/**
 * UPDATE (not upsert) one or more public.profiles columns for an EXISTING profile (P1-4). Only
 * called by handler.ts when `exists` is already true and `fields` is non-empty -- never used to
 * create a row (upsertProfileIfAbsent above remains the only creation path), so there is no
 * FK/required-field concern here, just a plain column update scoped to the caller's own id.
 */
export async function updateProfileFields(
  ctx: RequestContext,
  profileId: string,
  fields: Record<string, unknown>,
): Promise<void> {
  if (Object.keys(fields).length === 0) return;
  const db = createServiceRoleClient(ctx.config);
  const { error } = await withTimeout(
    db.from("profiles").update(fields).eq("id", profileId),
    "household.updateProfileFields",
  );
  if (error) throw error;
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
  const { error } = await withTimeout(
    db.from("onboarding_sessions").insert(
      screens.map((s) => ({
        profile_id: profileId,
        screen_id: s.screenId,
        question_key: s.questionKey,
        answer_value: s.answerValue ?? null,
        skipped: s.skipped,
      })),
    ),
    "household.insertOnboardingSessionRows",
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
  const { error } = await withTimeout(
    db.from("household_answers").upsert(
      { profile_id: profileId, updated_at: new Date().toISOString(), ...patch },
      { onConflict: "profile_id" },
    ),
    "household.upsertHouseholdAnswers",
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
  const { data, error } = await withTimeout(
    db
      .from("onboarding_sessions")
      .select("question_key, answer_value, skipped, answered_at")
      .eq("profile_id", profileId)
      .eq("skipped", false)
      .order("answered_at", { ascending: true }),
    "household.accumulatedProfileFields",
  );
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

/**
 * Does a profiles row already exist for this household? NON-AUTHORITATIVE — a cheap fast-path
 * read only, used to skip loading accumulated fields when the caller already knows a profile
 * exists. It is deliberately NOT relied on to decide whether to write (see
 * `upsertProfileIfAbsent` below, which is what closes the check-then-act race, MEDIUM audit
 * finding — a stale read here can at worst cause one harmless extra atomic upsert attempt, never
 * a double-insert).
 */
export async function profileExists(ctx: RequestContext, profileId: string): Promise<boolean> {
  const db = createServiceRoleClient(ctx.config);
  const { data, error } = await withTimeout(
    db.from("profiles").select("id").eq("id", profileId).maybeSingle(),
    "household.profileExists",
  );
  if (error) throw error;
  return data !== null;
}

/**
 * Atomically create the profiles row exactly once, even under concurrent retries — the
 * check-then-act race the audit flagged (`profileExists()` → `createProfile()` could double-insert
 * when two requests both observe "not exists" before either write lands). Fixed here with a single
 * `INSERT ... ON CONFLICT (id) DO NOTHING` (supabase-js `upsert(..., { ignoreDuplicates: true })`):
 * Postgres itself serializes the two concurrent inserts on the `id` primary key, so at most one can
 * ever win, and the loser's statement is a guaranteed no-op rather than a unique-violation error.
 *
 * `RETURNING` (via `.select()`) only reports rows the INSERT actually affected — a row skipped by
 * `DO NOTHING` because it already existed is never returned. That makes the returned row COUNT
 * itself the atomicity signal: `> 0` means THIS call created the row; `0` means it already existed
 * (created by a concurrent or earlier call). No separate follow-up SELECT is needed to know which.
 *
 * `callerUserId` is a SEPARATE parameter from any request-supplied id, and this function always
 * upserts `id: callerUserId` — never a value threaded from the request body (same defense-in-depth
 * rationale as the previous `createProfile`: the ownership check in handler.ts is not the only
 * thing standing between an authenticated caller and writing someone else's profile).
 *
 * `fields` must already contain all five PROFILE_REQUIRED_FIELDS — the caller (handler.ts) gates
 * this. Optional profiles columns not present in `fields` are simply omitted, so Postgres applies
 * the column's own DEFAULT (religious_pref='all', allergen_flags=0, city_overlay_weight=0.50,
 * push_notification_time='07:00:00') rather than a value invented here (FD-11).
 *
 * @returns true if this call created the row, false if a profiles row for `callerUserId` already
 *   existed (including one created a moment earlier by a concurrent retry of this same request).
 */
export async function upsertProfileIfAbsent(
  ctx: RequestContext,
  callerUserId: string,
  fields: Record<string, unknown>,
): Promise<boolean> {
  const db = createServiceRoleClient(ctx.config);
  const { data, error } = await withTimeout(
    db
      .from("profiles")
      .upsert({ id: callerUserId, ...fields }, { onConflict: "id", ignoreDuplicates: true })
      .select("id"),
    "household.upsertProfileIfAbsent",
  );
  if (error) throw error;
  return (data ?? []).length > 0;
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
    const { error } = await withTimeout(
      db.from("household_members").insert(
        toInsert.map((m) => ({
          profile_id: profileId,
          member_name: m.memberName ?? null,
          conditions: m.conditions ?? [],
          allergen_flags: m.allergenFlags ?? 0,
          diet_type: m.dietType ?? null,
          is_active: m.isActive ?? true,
        })),
      ),
      "household.upsertHouseholdMembers.insert",
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

    const { error } = await withTimeout(
      db
        .from("household_members")
        .update(patch)
        .eq("id", m.id as string)
        .eq("profile_id", profileId),
      "household.upsertHouseholdMembers.update",
    );
    if (error) throw error;
  }

  return members.length;
}
