import { render, screen } from "@testing-library/react-native";

import History from "../history";

const mockHistoryResponse = {
  kind: "recommendation_history",
  events: [
    {
      id: "event-1",
      request_id: "request-1",
      created_at: "2026-08-04T08:00:00.000Z",
      slot: "breakfast",
      outcome: "success",
      plate_count: 1,
    },
  ],
};

jest.mock("@tanstack/react-query", () => ({
  useQuery: jest.fn(() => ({ data: mockHistoryResponse, isLoading: false, isError: false })),
}));
jest.mock("@/api/plan", () => ({ fetchHistory: jest.fn() }));
jest.mock("@/api/errorMessages", () => ({ describeApiError: () => "Request failed" }));

describe("History", () => {
  it("renders a human-readable outcome and dish count", () => {
    const view = render(<History />);

    expect(screen.getByText("Your recommendation history")).toBeTruthy();
    expect(screen.getByText("Served · 1 dish")).toBeTruthy();

    view.unmount();
  });
});
