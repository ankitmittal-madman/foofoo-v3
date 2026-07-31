-- Migration: 040_enable_pg_cron_extension.sql
-- Prerequisite for scheduling the DPDP retention-purge and hard-delete Edge Functions
-- (supabase/functions/cron-retention-purge/, supabase/functions/cron-hard-delete/, built this
-- session per LF-M03 §15 / DOC-09 §03). Enables the extensions; does NOT create the actual cron
-- schedules — that step needs the project's service_role key to authenticate the HTTP call from
-- pg_cron/pg_net to the deployed function, which must be provisioned via Supabase Vault through
-- the Dashboard (Database > Cron in the Supabase Studio, or `vault.create_secret` run manually
-- with the real key value) — not something this migration file should ever contain in plain SQL.
-- See ops/audits/audit-dpdp/dpdp-compliance-report.md and the RUNBOOK note alongside this file
-- for the exact manual step remaining.

CREATE EXTENSION IF NOT EXISTS pg_cron;
CREATE EXTENSION IF NOT EXISTS pg_net;
