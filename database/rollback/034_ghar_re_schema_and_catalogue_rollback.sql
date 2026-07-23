-- Rollback: 034_ghar_re_schema_and_catalogue.sql
DROP TABLE IF EXISTS ghar_re.community_priors;
DROP TABLE IF EXISTS ghar_re.region_food_affinity;
DROP TABLE IF EXISTS ghar_re.dish_combo_items;
DROP TABLE IF EXISTS ghar_re.dish_combos;
DROP TABLE IF EXISTS ghar_re.tags;
DROP TABLE IF EXISTS ghar_re.dish_name_synonyms;
DROP TABLE IF EXISTS ghar_re.ingredient_aliases;
DROP TABLE IF EXISTS ghar_re.dish_ingredients;
DROP TABLE IF EXISTS ghar_re.ingredients;
DROP TABLE IF EXISTS ghar_re.dishes;
DROP TABLE IF EXISTS ghar_re.cuisines;
DROP TABLE IF EXISTS ghar_re.cuisine_groups;
DROP TYPE  IF EXISTS ghar_re.data_source_kind;
-- schema left in place if other objects exist; drop explicitly if fully tearing down:
-- DROP SCHEMA IF EXISTS ghar_re CASCADE;
