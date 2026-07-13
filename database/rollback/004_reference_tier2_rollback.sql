-- Rollback: 004_reference_tier2_rollback.sql
-- Reverses: 004_reference_tier2.sql
-- RECONSTRUCTED FROM EVIDENCE (WP-5C Rollback Recovery, 2026-07-13).
--   Source of truth: the forward migration file 004_reference_tier2.sql (the authoritative record of exactly what
--   this migration created). No original rollback existed for 001-020 (never authored — see
--   REPO-WP-02 discovery); the 021-026 rollbacks were lost in the apverse-labs repository loss
--   and are reconstructed from the WP-5B-recovered forward migrations.
--   APPLY ORDER: rollbacks run in REVERSE (028 -> 001). Each reverses ONLY what its own migration
--   created and assumes later migrations are already rolled back. Plain DROP / RESTRICT are used
--   deliberately so out-of-order or on-populated-data application FAILS LOUDLY rather than
--   cascading silently — matching the 027/028 rollback precedent.

DROP TABLE re_engine.re_city_migration_overlays;
DROP TABLE re_engine.re_nonveg_logic;
DROP TABLE re_engine.re_household_addon_plans;
DROP TABLE re_engine.re_weekly_class_plans;
DROP TABLE re_engine.re_cohorts;
DROP TABLE re_engine.re_addon_dish_options;
DROP TABLE re_engine.re_addon_classes;
DROP TABLE re_engine.re_class_dish_options;
DROP TABLE re_engine.re_meal_class_overlap_rules;
