-- Roll back the forward-only cutover. Migration 117 must be reapplied immediately if the v1
-- historical-window report is still required by operations.
DROP TABLE IF EXISTS ml.preference_attribution_slo_control;
DROP FUNCTION IF EXISTS ml.fresh_preference_attribution_report(timestamptz);
