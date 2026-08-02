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
    // TEMPORARY (testing, 2026-08-02): caching fully disabled so every screen re-fetches from the
    // API on each mount/focus — no stale plate is ever shown while validating the RE fixes. Revert
    // to `{ retry: 1 }` before launch (staleTime>0 + normal gc is the right production posture).
    queries: {
      retry: 1,
      staleTime: 0, // data is immediately stale -> always eligible to refetch
      gcTime: 0, // don't keep inactive query data in cache at all
      refetchOnMount: "always", // remount (route change / reload) always refetches
      refetchOnWindowFocus: true, // tab focus refetches
      refetchOnReconnect: true,
    },
    mutations: { retry: 0 },
  },
});
