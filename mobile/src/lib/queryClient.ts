import { QueryClient } from "@tanstack/react-query";

/**
 * Shared TanStack Query client for the whole app (wired in at the root of app/_layout.tsx via
 * QueryClientProvider). Every screen's useQuery/useMutation call (recommendations, onboarding
 * step submissions, create-id) shares this one instance and its cache. Queries retry once on
 * failure; mutations (writes like postHousehold) never auto-retry, since a household/recommendation
 * write should surface its error to the user rather than silently repeat it.
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
    },
    mutations: { retry: 0 },
  },
});
