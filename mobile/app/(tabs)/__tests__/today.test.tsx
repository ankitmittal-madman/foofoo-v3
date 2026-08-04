import { fireEvent, render, screen } from "@testing-library/react-native";

import { SlotSection } from "../today";

const mockRefetch = jest.fn();
const mockDishResponse = {
  slot: "breakfast",
  weekday: "Monday",
  class_code: "BF_CLASS",
  count: 1,
  request_id: "request-1",
  options: [
    {
      name: "Poha",
      cuisine: "Maharashtrian",
      diet: "veg",
      meal_class_code: "BF_CLASS",
      meal_class_name: "Quick breakfast",
      spice_level: 1,
      heaviness: 1,
      total_mins: 20,
      score: 1.25,
      image_url: null,
      explanation: {
        base_total: 1,
        q15_contribution: 0.1,
        weather_contribution: 0,
        top_contributors: [{ module: "m_palette", value: 1, weight: 0.4, weighted: 0.4 }],
      },
    },
  ],
};

jest.mock("expo-router", () => ({ router: { push: jest.fn() } }));
jest.mock("@tanstack/react-query", () => ({
  useQuery: jest.fn(() => ({
    data: mockDishResponse,
    isLoading: false,
    isError: false,
    refetch: mockRefetch,
  })),
  useMutation: jest.fn(() => ({ mutate: jest.fn(), isPending: false, isError: false })),
}));
jest.mock("@/api/errorMessages", () => ({ describeApiError: () => "Request failed" }));
jest.mock("@/api/feedback", () => ({ postFeedback: jest.fn() }));
jest.mock("@/lib/weeklyPlanStore", () => ({ loadWeeklyPlan: jest.fn().mockResolvedValue({}) }));
jest.mock("@/api/plan", () => ({
  fetchClassDishes: jest.fn(),
  fetchSavedWeek: jest.fn().mockResolvedValue({}),
  fetchSlotOptions: jest.fn(),
  savedWeekLocks: jest.fn(() => ({
    Sunday: { breakfast: true }, Monday: { breakfast: true }, Tuesday: { breakfast: true },
    Wednesday: { breakfast: true }, Thursday: { breakfast: true }, Friday: { breakfast: true },
    Saturday: { breakfast: true },
  })),
  savedWeekSelections: jest.fn(() => ({
    Sunday: { breakfast: "BF_CLASS", lunch: "LD_CLASS", dinner: "DN_CLASS" },
    Monday: { breakfast: "BF_CLASS", lunch: "LD_CLASS", dinner: "DN_CLASS" },
    Tuesday: { breakfast: "BF_CLASS", lunch: "LD_CLASS", dinner: "DN_CLASS" },
    Wednesday: { breakfast: "BF_CLASS", lunch: "LD_CLASS", dinner: "DN_CLASS" },
    Thursday: { breakfast: "BF_CLASS", lunch: "LD_CLASS", dinner: "DN_CLASS" },
    Friday: { breakfast: "BF_CLASS", lunch: "LD_CLASS", dinner: "DN_CLASS" },
    Saturday: { breakfast: "BF_CLASS", lunch: "LD_CLASS", dinner: "DN_CLASS" },
  })),
  setPlanSlotLock: jest.fn().mockResolvedValue({}),
}));

describe("Today", () => {
  it("renders persisted lock state and rich scoring reasons", () => {
    const view = render(
      <SlotSection
        slot="breakfast"
        weekday="Monday"
        classCode="BF_CLASS"
        initiallyLocked
        refreshNonce={0}
      />,
    );

    expect(screen.getByText("Poha")).toBeTruthy();
    expect(screen.getByText("Locked")).toBeTruthy();
    fireEvent.press(screen.getByText("Why this?"));
    expect(screen.getByText("palette: +0.40")).toBeTruthy();
    expect(mockRefetch).not.toHaveBeenCalled();

    view.unmount();
  });
});
