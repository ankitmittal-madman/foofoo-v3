-- Rollback: 032_interaction_events_dedup_key_rollback.sql
-- Reverses: 032_interaction_events_dedup_key.sql
-- Safe at any time before POST /v1/events (Epic 5, not yet built) depends on this column.
--   Drops the partitioned unique index before the column, same order as forward migration
--   reversed.

DROP INDEX IF EXISTS idx_ie_dedup_key;

ALTER TABLE public.interaction_events
  DROP COLUMN dedup_key;
