/** Server-authoritative weekly plan and slot-lock persistence. */
import { createServiceRoleClient } from "../_shared/db/client.ts";
import type { RequestContext } from "../_shared/types/context.ts";
import { withTimeout } from "../_shared/utils/timeout.ts";

const WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

function mondayUtc(value = new Date()): Date {
  const day = value.getUTCDay();
  const out = new Date(Date.UTC(value.getUTCFullYear(), value.getUTCMonth(), value.getUTCDate()));
  out.setUTCDate(out.getUTCDate() - (day === 0 ? 6 : day - 1));
  return out;
}

function isoDate(value: Date): string {
  return value.toISOString().slice(0, 10);
}

export async function loadSavedWeek(ctx: RequestContext, profileId: string, slotDate?: string) {
  const db = createServiceRoleClient(ctx.config);
  const reference = slotDate ? new Date(`${slotDate}T12:00:00Z`) : new Date();
  if (Number.isNaN(reference.getTime())) throw new Error("invalid slot_date");
  const weekStart = isoDate(mondayUtc(reference));
  const { data: plan, error } = await withTimeout(
    db.from("week_plans").select("id,status,is_locked,week_start_date,plan_slots(*)")
      .eq("profile_id", profileId).eq("week_start_date", weekStart).maybeSingle(),
    "plan.state.load",
  );
  if (error) throw error;
  return plan;
}

export async function saveWeek(
  ctx: RequestContext,
  profileId: string,
  selections: Record<string, Record<string, string>>,
  finalize: boolean,
) {
  const chosen = Object.values(selections).reduce((n, slots) => n + Object.keys(slots).length, 0);
  if (finalize && chosen !== 21) {
    throw new Error("all 21 meal slots are required before finalizing");
  }
  const db = createServiceRoleClient(ctx.config);
  const monday = mondayUtc();
  const weekStart = isoDate(monday);
  const { data: plan, error: planError } = await withTimeout(
    db.from("week_plans").upsert({
      profile_id: profileId,
      household_id: profileId,
      week_start_date: weekStart,
      re_version: "ghar-re-v1",
      status: finalize ? "finalized" : "draft",
      updated_at: new Date().toISOString(),
    }, { onConflict: "profile_id,week_start_date" }).select("id,status").single(),
    "plan.state.save_week",
  );
  if (planError) throw planError;
  const rows: Record<string, unknown>[] = [];
  for (const [weekday, slots] of Object.entries(selections)) {
    const offset = WEEKDAYS.indexOf(weekday);
    if (offset < 0) continue;
    const date = new Date(monday);
    date.setUTCDate(date.getUTCDate() + offset);
    for (const [mealSlot, classCode] of Object.entries(slots)) {
      rows.push({
        week_plan_id: plan.id,
        slot_date: isoDate(date),
        meal_slot: mealSlot,
        class_code: classCode,
      });
    }
  }
  if (rows.length) {
    const { error } = await withTimeout(
      db.from("plan_slots").upsert(rows, { onConflict: "week_plan_id,slot_date,meal_slot" }),
      "plan.state.save_slots",
    );
    if (error) throw error;
  }
  if (finalize) {
    const { data: profile } = await withTimeout(
      db.from("profiles").select("push_notification_time").eq("id", profileId).maybeSingle(),
      "plan.state.notification_profile",
    );
    const { data: consent } = await withTimeout(
      db.from("consent_records").select("granted").eq("profile_id", profileId)
        .eq("consent_type", "push_notifications").order("granted_at", { ascending: false })
        .limit(1).maybeSingle(),
      "plan.state.notification_consent",
    );
    if (consent?.granted) {
      const tomorrow = new Date();
      tomorrow.setUTCDate(tomorrow.getUTCDate() + 1);
      const [hour, minute] = String(profile?.push_notification_time ?? "07:00").split(":").map(
        Number,
      );
      tomorrow.setUTCHours((hour + 18) % 24, minute + 30, 0, 0); // configured IST -> UTC
      const { error } = await withTimeout(
        db.from("notification_jobs").upsert({
          profile_id: profileId,
          job_date: isoDate(tomorrow),
          scheduled_for: tomorrow.toISOString(),
          payload: { title: "Your Foofoo plan is ready", route: "/today" },
          status: "pending",
          updated_at: new Date().toISOString(),
        }, { onConflict: "profile_id,job_date,notification_type" }),
        "plan.state.notification_schedule",
      );
      if (error) throw error;
    }
  }
  return { id: plan.id, status: plan.status, chosen_slots: chosen, required_slots: 21 };
}

export async function setSlotLock(
  ctx: RequestContext,
  profileId: string,
  weekday: string,
  mealSlot: string,
  locked: boolean,
  slotDate?: string,
) {
  const plan = await loadSavedWeek(ctx, profileId, slotDate) as Record<string, unknown> | null;
  if (!plan) throw new Error("save the weekly plan before locking a slot");
  const offset = WEEKDAYS.indexOf(weekday);
  if (offset < 0) throw new Error("invalid weekday");
  const date = slotDate ? new Date(`${slotDate}T12:00:00Z`) : mondayUtc();
  if (!slotDate) date.setUTCDate(date.getUTCDate() + offset);
  if (Number.isNaN(date.getTime())) throw new Error("invalid slot_date");
  const db = createServiceRoleClient(ctx.config);
  const { data, error } = await withTimeout(
    db.from("plan_slots").update({
      is_locked: locked,
      locked_at: locked ? new Date().toISOString() : null,
    })
      .eq("week_plan_id", plan.id).eq("slot_date", isoDate(date)).eq("meal_slot", mealSlot)
      .select("id,is_locked,locked_at").single(),
    "plan.state.lock_slot",
  );
  if (error) throw error;
  return data;
}

export async function addDishToDate(
  ctx: RequestContext,
  profileId: string,
  slotDate: string,
  mealSlot: string,
  classCode: string,
  dishName: string,
) {
  const target = new Date(`${slotDate}T12:00:00Z`);
  if (Number.isNaN(target.getTime())) throw new Error("invalid slot_date");
  const max = new Date();
  max.setUTCDate(max.getUTCDate() + 7);
  if (target < new Date(new Date().toISOString().slice(0, 10)) || target > max) {
    throw new Error("slot_date must be within the next 7 days");
  }
  const db = createServiceRoleClient(ctx.config);
  const { data: dish, error: dishError } = await withTimeout(
    db.from("dishes").select("id").eq("name", dishName).maybeSingle(),
    "plan.state.add_date_dish",
  );
  if (dishError || !dish) throw dishError ?? new Error("dish not found");
  const weekStart = isoDate(mondayUtc(target));
  const { data: plan, error: planError } = await withTimeout(
    db.from("week_plans").upsert({
      profile_id: profileId,
      household_id: profileId,
      week_start_date: weekStart,
      re_version: "ghar-re-v1",
      status: "draft",
      updated_at: new Date().toISOString(),
    }, { onConflict: "profile_id,week_start_date" }).select("id").single(),
    "plan.state.add_date_week",
  );
  if (planError) throw planError;
  const { data, error } = await withTimeout(
    db.from("plan_slots").upsert({
      week_plan_id: plan.id,
      slot_date: slotDate,
      meal_slot: mealSlot,
      class_code: classCode,
      selected_dish_id: dish.id,
    }, { onConflict: "week_plan_id,slot_date,meal_slot" }).select("id,slot_date,meal_slot")
      .single(),
    "plan.state.add_date_slot",
  );
  if (error) throw error;
  return data;
}
