-- 050_drop_unused_ghar_re_schema.sql
-- WP-21 (production hardening audit): the `ghar_re` Postgres schema (28 tables, built across
-- migrations 034-037 and 045: catalogue/dishes/ingredients, household runtime mirrors, knowledge
-- base, dish-ontology synonyms) is confirmed unread by any currently-deployed runtime code.
--
-- Verified before writing this migration (not assumed):
--   - supabase/functions/recommendations/compose.ts and supabase/functions/household/store.ts
--     both explicitly state and were grepped to confirm they read `public.*` only, never `ghar_re.*`.
--   - ghar_re_service (the live deployed RE process on Fly.io) reads dishes.xlsx/YAML bundles via
--     ghar_re_core, never Postgres — the `ghar_re` name-collision in its own Python package name is
--     unrelated to the Postgres schema of the same name.
--   - mobile app has zero references to `ghar_re.*`.
--   - Only database/validation/906_ghar_re_validation.sql and 907_dish_ontology_validation.sql read
--     this schema, and only to validate its own internal consistency (data_source provenance,
--     dish_name_synonyms evidence integrity) — dropped alongside since they'd have nothing left to
--     validate.
--
-- This schema held real, citation-backed curated data (not fake/fixture data) — Founder decision
-- was to drop rather than keep as unused groundwork; no live code path depended on it.
SET client_min_messages = warning;
BEGIN;

DROP SCHEMA IF EXISTS ghar_re CASCADE;

COMMIT;
