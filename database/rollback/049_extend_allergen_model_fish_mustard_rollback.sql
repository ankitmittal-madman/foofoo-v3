-- Rollback 049 — clear the fish/mustard allergen bits added by 049_extend_allergen_model_fish_mustard.sql
-- Does not restore any application-code changes (onboarding chips, ETL map, compose.ts decode) —
-- those must be reverted separately if this migration is rolled back.
SET client_min_messages = warning;
BEGIN;

UPDATE public.ingredients
SET allergen_flags = allergen_flags & ~128
WHERE name IN ('fish_generic', 'pomfret', 'rohu', 'hilsa', 'surmai', 'bangda');

UPDATE public.ingredients
SET allergen_flags = allergen_flags & ~256
WHERE name IN ('mustard_seeds', 'mustard_oil');

COMMIT;
