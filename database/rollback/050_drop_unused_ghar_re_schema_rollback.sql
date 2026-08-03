-- Rollback 050 — NOT A DATA RESTORE.
-- DROP SCHEMA ... CASCADE is destructive: table structure and all 28 tables' data are gone once
-- this migration is applied. There is no SQL statement that recreates the data.
--
-- To actually recover: re-run migrations 034, 035, 036, 037, 045 (recreates empty table structure)
-- and re-apply seeds 120-122 (recreates the curated data those seeds captured, if the seed files
-- themselves are still accurate) — or restore from a database snapshot taken before 050 was applied.
-- This file intentionally does not attempt either automatically: which is correct depends on
-- whether a pre-migration snapshot exists, which this migration's author cannot know in advance.
SELECT 1; -- no-op placeholder; see comment above for the actual recovery procedure
