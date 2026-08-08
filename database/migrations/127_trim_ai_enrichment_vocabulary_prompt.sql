-- Trims the meal-class/cuisine vocabulary sent to Groq per dish (migration 126 sent the full
-- 131-code/66-cuisine list on every call, adding real prompt-token weight). Live production
-- testing after deploying 126 showed every AI call since then hitting a Groq 429 rate limit,
-- including natural, unforced cron ticks 10 minutes apart -- consistent with the larger prompt
-- tripping a free-tier tokens-per-minute cap our own ops.ai_provider_usage_daily budget has no
-- visibility into (it tracks our daily request/token ceiling, not Groq's live per-minute one).
--
-- Fix: ai_enrichment_closed_vocabulary() now takes the dish name and returns only class_codes
-- whose own code/display_name shares a word with it (simple ILIKE word-overlap, case-insensitive),
-- capped at 40 codes. If fewer than 15 codes match (a real risk for dishes whose class has no
-- shared vocabulary with the dish name, e.g. "Dry Sweet Potato Thoran" -> LD_SIMPLE_GREEN_VEG_SABZI
-- shares no word), it falls back to the full active list rather than under-serving accuracy --
-- this is a token-budget optimization, not an accuracy cap. Cuisine list is left full (66 names,
-- ~800 chars, a small fraction of the total prompt weight) since trimming it would risk losing the
-- correct cuisine for no meaningful token savings.

-- Postgres identifies functions by name+signature, so CREATE OR REPLACE on a new parameter list
-- creates a second overload rather than replacing the zero-arg version from migration 126 -- drop
-- it explicitly first so callers with zero args resolve unambiguously to the new default-NULL one.
DROP FUNCTION IF EXISTS public.ai_enrichment_closed_vocabulary();

CREATE OR REPLACE FUNCTION public.ai_enrichment_closed_vocabulary(p_dish_name text DEFAULT NULL)
RETURNS jsonb
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=public,pg_temp
AS $$
DECLARE
  v_words text[];
  v_matched jsonb;
  v_matched_count integer;
  v_all jsonb;
BEGIN
  v_all := coalesce(
    (SELECT jsonb_agg(class_code ORDER BY class_code) FROM public.meal_classes WHERE is_active),
    '[]'::jsonb
  );

  IF p_dish_name IS NULL OR btrim(p_dish_name) = '' THEN
    RETURN jsonb_build_object(
      'class_codes', v_all,
      'cuisine_names', coalesce((SELECT jsonb_agg(name ORDER BY name) FROM public.cuisines), '[]'::jsonb)
    );
  END IF;

  -- Split the dish name into words >= 3 chars (short words like "of"/"in" are too generic to filter on).
  v_words := ARRAY(
    SELECT lower(w) FROM regexp_split_to_table(p_dish_name, '\s+') AS w WHERE length(w) >= 3
  );

  SELECT jsonb_agg(class_code ORDER BY class_code), count(*)
  INTO v_matched, v_matched_count
  FROM (
    SELECT m.class_code
    FROM public.meal_classes m
    WHERE m.is_active
      AND EXISTS (
        SELECT 1 FROM unnest(v_words) AS word
        WHERE lower(m.class_code) LIKE '%' || word || '%'
           OR lower(m.display_name) LIKE '%' || word || '%'
      )
    LIMIT 40
  ) matched;

  RETURN jsonb_build_object(
    'class_codes', CASE WHEN coalesce(v_matched_count, 0) >= 15 THEN v_matched ELSE v_all END,
    'cuisine_names', coalesce((SELECT jsonb_agg(name ORDER BY name) FROM public.cuisines), '[]'::jsonb)
  );
END;
$$;

COMMENT ON FUNCTION public.ai_enrichment_closed_vocabulary(text) IS
  'Live class_code/cuisine name lists for the dish-ontology Groq prompt (ai.ts ClosedVocabulary). '
  'When p_dish_name is supplied, class_codes is filtered to a word-overlap-relevant subset (capped '
  'at 40) to reduce prompt token weight, falling back to the full active list when fewer than 15 '
  'codes match so accuracy is never sacrificed for token savings. cuisine_names is always the full '
  'list. Extended in migration 127; migration 126 introduced the unfiltered version.';

REVOKE ALL ON FUNCTION public.ai_enrichment_closed_vocabulary(text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.ai_enrichment_closed_vocabulary(text) TO service_role;
