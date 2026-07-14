-- Rollback 114
BEGIN;
DELETE FROM re_engine.re_weekly_class_plans WHERE cohort_id IN (SELECT cohort_id FROM re_engine.re_cohorts);
COMMIT;
