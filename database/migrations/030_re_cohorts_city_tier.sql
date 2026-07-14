-- Migration: 030_re_cohorts_city_tier.sql
-- Implements: SER-001 (docs/governance/[ACTIVE]_SER-001_re_cohorts_city_tier_v1.0.md)
--   — GAP-002 resolution, Founder-approved Option A (2026-07-14).
-- Evolves: DOC-P3-04 §03.27 re_engine.re_cohorts (first governed schema evolution post-Freeze).
-- Governance refs: SER-001; WP-6RE audit §Step-3; Batch1_Resolution RES-004 / GAP-002.
--
-- PROBLEM (proven, WP-6RE-DEC STEP 1): Cohort_Matrix_v3 = 2,952 rows = 1,476 (persona,state)
--   x 2 city tiers. re_cohorts UNIQUE(persona_id,state_code,diet_mode) with persona-determined
--   diet_mode admits only 1,476 rows -> Seed Gate S-11 (2,952) unsatisfiable; blocks S-12/S-13.
-- FIX: add city_tier as the minimal, non-redundant discriminator; evolve the unique key to
--   include it. Restores S-11=2,952 and S-12=20,664 (=2,952 x 7).
--
-- BACKWARD COMPATIBILITY: city_tier is nullable with a CHECK that permits NULL, so the two
--   pre-existing illustrative rows (seed 102) are preserved (city_tier = NULL). Idempotent:
--   guarded so re-application is a no-op.
-- ENGINEERING NOTE: the dropped constraint name (re_cohorts_persona_id_state_code_diet_mode_key)
--   is the Postgres auto-generated name for the inline UNIQUE(persona_id,state_code,diet_mode)
--   in migration 004. The new key is a superset; it only ever admits MORE distinct rows.

BEGIN;

-- 1. Add the city-tier discriminator (nullable; existing rows preserved as NULL).
ALTER TABLE re_engine.re_cohorts
  ADD COLUMN IF NOT EXISTS city_tier text;

-- 2. Constrain city_tier to the canonical source vocabulary (Cohort_Matrix_v3.city_tier_code).
--    NULL passes CHECK, preserving pre-existing rows.
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 're_cohorts_city_tier_check') THEN
    ALTER TABLE re_engine.re_cohorts
      ADD CONSTRAINT re_cohorts_city_tier_check CHECK (city_tier IN ('T1','T2'));
  END IF;
END $$;

-- 3. Evolve the uniqueness key: drop the 3-column key, add the 4-column key incl. city_tier.
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 're_cohorts_persona_id_state_code_diet_mode_key') THEN
    ALTER TABLE re_engine.re_cohorts DROP CONSTRAINT re_cohorts_persona_id_state_code_diet_mode_key;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 're_cohorts_persona_state_diet_tier_key') THEN
    ALTER TABLE re_engine.re_cohorts
      ADD CONSTRAINT re_cohorts_persona_state_diet_tier_key
      UNIQUE (persona_id, state_code, diet_mode, city_tier);
  END IF;
END $$;

COMMIT;
