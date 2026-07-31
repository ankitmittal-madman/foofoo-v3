-- Rollback: 040_enable_pg_cron_extension_rollback.sql
-- Only safe to run before any cron job has been scheduled using these extensions (see this
-- migration's own header — the actual schedules are a separate, manual Dashboard step not yet
-- taken as of this migration).

DROP EXTENSION IF EXISTS pg_net;
DROP EXTENSION IF EXISTS pg_cron;
