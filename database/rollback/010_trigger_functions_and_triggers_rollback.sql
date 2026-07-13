-- Rollback: 010_trigger_functions_and_triggers_rollback.sql
-- Reverses: 010_trigger_functions_and_triggers.sql
-- RECONSTRUCTED FROM EVIDENCE (WP-5C Rollback Recovery, 2026-07-13).
--   Source of truth: the forward migration file 010_trigger_functions_and_triggers.sql (the authoritative record of exactly what
--   this migration created). No original rollback existed for 001-020 (never authored — see
--   REPO-WP-02 discovery); the 021-026 rollbacks were lost in the apverse-labs repository loss
--   and are reconstructed from the WP-5B-recovered forward migrations.
--   APPLY ORDER: rollbacks run in REVERSE (028 -> 001). Each reverses ONLY what its own migration
--   created and assumes later migrations are already rolled back. Plain DROP / RESTRICT are used
--   deliberately so out-of-order or on-populated-data application FAILS LOUDLY rather than
--   cascading silently — matching the 027/028 rollback precedent.

DROP TRIGGER trg_update_genome_vector ON public.dish_tags;
DROP TRIGGER trg_sync_allergen_union ON public.household_members;
DROP TRIGGER trg_propagate_ingredient_change ON public.ingredients;
DROP TRIGGER trg_derive_dish_attributes ON public.dish_ingredients;
DROP FUNCTION public.fn_update_dish_genome_vector();
DROP FUNCTION public.fn_sync_profile_allergen_union();
DROP FUNCTION public.fn_propagate_ingredient_change();
DROP FUNCTION public.fn_derive_dish_attributes();
DROP TABLE public.derivation_conflicts;
