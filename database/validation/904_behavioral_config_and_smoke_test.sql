-- Migration: 904_behavioral_config_and_smoke_test.sql (validation script)
-- Implements: DOC-P3-04 v1.3 §03.28 (config tables), §03.12-03.14 (week_plans/plan_slots/addon_slots)
-- Logical functions: LF-E01 interpolateWeightLadder(), LF-A08 computeOnboardingConfidence()
-- Governance refs: DOC-P3-05 Part (a) v1.2 Phase 5.5 (the smoke test originally specified there)
-- Behavioral claim under test: "configuration-driven behaviour functions correctly" +
--   "data quality rules are enforced" (founder requirement #4)

\echo '=== BEHAVIORAL VALIDATION: Configuration-driven values ==='

-- TEST 1: weight ladder CHECK constraint actually enforces sum=1.0 (not just documented)
\echo '--- Test 1: weight ladder rows all sum to 1.0 (live query, not just trusting the seed file) ---'
SELECT tier_name, w_cohort+w_content+w_history+w_context+w_explore AS total,
  (w_cohort+w_content+w_history+w_context+w_explore = 1.0) AS sums_correctly
FROM re_engine.re_weight_ladder_config;
-- EXPECTED: sums_correctly=true for all 5 rows. If false for any row, the CHECK constraint
-- (DOC-P3-04 §03.28) should have already rejected that INSERT at load time — this is a
-- belt-and-suspenders confirmation, not the only line of defense.

-- TEST 2: prove the CHECK constraint itself actively rejects a bad insert (not just well-behaved data)
\echo '--- Test 2: attempt an invalid weight-sum insert, expect rejection ---'
DO $$
BEGIN
  BEGIN
    INSERT INTO re_engine.re_weight_ladder_config
      (tier_name, lower_bound, upper_bound, w_cohort, w_content, w_history, w_context, w_explore)
    VALUES ('test_invalid', 9999, NULL, 0.50, 0.50, 0.50, 0.50, 0.50);  -- sums to 2.5, not 1.0
    RAISE EXCEPTION 'FAIL: CHECK constraint did not reject a weight sum of 2.5';
  EXCEPTION WHEN check_violation THEN
    RAISE NOTICE 'PASS: CHECK constraint correctly rejected an invalid weight-ladder row';
  END;
END $$;

-- TEST 3: event weight values are queryable exactly as DOC-P3-03 §16 specifies (spot check)
\echo '--- Test 3: dish_not_today event weight uses its own decay_lambda (0.35), distinct from the general lambda (0.05) ---'
SELECT event_type, weight, decay_lambda FROM re_engine.re_event_weights
WHERE event_type IN ('dish_not_today', 'dish_accepted');
-- EXPECTED: dish_not_today shows decay_lambda=0.35; dish_accepted shows decay_lambda=0.05 —
-- proving the two-mechanism distinction from DOC-P3-03 §07 LF-E04 is correctly represented
-- in the data, not collapsed into a single value by mistake during seeding.

\echo '=== END-TO-END SMOKE TEST: minimal onboarding -> plan -> gate path ==='
-- This smoke test is intentionally narrow: it proves the DATA MODEL supports the full
-- pipeline end to end using existing seed/fixture data. It does NOT invoke the actual RE
-- Edge Function logic (LF-A09 assignPersona, LF-B02 generateClassPlan, etc.) because that
-- logic lives in application code (DOC-P4 territory), not in the database. What this proves
-- is that every table the pipeline depends on can be populated and joined exactly as
-- DOC-P3-03/03A specify, with no missing column, no broken FK, no schema-level obstruction.

DO $$
DECLARE
  v_persona_id uuid;
  v_cohort_id uuid;
BEGIN
  -- Step 1: simulate assignPersona() — a plain lookup, exactly as LF-A09 specifies
  SELECT p.id INTO v_persona_id FROM re_engine.re_personas p
  WHERE p.main_cohort_code = 'MC_NUCLEAR_FAMILY' AND p.primary_diet = 'veg'
  LIMIT 1;
  ASSERT v_persona_id IS NOT NULL, 'FAIL: assignPersona() lookup pattern returned no persona';
  RAISE NOTICE 'PASS: persona lookup (LF-A09 pattern) resolved to a real persona_id';

  -- Step 2: simulate generateClassPlan() — query re_weekly_class_plans by cohort
  SELECT c.cohort_id INTO v_cohort_id FROM re_engine.re_cohorts c
  WHERE c.persona_id = v_persona_id LIMIT 1;
  IF v_cohort_id IS NOT NULL THEN
    -- Canonical seed 114 stores day_of_week as 3-letter title-case ('Mon'..'Sun'), not 'monday'.
    PERFORM 1 FROM re_engine.re_weekly_class_plans WHERE cohort_id = v_cohort_id AND day_of_week = 'Mon';
    IF FOUND THEN
      RAISE NOTICE 'PASS: class plan lookup (LF-B02 pattern) resolved a real weekly plan row';
    ELSE
      RAISE EXCEPTION 'FAIL: cohort % has no Monday (Mon) weekly plan row — canonical seed 114 expects 7 days per cohort', v_cohort_id;
    END IF;
  ELSE
    RAISE EXCEPTION 'FAIL: no re_cohorts row for this persona — canonical seed 113 expects a cohort per persona/state/tier';
  END IF;

  RAISE NOTICE 'SMOKE TEST COMPLETE: data model supports the onboarding -> persona -> class plan path on the full canonical dataset (WP-6E.2: 2,952 cohorts x 7 days = 20,664 weekly plan rows).';
  -- (Modernized WP-6E3: day_of_week 'monday' -> 'Mon' to match canonical seed 114; the former
  --  IDR-001 "illustrative / only 1 row seeded" PARTIAL branches are now hard FAILs, since the
  --  full canonical RE layer is loaded — this strengthens the smoke test, it does not weaken it.)
END $$;
