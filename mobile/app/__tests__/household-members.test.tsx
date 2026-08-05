import { render, screen, waitFor } from "@testing-library/react-native";
import HouseholdMembers from "../household-members";

jest.mock("expo-router", () => ({ router: { back: jest.fn() } }));
jest.mock("@/auth/SessionContext", () => ({
  useSession: () => ({ session: { user: { id: "user-1" } } }),
}));
jest.mock("@/household/activeHousehold", () => ({
  getActiveHouseholdId: jest.fn(() => Promise.resolve("household-1")),
  setActiveHouseholdId: jest.fn(() => Promise.resolve()),
}));
jest.mock("@/api/errorMessages", () => ({ describeApiError: () => "Request failed" }));
jest.mock("@/api/householdAccess", () => ({
  listMyHouseholds: jest.fn(),
  listHouseholdAccess: jest.fn(),
  createHouseholdInvite: jest.fn(),
  acceptHouseholdInvite: jest.fn(),
  updateHouseholdMember: jest.fn(),
  leaveHousehold: jest.fn(),
}));
jest.mock("@tanstack/react-query", () => ({
  useQuery: jest.fn(({ queryKey }: { queryKey: string[] }) => queryKey[0] === "households"
    ? {
      data: {
        households: [{
          household_id: "household-1",
          name: "Shared home",
          role: "owner",
          joined_at: "2026-08-05T00:00:00Z",
          owner_user_id: "user-1",
        }],
      },
      isLoading: false,
      error: null,
    }
    : {
      data: {
        household_id: "household-1",
        caller_role: "owner",
        memberships: [{
          user_id: "user-1",
          role_code: "owner",
          status: "active",
          joined_at: "2026-08-05T00:00:00Z",
          revoked_at: null,
        }],
        invites: [],
        events: [],
      },
      isLoading: false,
      error: null,
    }),
  useMutation: jest.fn(() => ({ mutate: jest.fn(), isPending: false, error: null })),
  useQueryClient: () => ({
    removeQueries: jest.fn(),
    invalidateQueries: jest.fn(() => Promise.resolve()),
  }),
}));

describe("HouseholdMembers", () => {
  it("shows the selected household, owner role and secure invitation controls", async () => {
    render(<HouseholdMembers />);
    await waitFor(() => {
      expect(screen.getByText("Shared home · owner")).toBeTruthy();
      expect(screen.getByText("Your role: owner")).toBeTruthy();
      expect(screen.getByText("Create secure invite")).toBeTruthy();
      expect(screen.getByTestId("household-invite-token-input")).toBeTruthy();
    });
  });
});
