-- Immediate rollback only: restores the pre-091 ingredient associations and derived dish fields.
SET client_min_messages = warning;
BEGIN;

DELETE FROM public.dish_ingredients di
USING public.dishes d, public.ingredients i
WHERE di.dish_id = d.id
  AND di.ingredient_id = i.id
  AND (d.name, i.name) IN (
    ('Duck Curry (Assamese)', 'duck'),
    ('Eromba', 'fish_generic'),
    ('Singju', 'fish_generic'),
    ('Tisrya Masala', 'clam')
  );

DELETE FROM public.ingredients i
WHERE i.name IN ('duck', 'clam')
  AND NOT EXISTS (
    SELECT 1 FROM public.dish_ingredients di WHERE di.ingredient_id = i.id
  );

COMMIT;
