-- Rollback for 127_trim_ai_enrichment_vocabulary_prompt.sql.
-- Restores the unfiltered zero-arg ai_enrichment_closed_vocabulary() from migration 126.

DROP FUNCTION IF EXISTS public.ai_enrichment_closed_vocabulary(text);

CREATE OR REPLACE FUNCTION public.ai_enrichment_closed_vocabulary()
RETURNS jsonb
LANGUAGE sql STABLE SECURITY DEFINER SET search_path=public,pg_temp
AS $$
  SELECT jsonb_build_object(
    'class_codes', coalesce((SELECT jsonb_agg(class_code ORDER BY class_code) FROM public.meal_classes WHERE is_active), '[]'::jsonb),
    'cuisine_names', coalesce((SELECT jsonb_agg(name ORDER BY name) FROM public.cuisines), '[]'::jsonb)
  );
$$;

COMMENT ON FUNCTION public.ai_enrichment_closed_vocabulary() IS
  'Live class_code/cuisine name lists for the dish-ontology Groq prompt (ai.ts ClosedVocabulary). '
  'Always reflects the current public.meal_classes/public.cuisines rows — never hardcoded in '
  'application code, since those tables can gain or lose rows independently of a deploy.';

REVOKE ALL ON FUNCTION public.ai_enrichment_closed_vocabulary() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.ai_enrichment_closed_vocabulary() TO service_role;
