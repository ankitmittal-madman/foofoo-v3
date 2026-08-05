DROP TRIGGER IF EXISTS dish_name_synonyms_ai_quality_guard ON public.dish_name_synonyms;
DROP FUNCTION IF EXISTS public.guard_ai_dish_synonym();
DROP TRIGGER IF EXISTS dish_regional_affinities_groq_code_normalizer ON public.dish_regional_affinities;
DROP FUNCTION IF EXISTS public.normalize_groq_region_code();
