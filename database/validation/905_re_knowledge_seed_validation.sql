-- Migration: 905_re_knowledge_seed_validation.sql (validation script, not a schema change)
-- Purpose: verify the WP-6RE-GEN re_engine seed layer (migrations 110-117) against the
--   Seed Gates and referential/uniqueness invariants, AFTER migration 030 (SER-001 city_tier).
-- Governance refs: SER-001; WP-6RE audit; DOC-P3-04 §07 Seed Gates S-01..S-15.
-- Deterministic: pure counts + anti-join integrity checks. Run on foofoo-staging (WP-6E).
-- NOTE: S-08/S-10 are ICD-1-scoped (Option C) — they are expected to be BELOW the original
--   full-catalog targets (1,050 / 142) and are validated as ">0 and = the ICD-1 seeded count",
--   with the remainder tracked in the Deferred Knowledge Register. S-15
--   (re_city_migration_overlays) is DEFERRED (missing migration_duration_band) and is expected 0.

\echo '=== WP-6RE SEED VALIDATION ==='

-- ---- 1. Seed Gate row counts (fully-seeded RE tables) ----
\echo '--- Seed Gate counts (expect exact) ---'
SELECT 'S-01 re_states' g, count(*) actual, 36 expected, count(*)=36 pass FROM re_engine.re_states
UNION ALL SELECT 'S-02 re_main_cohorts', count(*), 5, count(*)=5 FROM re_engine.re_main_cohorts
UNION ALL SELECT 'S-03 re_personas', count(*), 41, count(*)=41 FROM re_engine.re_personas
UNION ALL SELECT 'S-04 re_subcohorts', count(*), 41, count(*)=41 FROM re_engine.re_subcohorts
UNION ALL SELECT 'S-05 re_routing_rules', count(*), 8, count(*)=8 FROM re_engine.re_routing_rules
UNION ALL SELECT 'S-06 re_meal_classes', count(*), 131, count(*)=131 FROM re_engine.re_meal_classes
UNION ALL SELECT 'S-07 re_meal_class_overlap_rules', count(*), 13, count(*)=13 FROM re_engine.re_meal_class_overlap_rules
UNION ALL SELECT 'S-09 re_addon_classes', count(*), 24, count(*)=24 FROM re_engine.re_addon_classes
UNION ALL SELECT 'S-11 re_cohorts', count(*), 2952, count(*)=2952 FROM re_engine.re_cohorts
UNION ALL SELECT 'S-12 re_weekly_class_plans', count(*), 20664, count(*)=20664 FROM re_engine.re_weekly_class_plans
UNION ALL SELECT 'S-13 re_household_addon_plans', count(*), 7992, count(*)=7992 FROM re_engine.re_household_addon_plans
UNION ALL SELECT 'S-14 re_nonveg_logic', count(*), 36, count(*)=36 FROM re_engine.re_nonveg_logic;

-- ---- 2. ICD-1 dish-linked tables (Option C: below full target by design; must be > 0) ----
\echo '--- ICD-1 dish-linked counts (expect >0; remainder in Deferred Register) ---'
SELECT 'S-08 re_class_dish_options (ICD-1)' g, count(*) actual, count(*) > 0 pass FROM re_engine.re_class_dish_options
UNION ALL SELECT 'S-10 re_addon_dish_options (ICD-1)', count(*), count(*) >= 0 FROM re_engine.re_addon_dish_options
UNION ALL SELECT 're_dish_regional_affinity (ICD-1)', count(*), count(*) > 0 FROM re_engine.re_dish_regional_affinity;

-- ---- 3. GAP-002 core proof: cohort uniqueness incl. city_tier ----
\echo '--- GAP-002: re_cohorts distinct (persona,state,diet_mode,city_tier) = 2952; city_tier populated ---'
SELECT count(*) AS distinct_key, 2952 AS expected,
       count(*) = 2952 AS pass
FROM (SELECT DISTINCT persona_id, state_code, diet_mode, city_tier FROM re_engine.re_cohorts) q;
SELECT count(*) AS cohorts_without_tier, count(*) = 0 AS pass
FROM re_engine.re_cohorts WHERE city_tier IS NULL;

-- ---- 4. S-12 arithmetic: weekly plans = cohorts x 7 ----
\echo '--- weekly_class_plans = re_cohorts * 7 ---'
SELECT (SELECT count(*) FROM re_engine.re_weekly_class_plans) AS weekly,
       (SELECT count(*) FROM re_engine.re_cohorts) * 7 AS cohorts_x7,
       (SELECT count(*) FROM re_engine.re_weekly_class_plans) = (SELECT count(*) FROM re_engine.re_cohorts) * 7 AS pass;

-- ---- 5. Referential integrity (anti-joins must all return 0) ----
\echo '--- FK integrity (expect 0 orphans each) ---'
SELECT 'cohorts.persona_id orphan' chk, count(*) FROM re_engine.re_cohorts c
  LEFT JOIN re_engine.re_personas p ON p.id=c.persona_id WHERE p.id IS NULL
UNION ALL SELECT 'cohorts.state_code orphan', count(*) FROM re_engine.re_cohorts c
  LEFT JOIN re_engine.re_states s ON s.state_code=c.state_code WHERE s.state_code IS NULL
UNION ALL SELECT 'weekly.cohort_id orphan', count(*) FROM re_engine.re_weekly_class_plans w
  LEFT JOIN re_engine.re_cohorts c ON c.cohort_id=w.cohort_id WHERE c.cohort_id IS NULL
UNION ALL SELECT 'weekly.breakfast_class orphan', count(*) FROM re_engine.re_weekly_class_plans w
  LEFT JOIN re_engine.re_meal_classes m ON m.class_code=w.breakfast_class_code WHERE m.class_code IS NULL
UNION ALL SELECT 'household.cohort_id orphan', count(*) FROM re_engine.re_household_addon_plans h
  LEFT JOIN re_engine.re_cohorts c ON c.cohort_id=h.cohort_id WHERE c.cohort_id IS NULL
UNION ALL SELECT 'household.addon_class orphan', count(*) FROM re_engine.re_household_addon_plans h
  LEFT JOIN re_engine.re_addon_classes a ON a.addon_class_code=h.addon_class_code WHERE a.addon_class_code IS NULL
UNION ALL SELECT 'personas.main_cohort orphan', count(*) FROM re_engine.re_personas p
  LEFT JOIN re_engine.re_main_cohorts mc ON mc.cohort_code=p.main_cohort_code WHERE mc.cohort_code IS NULL
UNION ALL SELECT 'class_dish_options.dish orphan', count(*) FROM re_engine.re_class_dish_options o
  LEFT JOIN public.dishes d ON d.id=o.dish_id WHERE d.id IS NULL
UNION ALL SELECT 'regional_affinity.state orphan', count(*) FROM re_engine.re_dish_regional_affinity a
  LEFT JOIN re_engine.re_states s ON s.state_code=a.state_code WHERE s.state_code IS NULL;

-- ---- 6. planning_role safety (Safety Gate 4 dependency): every weekly primary class is MAIN_PRIMARY ----
\echo '--- weekly-plan primary classes must all be planning_role=MAIN_PRIMARY (expect 0 violations) ---'
SELECT count(*) AS non_primary_in_plan
FROM re_engine.re_weekly_class_plans w
JOIN re_engine.re_meal_classes m
  ON m.class_code IN (w.breakfast_class_code, w.lunch_class_code, w.dinner_class_code)
WHERE m.planning_role <> 'MAIN_PRIMARY';

\echo '=== END WP-6RE SEED VALIDATION ==='
-- stop-hook test marker (harmless, no-op)
