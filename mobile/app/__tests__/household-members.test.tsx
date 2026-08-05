import { render, screen, waitFor } from "@testing-library/react-native";
import HouseholdMembers from "../household-members";

let mockCallerRole = "owner";
let mockMemberships = [{
  user_id: "user-1",
  role_code: "owner",
  status: "active",
  joined_at: "2026-08-05T00:00:00Z",
  revoked_at: null,
}];

jest.mock("expo-router", () => ({ router: { back: jest.fn() } }));
jest.mock("@/auth/SessionContext", () => ({
  useSession: () => ({ session: { user: { id: "user-1" } } }),
}));
jest.mock("@/household/activeHousehold", () => ({
  getActiveHouseholdId: jest.fn(() => Promise.resolve("household-1")),
  setActiveHouseholdId: jest.fn(() => Promise.resolve()),
  clearActiveHousehold: jest.fn(() => Promise.resolve()),
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
        caller_role: mockCallerRole,
        memberships: mockMemberships,
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
  beforeEach(() => {
    mockCallerRole = "owner";
    mockMemberships = [{
      user_id: "user-1",
      role_code: "owner",
      status: "active",
      joined_at: "2026-08-05T00:00:00Z",
      revoked_at: null,
    }];
  });

  it("shows the selected household, owner role and secure invitation controls", async () => {
    render(<HouseholdMembers />);
    await waitFor(() => {
      expect(screen.getByText("Shared home · owner")).toBeTruthy();
      expect(screen.getByText("Your role: owner")).toBeTruthy();
      expect(screen.getByText("Create secure invite")).toBeTruthy();
      expect(screen.getByTestId("household-invite-token-input")).toBeTruthy();
    });
  });

  it("shows owner-only administration for another active member", async () => {
    mockMemberships = [...mockMemberships, {
      user_id: "user-2",
      role_code: "cook",
      status: "active",
      joined_at: "2026-08-05T00:00:00Z",
      revoked_at: null,
    }];
    render(<HouseholdMembers />);

    await waitFor(() => {
      expect(screen.getByTestId("household-transfer-user-2")).toBeTruthy();
      expect(screen.getByTestId("household-revoke-user-2")).toBeTruthy();
      expect(screen.queryByTestId("household-leave")).toBeNull();
    });
  });

  it("keeps administration hidden and offers leave to non-owners", async () => {
    mockCallerRole = "member";
    mockMemberships = [{
      user_id: "user-1",
      role_code: "member",
      status: "active",
      joined_at: "2026-08-05T00:00:00Z",
      revoked_at: null,
    }, {
      user_id: "user-2",
      role_code: "owner",
      status: "active",
      joined_at: "2026-08-05T00:00:00Z",
      revoked_at: null,
    }];
    render(<HouseholdMembers />);

    await waitFor(() => {
      expect(screen.getByTestId("household-leave")).toBeTruthy();
      expect(screen.queryByText("Create secure invite")).toBeNull();
      expect(screen.queryByTestId("household-transfer-user-2")).toBeNull();
      expect(screen.queryByTestId("household-revoke-user-2")).toBeNull();
    });
  });
});
