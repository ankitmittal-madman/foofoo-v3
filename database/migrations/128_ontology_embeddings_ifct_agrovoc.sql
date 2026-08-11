-- Adds three independent capabilities requested by the Founder to make the food ontology
-- richer using only free/open sources, and to give the Groq vocabulary trim (migration 127) a
-- semantic alternative to its current ILIKE word-overlap heuristic:
--
-- 1. pgvector embedding columns on meal_classes/cuisines + a cosine-similarity vocabulary
--    function. Word-overlap (migration 127) misses dishes whose class shares no literal word
--    with the dish name (its own example: "Dry Sweet Potato Thoran" vs LD_SIMPLE_GREEN_VEG_SABZI).
--    Embeddings are populated separately by a one-time backfill Edge Function using the Supabase
--    Edge Runtime's built-in local `gte-small` model (free, no API key, no rate limit — this is
--    the correct free-local-embedding primitive for this Deno stack, not a Python
--    sentence-transformers install, which has no runtime home in an Edge Function). Until that
--    backfill runs, embedding columns are NULL and ai_enrichment_closed_vocabulary_by_embedding
--    returns NULL so the caller falls back to migration 127's existing function untouched.
-- 2. food_source_records.provider CHECK widened to accept 'ifct' and 'agrovoc' (existing values
--    'foodon_ols','usda_fdc' from migration 070 kept unchanged).
-- 3. ifct_nutrient_reference: schema only. IFCT (Indian Food Composition Tables, ICMR-NIN) has no
--    free public API — it is distributed as a static dataset. Per this repo's rule against
--    fabricating content that wasn't actually provided, no nutrient rows are seeded here; loading
--    real IFCT figures requires the Founder supplying the actual dataset file as a numbered seed
--    (1NN_ band) in a follow-up migration. match_ifct_nutrients is trigram-based (pg_trgm, already
--    installed) so it works the moment real rows exist, with zero further code changes.

CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA extensions;
CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA extensions;

ALTER TABLE public.meal_classes ADD COLUMN IF NOT EXISTS embedding extensions.vector(384);
ALTER TABLE public.cuisines ADD COLUMN IF NOT EXISTS embedding extensions.vector(384);

COMMENT ON COLUMN public.meal_classes.embedding IS
  'gte-small (384-dim) embedding of display_name, populated by the embeddings-backfill Edge '
  'Function. NULL until first backfill run — callers must treat NULL as "not yet available" and '
  'fall back to ai_enrichment_closed_vocabulary(text), never fail on it.';
COMMENT ON COLUMN public.cuisines.embedding IS
  'gte-small (384-dim) embedding of display_name, populated by the embeddings-backfill Edge '
  'Function. NULL until first backfill run.';

-- Small table sizes (131 meal_classes, 66 cuisines) make a brute-force scan fast enough that an
-- ivfflat/hnsw index is unnecessary overhead at this scale; add one later if either table grows
-- past a few thousand rows.

CREATE OR REPLACE FUNCTION public.ai_enrichment_closed_vocabulary_by_embedding(
  p_query_embedding extensions.vector(384),
  p_match_count integer DEFAULT 40
)
RETURNS jsonb
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=public,pg_temp
AS $$
DECLARE
  v_classes jsonb;
  v_cuisines jsonb;
BEGIN
  IF p_query_embedding IS NULL THEN
    RETURN NULL;
  END IF;

  -- NULL if no meal_classes have an embedding yet (backfill not run) -- signals the caller to
  -- fall back to ai_enrichment_closed_vocabulary(text) rather than returning an empty/wrong list.
  IF NOT EXISTS (SELECT 1 FROM public.meal_classes WHERE embedding IS NOT NULL) THEN
    RETURN NULL;
  END IF;

  SELECT jsonb_agg(class_code ORDER BY embedding <=> p_query_embedding)
  INTO v_classes
  FROM (
    SELECT class_code, embedding
    FROM public.meal_classes
    WHERE is_active AND embedding IS NOT NULL
    ORDER BY embedding <=> p_query_embedding
    LIMIT p_match_count
  ) nearest;

  SELECT coalesce(jsonb_agg(name ORDER BY name), '[]'::jsonb)
  INTO v_cuisines
  FROM public.cuisines;

  RETURN jsonb_build_object('class_codes', coalesce(v_classes, '[]'::jsonb), 'cuisine_names', v_cuisines);
END;
$$;

COMMENT ON FUNCTION public.ai_enrichment_closed_vocabulary_by_embedding(extensions.vector, integer) IS
  'Semantic alternative to ai_enrichment_closed_vocabulary(text) (migration 127): nearest '
  'meal_classes by gte-small embedding cosine distance instead of literal word overlap. Returns '
  'NULL (not an empty list) when no embeddings are populated yet, so cron-dish-ontology can fall '
  'back to the word-overlap version without a code branch on a specific error.';

REVOKE ALL ON FUNCTION public.ai_enrichment_closed_vocabulary_by_embedding(extensions.vector, integer) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.ai_enrichment_closed_vocabulary_by_embedding(extensions.vector, integer) TO service_role;

-- Widen the provider CHECK (migration 070) to admit the two new evidence sources below.
ALTER TABLE public.food_source_records DROP CONSTRAINT IF EXISTS food_source_records_provider_check;
ALTER TABLE public.food_source_records
  ADD CONSTRAINT food_source_records_provider_check
  CHECK (provider IN ('foodon_ols', 'usda_fdc', 'ifct', 'agrovoc', 'groq'));

CREATE TABLE IF NOT EXISTS public.ifct_nutrient_reference (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  food_name_en text NOT NULL,
  food_group text,
  ifct_code text,
  energy_kcal numeric,
  protein_g numeric,
  fat_g numeric,
  carbohydrate_g numeric,
  serving_basis text NOT NULL DEFAULT '100 g',
  source_edition text NOT NULL DEFAULT 'IFCT 2017 (ICMR-NIN)',
  created_at timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE public.ifct_nutrient_reference IS
  'Indian Food Composition Tables (ICMR-NIN) reference nutrients -- fills the India-specific gap '
  'USDA FDC has for regional dishes. No free public IFCT API exists; this table is intentionally '
  'empty until the Founder supplies the real dataset as a numbered seed file (1NN band) -- no '
  'nutrient values are fabricated by this migration.';

CREATE INDEX IF NOT EXISTS ifct_nutrient_reference_name_trgm
  ON public.ifct_nutrient_reference USING gin (food_name_en extensions.gin_trgm_ops);

ALTER TABLE public.ifct_nutrient_reference ENABLE ROW LEVEL SECURITY;
CREATE POLICY ifct_nutrient_reference_public_read
  ON public.ifct_nutrient_reference FOR SELECT USING (true);

CREATE OR REPLACE FUNCTION public.match_ifct_nutrients(
  p_dish_name text,
  p_min_similarity real DEFAULT 0.35
)
RETURNS TABLE (
  id uuid,
  food_name_en text,
  energy_kcal numeric,
  protein_g numeric,
  fat_g numeric,
  carbohydrate_g numeric,
  serving_basis text,
  similarity real
)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path=public,extensions,pg_temp
AS $$
  SELECT id, food_name_en, energy_kcal, protein_g, fat_g, carbohydrate_g, serving_basis,
    extensions.similarity(food_name_en, p_dish_name) AS similarity
  FROM public.ifct_nutrient_reference
  WHERE extensions.similarity(food_name_en, p_dish_name) >= p_min_similarity
  ORDER BY extensions.similarity(food_name_en, p_dish_name) DESC
  LIMIT 1;
$$;

COMMENT ON FUNCTION public.match_ifct_nutrients(text, real) IS
  'Trigram best-match lookup against ifct_nutrient_reference. Returns zero rows (never a forced '
  'match) below p_min_similarity -- the table is empty until real IFCT data is seeded, so this '
  'safely returns nothing rather than erroring in the interim.';

REVOKE ALL ON FUNCTION public.match_ifct_nutrients(text, real) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.match_ifct_nutrients(text, real) TO service_role;
GRANT SELECT ON public.ifct_nutrient_reference TO anon, authenticated, service_role;
