/**
 * Concrete Supabase adapters — persistence + caller-load path (WP-8E).
 *
 * Repository layer ONLY (DOC-P4-00 §4): thin query wrappers, zero business logic, no scoring, no
 * filtering. Columns match the verified DDL (migrations 005/006/007/011; DOC-P3-04 §03.1–03.13).
 * Because Edge Functions run under service_role (RLS bypassed), authorization is enforced upstream
 * (the ownership check in the handler) — these adapters trust the caller-verified profile id.
 *
 * NOTE (atomicity): the Supabase JS client does not wrap multi-statement transactions; production
 * should move persistWeekPlan into a Postgres RPC for the atomic slate write (DOC-P4-00 §16). This
 * adapter performs sequential upserts and is flagged as technical debt (WP-8E work package §debt).
 * These adapters are type-checked but NOT live-DB validated here (no live Supabase, per WP pattern).
 */
import type { SupabaseClient } from "../../db/client.ts";
import { PUBLIC_SCHEMA, RE_ENGINE_SCHEMA } from "../../constants/schemas.ts";
import { AppError } from "../../errors/app-error.ts";
import { ERROR_CATALOGUE } from "../../errors/catalogue.ts";
import type { PlanSlotRow, WeekPlanRow, WeekPlanStore } from "../planning/persistence.ts";
import type {
  HouseholdMemberRow,
  OnboardingSessionRow,
  OnboardingStore,
  ProfileRow,
  UserReStateRow,
} from "../onboarding/orchestrator.ts";
import type { PlanSlotStore, ReStateStore } from "../recommendations/service.ts";
import type { EligibleUser, EligibleUsersStore } from "../scheduler/nightly-plan.ts";
import type { MealSlot } from "../re/types.ts";

/** Raise a 500 without leaking the raw DB error to the client (DOC-P3-07). */
function dbFail(op: string, message: string): never {
  throw new AppError(ERROR_CATALOGUE.INTERNAL, { detail: `${op}: ${message}` });
}

// ── Plan persistence (public.week_plans + public.plan_slots) ─────────────────────────────────────

export class SupabaseWeekPlanStore implements WeekPlanStore {
  constructor(private readonly db: SupabaseClient) {}

  async persistWeekPlan(
    header: WeekPlanRow,
    slots: PlanSlotRow[],
  ): Promise<{ weekPlanId: string; weekStartDate: string }> {
    // Upsert the header on the natural key (profile_id, week_start_date) — DOC-P3-04 §03.12 UNIQUE.
    const { data: wp, error: wpErr } = await this.db
      .schema(PUBLIC_SCHEMA)
      .from("week_plans")
      .upsert({
        profile_id: header.profile_id,
        week_start_date: header.week_start_date,
        re_version: header.re_version,
      }, { onConflict: "profile_id,week_start_date" })
      .select("id")
      .single();
    if (wpErr || !wp) dbFail("persist week_plans", wpErr?.message ?? "no row");

    const weekPlanId = (wp as { id: string }).id;
    const slotRows = slots.map((s) => ({
      week_plan_id: weekPlanId,
      slot_date: s.slot_date,
      meal_slot: s.meal_slot,
      class_code: s.class_code,
      selected_dish_id: s.selected_dish_id,
      slate_dish_ids: s.slate_dish_ids,
      slate_reasons: s.slate_reasons,
      slate_confidence: s.slate_confidence,
      slate_generated_at: new Date().toISOString(),
      cold_start_mode: s.cold_start_mode,
    }));
    const { error: slotErr } = await this.db
      .schema(PUBLIC_SCHEMA)
      .from("plan_slots")
      .upsert(slotRows, { onConflict: "week_plan_id,slot_date,meal_slot" });
    if (slotErr) dbFail("persist plan_slots", slotErr.message);

    return { weekPlanId, weekStartDate: header.week_start_date };
  }

  async updateSlotSlate(weekPlanId: string, slot: PlanSlotRow): Promise<{ slotId: string }> {
    const { data, error } = await this.db
      .schema(PUBLIC_SCHEMA)
      .from("plan_slots")
      .update({
        selected_dish_id: slot.selected_dish_id,
        slate_dish_ids: slot.slate_dish_ids,
        slate_reasons: slot.slate_reasons,
        slate_confidence: slot.slate_confidence,
        slate_generated_at: new Date().toISOString(),
      })
      .eq("week_plan_id", weekPlanId)
      .eq("slot_date", slot.slot_date)
      .eq("meal_slot", slot.meal_slot)
      .select("id")
      .single();
    if (error || !data) dbFail("update plan_slots slate", error?.message ?? "no row");
    return { slotId: (data as { id: string }).id };
  }
}

// ── Onboarding writes (profiles, household_members, onboarding_sessions, user_re_state/vectors) ──

export class SupabaseOnboardingStore implements OnboardingStore {
  constructor(private readonly db: SupabaseClient) {}

  async isPersonalizationGranted(profileId: string): Promise<boolean> {
    // Latest 'personalization' consent row for this profile (append-only history, DOC-P3-04 §03.4).
    const { data, error } = await this.db
      .schema(PUBLIC_SCHEMA)
      .from("consent_records")
      .select("granted, granted_at")
      .eq("profile_id", profileId)
      .eq("consent_type", "personalization")
      .order("granted_at", { ascending: false })
      .limit(1)
      .maybeSingle();
    if (error) dbFail("read consent", error.message);
    return data ? (data as { granted: boolean }).granted === true : false;
  }

  async isOnboardingComplete(profileId: string): Promise<boolean> {
    const { data, error } = await this.db
      .schema(PUBLIC_SCHEMA)
      .from("profiles")
      .select("onboarding_completed")
      .eq("id", profileId)
      .maybeSingle();
    if (error) dbFail("read profile", error.message);
    return data ? (data as { onboarding_completed: boolean }).onboarding_completed === true : false;
  }

  async persistProfile(row: ProfileRow): Promise<void> {
    const { error } = await this.db.schema(PUBLIC_SCHEMA).from("profiles").upsert({
      id: row.id,
      primary_cook_name: row.primary_cook_name,
      home_state: row.home_state,
      current_city: row.current_city,
      migration_duration_band: row.migration_duration_band,
      city_overlay_weight: row.city_overlay_weight,
      diet_type: row.diet_type,
      religious_pref: row.religious_pref,
      allergen_flags: row.allergen_flags,
      cook_capability: row.cook_capability,
      push_notification_time: row.push_notification_time,
      onboarding_completed: row.onboarding_completed,
      updated_at: new Date().toISOString(),
    }, { onConflict: "id" });
    if (error) dbFail("persist profile", error.message);
  }

  async persistHouseholdMembers(profileId: string, members: HouseholdMemberRow[]): Promise<void> {
    if (members.length === 0) return;
    const { error } = await this.db.schema(PUBLIC_SCHEMA).from("household_members").insert(
      members.map((m) => ({
        profile_id: profileId,
        member_name: m.member_name,
        segment: m.segment,
        allergen_flags: m.allergen_flags,
      })),
    );
    if (error) dbFail("persist household_members", error.message);
  }

  async persistOnboardingSessions(
    profileId: string,
    sessions: OnboardingSessionRow[],
  ): Promise<void> {
    if (sessions.length === 0) return;
    const { error } = await this.db.schema(PUBLIC_SCHEMA).from("onboarding_sessions").insert(
      sessions.map((s) => ({
        profile_id: profileId,
        screen_id: s.screen_id,
        question_key: s.question_key,
        answer_value: s.answer_value ?? null,
        skipped: s.skipped,
      })),
    );
    if (error) dbFail("persist onboarding_sessions", error.message);
  }

  async persistUserReState(row: UserReStateRow): Promise<void> {
    const { error } = await this.db.schema(RE_ENGINE_SCHEMA).from("user_re_state").upsert({
      profile_id: row.profile_id,
      persona_id: row.persona_id,
      overlay_persona_ids: row.overlay_persona_ids,
      confidence_score: row.confidence_score,
      interaction_count: row.interaction_count,
      cold_start_mode: row.cold_start_mode,
      re_engine_version: row.re_engine_version,
      city_overlay_weight: row.city_overlay_weight,
      updated_at: new Date().toISOString(),
    }, { onConflict: "profile_id" });
    if (error) dbFail("persist user_re_state", error.message);
  }

  async persistTasteVector(
    profileId: string,
    classAffinity: Record<string, number>,
  ): Promise<void> {
    const { error } = await this.db.schema(RE_ENGINE_SCHEMA).from("user_taste_vectors").upsert({
      profile_id: profileId,
      class_affinity: classAffinity,
      updated_at: new Date().toISOString(),
    }, { onConflict: "profile_id" });
    if (error) dbFail("persist user_taste_vectors", error.message);
  }
}

// ── Recommendations caller-load path ─────────────────────────────────────────────────────────────

export class SupabasePlanSlotStore implements PlanSlotStore {
  constructor(private readonly db: SupabaseClient) {}

  async getSlotClass(
    profileId: string,
    slotDate: string,
    mealSlot: MealSlot,
  ): Promise<{ weekPlanId: string; classCode: string } | null> {
    // Join plan_slots → week_plans to scope by owner (service_role bypasses RLS; owner asserted upstream).
    const { data, error } = await this.db
      .schema(PUBLIC_SCHEMA)
      .from("plan_slots")
      .select("class_code, week_plan_id, week_plans!inner(profile_id)")
      .eq("slot_date", slotDate)
      .eq("meal_slot", mealSlot)
      .eq("week_plans.profile_id", profileId)
      .maybeSingle();
    if (error) dbFail("read plan_slot class", error.message);
    if (!data) return null;
    const row = data as { class_code: string; week_plan_id: string };
    return { weekPlanId: row.week_plan_id, classCode: row.class_code };
  }
}

/** Loads eligible users for the nightly job (last_active_at within 7 days, DOC-P3-03 §14). */
export class SupabaseEligibleUsersStore implements EligibleUsersStore {
  constructor(private readonly db: SupabaseClient, private readonly loadUser: ReStateStore) {}

  async getEligibleUsers(): Promise<EligibleUser[]> {
    const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 3600 * 1000).toISOString();
    const { data, error } = await this.db
      .schema(PUBLIC_SCHEMA)
      .from("profiles")
      .select("id")
      .eq("onboarding_completed", true)
      .is("deleted_at", null)
      .gte("last_active_at", sevenDaysAgo);
    if (error) dbFail("read eligible users", error.message);

    const weekStartDate = nextMonday();
    const out: EligibleUser[] = [];
    for (const r of (data ?? []) as Array<{ id: string }>) {
      const loaded = await this.loadUser.loadUser(r.id);
      if (loaded) out.push({ ...loaded, weekStartDate });
    }
    return out;
  }
}

/** Monday of next week (YYYY-MM-DD), UTC. */
function nextMonday(): string {
  const d = new Date();
  const day = d.getUTCDay(); // 0=Sun
  const add = ((8 - day) % 7) || 7;
  d.setUTCDate(d.getUTCDate() + add);
  return d.toISOString().slice(0, 10);
}
