-- Rollback 115
BEGIN;
DELETE FROM re_engine.re_household_addon_plans WHERE cohort_id IN (SELECT cohort_id FROM re_engine.re_cohorts);
COMMIT;
