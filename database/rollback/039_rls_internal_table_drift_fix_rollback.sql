-- Rollback: 039_rls_internal_table_drift_fix.sql
-- Restores the default Supabase public-schema grants for anon/authenticated on the 7 internal
-- tables. Only run this if you have a specific reason to reproduce the pre-fix grant state — RLS
-- (left enabled by the up-migration, unchanged either way) remains the primary protection, so this
-- rollback does not by itself reopen client access, but it does remove the defense-in-depth layer.

GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER
  ON public.audit_log, public.derivation_conflicts, public.coverage_gap_log,
     public.safety_gate_log, public.push_notification_logs, public.feature_flags,
     public.etl_job_runs
  TO anon, authenticated;
