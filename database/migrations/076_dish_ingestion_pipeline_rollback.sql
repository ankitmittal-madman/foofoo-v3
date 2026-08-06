-- Rollback: 076_dish_ingestion_pipeline_rollback.sql
-- Reverses 076_dish_ingestion_pipeline.sql. Drops only tables created by that migration;
-- touches nothing pre-existing (dishes, dish_ingredients, dish_tags, cuisines, meal_classes,
-- dish_regional_affinities, dish_name_synonyms, dish_enrichment_jobs, dish_taxonomy_assertions,
-- food_source_records are all untouched).

DROP TABLE IF EXISTS public.dish_images CASCADE;
DROP TABLE IF EXISTS public.image_assets CASCADE;
DROP TABLE IF EXISTS public.dish_aliases CASCADE;
DROP TABLE IF EXISTS public.dish_ingestion_review_queue CASCADE;
DROP TABLE IF EXISTS public.import_row_errors CASCADE;
DROP TABLE IF EXISTS public.import_row_results CASCADE;
DROP TABLE IF EXISTS public.dish_source_rows CASCADE;
DROP TABLE IF EXISTS public.import_runs CASCADE;
