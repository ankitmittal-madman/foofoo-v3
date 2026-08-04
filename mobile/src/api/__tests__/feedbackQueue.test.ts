import AsyncStorage from "@react-native-async-storage/async-storage";

import { ApiError, CLIENT_ERROR_CODES, apiPost } from "../client";
import { flushFeedbackQueue, postFeedback } from "../feedback";

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
    CLIENT_ERROR_CODES: { NETWORK_ERROR: "NETWORK_ERROR", TIMEOUT: "TIMEOUT" },
    apiPost: jest.fn(),
  };
});

const mockedPost = apiPost as jest.MockedFunction<typeof apiPost>;

describe("durable feedback queue", () => {
  beforeEach(async () => {
    mockedPost.mockReset();
    await AsyncStorage.clear();
  });

  it("queues a transport failure and flushes it later", async () => {
    mockedPost.mockRejectedValueOnce(
      new ApiError("offline", 0, undefined, CLIENT_ERROR_CODES.NETWORK_ERROR),
    );
    const body = { request_id: "request-1", event_type: "like" as const, dish_name: "Poha" };
    const queued = await postFeedback(body);
    expect(queued.queued).toBe(true);

    mockedPost.mockResolvedValueOnce({});
    await expect(flushFeedbackQueue()).resolves.toBe(1);
    expect(mockedPost).toHaveBeenLastCalledWith("/feedback", body);
  });

  it("does not hide a permanent API rejection", async () => {
    mockedPost.mockRejectedValueOnce(new ApiError("invalid", 422));
    await expect(postFeedback({ request_id: "request-1", event_type: "like" })).rejects.toThrow("invalid");
  });
});
