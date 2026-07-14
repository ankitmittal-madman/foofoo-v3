-- Rollback: 100_seed_config_tables_rollback.sql
-- WP-6E teardown finding: seed 100 (config) had no paired rollback. Its post-migration-028
-- weight-ladder rows (numeric weights) violate the PRE-028 CHECK constraint during migration
-- 028's down-migration, so config seed data must be cleared before rolling back migrations.
-- This clears exactly the 10 config tables seed 100 populates (DOC-P3-04 §03.28). Idempotent.
-- Provenance: 100_seed_config_tables.sql INSERT targets.
BEGIN;
DELETE FROM re_engine.re_weight_ladder_config;
DELETE FROM re_engine.re_scoring_config;
DELETE FROM re_engine.re_event_weights;
DELETE FROM re_engine.re_confidence_config;
DELETE FROM re_engine.re_city_overlay_config;
DELETE FROM re_engine.re_variety_rules;
DELETE FROM re_engine.re_class_affinity_config;
DELETE FROM re_engine.re_context_multipliers;
DELETE FROM re_engine.re_festival_calendar;
DELETE FROM re_engine.re_engine_versions;
COMMIT;
