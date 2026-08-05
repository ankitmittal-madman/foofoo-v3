import { ApiError, apiPost } from "../client";
import { fetchMealEpisodes } from "../plan";

jest.mock("../client", () => {
  class MockApiError extends Error {
    status: number;
    traceId?: string;
    code?: string;
    constructor(message: string, statusCode: number, traceValue?: string, codeValue?: string) {
      super(message);
      this.status = statusCode;
      this.traceId = traceValue;
      this.code = codeValue;
    }
  }
  return {
    ApiError: MockApiError,
    apiPost: jest.fn(),
  };
});

const mockedPost = apiPost as jest.MockedFunction<typeof apiPost>;

describe("fetchMealEpisodes", () => {
  const previousFlag = process.env.EXPO_PUBLIC_ENABLE_MEAL_EPISODES;

  beforeEach(() => {
    mockedPost.mockReset();
    delete process.env.EXPO_PUBLIC_ENABLE_MEAL_EPISODES;
  });

  afterEach(() => {
    if (previousFlag === undefined) {
      delete process.env.EXPO_PUBLIC_ENABLE_MEAL_EPISODES;
    } else {
      process.env.EXPO_PUBLIC_ENABLE_MEAL_EPISODES = previousFlag;
    }
  });

  it("uses stable slot options by default", async () => {
    mockedPost.mockResolvedValueOnce({
      slot: "breakfast",
      weekday: "Wednesday",
      class_code: null,
      count: 1,
      request_id: "request-1",
      options: [{
        name: "Poha",
        cuisine: "Maharashtrian",
        diet: "veg",
        meal_class_code: "BF_POHA",
        meal_class_name: "Poha",
        spice_level: 1,
        heaviness: 1,
        total_mins: 20,
        score: 4,
        image_url: "https://example.test/poha.jpg",
      }],
    });

    const response = await fetchMealEpisodes("breakfast", { weekday: "Wednesday", count: 1 });

    expect(mockedPost).toHaveBeenCalledTimes(1);
    expect(mockedPost).toHaveBeenCalledWith("/plan", {
      surface: "meal_plan",
      slot: "breakfast",
      weekday: "Wednesday",
      count: 1,
    });
    expect(response.kind).toBe("meal_episode_slate");
    expect(response.episodes[0].display_name).toBe("Poha");
  });

  it("falls back to slot options when the opted-in meal episode surface returns a bad request", async () => {
    process.env.EXPO_PUBLIC_ENABLE_MEAL_EPISODES = "true";
    mockedPost
      .mockRejectedValueOnce(new ApiError("Bad Request", 400))
      .mockResolvedValueOnce({
        slot: "breakfast",
        weekday: "Wednesday",
        class_code: null,
        count: 1,
        request_id: "request-1",
        options: [{
          name: "Poha",
          cuisine: "Maharashtrian",
          diet: "veg",
          meal_class_code: "BF_POHA",
          meal_class_name: "Poha",
          spice_level: 1,
          heaviness: 1,
          total_mins: 20,
          score: 4,
          image_url: "https://example.test/poha.jpg",
        }],
      });

    const response = await fetchMealEpisodes("breakfast", { weekday: "Wednesday", count: 1 });

    expect(mockedPost).toHaveBeenNthCalledWith(1, "/plan", {
      surface: "meal_episodes",
      slot: "breakfast",
      weekday: "Wednesday",
      count: 1,
    });
    expect(mockedPost).toHaveBeenNthCalledWith(2, "/plan", {
      surface: "meal_plan",
      slot: "breakfast",
      weekday: "Wednesday",
      count: 1,
    });
    expect(response.kind).toBe("meal_episode_slate");
    expect(response.request_id).toBe("request-1");
    expect(response.episodes[0].display_name).toBe("Poha");
    expect(response.episodes[0].components[0].image_url).toBe("https://example.test/poha.jpg");
  });

  it("does not fall back for auth failures", async () => {
    process.env.EXPO_PUBLIC_ENABLE_MEAL_EPISODES = "true";
    mockedPost.mockRejectedValueOnce(new ApiError("expired", 401, undefined, "ERR_UNAUTHENTICATED"));

    await expect(fetchMealEpisodes("lunch")).rejects.toThrow("expired");
    expect(mockedPost).toHaveBeenCalledTimes(1);
  });
});
