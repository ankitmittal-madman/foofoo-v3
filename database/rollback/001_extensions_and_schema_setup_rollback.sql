-- Rollback: 001_extensions_and_schema_setup_rollback.sql
-- Reverses: 001_extensions_and_schema_setup.sql
-- RECONSTRUCTED FROM EVIDENCE (WP-5C Rollback Recovery, 2026-07-13).
--   Source of truth: the forward migration file 001_extensions_and_schema_setup.sql (the authoritative record of exactly what
--   this migration created). No original rollback existed for 001-020 (never authored — see
--   REPO-WP-02 discovery); the 021-026 rollbacks were lost in the apverse-labs repository loss
--   and are reconstructed from the WP-5B-recovered forward migrations.
--   APPLY ORDER: rollbacks run in REVERSE (028 -> 001). Each reverses ONLY what its own migration
--   created and assumes later migrations are already rolled back. Plain DROP / RESTRICT are used
--   deliberately so out-of-order or on-populated-data application FAILS LOUDLY rather than
--   cascading silently — matching the 027/028 rollback precedent.
--
-- WARNING: DROP SCHEMA ... RESTRICT will fail loudly if any re_engine object still exists
--   (i.e. if migrations 002-026 have not been rolled back first) — this is intended.
--   DROP EXTENSION pgcrypto: on PostgreSQL 13+ gen_random_uuid() is a core function, so removing
--   pgcrypto is usually harmless; IF EXISTS guards the case where it was never actually installed
--   as an extension. Review before running on a shared database.

-- Reverse the default privileges and grants, then drop the (now-empty) schema and extension.
ALTER DEFAULT PRIVILEGES IN SCHEMA re_engine REVOKE ALL ON TABLES FROM service_role;
REVOKE ALL ON ALL TABLES IN SCHEMA re_engine FROM service_role;
REVOKE USAGE ON SCHEMA re_engine FROM service_role;
DROP SCHEMA re_engine RESTRICT;
DROP EXTENSION IF EXISTS pgcrypto;
