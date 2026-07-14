/**
 * Supabase client factories (WP-8B foundation).
 *
 * Two clients, per DOC-P3-06 §01 / DOC-P3-07 §10:
 *   - service-role client: full DB access, BYPASSES RLS. Used by Edge Functions (Surface B).
 *     Because RLS provides ZERO protection here, every authorization check must be coded
 *     explicitly (see auth/authorize.ts). NEVER expose the service-role key to a client.
 *   - authenticated client: scoped to a caller's JWT; RLS applies. Used for user-context reads
 *     where honoring RLS is desired.
 *
 * This module only CONSTRUCTS clients. It contains no queries and no business logic — data
 * access lives in repositories (WP-8C onward).
 */
import { createClient, type SupabaseClient } from "@supabase/supabase-js";
import type { AppConfig } from "../config/config.ts";

/** Service-role client (server-side only). RLS bypassed — authorize explicitly in code. */
export function createServiceRoleClient(config: AppConfig): SupabaseClient {
  return createClient(config.supabaseUrl, config.supabaseServiceRoleKey, {
    auth: { autoRefreshToken: false, persistSession: false },
  });
}

/** Per-request client bound to the caller's JWT (RLS applies). */
export function createAuthenticatedClient(config: AppConfig, jwt: string): SupabaseClient {
  return createClient(config.supabaseUrl, config.supabaseAnonKey, {
    auth: { autoRefreshToken: false, persistSession: false },
    global: { headers: { Authorization: `Bearer ${jwt}` } },
  });
}

export type { SupabaseClient };
