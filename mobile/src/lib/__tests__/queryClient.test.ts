import { shouldPersistQueryKey } from "../queryClient";

jest.mock("@/auth/supabaseClient", () => ({
  supabase: { auth: { getSession: jest.fn() } },
}));

describe("query cache persistence policy", () => {
  it("persists saved user state but never generated recommendation slates", () => {
    expect(shouldPersistQueryKey(["meal-episodes", "2026-08-05"])).toBe(false);
    expect(shouldPersistQueryKey(["daily-plan", "2026-08-05"])).toBe(false);
    expect(shouldPersistQueryKey(["saved-week", "2026-08-03"])).toBe(true);
    expect(shouldPersistQueryKey(["profile"])).toBe(false);
    expect(shouldPersistQueryKey(["households"])).toBe(false);
    expect(shouldPersistQueryKey(["household-access"])).toBe(false);
    expect(shouldPersistQueryKey([])).toBe(false);
  });
});
