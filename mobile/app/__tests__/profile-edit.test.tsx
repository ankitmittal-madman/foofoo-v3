import { fireEvent, render, screen, waitFor } from "@testing-library/react-native";

import ProfileEdit from "../profile-edit";
import { postHousehold } from "@/api/household";

jest.mock("expo-router", () => ({ router: { back: jest.fn() } }));
const mockRemoveQueries = jest.fn();
const mockInvalidateQueries = jest.fn();
const mockProfileResponse = {
  household: { q5_diet: "veg", q9_allergies: ["dairy"] },
};
jest.mock("@tanstack/react-query", () => ({
  useQuery: jest.fn(() => ({ data: mockProfileResponse, isLoading: false, isError: false })),
  useQueryClient: jest.fn(() => ({
    removeQueries: mockRemoveQueries,
    invalidateQueries: mockInvalidateQueries,
  })),
  useMutation: jest.fn((options) => ({
    mutate: jest.fn(async () => {
      const result = await options.mutationFn();
      options.onSuccess?.(result);
    }),
    isPending: false,
    isError: false,
  })),
}));
jest.mock("@/api/plan", () => ({ fetchProfile: jest.fn() }));
jest.mock("@/api/household", () => ({ postHousehold: jest.fn() }));
jest.mock("@/api/errorMessages", () => ({ describeApiError: () => "Request failed" }));

const mockedPostHousehold = postHousehold as jest.MockedFunction<typeof postHousehold>;

describe("ProfileEdit", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("pre-fills preferences, saves edits, and clears safety-sensitive plan caches", async () => {
    mockedPostHousehold.mockResolvedValue({} as Awaited<ReturnType<typeof postHousehold>>);
    const view = render(<ProfileEdit />);

    expect(screen.getByText("Edit preferences")).toBeTruthy();
    expect(screen.getByText("Vegetarian")).toBeTruthy();
    expect(screen.getByText("Dairy")).toBeTruthy();
    fireEvent.press(screen.getByTestId("profile-edit-diet-vegan"));
    fireEvent.press(screen.getByTestId("profile-edit-save"));

    expect(mockedPostHousehold).toHaveBeenCalledTimes(1);
    expect(mockedPostHousehold.mock.calls[0][0]).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ question_key: "diet_type", answer_value: "vegan" }),
      ]),
    );
    await waitFor(() => {
      expect(mockRemoveQueries).toHaveBeenCalledWith({ queryKey: ["daily-plan"] });
      expect(mockRemoveQueries).toHaveBeenCalledWith({ queryKey: ["meal-episodes"] });
      expect(mockRemoveQueries).toHaveBeenCalledWith({ queryKey: ["saved-week"] });
      expect(mockInvalidateQueries).toHaveBeenCalledWith({ queryKey: ["profile"] });
    });

    view.unmount();
  });
});
