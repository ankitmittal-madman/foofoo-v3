-- Rollback: 018_meal_classes_mirror_sync_rollback.sql
-- Reverses: 018_meal_classes_mirror_sync.sql
-- RECONSTRUCTED FROM EVIDENCE (WP-5C Rollback Recovery, 2026-07-13).
--   Source of truth: the forward migration file 018_meal_classes_mirror_sync.sql (the authoritative record of exactly what
--   this migration created). No original rollback existed for 001-020 (never authored — see
--   REPO-WP-02 discovery); the 021-026 rollbacks were lost in the apverse-labs repository loss
--   and are reconstructed from the WP-5B-recovered forward migrations.
--   APPLY ORDER: rollbacks run in REVERSE (028 -> 001). Each reverses ONLY what its own migration
--   created and assumes later migrations are already rolled back. Plain DROP / RESTRICT are used
--   deliberately so out-of-order or on-populated-data application FAILS LOUDLY rather than
--   cascading silently — matching the 027/028 rollback precedent.

-- Migration 018 is an intentionally empty, retired placeholder (AGR-002 resolution): it performs
-- no action against the database (its original responsibilities were relocated to files 003 and
-- 011). Therefore its rollback is also a deliberate no-op. This file exists only to keep rollback
-- numbering continuous with the migration sequence. It creates/drops nothing.
SELECT 1;  -- no-op
