-- Migration: 029_pf1_security_hardening.sql
-- ============================================================================
-- CANONICAL RECOVERY OF PRODUCTION MIGRATION — WP-5D (Founder Option B), 2026-07-13
-- ============================================================================
-- Production ledger identity: name "pf1_security_hardening", version 20260710101630,
-- applied to project slsqtlygeekdppuyiiff on 2026-07-10. Recovered VERBATIM from
-- supabase_migrations.schema_migrations.statements (HIGH confidence — exact applied SQL,
-- not reconstructed). Ordinal prefix 029_ follows the repository's own convention (as 027/028
-- did for their bare ledger names); the canonical repository has no migration numbered 029 yet.
--
-- Engineering intent (RPC-exposure + AGR-001 completion security hardening):
--   Finding 1 — lock down the one RPC-callable helper (fn_assign_tag_vector_positions) to
--     service_role and pin its search_path.
--   Finding 2 — complete migration 008's AGR-001 privilege lockdown: migration 008 revoked only
--     UPDATE on the derived dish columns; this adds INSERT and REFERENCES on the same columns,
--     from authenticated and anon.
--   Finding 3 — remove PUBLIC/anon/authenticated EXECUTE on the trigger functions (they are fired
--     by triggers as SECURITY DEFINER; no role needs direct EXECUTE) and grant EXECUTE only to
--     service_role.
--   Finding 4 — pin search_path = public, pg_catalog on all trigger functions (fn_assign already
--     carried this from migration 023; re-stating it is idempotent).
--
-- ---------------------------------------------------------------------------
-- OPTION B QUARANTINE (Founder decision, 2026-07-13 — final):
--   Production pf1 also contained the statement:
--       REVOKE EXECUTE ON FUNCTION public.rls_auto_enable() FROM PUBLIC, anon, authenticated;
--   public.rls_auto_enable() and its event trigger `ensure_rls` are a PRODUCTION OPERATIONAL
--   OVERLAY (postgres-owned, created out-of-band, NO migration provenance, absent from the
--   canonical repository, and behaviourally in conflict with migration 019's deliberate RLS
--   design). Per Founder Option B they SHALL remain operational and SHALL NOT become canonical
--   repository objects. That one statement targets an object that does not exist in a canonical
--   rebuild, so it is QUARANTINED here (retained, not deleted) to preserve deterministic clean
--   rebuild. Evidence & rationale: docs/project-history WP-5D completion + WP-5D Evidence Register.
--   Operational dependency: on production (and only there), that REVOKE is applied by the overlay
--   owner as part of the same operational hardening; it is intentionally out of canonical scope.
--       -- REVOKE EXECUTE ON FUNCTION public.rls_auto_enable() FROM PUBLIC, anon, authenticated;
-- ---------------------------------------------------------------------------
-- Note (parity, not effectiveness): Findings 2/3 are reproduced exactly as applied in production
--   for engineering parity. WP-5F2 established that the primary data protection on public.dishes
--   is RLS default-deny (an UPDATE by `authenticated` matches 0 rows); the column-level privilege
--   REVOKEs here are defense-in-depth. See the WP-5D completion document.

-- Finding 1
REVOKE EXECUTE ON FUNCTION public.fn_assign_tag_vector_positions() FROM PUBLIC, anon, authenticated;
GRANT  EXECUTE ON FUNCTION public.fn_assign_tag_vector_positions() TO service_role;
ALTER FUNCTION public.fn_assign_tag_vector_positions() SET search_path = public, pg_catalog;

-- Finding 2 — AGR-001 completion (INSERT/REFERENCES alongside migration 008's UPDATE revoke)
REVOKE INSERT, UPDATE, REFERENCES (
  diet_type, is_jain, allergen_flags, genome_vector,
  popularity_score, acceptance_rate_7d, acceptance_rate_30d
) ON public.dishes FROM authenticated, anon;

-- Finding 3 — trigger-function EXECUTE lockdown
REVOKE EXECUTE ON FUNCTION public.fn_derive_dish_attributes() FROM PUBLIC, anon, authenticated;
GRANT  EXECUTE ON FUNCTION public.fn_derive_dish_attributes() TO service_role;

REVOKE EXECUTE ON FUNCTION public.fn_propagate_ingredient_change() FROM PUBLIC, anon, authenticated;
GRANT  EXECUTE ON FUNCTION public.fn_propagate_ingredient_change() TO service_role;

REVOKE EXECUTE ON FUNCTION public.fn_update_dish_genome_vector() FROM PUBLIC, anon, authenticated;
GRANT  EXECUTE ON FUNCTION public.fn_update_dish_genome_vector() TO service_role;

-- (QUARANTINED — Option B — production operational overlay object, not canonical:)
-- REVOKE EXECUTE ON FUNCTION public.rls_auto_enable() FROM PUBLIC, anon, authenticated;

-- Finding 4 — pin search_path on the trigger functions
ALTER FUNCTION public.fn_derive_dish_attributes()      SET search_path = public, pg_catalog;
ALTER FUNCTION public.fn_propagate_ingredient_change() SET search_path = public, pg_catalog;
ALTER FUNCTION public.fn_update_dish_genome_vector()   SET search_path = public, pg_catalog;
ALTER FUNCTION public.fn_sync_profile_allergen_union() SET search_path = public, pg_catalog;
