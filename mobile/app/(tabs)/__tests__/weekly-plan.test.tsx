import { render, screen } from "@testing-library/react-native";

import WeeklyPlan from "../weekly-plan";

const weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
const slots = ["breakfast", "lunch", "dinner"] as const;
const mockWeeklyResponse = {
  kind: "weekly_class_plan",
  days: weekdays.map((weekday) => ({
    weekday,
    slots: Object.fromEntries(slots.map((slot) => [slot, [{ class_code: `${slot}-class`, class_name: `${slot} class`, plan_weight: 1, dish_count: 4 }]])),
  })),
};

jest.mock("expo-router", () => ({ router: { back: jest.fn(), replace: jest.fn() } }));
jest.mock("@/i18n", () => ({ useI18n: () => ({ t: (key: string) => key }) }));
jest.mock("@/api/errorMessages", () => ({ describeApiError: () => "Request failed" }));
jest.mock("@/lib/weeklyPlanStore", () => ({ saveWeeklyPlan: jest.fn() }));
jest.mock("@/api/plan", () => ({
  fetchSavedWeek: jest.fn(),
  fetchWeeklyPlan: jest.fn(),
  savedWeekSelections: jest.fn(() => ({})),
  saveWeekPlan: jest.fn(),
}));
jest.mock("@tanstack/react-query", () => ({
  useQuery: jest.fn(({ queryKey }: { queryKey: string[] }) => queryKey[0] === "weekly-plan"
    ? { data: mockWeeklyResponse, isLoading: false, isError: false, refetch: jest.fn() }
    : { data: null, isLoading: false, isError: false }),
  useMutation: jest.fn(() => ({ mutate: jest.fn(), isPending: false, isError: false })),
  useQueryClient: jest.fn(() => ({ invalidateQueries: jest.fn() })),
}));

describe("WeeklyPlan", () => {
  it("renders server-provided classes for all 21 weekly slots", () => {
    render(<WeeklyPlan />);

    for (const weekday of weekdays) {
      for (const slot of slots) {
        expect(screen.getByTestId(`weekly-plan-${weekday}-${slot}-0`)).toBeTruthy();
      }
    }
    expect(screen.getByTestId("weekly-plan-period-weekdays")).toBeTruthy();
    expect(screen.getByTestId("weekly-plan-period-weekend")).toBeTruthy();
    expect(screen.getByTestId("weekly-plan-finalize")).toBeTruthy();
    expect(screen.queryByText("13 – 17 May 2024")).toBeNull();
  });
});
