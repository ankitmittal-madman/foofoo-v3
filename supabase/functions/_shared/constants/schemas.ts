/**
 * Canonical schema + role name constants (WP-8B foundation).
 *
 * These mirror the frozen database architecture (DOC-P3-04 §03.26). They are names only — no
 * business logic. Kept centralized so repositories never hardcode schema strings.
 */

/** Public schema — client-facing content, RLS-protected (DOC-P3-04 §03.1–03.18). */
export const PUBLIC_SCHEMA = "public" as const;

// RE_ENGINE_SCHEMA ("re_engine") retired WP-20: the legacy TypeScript-RE's schema. Its only two
// live-code consumers (hard-delete.ts, user-export/store.ts) touched per-user RE state tables
// (never_list, not_today_suppression, user_re_state, user_taste_vectors, re_dish_bandit_state) and
// the re_states reference table — all re-homed into `public` by migration 046 BEFORE the schema
// itself is dropped by migration 047. Every re_engine row (including the ~30 tables no live code
// ever referenced) is preserved at database/archive/re_engine_backup_20260803/.

/** Supabase platform roles (DOC-P3-07 §10). `service_role` bypasses RLS — see auth/authorize. */
export const ROLES = {
  ANON: "anon",
  AUTHENTICATED: "authenticated",
  SERVICE_ROLE: "service_role",
} as const;

export type Role = typeof ROLES[keyof typeof ROLES];
