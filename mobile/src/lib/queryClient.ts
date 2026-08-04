import AsyncStorage from "@react-native-async-storage/async-storage";
import { QueryClient, dehydrate, hydrate } from "@tanstack/react-query";

const CACHE_KEY = "foofoo.queryCache.v1";
const CACHE_MAX_AGE_MS = 24 * 60 * 60 * 1000;
let persistTimer: ReturnType<typeof setTimeout> | null = null;

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
      staleTime: 5 * 60 * 1000,
    },
    mutations: { retry: 0 },
  },
});

/** Restores successful query results so the last plan remains available after an offline restart. */
export async function restoreQueryCache(): Promise<void> {
  const raw = await AsyncStorage.getItem(CACHE_KEY);
  if (!raw) return;
  try {
    const persisted = JSON.parse(raw) as { savedAt: number; state: unknown };
    if (Date.now() - persisted.savedAt > CACHE_MAX_AGE_MS) {
      await AsyncStorage.removeItem(CACHE_KEY);
      return;
    }
    hydrate(queryClient, persisted.state);
  } catch {
    await AsyncStorage.removeItem(CACHE_KEY);
  }
}

/** Starts a throttled AsyncStorage mirror of successful query state. */
export function startQueryCachePersistence(): () => void {
  return queryClient.getQueryCache().subscribe(() => {
    if (persistTimer) clearTimeout(persistTimer);
    persistTimer = setTimeout(() => {
      const state = dehydrate(queryClient, {
        shouldDehydrateQuery: (query) => query.state.status === "success",
      });
      AsyncStorage.setItem(CACHE_KEY, JSON.stringify({ savedAt: Date.now(), state })).catch(() => {});
    }, 250);
  });
}
