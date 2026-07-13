-- Migration: 102_seed_illustrative_content_and_dependents.sql
-- Implements: DOC-P3-04 v1.3 §03.5/03.6/03.7/03.9 (ingredients, dishes, dish_ingredients,
--   dish_tags), §03.27 (re_class_dish_options, re_cohorts, re_weekly_class_plans,
--   re_household_addon_plans, re_addon_dish_options)
-- Logical functions: LF-K01 (derivation trigger exercise), LF-D01 (class candidates),
--   LF-B02 (class plan), LF-C01/C02 (addon resolution)
-- *** IDR-001 APPLIES *** — same standing reason as file 101. DOC-04's NFR specifies 500+
-- dishes fully tagged before launch; that content set does not exist in project files either.
-- The handful of dishes below exist solely to give files 101's illustrative reference rows
-- something real to point at, and to give file 902 (trigger behavioral test) a live dish to
-- exercise fn_derive_dish_attributes() and fn_propagate_ingredient_change() against.

-- Minimal ingredient set (ground truth, per CDM Invariant 6 — these ARE real, correct facts
-- about these specific ingredients, not placeholders; only the SET is incomplete)
INSERT INTO public.ingredients (name, allergen_flags, is_veg, is_vegan, is_jain_excluded) VALUES
  ('Poha (flattened rice)', 0, true, true, false),
  ('Onion', 0, true, true, true),
  ('Mustard seeds', 0, true, true, false),
  ('Peanuts', 1, true, true, false),
  ('Turmeric', 0, true, true, false),
  ('Potato', 0, true, true, true),
  ('Ghee', 2, true, false, false),
  ('Chicken', 0, false, false, false);

-- Two illustrative dishes — note diet_type/is_jain/allergen_flags are deliberately omitted
-- below; they MUST be left for the trigger to compute (this is the entire point of the
-- behavioral test in file 902 — manually inserting these would defeat the test).
INSERT INTO public.dishes (name, meal_occasion, cook_time_minutes, difficulty) VALUES
  ('Poha', ARRAY['breakfast'], 15, 'beginner'),
  ('Aloo Poha with Peanuts', ARRAY['breakfast'], 20, 'beginner'),
  ('Butter Chicken', ARRAY['dinner'], 45, 'intermediate');

-- Link ingredients to dishes — THIS is what fires trg_derive_dish_attributes (file 010/1.1)
INSERT INTO public.dish_ingredients (dish_id, ingredient_id)
SELECT d.id, i.id FROM public.dishes d, public.ingredients i
WHERE d.name = 'Poha' AND i.name IN ('Poha (flattened rice)', 'Onion', 'Mustard seeds', 'Turmeric');

INSERT INTO public.dish_ingredients (dish_id, ingredient_id)
SELECT d.id, i.id FROM public.dishes d, public.ingredients i
WHERE d.name = 'Aloo Poha with Peanuts'
  AND i.name IN ('Poha (flattened rice)', 'Potato', 'Peanuts', 'Mustard seeds');

INSERT INTO public.dish_ingredients (dish_id, ingredient_id)
SELECT d.id, i.id FROM public.dishes d, public.ingredients i
WHERE d.name = 'Butter Chicken' AND i.name IN ('Chicken', 'Ghee', 'Onion');

-- S-08: re_class_dish_options — illustrative (target: 1,050)
INSERT INTO re_engine.re_class_dish_options (meal_class_code, dish_id, base_score, is_primary_candidate)
SELECT 'BF_LIGHT_GRAIN', id, 0.85, true FROM public.dishes WHERE name = 'Poha';
INSERT INTO re_engine.re_class_dish_options (meal_class_code, dish_id, base_score, is_primary_candidate)
SELECT 'BF_LIGHT_GRAIN', id, 0.70, false FROM public.dishes WHERE name = 'Aloo Poha with Peanuts';
INSERT INTO re_engine.re_class_dish_options (meal_class_code, dish_id, base_score, is_primary_candidate)
SELECT 'DIN_NON_VEG_MAIN', id, 0.80, true FROM public.dishes WHERE name = 'Butter Chicken';
-- AWAITING SOURCE DATA: 1,047 remaining class-dish option rows.

-- S-11: re_cohorts — illustrative (target: 2,952-2,953)
INSERT INTO re_engine.re_cohorts (persona_id, state_code, diet_mode, prior_weight)
SELECT p.id, 'MP', 'veg', 1.0 FROM re_engine.re_personas p WHERE p.persona_code = 'MC3_NORTH_VEG';
INSERT INTO re_engine.re_cohorts (persona_id, state_code, diet_mode, prior_weight)
SELECT p.id, 'TN', 'veg', 1.0 FROM re_engine.re_personas p WHERE p.persona_code = 'MC3_SOUTH_VEG';
-- AWAITING SOURCE DATA: 2,950 remaining cohort rows.

-- S-12: re_weekly_class_plans — illustrative (target: 20,664)
INSERT INTO re_engine.re_weekly_class_plans
  (cohort_id, day_of_week, breakfast_class_code, lunch_class_code, dinner_class_code)
SELECT c.cohort_id, 'monday', 'BF_LIGHT_GRAIN', 'LUNCH_DAL_SABZI_ROTI', 'DIN_CURRY_ROTI'
FROM re_engine.re_cohorts c
JOIN re_engine.re_personas p ON p.id = c.persona_id
WHERE p.persona_code = 'MC3_NORTH_VEG' AND c.state_code = 'MP';
-- AWAITING SOURCE DATA: 20,663 remaining weekly plan rows (6 remaining days x all cohorts).

-- S-13: re_household_addon_plans — illustrative (target: 7,992)
INSERT INTO re_engine.re_household_addon_plans (segment, cohort_id, addon_class_code)
SELECT 'INFANT', c.cohort_id, 'ADDON_INFANT'
FROM re_engine.re_cohorts c
JOIN re_engine.re_personas p ON p.id = c.persona_id
WHERE p.persona_code = 'MC3_NORTH_VEG' AND c.state_code = 'MP';
-- AWAITING SOURCE DATA: 7,991 remaining addon plan rows.

-- S-10: re_addon_dish_options — illustrative (target: 142-143)
INSERT INTO re_engine.re_addon_dish_options (addon_class_code, dish_id, suitability_rank)
SELECT 'ADDON_INFANT', id, 1 FROM public.dishes WHERE name = 'Poha';
-- AWAITING SOURCE DATA: 141 remaining addon dish option rows.
