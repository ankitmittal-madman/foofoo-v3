/**
 * Canonical schema + role name constants (WP-8B foundation).
 *
 * These mirror the frozen database architecture (DOC-P3-04 §03.26). They are names only — no
 * business logic. Kept centralized so repositories never hardcode schema strings.
 */

/** Public schema — client-facing content, RLS-protected (DOC-P3-04 §03.1–03.18). */
export const PUBLIC_SCHEMA = "public" as const;

/** RE schema — service-role only; REVOKED from anon/authenticated (DOC-P3-04 §03.26). */
export const RE_ENGINE_SCHEMA = "re_engine" as const;

/** Supabase platform roles (DOC-P3-07 §10). `service_role` bypasses RLS — see auth/authorize. */
export const ROLES = {
  ANON: "anon",
  AUTHENTICATED: "authenticated",
  SERVICE_ROLE: "service_role",
} as const;

export type Role = typeof ROLES[keyof typeof ROLES];
