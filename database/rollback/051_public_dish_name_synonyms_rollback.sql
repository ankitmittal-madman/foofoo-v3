-- Rollback: 051_public_dish_name_synonyms.sql
-- Drops the alias table added for WP-19 (retargeted). public.dishes itself is untouched.

DROP TABLE IF EXISTS public.dish_name_synonyms;
