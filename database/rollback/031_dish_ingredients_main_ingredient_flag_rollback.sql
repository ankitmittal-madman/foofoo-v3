-- Rollback: 031_dish_ingredients_main_ingredient_flag_rollback.sql
-- Reverses: 031_dish_ingredients_main_ingredient_flag.sql
-- Safe at any time before downstream code (CandidateRepository.mainIngredientClass) is built
--   and reads this column — as of this migration's authoring, nothing does. No data or code
--   depends on is_main_ingredient yet.

ALTER TABLE public.dish_ingredients
  DROP COLUMN is_main_ingredient;
