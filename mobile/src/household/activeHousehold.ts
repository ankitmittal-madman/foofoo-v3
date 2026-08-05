import AsyncStorage from "@react-native-async-storage/async-storage";
import { supabase } from "@/auth/supabaseClient";

const ACTIVE_HOUSEHOLD_KEY = "foofoo.activeHousehold.v1";

interface ActiveHouseholdRecord {
  user_id: string;
  household_id: string;
}

export async function getActiveHouseholdId(): Promise<string | null> {
  const [{ data }, raw] = await Promise.all([
    supabase.auth.getSession(),
    AsyncStorage.getItem(ACTIVE_HOUSEHOLD_KEY),
  ]);
  if (!data.session?.user.id || !raw) return null;
  try {
    const record = JSON.parse(raw) as ActiveHouseholdRecord;
    return record.user_id === data.session.user.id ? record.household_id : null;
  } catch {
    await AsyncStorage.removeItem(ACTIVE_HOUSEHOLD_KEY);
    return null;
  }
}

export async function setActiveHouseholdId(householdId: string): Promise<void> {
  const { data } = await supabase.auth.getSession();
  const userId = data.session?.user.id;
  if (!userId) throw new Error("Sign in before selecting a household");
  await AsyncStorage.setItem(
    ACTIVE_HOUSEHOLD_KEY,
    JSON.stringify({ user_id: userId, household_id: householdId } satisfies ActiveHouseholdRecord),
  );
}

export function clearActiveHousehold(): Promise<void> {
  return AsyncStorage.removeItem(ACTIVE_HOUSEHOLD_KEY);
}

export async function withActiveHousehold<T extends Record<string, unknown>>(
  body: T,
): Promise<T & { household_id?: string }> {
  if (typeof body.household_id === "string") return body;
  const householdId = await getActiveHouseholdId();
  return householdId ? { ...body, household_id: householdId } : body;
}
