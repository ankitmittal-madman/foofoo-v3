-- Migration: 047_drop_legacy_re_engine_schema.sql
-- WP-20 (retire legacy re_engine schema) — STEP 2 of 2. CUTOVER-GATED — see guard below.
--
-- Drops the entire re_engine schema: the legacy TypeScript-RE's ~30 reference tables (re_cohorts,
-- re_weekly_class_plans, re_personas, re_meal_classes, re_addon_classes, ...) that NO live code
-- references (superseded by the Python RE's bundle-based catalogue/cohort model), plus the 6 tables
-- 046 already re-homed into `public` (re_states, never_list, not_today_suppression, user_re_state,
-- user_taste_vectors, re_dish_bandit_state).
--
-- ALL data is preserved before this runs:
--   - the 6 re-homed tables' rows already live in public (046, copied not moved)
--   - EVERY table in re_engine (populated or not) has a full JSON export committed at
--     database/archive/re_engine_backup_20260803/ (WP-20 backup, ~32k rows, done 2026-08-03)
--
-- HARD PREREQUISITE — DO NOT run this before:
--   1. Migration 046 has been applied (re_states + per-user tables exist in public).
--   2. The edge functions have been updated to stop referencing re_engine and REDEPLOYED:
--        supabase/functions/_shared/constants/schemas.ts   (drop RE_ENGINE_SCHEMA export)
--        supabase/functions/_shared/mod.ts                  (drop the re-export)
--        supabase/functions/_shared/services/scheduler/hard-delete.ts  (RE_ENGINE_SCHEMA -> PUBLIC_SCHEMA)
--        supabase/functions/user-export/store.ts                       (RE_ENGINE_SCHEMA -> PUBLIC_SCHEMA)
--   Running this before the redeploy will break the DPDP hard-delete and user-export edge functions
--   at runtime (relation "re_engine.never_list" does not exist, etc). See the WP-20 work package /
--   runbook for the full cutover sequence. The guard below is a best-effort safety check, not a
--   substitute for actually completing the redeploy — it can only see the DB, not what's deployed.

-- Guard + drop are ONE DO block (the drop runs via EXECUTE) so the guard is actually load-bearing:
-- if the guard and the DROP were two separate top-level statements, a client running this script
-- WITHOUT `psql -v ON_ERROR_STOP=1` (the default) would print the guard's exception and then still
-- execute the next statement — confirmed by testing this exact failure mode on Postgres 16, where a
-- guard-then-DROP as separate statements let the DROP proceed anyway after the guard "failed". Folding
-- the DROP into the same DO block means the RAISE EXCEPTION genuinely aborts before EXECUTE runs,
-- regardless of the calling client's error-stop setting.
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.tables
                 WHERE table_schema='public' AND table_name='re_states') THEN
    RAISE EXCEPTION 'WP-20 GUARD: public.re_states does not exist — run migration 046 first.';
  END IF;
  EXECUTE 'DROP SCHEMA re_engine CASCADE';
END $$;
