-- Rollback: 121_ghar_re_golden_sample.sql — remove the golden SAMPLE (ai_generated) rows.
BEGIN;
UPDATE ghar_re.comfort_hero_map SET dish_id = NULL;   -- unlink golden dishes
DELETE FROM ghar_re.dish_variants        WHERE data_source='ai_generated';
DELETE FROM ghar_re.region_food_affinity WHERE data_source='ai_generated';
DELETE FROM ghar_re.sig_scores           WHERE data_source='ai_generated';
DELETE FROM ghar_re.dish_macro           WHERE data_source='ai_generated';
DELETE FROM ghar_re.dish_name_synonyms   WHERE data_source='ai_generated';
DELETE FROM ghar_re.dish_ingredients     WHERE data_source='ai_generated';
DELETE FROM ghar_re.household_modes       WHERE data_source='ai_generated';
DELETE FROM ghar_re.households            WHERE data_source='ai_generated';
DELETE FROM ghar_re.dishes                WHERE data_source='ai_generated';
COMMIT;
