-- Rollback: 028_weight_ladder_config_numeric_weights_rollback.sql
-- Reverses: 028_weight_ladder_config_numeric_weights.sql
-- WARNING: this deliberately restores the ORIGINAL float4 exact-equality defect (AGR-006).
--   If run after seed data (including the 'emerging' tier's values) has been loaded, this
--   rollback's own re-added CHECK will immediately reject that already-loaded row — expected
--   and correct: reverting a correctness fix while relying data exists should fail loudly, not
--   silently corrupt or round the stored values. On the currently-unseeded table this reverses
--   cleanly.

ALTER TABLE re_engine.re_weight_ladder_config
  DROP CONSTRAINT re_weight_ladder_config_check;

ALTER TABLE re_engine.re_weight_ladder_config
  ALTER COLUMN w_cohort  TYPE real USING w_cohort::real,
  ALTER COLUMN w_content TYPE real USING w_content::real,
  ALTER COLUMN w_history TYPE real USING w_history::real,
  ALTER COLUMN w_context TYPE real USING w_context::real,
  ALTER COLUMN w_explore TYPE real USING w_explore::real;

ALTER TABLE re_engine.re_weight_ladder_config
  ADD CONSTRAINT re_weight_ladder_config_check
  CHECK (w_cohort + w_content + w_history + w_context + w_explore = 1.0::double precision);
