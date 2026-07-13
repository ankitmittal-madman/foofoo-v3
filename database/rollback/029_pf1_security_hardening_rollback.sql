-- Rollback: 029_pf1_security_hardening_rollback.sql
-- Reverses: 029_pf1_security_hardening.sql
-- RECONSTRUCTED FROM EVIDENCE (WP-5D, 2026-07-13). Source of truth: the forward migration 029
--   (itself the verbatim canonical recovery of production pf1_security_hardening) plus the prior
--   grant/search_path state established by migrations 008 (dishes column privileges), 010 (the
--   four trigger functions, created with default PUBLIC EXECUTE and no explicit search_path) and
--   023 (fn_assign_tag_vector_positions, created WITH search_path = public, pg_catalog).
--   APPLY ORDER: rollbacks run in REVERSE (029 -> 001); this one runs FIRST.
--
-- WARNING (parallel to the 023/027/028 rollback precedent): this REVERSES a security-hardening
--   migration and therefore RE-OPENS the surface it closed (restores PUBLIC EXECUTE on the
--   trigger functions and the authenticated/anon column privileges on public.dishes). It is
--   intended ONLY for a clean-environment teardown, never for production. The quarantined
--   rls_auto_enable() statement in 029 did nothing in a canonical build, so there is nothing to
--   reverse for it here.

-- Reverse Finding 3 (+ the service_role grants from Findings 1/3): restore default PUBLIC EXECUTE
GRANT  EXECUTE ON FUNCTION public.fn_assign_tag_vector_positions() TO PUBLIC;
REVOKE EXECUTE ON FUNCTION public.fn_assign_tag_vector_positions() FROM service_role;
GRANT  EXECUTE ON FUNCTION public.fn_derive_dish_attributes() TO PUBLIC;
REVOKE EXECUTE ON FUNCTION public.fn_derive_dish_attributes() FROM service_role;
GRANT  EXECUTE ON FUNCTION public.fn_propagate_ingredient_change() TO PUBLIC;
REVOKE EXECUTE ON FUNCTION public.fn_propagate_ingredient_change() FROM service_role;
GRANT  EXECUTE ON FUNCTION public.fn_update_dish_genome_vector() TO PUBLIC;
REVOKE EXECUTE ON FUNCTION public.fn_update_dish_genome_vector() FROM service_role;

-- Reverse Finding 2: restore the authenticated/anon column privileges 029 revoked on dishes
GRANT INSERT, UPDATE, REFERENCES (
  diet_type, is_jain, allergen_flags, genome_vector,
  popularity_score, acceptance_rate_7d, acceptance_rate_30d
) ON public.dishes TO authenticated, anon;

-- Reverse Finding 4: reset search_path on the four migration-010 trigger functions (they had no
--   explicit search_path before 029). fn_assign_tag_vector_positions KEEPS search_path =
--   public, pg_catalog, because that is its migration-023 state (029's pin was a no-op for it).
ALTER FUNCTION public.fn_derive_dish_attributes()      RESET search_path;
ALTER FUNCTION public.fn_propagate_ingredient_change() RESET search_path;
ALTER FUNCTION public.fn_update_dish_genome_vector()   RESET search_path;
ALTER FUNCTION public.fn_sync_profile_allergen_union() RESET search_path;
