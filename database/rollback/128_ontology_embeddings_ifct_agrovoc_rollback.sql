-- Rollback for 128_ontology_embeddings_ifct_agrovoc.sql

DROP FUNCTION IF EXISTS public.match_ifct_nutrients(text, real);
DROP POLICY IF EXISTS ifct_nutrient_reference_public_read ON public.ifct_nutrient_reference;
DROP TABLE IF EXISTS public.ifct_nutrient_reference;

ALTER TABLE public.food_source_records DROP CONSTRAINT IF EXISTS food_source_records_provider_check;
ALTER TABLE public.food_source_records
  ADD CONSTRAINT food_source_records_provider_check
  CHECK (provider IN ('foodon_ols', 'usda_fdc'));

DROP FUNCTION IF EXISTS public.ai_enrichment_closed_vocabulary_by_embedding(extensions.vector, integer);

ALTER TABLE public.meal_classes DROP COLUMN IF EXISTS embedding;
ALTER TABLE public.cuisines DROP COLUMN IF EXISTS embedding;

-- vector extension left installed (other objects may depend on it by the time this runs); drop
-- manually only if confirmed unused elsewhere.
