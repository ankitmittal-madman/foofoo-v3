import AsyncStorage from "@react-native-async-storage/async-storage";
import { QueryClient, dehydrate, hydrate } from "@tanstack/react-query";
import { supabase } from "@/auth/supabaseClient";

const CACHE_KEY_PREFIX = "foofoo.queryCache.v3";
const CACHE_MAX_AGE_MS = 24 * 60 * 60 * 1000;
const PERSISTED_PLAN_QUERY_KEYS = new Set(["daily-plan", "meal-episodes", "saved-week"]);
let persistTimer: ReturnType<typeof setTimeout> | null = null;

/** Returns true only for meal-plan queries that are safe and useful during an offline restart. */
export function shouldPersistQueryKey(queryKey: readonly unknown[]): boolean {
  return typeof queryKey[0] === "string" && PERSISTED_PLAN_QUERY_KEYS.has(queryKey[0]);
}

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
  const { data } = await supabase.auth.getSession();
  const userId = data.session?.user.id;
  if (!userId) return;
  const cacheKey = `${CACHE_KEY_PREFIX}.${userId}`;
  const raw = await AsyncStorage.getItem(cacheKey);
  if (!raw) return;
  try {
    const persisted = JSON.parse(raw) as { savedAt: number; state: unknown };
    if (Date.now() - persisted.savedAt > CACHE_MAX_AGE_MS) {
      await AsyncStorage.removeItem(cacheKey);
      return;
    }
    hydrate(queryClient, persisted.state);
  } catch {
    await AsyncStorage.removeItem(cacheKey);
  }
}

/** Starts a throttled AsyncStorage mirror of successful meal-plan query state. */
export function startQueryCachePersistence(): () => void {
  return queryClient.getQueryCache().subscribe(() => {
    if (persistTimer) clearTimeout(persistTimer);
    persistTimer = setTimeout(async () => {
      const { data } = await supabase.auth.getSession();
      const userId = data.session?.user.id;
      if (!userId) return;
      const state = dehydrate(queryClient, {
        shouldDehydrateQuery: (query) =>
          query.state.status === "success" && shouldPersistQueryKey(query.queryKey),
      });
      AsyncStorage.setItem(
        `${CACHE_KEY_PREFIX}.${userId}`,
        JSON.stringify({ savedAt: Date.now(), state }),
      ).catch(() => {});
    }, 250);
  });
}
