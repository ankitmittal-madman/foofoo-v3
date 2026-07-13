-- Migration: 015_operational_audit_public.sql
-- Implements: DOC-P3-04 v1.3 §03.19 (audit_log), §03.21-03.24 (coverage_gap_log, safety_gate_log,
--   push_notification_logs, feature_flags), §03.25 (etl_job_runs)
-- Logical functions: LF-M02/M03 (audit_log), LF-D07/F03 (coverage_gap_log), LF-H01-H04
--   (safety_gate_log), DOC-10 morning notification (push_notification_logs), P3-03A §03
--   feature-flag class (feature_flags), all 6 scheduled CRON jobs from P3-03A §07 (etl_job_runs)
-- Governance refs: DOC-P3-05 Part (a) v1.2 Phase 7 (prerequisite: 005 for push_notification_logs;
--   otherwise standalone)
-- CDM entities: Entity 48 (Safety Gate, via safety_gate_log)
-- CDM invariants enforced: none directly — these are operational/audit tables, not
--   business-logic-bearing
-- AGR-003 RESOLVED (v1.2): public.derivation_conflicts was relocated to file 010, where the
-- trigger function that writes to it is defined, closing the forward-reference gap that
-- previously existed when this table was created here, after its consumer. See DOC-P3-05
-- Part (a) v1.2 Phase 16 and the Architecture Gap Register, entry AGR-003.

CREATE TABLE public.audit_log (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  actor_id     uuid,
  action       text NOT NULL,
  table_name   text NOT NULL,
  record_id    uuid,
  old_value    jsonb,
  new_value    jsonb,
  occurred_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE public.coverage_gap_log (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  profile_id    uuid REFERENCES public.profiles(id),
  class_code    text,
  gap_type      text NOT NULL CHECK (gap_type IN ('constraint_conflict','variety_exhausted')),
  candidate_count integer,
  logged_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE public.safety_gate_log (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  gate_number  smallint NOT NULL CHECK (gate_number BETWEEN 1 AND 4),
  violation_count integer NOT NULL,
  sample_rows   jsonb,
  run_at        timestamptz NOT NULL DEFAULT now(),
  blocked_deploy boolean NOT NULL DEFAULT false
);

CREATE TABLE public.push_notification_logs (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  profile_id      uuid NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  sent_at         timestamptz NOT NULL DEFAULT now(),
  notification_type text NOT NULL,
  onesignal_id     text,
  delivered        boolean
);

CREATE TABLE public.feature_flags (
  flag_key     text PRIMARY KEY,
  is_enabled   boolean NOT NULL DEFAULT false,
  rollout_pct  smallint NOT NULL DEFAULT 0 CHECK (rollout_pct BETWEEN 0 AND 100),
  updated_at   timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE public.etl_job_runs (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  job_name      text NOT NULL,
  started_at    timestamptz NOT NULL DEFAULT now(),
  finished_at   timestamptz,
  status        text CHECK (status IN ('running','success','failed')),
  rows_affected integer,
  error_message text
);
