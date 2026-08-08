-- Deterministic, ingredient-text-derived safety-field correctness audit and confidence-gated
-- autocorrect for public.dishes. Additive only; does not touch catalogue publication (097/102).
--
-- Background: a manual sample review (2026-08-08) found that public.ingredients' own
-- is_veg/is_vegan/is_jain_excluded/allergen_flags columns are effectively unpopulated (12,033
-- rows, only 15 marked non-veg and 29 marked jain-excluded — e.g. "1 Chicken legs" is flagged
-- is_veg=true), so they cannot be used as a derivation source. Instead, these functions match
-- ingredient NAME TEXT (dish_ingredients -> ingredients.name, non-rejected rows only) against a
-- narrow, spot-checked keyword set. Two false-positive patterns were found and excluded during
-- verification: bare "meat" (matches "coconut meat", a vegan ingredient) and bare "goat" (matches
-- "goat cheese"/"goat milk", vegetarian dairy) — both are deliberately left out of the keyword
-- list below. 37 sampled matches were manually verified as true positives before this logic was
-- applied to production.
--
-- Only three kinds of correction are ever made, and all are conservative/one-directional:
--   1. is_jain: true -> false, only when an onion/garlic-family ingredient is present AND the
--      dish is not merely using asafoetida/hing (a jain-safe onion/garlic substitute).
--   2. diet_type: veg/vegan -> non_veg (if meat/seafood present) or -> egg (if egg present and no
--      meat/seafood) — never the reverse; a dish already marked non_veg/egg is never touched.
--   3. allergen_flags: bitwise OR only (nuts=1, fish=128) — existing bits are never cleared, and
--      no bit is ever removed based on absence of a keyword (absence of evidence is not evidence
--      of absence for allergens; this audit only ever closes under-flagging, never over-flags).
-- Nothing here touches ontology_status, meal-class mappings, taxonomy, or cuisine — those remain
-- governed by the existing dish-ontology Groq pipeline (supabase/functions/dish-ontology/), which
-- deliberately excludes safety fields from AI inference. This audit is the safety-field-specific,
-- non-AI complement to that pipeline, callable standalone and safe to schedule on every dish
-- (existing and future, published and unpublished).

CREATE SCHEMA IF NOT EXISTS re_engine;

CREATE OR REPLACE FUNCTION re_engine.dish_safety_field_violations()
RETURNS TABLE (
  dish_id uuid,
  dish_name text,
  violation text,
  current_value text,
  suggested_value text
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path TO 'public', 're_engine', 'pg_temp'
AS $$
  WITH dish_ing_text AS (
    SELECT di.dish_id, string_agg(lower(i.name), ' | ') AS ing_blob
    FROM public.dish_ingredients di
    JOIN public.ingredients i ON i.id = di.ingredient_id
    WHERE di.review_status <> 'rejected'
    GROUP BY di.dish_id
  ),
  flagged AS (
    SELECT
      d.id, d.name, d.diet_type, d.is_jain, d.allergen_flags,
      (t.ing_blob ~ '\y(onion|garlic|lahsun|pyaz)\y' AND t.ing_blob !~ 'asafoetida|hing') AS has_onion_garlic,
      (t.ing_blob ~ '\y(chicken|mutton|prawn|shrimp|crab|fish|beef|pork|lamb)\y') AS has_meat_or_seafood,
      (t.ing_blob ~ '\yegg\y' AND t.ing_blob !~ '\yeggplant\y') AS has_egg,
      (t.ing_blob ~ '\y(almond|badam|cashew|kaju|peanut|moongphali|walnut|pistachio)\y') AS has_nuts,
      (t.ing_blob ~ '\yfish\y') AS has_fish
    FROM public.dishes d
    JOIN dish_ing_text t ON t.dish_id = d.id
    WHERE d.is_active
  )
  SELECT id, name, 'is_jain_true_but_onion_garlic_present', is_jain::text, 'false'
  FROM flagged WHERE is_jain = true AND has_onion_garlic
  UNION ALL
  SELECT id, name, 'veg_diet_but_meat_or_seafood_present', diet_type, 'non_veg'
  FROM flagged WHERE diet_type IN ('veg', 'vegan') AND has_meat_or_seafood
  UNION ALL
  SELECT id, name, 'veg_diet_but_egg_present', diet_type, 'egg'
  FROM flagged WHERE diet_type IN ('veg', 'vegan') AND has_egg AND NOT has_meat_or_seafood
  UNION ALL
  SELECT id, name, 'nuts_present_but_allergen_not_flagged', coalesce(allergen_flags, 0)::text, (coalesce(allergen_flags, 0) | 1)::text
  FROM flagged WHERE has_nuts AND (coalesce(allergen_flags, 0) & 1) = 0
  UNION ALL
  SELECT id, name, 'fish_present_but_allergen_not_flagged', coalesce(allergen_flags, 0)::text, (coalesce(allergen_flags, 0) | 128)::text
  FROM flagged WHERE has_fish AND (coalesce(allergen_flags, 0) & 128) = 0;
$$;

COMMENT ON FUNCTION re_engine.dish_safety_field_violations() IS
  'Read-only. Every currently-active dish whose stored is_jain/diet_type/allergen_flags '
  'contradicts its own mapped ingredient text. One row per violation (a dish may appear more '
  'than once). Never guesses missing data — only flags contradictions against real ingredient '
  'text already in the DB. See migration 125 header for the exact keyword set and its two '
  'known-excluded false-positive patterns (bare "meat", bare "goat").';

CREATE OR REPLACE FUNCTION re_engine.dish_safety_field_autocorrect()
RETURNS TABLE (violation text, rows_corrected bigint)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO 'public', 're_engine', 'pg_temp'
AS $$
DECLARE
  n_jain bigint;
  n_nonveg bigint;
  n_egg bigint;
  n_allergen bigint;
BEGIN
  WITH v AS (
    SELECT f.dish_id FROM re_engine.dish_safety_field_violations() f
    WHERE f.violation = 'is_jain_true_but_onion_garlic_present'
  )
  UPDATE public.dishes d SET is_jain = false
  FROM v WHERE v.dish_id = d.id;
  GET DIAGNOSTICS n_jain = ROW_COUNT;

  WITH v AS (
    SELECT f.dish_id FROM re_engine.dish_safety_field_violations() f
    WHERE f.violation = 'veg_diet_but_meat_or_seafood_present'
  )
  UPDATE public.dishes d SET diet_type = 'non_veg'
  FROM v WHERE v.dish_id = d.id;
  GET DIAGNOSTICS n_nonveg = ROW_COUNT;

  WITH v AS (
    SELECT f.dish_id FROM re_engine.dish_safety_field_violations() f
    WHERE f.violation = 'veg_diet_but_egg_present'
  )
  UPDATE public.dishes d SET diet_type = 'egg'
  FROM v WHERE v.dish_id = d.id;
  GET DIAGNOSTICS n_egg = ROW_COUNT;

  WITH v AS (
    SELECT f.dish_id, bit_or(f.suggested_value::int) AS new_flags
    FROM re_engine.dish_safety_field_violations() f
    WHERE f.violation IN ('nuts_present_but_allergen_not_flagged', 'fish_present_but_allergen_not_flagged')
    GROUP BY f.dish_id
  )
  UPDATE public.dishes d SET allergen_flags = v.new_flags
  FROM v WHERE v.dish_id = d.id;
  GET DIAGNOSTICS n_allergen = ROW_COUNT;

  RETURN QUERY VALUES
    ('is_jain_corrected', n_jain),
    ('diet_type_corrected_to_non_veg', n_nonveg),
    ('diet_type_corrected_to_egg', n_egg),
    ('allergen_flags_corrected', n_allergen);
END;
$$;

COMMENT ON FUNCTION re_engine.dish_safety_field_autocorrect() IS
  'Applies re_engine.dish_safety_field_violations() corrections directly. Idempotent (running '
  'twice in a row corrects 0 rows the second time) and safe on every existing + future dish: '
  'only ever tightens is_jain/diet_type/allergen_flags to match already-present ingredient text, '
  'never invents ingredients or taxonomy. Intended to run on a schedule (e.g. alongside the '
  'dish-ontology cron) so newly-ingested dishes get the same safety check, not just the 2026-08-08 '
  'backlog. Call re_engine.dish_safety_field_violations() first to review before calling this.';

REVOKE ALL ON FUNCTION re_engine.dish_safety_field_violations() FROM PUBLIC;
REVOKE ALL ON FUNCTION re_engine.dish_safety_field_autocorrect() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION re_engine.dish_safety_field_violations() TO service_role, authenticated;
GRANT EXECUTE ON FUNCTION re_engine.dish_safety_field_autocorrect() TO service_role;

-- PostgREST only exposes the `public` schema by default; supabase/functions/cron-dish-ontology
-- calls RPCs through the Supabase JS client (db.rpc(...)), so the re_engine function above needs
-- a public-schema wrapper to be callable from there.
CREATE OR REPLACE FUNCTION public.dish_safety_field_autocorrect()
RETURNS TABLE (violation text, rows_corrected bigint)
LANGUAGE sql
SECURITY DEFINER
SET search_path TO 'public', 're_engine', 'pg_temp'
AS $$
  SELECT * FROM re_engine.dish_safety_field_autocorrect();
$$;

COMMENT ON FUNCTION public.dish_safety_field_autocorrect() IS
  'PostgREST-reachable wrapper for re_engine.dish_safety_field_autocorrect(). Called by '
  'supabase/functions/cron-dish-ontology on every scheduled run so newly-ingested and existing '
  'dishes both get the deterministic is_jain/diet_type/allergen_flags correctness check, not just '
  'the 2026-08-08 backlog pass.';

REVOKE ALL ON FUNCTION public.dish_safety_field_autocorrect() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.dish_safety_field_autocorrect() TO service_role;
