-- Migration: 032_interaction_events_dedup_key.sql
-- Implements: SER-003 (Founder-approved) — adds a client-supplied dedup key to
--   public.interaction_events so a retried POST /v1/events request can be recognized instead
--   of double-counting into LF-J02's interaction_count (which feeds cold-start-exit logic J02/
--   J05 and the MVP's Day-0/Day-90 acceptance metric, DOC-01 §07).
-- Governance refs: [ACTIVE]_SER-003_interaction_events_idempotency_key_v1.0.md (approved as
--   written, including the partition-scoped uniqueness approach below — promoted DRAFT ->
--   ACTIVE alongside this migration). DOC-P3-06 §08 (the DCR this SER resolves).
--
-- Partitioning constraint (documented, not worked around): public.interaction_events is
--   PARTITION BY RANGE (occurred_at) (migration 017). Postgres requires the partition key in
--   any unique index on a partitioned table, so a bare UNIQUE (dedup_key) is not possible.
--   UNIQUE (dedup_key, occurred_at) WHERE dedup_key IS NOT NULL is the DB-level guarantee
--   within a partition; the app-level 24h lookback check (POST /v1/events, Epic 5, not yet
--   built) is the actual dedup mechanism across a possible partition boundary. This two-layer
--   approach is Founder-approved as the correct trade-off, not a compromise to revisit.
--
-- Verified before writing this migration: no existing column serves this purpose; dedup_key
--   is added nullable so every existing row (dedup_key = NULL) is unaffected and never treated
--   as a duplicate of anything (standard NULL-not-equal-NULL semantics). Created directly on
--   the partitioned parent, matching this repository's existing index convention (020_indexes.
--   sql creates all interaction_events indexes on the parent; Postgres propagates automatically
--   to existing and future partitions once the partition key is included).

ALTER TABLE public.interaction_events
  ADD COLUMN dedup_key uuid;

CREATE UNIQUE INDEX idx_ie_dedup_key
  ON public.interaction_events (dedup_key, occurred_at)
  WHERE dedup_key IS NOT NULL;
