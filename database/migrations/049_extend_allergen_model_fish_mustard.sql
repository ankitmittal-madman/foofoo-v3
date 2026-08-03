-- 049_extend_allergen_model_fish_mustard.sql
-- Provenance: DOC-P3-03 §07 line 163 froze a 7-bit allergen model (bits 0-6) with fish/mustard
-- explicitly left unmapped as a "safety-scope decision, deferred" (database/etl/generate_icd1_seeds.py).
-- WP-21 (production hardening audit) flagged this as a real safety gap: households with fish or
-- mustard allergies had no way to have those excluded, even though data/source/ingredients_v5.csv
-- already tags 8 ingredients with allergen_type in {fish, mustard} (verified directly against the
-- source CSV, not guessed) — the source data was correct, only the bitmask never had room for it.
-- This migration extends the model to 9 bits (128 = fish, 256 = mustard) and backfills
-- allergen_flags for exactly those 8 already-seeded ingredient rows.
--
-- profiles.allergen_flags / household_members.allergen_flags / public.dishes.allergen_flags are all
-- plain `integer` columns (32-bit) — no schema change needed. Companion application-code changes
-- (onboarding chip list, ETL generator ALLERGEN_BIT map, compose.ts decode map) are in the same
-- WP-21 change set.
--
-- Idempotency: only sets the bit where not already set; re-runnable, no-op on a second run.
-- Paired _rollback.sql clears just these two bits.
SET client_min_messages = warning;
BEGIN;

-- fish (bit 7 = 128) — 6 ingredients tagged allergen_type='fish' in ingredients_v5.csv
UPDATE public.ingredients
SET allergen_flags = allergen_flags | 128
WHERE name IN ('fish_generic', 'pomfret', 'rohu', 'hilsa', 'surmai', 'bangda')
  AND (allergen_flags & 128) = 0;

-- mustard (bit 8 = 256) — 2 ingredients tagged allergen_type='mustard' in ingredients_v5.csv
UPDATE public.ingredients
SET allergen_flags = allergen_flags | 256
WHERE name IN ('mustard_seeds', 'mustard_oil')
  AND (allergen_flags & 256) = 0;

COMMIT;
