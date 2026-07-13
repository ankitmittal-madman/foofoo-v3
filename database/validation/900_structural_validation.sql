-- Migration: 900_structural_validation.sql (validation script, not a schema change)
-- Implements: DOC-P3-05 Part (a) v1.2 Phase 2 (Implementation Readiness Assessment checks,
--   re-run here at the database level rather than the document level)
-- Logical functions: n/a — this is a verification artifact
-- Governance refs: DOC-P3-05 Part (a) v1.2 Phase 12 (Verification Ownership Matrix — this
--   script is the "SQL script" owner for schema/FK/trigger validation)
-- Traceability: every check below cites the DOC-P3-04 §03 table/object it verifies.

\echo '=== STRUCTURAL VALIDATION — Part (d) ==='

-- Check 1: base-table count.
-- WP-5E CORRECTION (2026-07-13) — VALIDATION-01: the prior expected value of 60
-- was DOC-P3-04 §02's figure, written before migrations 021 and 024 were added.
-- The expected count is DERIVED FROM THE REPOSITORY (the migration files), not
-- from stale documentation: 60 baseline (001–016 structural tables per §02)
--   + 1 public.cuisines            (migration 021)
--   + 1 re_engine.re_dish_regional_affinity (migration 024)
--   = 62 base tables.
-- Verifiable in-repo: `grep -cE '^\s*CREATE TABLE' database/migrations/*.sql`
-- totals 62 (partition CHILDREN are created dynamically by 017's DO block and
-- are correctly excluded below and from the count). If a future STRUCTURAL
-- migration adds or drops a base table, update this derivation and the count
-- together — the number must always trace to the migration set, never to a doc.
\echo '--- Check 1: Total base-table count (expect 62 — see WP-5E derivation) ---'
SELECT count(*) AS table_count, 62 AS expected, count(*) = 62 AS pass
FROM information_schema.tables
WHERE table_schema IN ('public','re_engine') AND table_type = 'BASE TABLE'
  AND table_name NOT LIKE 'interaction_events_2%'  -- exclude partition children
  AND table_name NOT LIKE 'suggestion_logs_2%';

-- Check 2: every FK declared in DOC-P3-04 actually exists (spot-check the safety-critical ones)
\echo '--- Check 2: Safety-critical FKs present ---'
SELECT conname, conrelid::regclass AS table_name
FROM pg_constraint
WHERE contype = 'f'
  AND conrelid::regclass::text IN ('public.dish_ingredients','public.plan_slots','public.dishes')
ORDER BY table_name;

-- Check 3: the 4 trigger functions and 4 triggers exist (DOC-P3-04 §03.6A)
\echo '--- Check 3: Trigger functions and triggers (expect 4 + 4) ---'
SELECT proname FROM pg_proc WHERE proname LIKE 'fn_%' AND pronamespace = 'public'::regnamespace;
SELECT tgname FROM pg_trigger WHERE NOT tgisinternal;

-- Check 4: REVOKE on dishes derived columns is in force (AGR-001 resolution, DOC-P3-04 v1.3)
\echo '--- Check 4: authenticated/anon cannot UPDATE derived dish columns ---'
SELECT has_column_privilege('authenticated', 'public.dishes', 'diet_type', 'UPDATE') AS should_be_false;

-- Check 5: RLS enabled on every personal-data table (expect 19 rows per DOC-P3-04 §03)
\echo '--- Check 5: RLS-enabled table count (expect 19) ---'
SELECT count(*) FROM pg_tables WHERE schemaname = 'public' AND rowsecurity = true;

-- Check 6: re_engine schema is locked to service_role (DOC-P3-04 §03.26)
\echo '--- Check 6: re_engine privileges (expect anon/authenticated to have none) ---'
SELECT has_schema_privilege('authenticated', 're_engine', 'USAGE') AS should_be_false;

-- Check 7: 15 seed gate row counts (DOC-P3-05 Part (a) §07, Contract 14.5)
-- NOTE: per IDR-001, gates marked [ILLUSTRATIVE ONLY] are EXPECTED to fail until the source
-- spreadsheet is provided and migration 103+ supersedes files 101/102's placeholder rows.
\echo '--- Check 7: Seed Gate row counts ---'
SELECT 'S-01 re_states' AS gate, count(*) AS actual, 36 AS expected, count(*)=36 AS pass FROM re_engine.re_states
UNION ALL SELECT 'S-02 re_main_cohorts', count(*), 5, count(*)=5 FROM re_engine.re_main_cohorts
UNION ALL SELECT 'S-03 re_personas', count(*), 41, count(*)=41 FROM re_engine.re_personas
UNION ALL SELECT 'S-04 re_subcohorts', count(*), 41, count(*)=41 FROM re_engine.re_subcohorts
UNION ALL SELECT 'S-05 re_routing_rules', count(*), 8, count(*)=8 FROM re_engine.re_routing_rules
UNION ALL SELECT 'S-06 re_meal_classes', count(*), 131, count(*)=131 FROM re_engine.re_meal_classes
UNION ALL SELECT 'S-07 re_meal_class_overlap_rules', count(*), 13, count(*)=13 FROM re_engine.re_meal_class_overlap_rules
UNION ALL SELECT 'S-08 re_class_dish_options', count(*), 1050, count(*)=1050 FROM re_engine.re_class_dish_options
UNION ALL SELECT 'S-09 re_addon_classes', count(*), 24, count(*)=24 FROM re_engine.re_addon_classes
UNION ALL SELECT 'S-10 re_addon_dish_options', count(*), 142, count(*)>=142 FROM re_engine.re_addon_dish_options
UNION ALL SELECT 'S-11 re_cohorts', count(*), 2952, count(*)>=2952 FROM re_engine.re_cohorts
UNION ALL SELECT 'S-12 re_weekly_class_plans', count(*), 20664, count(*)=20664 FROM re_engine.re_weekly_class_plans
UNION ALL SELECT 'S-13 re_household_addon_plans', count(*), 7992, count(*)=7992 FROM re_engine.re_household_addon_plans
UNION ALL SELECT 'S-14 re_nonveg_logic', count(*), 36, count(*)=36 FROM re_engine.re_nonveg_logic
UNION ALL SELECT 'S-15 re_city_migration_overlays', count(*), 324, count(*)=324 FROM re_engine.re_city_migration_overlays;
