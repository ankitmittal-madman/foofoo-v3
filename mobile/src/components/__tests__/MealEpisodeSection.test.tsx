import { fireEvent, render, screen, waitFor } from "@testing-library/react-native";

import { MealEpisodeSection } from "../MealEpisodeSection";

const mockMutate = jest.fn();
const mockRefetch = jest.fn();
const mockResponse = {
  kind: "meal_episode_slate" as const,
  slot: "dinner",
  model_version: "episode-practicality-rule-v1",
  warnings: [],
  request_id: "request-episode-1",
  episodes: [{
    episode_hash: "hash-1",
    rank: 1,
    plate_form: "pair" as const,
    display_name: "Tori chana dal + phulka",
    components: [
      { dish_id: "dish-1", dish_name: "Tori chana dal", component_role: "hero", is_required: true },
      { dish_id: null, dish_name: "Phulka", component_role: "staple", is_required: true },
    ],
    intent: "routine",
    intent_posterior: { routine: 0.7 },
    practicality: {
      active_minutes: 28,
      critical_path_minutes: 40,
      vessel_count: 2,
      burner_peak: 1,
      ingredient_count: 9,
      complex_method_count: 0,
      pantry_coverage: null,
      feature_version: "episode-practicality-rule-v1",
      estimation_confidence: 0.45,
    },
    cadence_tier: "daily_staple",
    richness_score: 0.2,
    predictions: {
      p_choose: 0.6,
      p_execute: 0.8,
      p_regret: 0.1,
      p_success: 0.432,
      model_version: "episode-practicality-rule-v1",
      calibration_status: "rule_baseline_untrained" as const,
    },
    reasons: ["daily staple for this household context", "about 28 active minutes"],
    source_plate_score: 1.2,
  }],
};

jest.mock("expo-router", () => ({ router: { push: jest.fn() } }));
jest.mock("@tanstack/react-query", () => ({
  useQuery: jest.fn(() => ({
    data: mockResponse,
    isLoading: false,
    isError: false,
    refetch: mockRefetch,
  })),
  useMutation: jest.fn(() => ({ mutate: mockMutate, isPending: false })),
}));
jest.mock("@/api/plan", () => ({ fetchMealEpisodes: jest.fn(), setPlanSlotLock: jest.fn() }));
jest.mock("@/api/feedback", () => ({ postFeedback: jest.fn() }));
jest.mock("@/api/errorMessages", () => ({ describeApiError: () => "Request failed" }));

describe("MealEpisodeSection", () => {
  beforeEach(() => mockMutate.mockClear());

  it("renders a complete meal with practicality and reasoned rejection", async () => {
    render(
      <MealEpisodeSection
        slot="dinner"
        weekday="Monday"
        slotDate="2026-08-05"
        classCode="LD_DAL_SABZI"
        initiallyLocked={false}
        refreshNonce={0}
      />,
    );

    expect(screen.getByText("Tori chana dal + phulka")).toBeTruthy();
    expect(screen.getByText("Tori chana dal + Phulka")).toBeTruthy();
    expect(screen.getByText("28 active min · 1 burner · 2 vessels")).toBeTruthy();
    expect(screen.getByText("Safe starting point")).toBeTruthy();
    fireEvent.press(screen.getByText("Not today"));
    expect(screen.getByText("Too much work")).toBeTruthy();
    fireEvent.press(screen.getByText("Too much work"));
    await waitFor(() => expect(mockMutate).toHaveBeenCalled());
  });
});
