-- Rollback: 013_config_tables_rollback.sql
-- Reverses: 013_config_tables.sql
-- RECONSTRUCTED FROM EVIDENCE (WP-5C Rollback Recovery, 2026-07-13).
--   Source of truth: the forward migration file 013_config_tables.sql (the authoritative record of exactly what
--   this migration created). No original rollback existed for 001-020 (never authored — see
--   REPO-WP-02 discovery); the 021-026 rollbacks were lost in the apverse-labs repository loss
--   and are reconstructed from the WP-5B-recovered forward migrations.
--   APPLY ORDER: rollbacks run in REVERSE (028 -> 001). Each reverses ONLY what its own migration
--   created and assumes later migrations are already rolled back. Plain DROP / RESTRICT are used
--   deliberately so out-of-order or on-populated-data application FAILS LOUDLY rather than
--   cascading silently — matching the 027/028 rollback precedent.

DROP TABLE re_engine.re_engine_versions;
DROP TABLE re_engine.re_festival_calendar;
DROP TABLE re_engine.re_context_multipliers;
DROP TABLE re_engine.re_class_affinity_config;
DROP TABLE re_engine.re_variety_rules;
DROP TABLE re_engine.re_city_overlay_config;
DROP TABLE re_engine.re_confidence_config;
DROP TABLE re_engine.re_event_weights;
DROP TABLE re_engine.re_scoring_config;
DROP TABLE re_engine.re_weight_ladder_config;
