-- Rollback: 120_ghar_re_kb_reference.sql — remove the KB/reference rows.
-- (Run AFTER 121 rollback, since golden dishes FK-reference these ingredients/cuisines.)
BEGIN;
DELETE FROM ghar_re.ingredient_normalization_map;
DELETE FROM ghar_re.community_priors;
DELETE FROM ghar_re.prior_zone_slot_season;
DELETE FROM ghar_re.negative_priors;
DELETE FROM ghar_re.sig_score_bands;
DELETE FROM ghar_re.comfort_hero_map;
DELETE FROM ghar_re.zone_map;
DELETE FROM ghar_re.dish_ingredients;   -- any remaining links to reference ingredients
DELETE FROM ghar_re.ingredients;
DELETE FROM ghar_re.tags;
DELETE FROM ghar_re.cuisines;
DELETE FROM ghar_re.cuisine_groups;
COMMIT;
