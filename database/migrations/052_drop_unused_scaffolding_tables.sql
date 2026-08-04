-- 052_drop_unused_scaffolding_tables.sql
-- reports/re_audit backlog item #5 (orphaned-table disposition), investigated 2026-08-04.
--
-- Of the ~11 tables report 07 §2 flagged as "orphaned" (zero seed rows, zero app-code references),
-- a follow-up investigation found the set was NOT uniform:
--   - `interaction_events_` / `suggestion_logs_` were never real tables (partition-name templates
--     from migration 017) — no action needed, not part of this migration.
--   - `meal_classes` has 131 seeded rows (a real public mirror of re_engine.re_meal_classes) — not
--     orphaned, not touched here.
--   - `derivation_conflicts` is NOT dropped here (see below) — it is live infrastructure, not
--     scaffolding, despite having zero rows today.
--   - `addon_slots`, `context_log`, `weather_cache` are NOT dropped here — each carries a
--     hand-authored RLS policy (019_rls_policies.sql) and, for weather_cache, a live config value
--     (`weather_cache_ttl_hours` in seed 100) — real work anticipating near-term use, not
--     accidentally-orphaned debris. Kept, pending a product decision on when to build their
--     consumer code, not a schema decision.
--
-- The 5 tables actually dropped below were independently re-verified (2026-08-04) to have: no
-- trigger writing to them, no RLS policy ever authored for them (019/029 explicitly left them with
-- no client grants "by design"), and zero producer code anywhere in supabase/functions, mobile, or
-- ghar_re_service/ghar_re_core — pure unconsumed scaffolding for features never built:
--   coverage_gap_log        (015_operational_audit_public.sql) — constraint-conflict/variety-gap logging
--   etl_job_runs            (015_operational_audit_public.sql) — scheduled-CRON-job run log
--   feature_flags           (015_operational_audit_public.sql) — generic feature-flag table
--   push_notification_logs (015_operational_audit_public.sql) — OneSignal push-notification log
--   safety_gate_log         (015_operational_audit_public.sql) — CI/CD safety-gate blocked-deploy log
--
-- IMPORTANT — explicitly excluded, do not add to this migration without re-deriving the same
-- evidence: `derivation_conflicts` (010_trigger_functions_and_triggers.sql) is actively written by
-- the live AFTER trigger `trg_derive_dish_attributes` on every `dish_ingredients` INSERT/UPDATE/
-- DELETE (fn_derive_dish_attributes body, same migration) — its "zero rows today" reflects a
-- post-rollback state (the seed-rollback script DELETEs from it), not disuse. Dropping it would
-- break that trigger the next time any dish's ingredients are edited.

SET client_min_messages = warning;

DROP TABLE IF EXISTS public.coverage_gap_log;
DROP TABLE IF EXISTS public.etl_job_runs;
DROP TABLE IF EXISTS public.feature_flags;
DROP TABLE IF EXISTS public.push_notification_logs;
DROP TABLE IF EXISTS public.safety_gate_log;
