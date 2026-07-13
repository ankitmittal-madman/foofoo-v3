-- Rollback: 017_initial_partitions_rollback.sql
-- Reverses: 017_initial_partitions.sql
-- RECONSTRUCTED FROM EVIDENCE (WP-5C Rollback Recovery, 2026-07-13).
--   Source of truth: the forward migration file 017_initial_partitions.sql (the authoritative record of exactly what
--   this migration created). No original rollback existed for 001-020 (never authored — see
--   REPO-WP-02 discovery); the 021-026 rollbacks were lost in the apverse-labs repository loss
--   and are reconstructed from the WP-5B-recovered forward migrations.
--   APPLY ORDER: rollbacks run in REVERSE (028 -> 001). Each reverses ONLY what its own migration
--   created and assumes later migrations are already rolled back. Plain DROP / RESTRICT are used
--   deliberately so out-of-order or on-populated-data application FAILS LOUDLY rather than
--   cascading silently — matching the 027/028 rollback precedent.
--
-- WARNING: this drops EVERY partition of the two parents, including any created after 017 by
--   the ongoing monthly-partition job (a DOC-P4 concern) — not only 017's initial three. That is
--   the correct full reversal of "the partition layer", but review if a scheduled job is live.

-- Migration 017 created RANGE partitions of interaction_events and suggestion_logs whose names
-- are generated at deploy time from CURRENT_DATE (e.g. interaction_events_2026_07). Because the
-- exact names are runtime-derived, this rollback drops ALL current partitions of both parents.
DO $$
DECLARE r record;
BEGIN
  FOR r IN
    SELECT inhrelid::regclass AS part
    FROM pg_inherits
    WHERE inhparent IN ('public.interaction_events'::regclass, 'public.suggestion_logs'::regclass)
  LOOP
    EXECUTE 'DROP TABLE ' || r.part::text;
  END LOOP;
END $$;
