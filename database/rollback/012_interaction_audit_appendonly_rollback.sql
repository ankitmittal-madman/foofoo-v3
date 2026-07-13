-- Rollback: 012_interaction_audit_appendonly_rollback.sql
-- Reverses: 012_interaction_audit_appendonly.sql
-- RECONSTRUCTED FROM EVIDENCE (WP-5C Rollback Recovery, 2026-07-13).
--   Source of truth: the forward migration file 012_interaction_audit_appendonly.sql (the authoritative record of exactly what
--   this migration created). No original rollback existed for 001-020 (never authored — see
--   REPO-WP-02 discovery); the 021-026 rollbacks were lost in the apverse-labs repository loss
--   and are reconstructed from the WP-5B-recovered forward migrations.
--   APPLY ORDER: rollbacks run in REVERSE (028 -> 001). Each reverses ONLY what its own migration
--   created and assumes later migrations are already rolled back. Plain DROP / RESTRICT are used
--   deliberately so out-of-order or on-populated-data application FAILS LOUDLY rather than
--   cascading silently — matching the 027/028 rollback precedent.
--
-- WARNING: public.interaction_events and public.suggestion_logs are RANGE-partitioned parents.
--   Their child partitions are created by migration 017 and must be dropped first (run 017's
--   rollback before this one). Plain DROP TABLE will fail loudly if partitions still exist.

DROP TABLE public.weather_cache;
DROP TABLE public.context_log;
DROP TABLE public.suggestion_logs;
DROP TABLE public.interaction_events;
