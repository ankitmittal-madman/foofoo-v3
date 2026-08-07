import { fireEvent, render, screen, waitFor } from "@testing-library/react-native";

import WeeklyPlan from "../weekly-plan";
import { postFeedback } from "@/api/feedback";
const mockedPostFeedback = postFeedback as jest.MockedFunction<typeof postFeedback>;

const weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
const slots = ["breakfast", "lunch", "dinner"] as const;
const mockWeeklyResponse = {
  kind: "weekly_class_plan",
  request_id: "weekly-request-1",
  config_version: "class-first-v1",
  catalog_version: "catalogue-v1",
  days: weekdays.map((weekday) => ({
    weekday,
    slots: Object.fromEntries(slots.map((slot) => [slot, [
      { class_code: `${slot}-class`, class_name: `${slot} class`, plan_weight: 1, dish_count: 4 },
      { class_code: `${slot}-class-2`, class_name: `${slot} class two`, plan_weight: 0.8, dish_count: 3 },
    ]])),
  })),
};

jest.mock("expo-router", () => ({ router: { back: jest.fn(), replace: jest.fn() } }));
jest.mock("@/i18n", () => ({ useI18n: () => ({ t: (key: string) => key }) }));
jest.mock("@/api/errorMessages", () => ({ describeApiError: () => "Request failed" }));
jest.mock("@/lib/weeklyPlanStore", () => ({ saveWeeklyPlan: jest.fn() }));
jest.mock("@/api/feedback", () => ({ postFeedback: jest.fn(() => Promise.resolve({ id: "event-1" })) }));
jest.mock("@/api/plan", () => ({
  fetchSavedWeek: jest.fn(),
  fetchWeeklyPlan: jest.fn(),
  savedWeekSelections: jest.fn(() => ({})),
  saveWeekPlan: jest.fn(),
  setPlanSlotLock: jest.fn(),
}));
jest.mock("@tanstack/react-query", () => ({
  useQuery: jest.fn(({ queryKey }: { queryKey: string[] }) => queryKey[0] === "weekly-plan"
    ? { data: mockWeeklyResponse, isLoading: false, isError: false, refetch: jest.fn() }
    : { data: null, isLoading: false, isError: false }),
  useMutation: jest.fn(({ mutationFn }: { mutationFn: (input: unknown) => Promise<unknown> }) => ({ mutate: (input: unknown) => { void mutationFn(input); }, mutateAsync: mutationFn, isPending: false, isError: false })),
  useQueryClient: jest.fn(() => ({ invalidateQueries: jest.fn() })),
}));

describe("WeeklyPlan", () => {
  beforeEach(() => mockedPostFeedback.mockClear());
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

  it("records an explicit meal-class replacement with date and moment context", async () => {
    render(<WeeklyPlan />); fireEvent.press(screen.getByTestId("weekly-plan-Monday-lunch-1"));
    await waitFor(() => expect(mockedPostFeedback).toHaveBeenCalledWith(expect.objectContaining({
      schema_version: "2", request_id: "weekly-request-1", event_type: "replaced",
      target: expect.objectContaining({ type: "meal_class", id: "lunch-class-2", identity_status: "resolved" }),
      replacement: expect.objectContaining({ from: expect.objectContaining({ id: "lunch-class" }), to: expect.objectContaining({ id: "lunch-class-2" }) }),
      moment: expect.objectContaining({ meal_slot: "lunch", weekday: "Monday", day_type: "weekday" }),
      evidence: { kind: "explicit", source_surface: "weekly_plan" },
    })));
  });
});
