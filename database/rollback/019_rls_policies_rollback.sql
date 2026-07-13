-- Rollback: 019_rls_policies_rollback.sql
-- Reverses: 019_rls_policies.sql
-- RECONSTRUCTED FROM EVIDENCE (WP-5C Rollback Recovery, 2026-07-13).
--   Source of truth: the forward migration file 019_rls_policies.sql (the authoritative record of exactly what
--   this migration created). No original rollback existed for 001-020 (never authored — see
--   REPO-WP-02 discovery); the 021-026 rollbacks were lost in the apverse-labs repository loss
--   and are reconstructed from the WP-5B-recovered forward migrations.
--   APPLY ORDER: rollbacks run in REVERSE (028 -> 001). Each reverses ONLY what its own migration
--   created and assumes later migrations are already rolled back. Plain DROP / RESTRICT are used
--   deliberately so out-of-order or on-populated-data application FAILS LOUDLY rather than
--   cascading silently — matching the 027/028 rollback precedent.
--
-- NOTE: migration 021 separately enabled RLS + a public-read policy on public.cuisines; that is
--   reversed by 021's rollback, not here. This file reverses only the 019 policy set.

DROP POLICY profiles_select_own ON public.profiles;
DROP POLICY profiles_update_own ON public.profiles;
ALTER TABLE public.profiles DISABLE ROW LEVEL SECURITY;
DROP POLICY hm_all_own ON public.household_members;
ALTER TABLE public.household_members DISABLE ROW LEVEL SECURITY;
DROP POLICY ob_sessions_own ON public.onboarding_sessions;
ALTER TABLE public.onboarding_sessions DISABLE ROW LEVEL SECURITY;
DROP POLICY consent_select_own ON public.consent_records;
ALTER TABLE public.consent_records DISABLE ROW LEVEL SECURITY;
DROP POLICY ingredients_public_read ON public.ingredients;
ALTER TABLE public.ingredients DISABLE ROW LEVEL SECURITY;
DROP POLICY dishes_public_read ON public.dishes;
ALTER TABLE public.dishes DISABLE ROW LEVEL SECURITY;
DROP POLICY di_public_read ON public.dish_ingredients;
ALTER TABLE public.dish_ingredients DISABLE ROW LEVEL SECURITY;
DROP POLICY tags_public_read ON public.tags;
ALTER TABLE public.tags DISABLE ROW LEVEL SECURITY;
DROP POLICY dish_tags_public_read ON public.dish_tags;
ALTER TABLE public.dish_tags DISABLE ROW LEVEL SECURITY;
DROP POLICY combos_public_read ON public.dish_combos;
ALTER TABLE public.dish_combos DISABLE ROW LEVEL SECURITY;
DROP POLICY combo_items_public_read ON public.dish_combo_items;
ALTER TABLE public.dish_combo_items DISABLE ROW LEVEL SECURITY;
DROP POLICY meal_classes_public_read ON public.meal_classes;
ALTER TABLE public.meal_classes DISABLE ROW LEVEL SECURITY;
DROP POLICY week_plans_select_own ON public.week_plans;
DROP POLICY week_plans_update_own ON public.week_plans;
ALTER TABLE public.week_plans DISABLE ROW LEVEL SECURITY;
DROP POLICY plan_slots_select_own ON public.plan_slots;
DROP POLICY plan_slots_update_own ON public.plan_slots;
ALTER TABLE public.plan_slots DISABLE ROW LEVEL SECURITY;
DROP POLICY addon_slots_select_own ON public.addon_slots;
ALTER TABLE public.addon_slots DISABLE ROW LEVEL SECURITY;
DROP POLICY ie_insert_own ON public.interaction_events;
DROP POLICY ie_select_own ON public.interaction_events;
ALTER TABLE public.interaction_events DISABLE ROW LEVEL SECURITY;
DROP POLICY sl_select_own ON public.suggestion_logs;
ALTER TABLE public.suggestion_logs DISABLE ROW LEVEL SECURITY;
DROP POLICY context_log_select_own ON public.context_log;
ALTER TABLE public.context_log DISABLE ROW LEVEL SECURITY;
DROP POLICY weather_cache_public_read ON public.weather_cache;
ALTER TABLE public.weather_cache DISABLE ROW LEVEL SECURITY;
