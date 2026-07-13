-- Migration: 001_extensions_and_schema_setup.sql
-- Implements: DOC-P3-04 v1.2 §03.26 (re_engine schema creation and lockdown)
-- Logical functions: (foundational — required by all LF-numbers that touch re_engine)
-- Governance refs: DOC-P3-05 Part (a) Phase 7 (no prerequisite — first file), Phase 13 (Environment Assumptions: pgcrypto required)
-- CDM entities: Aggregate 6 (Reference Data), Aggregate 2 (RE Identity) — schema boundary enforcing CDM ownership separation
-- CDM invariants enforced: none directly (this file establishes the privilege boundary other invariants depend on)

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS re_engine;

REVOKE ALL ON SCHEMA re_engine FROM PUBLIC, anon, authenticated;
GRANT USAGE ON SCHEMA re_engine TO service_role;
GRANT ALL ON ALL TABLES IN SCHEMA re_engine TO service_role;

-- Note: the GRANT ALL ON ALL TABLES above applies only to tables that already exist at the
-- time this statement runs. Files 002-007/013-014/016 (which create re_engine tables) must each
-- re-issue an equivalent GRANT for their own new tables, OR this project relies on Postgres's
-- ALTER DEFAULT PRIVILEGES mechanism set up here so all *future* tables in this schema inherit
-- the grant automatically. The latter is the production-safe approach and is used below.
ALTER DEFAULT PRIVILEGES IN SCHEMA re_engine GRANT ALL ON TABLES TO service_role;
