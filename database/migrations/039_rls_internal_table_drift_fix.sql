-- Migration: 039_rls_internal_table_drift_fix.sql
-- Investigates: docs/archive/audits/ops/audit-rls/ARCHIVED_rls-audit.md Findings 1 and 2,
--   live-DB drift against
--   019_rls_policies.sql's stated intent.
--
-- Finding 1 (partition-child tables) — INVESTIGATED, NO FIX NEEDED, not applied here:
--   interaction_events_2026_07/08/09 and suggestion_logs_2026_07/08/09 are true declarative
--   partitions (confirmed via pg_inherits). Verified live via EXPLAIN under `SET ROLE authenticated`
--   with a fake JWT claim: querying a partition directly by name produces the exact same RLS filter
--   (`profile_id = auth.uid()`) as the parent's own ie_select_own/sl_select_own policies, using a
--   real Bitmap Index Scan on profile_id — Postgres automatically applies a partitioned table's RLS
--   policies to all its partitions regardless of access path. No security gap, no PostgREST bypass.
--
-- Finding 2 (7 internal tables: audit_log, derivation_conflicts, coverage_gap_log, safety_gate_log,
--   push_notification_logs, feature_flags, etl_job_runs) — INVESTIGATED, RLS LEFT ENABLED, NOT
--   disabled, contrary to this migration's original intent:
--   019_rls_policies.sql (lines 83-88) states these are "internal-only" tables where "leaving RLS
--   disabled is correct." That assumption depends on these tables having no PostgREST-reachable
--   grants for anon/authenticated. Live inspection (2026-07-30) found the OPPOSITE: anon and
--   authenticated both hold full SELECT/INSERT/UPDATE/DELETE/TRUNCATE grants on all 7 tables (the
--   Supabase default public-schema grant, never revoked by any canonical migration for these
--   tables). Disabling RLS under that condition would make all 7 fully read/writable by any client
--   via the REST API — confirmed empirically: doing so live immediately produced Supabase's own
--   `rls_disabled_in_public` ERROR-level security lint on all 7 tables. The change was reverted
--   within the same session before being written here.
--
--   029_pf1_security_hardening.sql's own header (Option B QUARANTINE, Founder decision
--   2026-07-13) independently confirms this exact tension was already known: a production-only
--   operational overlay (`public.rls_auto_enable()` + an `ensure_rls` event trigger, deliberately
--   kept OUT of canonical migrations for clean-rebuild determinism) automatically re-enables RLS
--   whenever it's found disabled, "behaviourally in conflict with migration 019's deliberate RLS
--   design" by the Founder's own words. In other words: what audit-rls flagged as "drift" from
--   019's documented intent is that approved overlay doing its job — 019's intent was based on an
--   incomplete premise (grants), and the Founder's already-shipped fix is the live RLS-enabled
--   state, not 019's text. RLS is therefore correctly left ENABLED on all 7 tables by this
--   migration (no ALTER ... DISABLE statement here, unlike the reverted first attempt).
--
--   What this migration DOES fix, as defense-in-depth matching the exact precedent already
--   established in 029_pf1_security_hardening.sql (Finding 2, column-level REVOKE on `dishes`
--   "defense-in-depth" alongside RLS default-deny as the primary protection): revoke the
--   unnecessary broad grants for anon/authenticated on these 7 internal-only tables. RLS
--   (kept enabled) is the primary protection; this REVOKE means even a future disabling of RLS
--   (accidental, or if the production-only overlay above is ever removed) would not by itself
--   reopen these tables to client access.

REVOKE INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER, SELECT
  ON public.audit_log, public.derivation_conflicts, public.coverage_gap_log,
     public.safety_gate_log, public.push_notification_logs, public.feature_flags,
     public.etl_job_runs
  FROM anon, authenticated;
