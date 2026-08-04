import { render, screen } from "@testing-library/react-native";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import SearchScreen from "../search";
import { searchDishes } from "@/api/plan";

jest.mock("expo-router", () => ({ router: { push: jest.fn() } }));
jest.mock("@/api/plan", () => ({ searchDishes: jest.fn() }));
jest.mock("@/api/errorMessages", () => ({ describeApiError: () => "Request failed" }));

const mockedSearch = searchDishes as jest.MockedFunction<typeof searchDishes>;

describe("SearchScreen", () => {
  it("renders the search input and meal filters", () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const view = render(<QueryClientProvider client={queryClient}><SearchScreen /></QueryClientProvider>);
    expect(screen.getByLabelText("Dish, cuisine, or meal class")).toBeTruthy();
    expect(screen.getByText("Search")).toBeTruthy();
    expect(screen.getByText("breakfast")).toBeTruthy();
    expect(screen.getByText("dinner")).toBeTruthy();
    expect(mockedSearch).not.toHaveBeenCalled();
    view.unmount();
    queryClient.clear();
  });
});
