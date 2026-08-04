jest.mock("../../auth/supabaseClient", () => ({
  supabase: { auth: { getSession: jest.fn() } },
}));

import { describeApiError } from "../errorMessages";
import { ApiError } from "../client";

describe("describeApiError", () => {
  it("maps a known error code to its distinct message", () => {
    const err = new ApiError("raw backend message", 401, "trace-1", "ERR_UNAUTHENTICATED");
    expect(describeApiError(err)).toBe("Your session has expired — please sign in again.");
  });

  it("falls back to the ApiError's own message for an unrecognized code", () => {
    const err = new ApiError("some specific detail", 500, "trace-2", "ERR_SOMETHING_NEW");
    expect(describeApiError(err)).toBe("some specific detail");
  });

  it("falls back to a generic message for a non-ApiError value", () => {
    expect(describeApiError(new Error("plain error"))).toBe("Something went wrong. Please try again.");
    expect(describeApiError("a string")).toBe("Something went wrong. Please try again.");
  });

  it("maps the two client-only transport codes", () => {
    const timeout = new ApiError("timed out", 0, undefined, "TIMEOUT");
    expect(describeApiError(timeout)).toMatch(/timed out/i);
    const network = new ApiError("network", 0, undefined, "NETWORK_ERROR");
    expect(describeApiError(network)).toMatch(/network error/i);
  });
});
