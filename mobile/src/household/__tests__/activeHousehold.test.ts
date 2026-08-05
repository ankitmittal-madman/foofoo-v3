import AsyncStorage from "@react-native-async-storage/async-storage";
import { supabase } from "@/auth/supabaseClient";
import {
  clearActiveHousehold,
  getActiveHouseholdId,
  setActiveHouseholdId,
  withActiveHousehold,
} from "../activeHousehold";

jest.mock("@/auth/supabaseClient", () => ({
  supabase: {
    auth: {
      getSession: jest.fn(() => Promise.resolve({
        data: { session: { user: { id: "user-1" } } },
      })),
    },
  },
}));

const mockGetSession = supabase.auth.getSession as jest.MockedFunction<
  typeof supabase.auth.getSession
>;

describe("active household selection", () => {
  beforeEach(async () => {
    await AsyncStorage.clear();
    mockGetSession.mockClear();
  });

  it("stores the selection per signed-in user and injects it into household requests", async () => {
    await setActiveHouseholdId("household-2");
    await expect(getActiveHouseholdId()).resolves.toBe("household-2");
    await expect(withActiveHousehold({ surface: "meal_episodes" })).resolves.toEqual({
      surface: "meal_episodes",
      household_id: "household-2",
    });
  });

  it("clears the selected tenant on sign-out", async () => {
    await setActiveHouseholdId("household-2");
    await clearActiveHousehold();
    await expect(getActiveHouseholdId()).resolves.toBeNull();
  });
});
