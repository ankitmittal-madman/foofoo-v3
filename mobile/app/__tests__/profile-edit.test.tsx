import { fireEvent, render, screen } from "@testing-library/react-native";

import ProfileEdit from "../profile-edit";
import { postHousehold } from "@/api/household";

jest.mock("expo-router", () => ({ router: { back: jest.fn() } }));
const mockProfileResponse = {
  household: { q5_diet: "veg", q9_allergies: ["dairy"] },
};
jest.mock("@tanstack/react-query", () => ({
  useQuery: jest.fn(() => ({ data: mockProfileResponse, isLoading: false, isError: false })),
  useMutation: jest.fn((options) => ({
    mutate: jest.fn(() => options.mutationFn()),
    isPending: false,
    isError: false,
  })),
}));
jest.mock("@/api/plan", () => ({ fetchProfile: jest.fn() }));
jest.mock("@/api/household", () => ({ postHousehold: jest.fn() }));
jest.mock("@/api/errorMessages", () => ({ describeApiError: () => "Request failed" }));

const mockedPostHousehold = postHousehold as jest.MockedFunction<typeof postHousehold>;

describe("ProfileEdit", () => {
  it("pre-fills preferences and saves the edited values", () => {
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

    view.unmount();
  });
});
