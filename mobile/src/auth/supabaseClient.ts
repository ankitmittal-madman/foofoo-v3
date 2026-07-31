/**
 * Shared Supabase client for the whole app — the single source of the user's auth session
 * (used by SessionContext, sign-in.tsx, create-id.tsx) and the JWT that api/client.ts attaches
 * to every backend call. Session storage is AsyncStorage-backed with auto-refresh, so a signed-in
 * user stays signed in across app restarts. Reads its project URL/anon key from
 * EXPO_PUBLIC_SUPABASE_URL / EXPO_PUBLIC_SUPABASE_ANON_KEY (see .env.example).
 */
import "react-native-url-polyfill/auto";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { createClient } from "@supabase/supabase-js";
import { logger } from "../lib/logger";

const supabaseUrl = process.env.EXPO_PUBLIC_SUPABASE_URL ?? "";
const supabaseAnonKey = process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY ?? "";

if (!supabaseUrl || !supabaseAnonKey) {
  // Fails loudly at startup rather than silently hitting an empty-string URL — Phase 1 has no
  // live project ref to default to (see .env.example).
  logger.warn(
    "EXPO_PUBLIC_SUPABASE_URL / EXPO_PUBLIC_SUPABASE_ANON_KEY are not set — copy .env.example to .env and fill in a real Supabase project.",
  );
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    storage: AsyncStorage,
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: false,
  },
});
