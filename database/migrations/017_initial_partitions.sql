-- Migration: 017_initial_partitions.sql
-- Implements: DOC-P3-04 v1.3 §07 (Partitioning, Archival, Retention strategy — monthly
--   RANGE partitions for interaction_events and suggestion_logs)
-- Logical functions: LF-J01-J09 (interaction_events writes require a matching partition to exist
--   before any row can be inserted), LF-F01/H01-H04 (suggestion_logs, same requirement)
-- Governance refs: DOC-P3-05 Part (a) Phase 7 (prerequisite: 012); Phase 9 (this file is
--   explicitly named as safe to re-run/idempotent if it fails partway, per Part (a)'s own
--   Intentional Exception 1)
-- CDM entities: Entity 29 (Interaction Event), Safety Gate (48, via suggestion_logs)
-- CDM invariants enforced: none directly — this file makes the parent tables from file 012
--   actually usable; without it, every INSERT into interaction_events or suggestion_logs fails
--   with "no partition found for row" since a RANGE-partitioned table with zero child partitions
--   accepts no rows.
--
-- This file creates partitions for the current month and the following two months (a 3-month
-- rolling window), consistent with DOC-P3-04 §07's "created one month ahead by a scheduled job"
-- policy — this migration provides the INITIAL set; the ongoing monthly creation job itself is
-- a DOC-P4 CRON/scheduling concern, not recreated here, per the boundary already established in
-- Part (a) Phase 2.4/2.10/8.7.
--
-- Date literals below are illustrative placeholders for July-September 2026 (current month at
-- time of writing being June 2026, with one month of lead margin). The actual values used at
-- deployment time must be generated dynamically from CURRENT_DATE by whatever tool applies this
-- migration, NOT hardcoded as literals in a checked-in file — hardcoding specific calendar dates
-- into a versioned migration file would make this file's correctness silently expire. This is
-- flagged explicitly: the SQL below is a TEMPLATE pattern, and the actual apply-time values are
-- a Part (d)/deployment-tooling responsibility, consistent with Phase 14's non-goals on
-- deployment pipeline tooling.

DO $$
DECLARE
  v_month_start date := date_trunc('month', CURRENT_DATE)::date;
  v_i integer;
BEGIN
  FOR v_i IN 0..2 LOOP
    EXECUTE format(
      'CREATE TABLE IF NOT EXISTS public.interaction_events_%s PARTITION OF public.interaction_events
         FOR VALUES FROM (%L) TO (%L)',
      to_char(v_month_start + (v_i || ' months')::interval, 'YYYY_MM'),
      v_month_start + (v_i || ' months')::interval,
      v_month_start + ((v_i+1) || ' months')::interval
    );
    EXECUTE format(
      'CREATE TABLE IF NOT EXISTS public.suggestion_logs_%s PARTITION OF public.suggestion_logs
         FOR VALUES FROM (%L) TO (%L)',
      to_char(v_month_start + (v_i || ' months')::interval, 'YYYY_MM'),
      v_month_start + (v_i || ' months')::interval,
      v_month_start + ((v_i+1) || ' months')::interval
    );
  END LOOP;
END $$;
