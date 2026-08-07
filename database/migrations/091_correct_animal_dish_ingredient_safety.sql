-- Correct four authored animal dishes whose source ingredient lists omitted the animal itself.
-- The omission caused trigger-derived diet_type to become vegetarian and allowed unsafe serving.
SET client_min_messages = warning;
BEGIN;

INSERT INTO public.ingredients (
  name, is_veg, is_vegan, is_jain_excluded, allergen_flags, is_active
) VALUES
  ('duck', false, false, true, 0, true),
  ('clam', false, false, true, 8, true)
ON CONFLICT (name) DO UPDATE SET
  is_veg = excluded.is_veg,
  is_vegan = excluded.is_vegan,
  is_jain_excluded = excluded.is_jain_excluded,
  allergen_flags = excluded.allergen_flags,
  is_active = excluded.is_active;

WITH required(dish_name, ingredient_name) AS (
  VALUES
    ('Duck Curry (Assamese)', 'duck'),
    ('Eromba', 'fish_generic'),
    ('Singju', 'fish_generic'),
    ('Tisrya Masala', 'clam')
)
INSERT INTO public.dish_ingredients (dish_id, ingredient_id, is_main_ingredient)
SELECT d.id, i.id, true
FROM required r
JOIN public.dishes d ON d.name = r.dish_name
JOIN public.ingredients i ON i.name = r.ingredient_name
ON CONFLICT (dish_id, ingredient_id) DO UPDATE
SET is_main_ingredient = true;

DO $$
DECLARE
  v_missing integer;
  v_unsafe integer;
BEGIN
  SELECT count(*) INTO v_missing
  FROM (VALUES
    ('Duck Curry (Assamese)', 'duck'),
    ('Eromba', 'fish_generic'),
    ('Singju', 'fish_generic'),
    ('Tisrya Masala', 'clam')
  ) AS required(dish_name, ingredient_name)
  LEFT JOIN public.dishes d ON d.name = required.dish_name
  LEFT JOIN public.ingredients i ON i.name = required.ingredient_name
  LEFT JOIN public.dish_ingredients di
    ON di.dish_id = d.id AND di.ingredient_id = i.id AND di.is_main_ingredient
  WHERE di.dish_id IS NULL;

  SELECT count(*) INTO v_unsafe
  FROM public.dishes
  WHERE name IN ('Duck Curry (Assamese)', 'Eromba', 'Singju', 'Tisrya Masala')
    AND diet_type <> 'non_veg';

  IF v_missing <> 0 OR v_unsafe <> 0 THEN
    RAISE EXCEPTION 'animal dish safety correction failed: missing %, unsafe %',
      v_missing, v_unsafe;
  END IF;
END $$;

COMMIT;
