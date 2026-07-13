-- Migration: 028_weight_ladder_config_numeric_weights.sql
-- Implements: AGR-006 resolution — re_weight_ladder_config's weight columns were declared
--   `real` (float4) with an exact-equality CHECK (sum = 1.0). Binary floating-point cannot
--   represent several of the seed file's decimal literals exactly, and their rounding errors
--   do not cancel for the 'emerging' tier's specific combination
--   (0.20+0.25+0.35+0.15+0.05 evaluates to 0.999999940395355 under float4, confirmed live).
--   The seed data is mathematically correct in decimal arithmetic; the column type is not
--   suited to an exact-equality invariant.
-- Discovered: WP-4C execution, statement 1 of 23, 2026-07-09.
--
-- Root cause (confirmed via architecture review, not assumed): the defect is the PAIRING of
--   an exact-equality CHECK with a binary floating-point type — neither alone is the problem.
--   `real` is safe everywhere else in this schema (profiles.city_overlay_weight, user_re_state.
--   confidence_score, dish_tags.confidence all use `real` with range checks, which are immune
--   to rounding error). This table is the ONLY case in the entire schema pairing exact equality
--   with float4 — confirmed via a full repository + live-catalog audit.
--
-- Why NUMERIC and not a tolerance-based CHECK: these five columns represent a hand-authored,
--   normalized weight vector with NO acceptable margin of error by definition (DOC-P3-03 §16,
--   RE-DOC-03 §02) — not a measurement with inherent uncertainty. A tolerance/epsilon comparison
--   would introduce an arbitrary constant requiring its own justification, and this repository
--   has zero existing precedent for tolerance-based float comparison anywhere (confirmed via
--   audit). NUMERIC validates the authored data exactly, with no magic constant.
--
-- Lifecycle note (confirmed via RE-DOC-05 Evolution Roadmap, not assumed): these weights remain
--   business-owned, hand-tuned configuration through classfirst_v1/v2/v3. When true ML-learned
--   scoring arrives (ltr_v1, Phase 3), RE-DOC-05 explicitly states the hand-tuned-weight approach
--   is REPLACED, with trained parameters stored in a new, separate table (re_engine.model_
--   artifacts per DOC-P3-04 §12's Schema Evolution Strategy) — this table is never repurposed to
--   hold ML output. The exact-sum invariant is therefore not expected to ever need loosening.
--
-- NOTE (migration 024 precedent, corrected): an earlier draft of this fix cited migration 024's
--   use of `numeric` for re_dish_regional_affinity.affinity_score as precedent. On review, that
--   precedent does not actually apply — affinity_score is an independent bounded score validated
--   by a range check (BETWEEN 0 AND 1), immune to float rounding regardless of type, and carries
--   no sum invariant. This migration's justification rests entirely on the exact-sum-invariant
--   reasoning above, not on architectural consistency with migration 024.
--
-- Verified before writing this migration: table holds 0 rows (confirmed live) — no data
--   conversion risk. No view, trigger, function, or SQL-side consumer references these columns
--   anywhere in the live schema (confirmed via pg_proc scan) — the only in-database consumer is
--   the behavioral smoke test (904_behavioral_config_and_smoke_test.sql), which this migration
--   does not need to change.

ALTER TABLE re_engine.re_weight_ladder_config
  DROP CONSTRAINT re_weight_ladder_config_check;

ALTER TABLE re_engine.re_weight_ladder_config
  ALTER COLUMN w_cohort  TYPE numeric USING w_cohort::numeric,
  ALTER COLUMN w_content TYPE numeric USING w_content::numeric,
  ALTER COLUMN w_history TYPE numeric USING w_history::numeric,
  ALTER COLUMN w_context TYPE numeric USING w_context::numeric,
  ALTER COLUMN w_explore TYPE numeric USING w_explore::numeric;

ALTER TABLE re_engine.re_weight_ladder_config
  ADD CONSTRAINT re_weight_ladder_config_check
  CHECK (w_cohort + w_content + w_history + w_context + w_explore = 1.0);
