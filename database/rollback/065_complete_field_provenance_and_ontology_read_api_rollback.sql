DROP FUNCTION IF EXISTS public.get_dish_ontology_record(uuid,text);

DROP INDEX IF EXISTS public.dish_regional_affinities_source_record;
DROP INDEX IF EXISTS public.dish_constraints_source_record;
DROP INDEX IF EXISTS public.dish_ingredients_source_record;

ALTER TABLE food.nutrient_assertions DROP COLUMN IF EXISTS last_verified_at;
ALTER TABLE public.dish_name_synonyms
  DROP COLUMN IF EXISTS updated_at,
  DROP COLUMN IF EXISTS created_at,
  DROP COLUMN IF EXISTS last_verified_at,
  DROP COLUMN IF EXISTS review_status,
  DROP COLUMN IF EXISTS source_version,
  DROP COLUMN IF EXISTS extraction_method,
  DROP COLUMN IF EXISTS source_record_id;
ALTER TABLE public.dish_ingredients
  DROP CONSTRAINT IF EXISTS dish_ingredients_ml_model_name,
  DROP COLUMN IF EXISTS updated_at,
  DROP COLUMN IF EXISTS last_verified_at,
  DROP COLUMN IF EXISTS review_status,
  DROP COLUMN IF EXISTS confidence,
  DROP COLUMN IF EXISTS model_version,
  DROP COLUMN IF EXISTS model_name,
  DROP COLUMN IF EXISTS extraction_method,
  DROP COLUMN IF EXISTS source_url,
  DROP COLUMN IF EXISTS source_record_id,
  DROP COLUMN IF EXISTS source_type,
  DROP COLUMN IF EXISTS source_name;
ALTER TABLE public.dish_regional_affinities
  DROP CONSTRAINT IF EXISTS dish_regional_affinities_ml_model_name,
  DROP COLUMN IF EXISTS last_verified_at,
  DROP COLUMN IF EXISTS model_version,
  DROP COLUMN IF EXISTS model_name,
  DROP COLUMN IF EXISTS extraction_method,
  DROP COLUMN IF EXISTS source_url,
  DROP COLUMN IF EXISTS source_record_id;
ALTER TABLE public.dish_constraints
  DROP CONSTRAINT IF EXISTS dish_constraints_ml_model_name,
  DROP COLUMN IF EXISTS last_verified_at,
  DROP COLUMN IF EXISTS model_version,
  DROP COLUMN IF EXISTS model_name,
  DROP COLUMN IF EXISTS extraction_method,
  DROP COLUMN IF EXISTS source_url,
  DROP COLUMN IF EXISTS source_record_id;
ALTER TABLE public.dish_meal_class_mappings
  DROP COLUMN IF EXISTS last_verified_at,
  DROP COLUMN IF EXISTS source_record_id;
ALTER TABLE public.dish_taxonomy_assertions
  DROP COLUMN IF EXISTS last_verified_at,
  DROP COLUMN IF EXISTS source_version,
  DROP COLUMN IF EXISTS extraction_method;
