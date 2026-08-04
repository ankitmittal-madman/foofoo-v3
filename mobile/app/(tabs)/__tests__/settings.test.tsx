import { fireEvent, render, screen } from "@testing-library/react-native";

import Settings from "../settings";
import { router } from "expo-router";

jest.mock("expo-router", () => ({ router: { push: jest.fn() } }));
jest.mock("@tanstack/react-query", () => ({
  useMutation: jest.fn(() => ({ mutate: jest.fn(), isPending: false, isError: false })),
}));
jest.mock("@/auth/SessionContext", () => ({
  useSession: () => ({ session: { user: { id: "user-1" } }, signOut: jest.fn() }),
}));
jest.mock("@/api/account", () => ({
  REQUIRED_CONFIRMATION_PHRASE: "DELETE MY ACCOUNT",
  requestExport: jest.fn(),
  pollExport: jest.fn(),
  deleteAccount: jest.fn(),
}));
jest.mock("@/api/errorMessages", () => ({ describeApiError: () => "Request failed" }));

describe("Settings", () => {
  it("routes to profile/history and gates destructive deletion by the exact phrase", () => {
    const view = render(<Settings />);

    fireEvent.press(screen.getByTestId("settings-profile-edit-link"));
    fireEvent.press(screen.getByTestId("settings-history-link"));
    expect(router.push).toHaveBeenNthCalledWith(1, "/profile-edit");
    expect(router.push).toHaveBeenNthCalledWith(2, "/history");

    expect(
      screen.getByTestId("settings-delete-confirm-button").props.accessibilityState.disabled,
    ).toBe(true);
    fireEvent.changeText(screen.getByTestId("settings-delete-confirm-input"), "DELETE MY ACCOUNT");
    expect(
      screen.getByTestId("settings-delete-confirm-button").props.accessibilityState.disabled,
    ).toBe(false);

    view.unmount();
  });
});
