-- Rollback: 030_re_cohorts_city_tier_rollback.sql
-- Reverses migration 030 (SER-001, GAP-002 Option A).
--
-- ORDER NOTE: this rollback restores the original 3-column UNIQUE
-- (persona_id, state_code, diet_mode). If tier-distinct cohort seed rows (bands 113+) are
-- present, that restore would fail on duplicate keys. Therefore this rollback MUST run only
-- AFTER the RE cohort seeds (113_* and dependents 114/115) have been rolled back — standard
-- reverse-order teardown. Applied against the empty/illustrative baseline it is a clean no-op-safe
-- reversal.

BEGIN;

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 're_cohorts_persona_state_diet_tier_key') THEN
    ALTER TABLE re_engine.re_cohorts DROP CONSTRAINT re_cohorts_persona_state_diet_tier_key;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 're_cohorts_persona_id_state_code_diet_mode_key') THEN
    ALTER TABLE re_engine.re_cohorts
      ADD CONSTRAINT re_cohorts_persona_id_state_code_diet_mode_key
      UNIQUE (persona_id, state_code, diet_mode);
  END IF;
  IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 're_cohorts_city_tier_check') THEN
    ALTER TABLE re_engine.re_cohorts DROP CONSTRAINT re_cohorts_city_tier_check;
  END IF;
END $$;

ALTER TABLE re_engine.re_cohorts DROP COLUMN IF EXISTS city_tier;

COMMIT;
