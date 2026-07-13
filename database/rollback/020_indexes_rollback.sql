-- Rollback: 020_indexes_rollback.sql
-- Reverses: 020_indexes.sql
-- RECONSTRUCTED FROM EVIDENCE (WP-5C Rollback Recovery, 2026-07-13).
--   Source of truth: the forward migration file 020_indexes.sql (the authoritative record of exactly what
--   this migration created). No original rollback existed for 001-020 (never authored — see
--   REPO-WP-02 discovery); the 021-026 rollbacks were lost in the apverse-labs repository loss
--   and are reconstructed from the WP-5B-recovered forward migrations.
--   APPLY ORDER: rollbacks run in REVERSE (028 -> 001). Each reverses ONLY what its own migration
--   created and assumes later migrations are already rolled back. Plain DROP / RESTRICT are used
--   deliberately so out-of-order or on-populated-data application FAILS LOUDLY rather than
--   cascading silently — matching the 027/028 rollback precedent.
--
-- NOTE: only the 36 explicit indexes created by migration 020 are dropped here. Indexes that
--   PostgreSQL auto-creates for PK/UNIQUE constraints are NOT dropped (they belong to their
--   table's CREATE, reversed when that table is dropped). idx_tags_vector_position is the
--   AGR-004 redundant index and is included.

DROP INDEX public.idx_profiles_last_active;
DROP INDEX public.idx_profiles_home_state;
DROP INDEX public.idx_household_members_profile;
DROP INDEX public.idx_onboarding_sessions_profile;
DROP INDEX public.idx_consent_profile_type;
DROP INDEX public.idx_ingredients_allergen;
DROP INDEX public.idx_dishes_active;
DROP INDEX public.idx_dishes_diet_type;
DROP INDEX public.idx_dishes_is_jain;
DROP INDEX public.idx_dishes_allergen;
DROP INDEX public.idx_dishes_meal_occasion;
DROP INDEX public.idx_dishes_parent;
DROP INDEX public.idx_dish_ingredients_ingredient;
DROP INDEX public.idx_dish_tags_tag;
DROP INDEX public.idx_plan_slots_week_plan;
DROP INDEX public.idx_plan_slots_locked;
DROP INDEX public.idx_addon_slots_plan_slot;
DROP INDEX public.idx_week_plans_profile_date;
DROP INDEX public.idx_ie_profile_dish;
DROP INDEX public.idx_ie_unsynced;
DROP INDEX public.idx_sl_profile_dish_date;
DROP INDEX public.idx_sl_slate;
DROP INDEX public.idx_context_log_slate;
DROP INDEX re_engine.idx_re_meal_classes_role;
DROP INDEX re_engine.idx_re_class_dish_class;
DROP INDEX re_engine.idx_re_addon_dish_class;
DROP INDEX re_engine.idx_re_cohorts_lookup;
DROP INDEX re_engine.idx_re_weekly_plans_cohort;
DROP INDEX re_engine.idx_user_re_state_cold_start;
DROP INDEX re_engine.idx_never_list_active;
DROP INDEX re_engine.idx_never_list_reactivation;
DROP INDEX re_engine.idx_not_today_active;
DROP INDEX public.idx_tags_vector_position;
DROP INDEX public.idx_audit_log_actor;
DROP INDEX public.idx_etl_job_runs_name;
DROP INDEX public.idx_sl_gate_diet;
