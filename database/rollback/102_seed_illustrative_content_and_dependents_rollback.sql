-- Rollback: 102_seed_illustrative_content_and_dependents_rollback.sql
-- Reverses exactly the illustrative rows 102_seed_illustrative_content_and_dependents.sql
-- inserted. Scoped by natural key / the same subqueries the seed itself used, not a blanket
-- DELETE FROM. Deleted in strict child-before-parent order so every FK-dependent row is gone
-- before its parent (dishes, ingredients, re_cohorts, re_personas) is removed.
--
-- IMPORTANT — like every rollback in this repo, apply in strict reverse numeric order: seeds
-- 103-121 (the real, non-illustrative seed pipeline) reference the dishes/re_cohorts/re_personas
-- rows this file inserts (e.g. 117_seed_re_dish_linked_icd1.sql adds further re_class_dish_options
-- rows against the same meal classes). Roll back 121 down through 103 first, in that order, before
-- running this file — verified live (2026-07-30) that running it out of order fails on a foreign-
-- key violation, which is correct protective behavior, not a bug in this script.
BEGIN;

DELETE FROM re_engine.re_household_addon_plans
WHERE addon_class_code = 'ADDON_INFANT'
  AND cohort_id IN (
    SELECT c.cohort_id FROM re_engine.re_cohorts c
    JOIN re_engine.re_personas p ON p.id = c.persona_id
    WHERE p.persona_code = 'MC3_NORTH_VEG' AND c.state_code = 'MP'
  );

DELETE FROM re_engine.re_weekly_class_plans
WHERE day_of_week = 'monday'
  AND cohort_id IN (
    SELECT c.cohort_id FROM re_engine.re_cohorts c
    JOIN re_engine.re_personas p ON p.id = c.persona_id
    WHERE p.persona_code = 'MC3_NORTH_VEG' AND c.state_code = 'MP'
  );

DELETE FROM re_engine.re_addon_dish_options
WHERE addon_class_code = 'ADDON_INFANT'
  AND dish_id IN (SELECT id FROM public.dishes WHERE name = 'Poha');

DELETE FROM re_engine.re_class_dish_options
WHERE (meal_class_code, dish_id) IN (
  SELECT 'BF_LIGHT_GRAIN', id FROM public.dishes WHERE name = 'Poha'
  UNION ALL
  SELECT 'BF_LIGHT_GRAIN', id FROM public.dishes WHERE name = 'Aloo Poha with Peanuts'
  UNION ALL
  SELECT 'DIN_NON_VEG_MAIN', id FROM public.dishes WHERE name = 'Butter Chicken'
);

DELETE FROM re_engine.re_cohorts
WHERE (persona_id, state_code) IN (
  SELECT p.id, 'MP' FROM re_engine.re_personas p WHERE p.persona_code = 'MC3_NORTH_VEG'
  UNION ALL
  SELECT p.id, 'TN' FROM re_engine.re_personas p WHERE p.persona_code = 'MC3_SOUTH_VEG'
);

DELETE FROM public.dish_ingredients
WHERE dish_id IN (
  SELECT id FROM public.dishes WHERE name IN ('Poha', 'Aloo Poha with Peanuts', 'Butter Chicken')
);

-- 102's own header states these dishes exist specifically to give file 902's trigger-behavioral
-- test (fn_derive_dish_attributes) something live to exercise — any derivation_conflicts row
-- logged against them is therefore a byproduct of 102's own existence, not independent
-- operational data, and is in-scope to remove here so the FK doesn't block dish deletion.
DELETE FROM public.derivation_conflicts
WHERE dish_id IN (
  SELECT id FROM public.dishes WHERE name IN ('Poha', 'Aloo Poha with Peanuts', 'Butter Chicken')
);

DELETE FROM public.dishes
WHERE name IN ('Poha', 'Aloo Poha with Peanuts', 'Butter Chicken');

DELETE FROM public.ingredients
WHERE name IN (
  'Poha (flattened rice)', 'Onion', 'Mustard seeds', 'Peanuts', 'Turmeric', 'Potato', 'Ghee', 'Chicken'
);

COMMIT;
