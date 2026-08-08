-- Remove only the read-only aggregate report. Feedback, outcome and training evidence is retained.
REVOKE ALL ON FUNCTION ml.preference_attribution_recovery_report()
  FROM PUBLIC, anon, authenticated, service_role;
DROP FUNCTION IF EXISTS ml.preference_attribution_recovery_report();
