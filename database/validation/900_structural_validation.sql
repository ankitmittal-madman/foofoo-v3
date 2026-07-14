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
  -- WP-6E3 fix: compare by OID (regclass[]) not by text; ::regclass::text renders unqualified
  -- ('dishes') when 'public' is on search_path, so the prior schema-qualified text IN (...) never matched.
  AND conrelid = ANY (ARRAY['public.dish_ingredients','public.plan_slots','public.dishes']::regclass[])
ORDER BY table_name;

-- Check 3: the 4 trigger functions and 4 triggers exist (DOC-P3-04 §03.6A)
-- WP-6E3: expect the 5 canonical fn_* functions (4 dish-derivation + fn_sync_profile_allergen_union)
-- and the 4 app triggers below; any additional triggers are Supabase-managed (storage.*), not app schema.
\echo '--- Check 3: Trigger functions (expect 5 fn_*) and app triggers (expect 4: derive, propagate, genome, allergen-sync) ---'
SELECT proname FROM pg_proc WHERE proname LIKE 'fn_%' AND pronamespace = 'public'::regnamespace ORDER BY proname;
SELECT tgname, tgrelid::regclass AS on_table FROM pg_trigger
WHERE NOT tgisinternal AND tgrelid IN (SELECT oid FROM pg_class WHERE relnamespace IN ('public'::regnamespace,'re_engine'::regnamespace))
ORDER BY tgname;

-- Check 4: REVOKE on dishes derived columns is in force (AGR-001 resolution, DOC-P3-04 v1.3)
\echo '--- Check 4: authenticated/anon cannot UPDATE derived dish columns ---'
SELECT has_column_privilege('authenticated', 'public.dishes', 'diet_type', 'UPDATE') AS should_be_false;

-- Check 5: RLS enabled on every public base table (WP-6E3 modernization).
-- The prior fixed expectation of 19 was stale (pre-migration-021) and brittle. The real
-- invariant DOC-P3-04 §03 cares about is that NO public table is left without row-level
-- security — expressed here as "0 tables without RLS", which is stronger than a magic count
-- and robust to the exact table set (currently every public table has RLS enabled).
\echo '--- Check 5: RLS on every public base table (expect 0 without RLS) ---'
SELECT count(*) FILTER (WHERE NOT rowsecurity) AS tables_without_rls,
       count(*)                                AS total_public_tables,
       count(*) FILTER (WHERE NOT rowsecurity) = 0 AS pass
FROM pg_tables WHERE schemaname = 'public';

-- Check 6: re_engine schema is locked to service_role (DOC-P3-04 §03.26)
\echo '--- Check 6: re_engine privileges (expect anon/authenticated to have none) ---'
SELECT has_schema_privilege('authenticated', 're_engine', 'USAGE') AS should_be_false;

-- Check 7: 15 seed gate row counts (DOC-P3-05 Part (a) §07, Contract 14.5)
-- WP-6E3 modernization: targets updated to the Founder-approved Option C / ICD-1 canonical
-- baseline (REPO-CERT-007, REPO-CERT-009). The dish-linked gates S-08/S-10 are scoped to the
-- dishes actually in the catalog (165 / 6), with the remainder in the Deferred Knowledge
-- Register; S-15 (re_city_migration_overlays) is DEFERRED and canonically 0. These replace the
-- stale pre-Option-C full-catalog targets (1050 / 142 / 324) that the removed illustrative
-- seeds 101/102 could never satisfy. 905 remains the authoritative RE seed-gate validation.
\echo '--- Check 7: Seed Gate row counts ---'
SELECT 'S-01 re_states' AS gate, count(*) AS actual, 36 AS expected, count(*)=36 AS pass FROM re_engine.re_states
UNION ALL SELECT 'S-02 re_main_cohorts', count(*), 5, count(*)=5 FROM re_engine.re_main_cohorts
UNION ALL SELECT 'S-03 re_personas', count(*), 41, count(*)=41 FROM re_engine.re_personas
UNION ALL SELECT 'S-04 re_subcohorts', count(*), 41, count(*)=41 FROM re_engine.re_subcohorts
UNION ALL SELECT 'S-05 re_routing_rules', count(*), 8, count(*)=8 FROM re_engine.re_routing_rules
UNION ALL SELECT 'S-06 re_meal_classes', count(*), 131, count(*)=131 FROM re_engine.re_meal_classes
UNION ALL SELECT 'S-07 re_meal_class_overlap_rules', count(*), 13, count(*)=13 FROM re_engine.re_meal_class_overlap_rules
UNION ALL SELECT 'S-08 re_class_dish_options (ICD-1)', count(*), 165, count(*)=165 FROM re_engine.re_class_dish_options
UNION ALL SELECT 'S-09 re_addon_classes', count(*), 24, count(*)=24 FROM re_engine.re_addon_classes
UNION ALL SELECT 'S-10 re_addon_dish_options (ICD-1)', count(*), 6, count(*)=6 FROM re_engine.re_addon_dish_options
UNION ALL SELECT 'S-11 re_cohorts', count(*), 2952, count(*)=2952 FROM re_engine.re_cohorts
UNION ALL SELECT 'S-12 re_weekly_class_plans', count(*), 20664, count(*)=20664 FROM re_engine.re_weekly_class_plans
UNION ALL SELECT 'S-13 re_household_addon_plans', count(*), 7992, count(*)=7992 FROM re_engine.re_household_addon_plans
UNION ALL SELECT 'S-14 re_nonveg_logic', count(*), 36, count(*)=36 FROM re_engine.re_nonveg_logic
UNION ALL SELECT 'S-15 re_city_migration_overlays (DEFERRED)', count(*), 0, count(*)=0 FROM re_engine.re_city_migration_overlays;
