DO $$
DECLARE
  v_missing integer;
  v_unsafe integer;
  v_shellfish_missing integer;
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

  SELECT count(*) INTO v_shellfish_missing
  FROM public.dishes
  WHERE name = 'Tisrya Masala' AND (allergen_flags & 8) = 0;

  IF v_missing <> 0 OR v_unsafe <> 0 OR v_shellfish_missing <> 0 THEN
    RAISE EXCEPTION 'animal dish validation failed: missing %, unsafe %, shellfish %',
      v_missing, v_unsafe, v_shellfish_missing;
  END IF;
END $$;

SELECT name, diet_type, is_jain, allergen_flags
FROM public.dishes
WHERE name IN ('Duck Curry (Assamese)', 'Eromba', 'Singju', 'Tisrya Masala')
ORDER BY name;
