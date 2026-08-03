/**
 * weeklyPlanStore — local persistence for the user's FINALIZED weekly class selections (WP-18
 * surface 3→4 handoff). No backend table exists yet for "this household's chosen weekly plan", so
 * this is a device-local placeholder: the weekly-plan screen writes {weekday: {slot: class_code}}
 * here when the user finalizes, and daily-plan reads it back to reconcile dishes for each day.
 *
 * Deliberately AsyncStorage, not component state: the two screens are separate route pushes, and a
 * user may background/resume the app between finalizing the week and browsing a day's dishes.
 */
import AsyncStorage from "@react-native-async-storage/async-storage";

const KEY = "foofoo.weeklyPlan.v1";

export type SlotName = "breakfast" | "lunch" | "dinner";
export type FinalizedWeek = Record<string, Partial<Record<SlotName, string>>>;

export async function saveWeeklyPlan(plan: FinalizedWeek): Promise<void> {
  await AsyncStorage.setItem(KEY, JSON.stringify(plan));
}

export async function loadWeeklyPlan(): Promise<FinalizedWeek | null> {
  const raw = await AsyncStorage.getItem(KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as FinalizedWeek;
  } catch {
    return null;
  }
}
