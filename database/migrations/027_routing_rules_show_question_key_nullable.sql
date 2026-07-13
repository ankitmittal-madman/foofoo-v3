-- Migration: 027_routing_rules_show_question_key_nullable.sql
-- Implements: AGR-005 resolution — re_engine.re_routing_rules.show_question_key incorrectly
--   specified NOT NULL in migration 003 (DOC-P3-04 v1.3 §03.27), contradicting the authoritative
--   8-row dataset in 101_seed_reference_data_framework.sql (DOC-P3-03 §03 LF-A02, marked
--   "COMPLETE, no IDR" — i.e. design intent, not placeholder data).
-- Discovered: WP-4B execution, statement 3 of 10, 2026-07-09 — ERROR 23502 on the first
--   "skip rule" row (MC_SOLO), which by design shows no question and therefore has no
--   non-null value to put in show_question_key.
-- Governance refs: DOC-P3-05 Part (a) v1.2 §06E persistence rule — this migration corrects a
--   frozen DDL file's column constraint; DOC-P3-04 v1.4 receives a corresponding additive
--   amendment (this migration's forward file is the canonical record of the change itself).
-- Logical functions: LF-A02 (BUILD-02 dynamic onboarding) — re_routing_rules rows encode two
--   distinct rule shapes: "show a question" (show_question_key populated, skip_if_answered
--   NULL) and "skip questions" (show_question_key NULL, skip_if_answered populated). The
--   original NOT NULL made the second shape unrepresentable, even though 4 of the 8
--   authoritative rows are exactly that shape.
--
-- Why DROP NOT NULL alone is insufficient, and what replaces it:
-- A bare DROP NOT NULL would permit a row with BOTH columns null — a rule that neither shows
-- a question nor skips one, which is not a valid rule under LF-A02 and would silently produce
-- a routing no-op BUILD-02 could not detect. The replacement CHECK enforces the actual
-- invariant this table exists to guarantee: every rule does at least one of the two things.
-- This is stricter integrity than the original NOT NULL, not merely a relaxation of it.
--
-- Verified before writing this migration: no view, trigger, function, or index references
-- show_question_key's nullability directly (catalog-scanned per the WP-3A/WP-3B discovery
-- method); table is unseeded at 003/025/026 execution time and, at the moment this migration
-- is authored, holds exactly 0 rows in re_routing_rules (re_states: 6, re_main_cohorts: 5
-- loaded from WP-4B statements 1-2; re_routing_rules itself still 0 following the atomic
-- rejection) — so no existing data requires migration, only the constraint shape changes.

ALTER TABLE re_engine.re_routing_rules
  ALTER COLUMN show_question_key DROP NOT NULL;

ALTER TABLE re_engine.re_routing_rules
  ADD CONSTRAINT re_routing_rules_action_check
  CHECK (show_question_key IS NOT NULL OR skip_if_answered IS NOT NULL);
