-- Roll back migration 056. This removes ontology/enrichment data but never deletes canonical dishes.
DROP VIEW IF EXISTS public.dish_taxonomy_review_queue;
DROP VIEW IF EXISTS public.dish_ontology_coverage;
DROP VIEW IF EXISTS public.dish_candidates_by_class;
DROP TRIGGER IF EXISTS dish_taxonomy_current_integrity_guard ON public.dish_taxonomy_current;
DROP FUNCTION IF EXISTS public.validate_current_taxonomy_assertion();
DROP TRIGGER IF EXISTS dish_taxonomy_current_guard ON public.dish_taxonomy_current;
DROP FUNCTION IF EXISTS public.protect_reviewed_taxonomy_value();
DROP TRIGGER IF EXISTS dish_meal_class_role_guard ON public.dish_meal_class_mappings;
DROP FUNCTION IF EXISTS public.validate_dish_class_role();
DROP TRIGGER IF EXISTS dish_submissions_queue_enrichment ON public.dish_submissions;
DROP FUNCTION IF EXISTS public.create_submission_enrichment_job();
DROP TRIGGER IF EXISTS dishes_queue_ontology_enrichment ON public.dishes;
DROP FUNCTION IF EXISTS public.create_dish_enrichment_job();
DROP TRIGGER IF EXISTS dishes_mark_ontology_pending ON public.dishes;
DROP FUNCTION IF EXISTS public.enqueue_dish_enrichment();
ALTER TABLE public.dishes
  DROP COLUMN IF EXISTS ontology_last_reviewed_at,
  DROP COLUMN IF EXISTS ontology_confidence,
  DROP COLUMN IF EXISTS ontology_status;
DROP TABLE IF EXISTS public.dish_regional_affinities;
DROP TABLE IF EXISTS public.dish_constraints;
DROP TABLE IF EXISTS public.dish_meal_class_mappings;
DROP TABLE IF EXISTS public.dish_taxonomy_current;
DROP TABLE IF EXISTS public.dish_taxonomy_assertions;
DROP TABLE IF EXISTS public.dish_enrichment_jobs;
DROP TABLE IF EXISTS public.food_source_records;
DROP TABLE IF EXISTS public.dish_submissions;
DROP TABLE IF EXISTS public.taxonomy_term_aliases;
DROP TABLE IF EXISTS public.taxonomy_terms;
ALTER TABLE public.meal_classes DROP CONSTRAINT IF EXISTS meal_classes_family_fkey;
ALTER TABLE public.meal_classes
  DROP COLUMN IF EXISTS weekend_fit_1_5,
  DROP COLUMN IF EXISTS weekday_fit_1_5,
  DROP COLUMN IF EXISTS planning_role,
  DROP COLUMN IF EXISTS class_family_code,
  DROP COLUMN IF EXISTS parent_class_code;
DROP TABLE IF EXISTS public.meal_class_families;
