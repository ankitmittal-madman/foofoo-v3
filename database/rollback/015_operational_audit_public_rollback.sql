-- Rollback: 015_operational_audit_public_rollback.sql
-- Reverses: 015_operational_audit_public.sql
-- RECONSTRUCTED FROM EVIDENCE (WP-5C Rollback Recovery, 2026-07-13).
--   Source of truth: the forward migration file 015_operational_audit_public.sql (the authoritative record of exactly what
--   this migration created). No original rollback existed for 001-020 (never authored — see
--   REPO-WP-02 discovery); the 021-026 rollbacks were lost in the apverse-labs repository loss
--   and are reconstructed from the WP-5B-recovered forward migrations.
--   APPLY ORDER: rollbacks run in REVERSE (028 -> 001). Each reverses ONLY what its own migration
--   created and assumes later migrations are already rolled back. Plain DROP / RESTRICT are used
--   deliberately so out-of-order or on-populated-data application FAILS LOUDLY rather than
--   cascading silently — matching the 027/028 rollback precedent.

DROP TABLE public.etl_job_runs;
DROP TABLE public.feature_flags;
DROP TABLE public.push_notification_logs;
DROP TABLE public.safety_gate_log;
DROP TABLE public.coverage_gap_log;
DROP TABLE public.audit_log;
