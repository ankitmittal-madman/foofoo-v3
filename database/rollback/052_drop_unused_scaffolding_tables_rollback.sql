-- Rollback 052 — recreates the 5 dropped tables' empty structure (they held zero rows in every
-- environment this was verified against, so structure-only recreation is a complete rollback here,
-- unlike migration 050's rollback which explicitly could not restore data). Definitions copied
-- verbatim from 015_operational_audit_public.sql.

SET client_min_messages = warning;

CREATE TABLE IF NOT EXISTS public.coverage_gap_log (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  profile_id    uuid REFERENCES public.profiles(id),
  class_code    text,
  gap_type      text NOT NULL CHECK (gap_type IN ('constraint_conflict','variety_exhausted')),
  candidate_count integer,
  logged_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.safety_gate_log (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  gate_number  smallint NOT NULL CHECK (gate_number BETWEEN 1 AND 4),
  violation_count integer NOT NULL,
  sample_rows   jsonb,
  run_at        timestamptz NOT NULL DEFAULT now(),
  blocked_deploy boolean NOT NULL DEFAULT false
);

CREATE TABLE IF NOT EXISTS public.push_notification_logs (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  profile_id      uuid NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  sent_at         timestamptz NOT NULL DEFAULT now(),
  notification_type text NOT NULL,
  onesignal_id     text,
  delivered        boolean
);

CREATE TABLE IF NOT EXISTS public.feature_flags (
  flag_key     text PRIMARY KEY,
  is_enabled   boolean NOT NULL DEFAULT false,
  rollout_pct  smallint NOT NULL DEFAULT 0 CHECK (rollout_pct BETWEEN 0 AND 100),
  updated_at   timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.etl_job_runs (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  job_name      text NOT NULL,
  started_at    timestamptz NOT NULL DEFAULT now(),
  finished_at   timestamptz,
  status        text CHECK (status IN ('running','success','failed')),
  rows_affected integer,
  error_message text
);
