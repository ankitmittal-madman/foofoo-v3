-- Migration: 069_prioritize_ai_retries_and_canonical_regions.sql
-- Due retries run before untouched backfill rows, and Groq India prefixes collapse only when the
-- target region code already exists in Foofoo's governed regional vocabulary.

CREATE OR REPLACE FUNCTION ops.claim_ai_dish_enrichment(
  p_worker_id text,p_batch_size integer DEFAULT 2
)
RETURNS TABLE(dish_id uuid,query_text text,attempts smallint)
LANGUAGE plpgsql SECURITY DEFINER SET search_path=ops,public,pg_temp AS $$
BEGIN
  IF p_worker_id IS NULL OR length(btrim(p_worker_id))<3 THEN RAISE EXCEPTION 'worker id required'; END IF;
  RETURN QUERY
  WITH due AS (
    SELECT s.dish_id FROM ops.ai_dish_enrichment_state s
    WHERE s.status IN ('pending','budget_deferred','failed') AND s.next_attempt_at<=now()
      AND (s.lease_expires_at IS NULL OR s.lease_expires_at<now()) AND s.attempts<8
    ORDER BY (s.status='failed') DESC,s.next_attempt_at,s.created_at
    FOR UPDATE SKIP LOCKED LIMIT greatest(1,least(coalesce(p_batch_size,2),12))
  ), claimed AS (
    UPDATE ops.ai_dish_enrichment_state s SET status='running',attempts=s.attempts+1,
      locked_at=now(),locked_by=p_worker_id,lease_expires_at=now()+interval '5 minutes',updated_at=now()
    FROM due WHERE s.dish_id=due.dish_id RETURNING s.*
  )
  SELECT c.dish_id,d.name,c.attempts FROM claimed c JOIN public.dishes d ON d.id=c.dish_id;
END $$;

CREATE OR REPLACE FUNCTION public.normalize_groq_region_code()
RETURNS trigger LANGUAGE plpgsql SET search_path=public,pg_temp AS $$
DECLARE candidate text;
BEGIN
  IF NEW.source_name='groq' THEN
    NEW.region_code:=CASE NEW.region_code
      WHEN 'it' THEN 'italy' ELSE NEW.region_code END;
    candidate:=regexp_replace(NEW.region_code,'^(in|india)_','');
    IF candidate<>NEW.region_code AND EXISTS (
      SELECT 1 FROM public.dish_regional_affinities r
      WHERE r.region_code=candidate AND r.source_name<>'groq'
    ) THEN NEW.region_code:=candidate; END IF;
  END IF;
  RETURN NEW;
END $$;

DELETE FROM public.dish_regional_affinities g
USING public.dish_regional_affinities canonical
WHERE g.source_name='groq' AND g.dish_id=canonical.dish_id AND canonical.source_name<>'groq'
  AND canonical.region_code=regexp_replace(g.region_code,'^(in|india)_','')
  AND canonical.region_code<>g.region_code;

UPDATE public.dish_regional_affinities g
SET region_code=regexp_replace(g.region_code,'^(in|india)_','')
WHERE g.source_name='groq' AND g.region_code~'^(in|india)_' AND EXISTS (
  SELECT 1 FROM public.dish_regional_affinities canonical
  WHERE canonical.region_code=regexp_replace(g.region_code,'^(in|india)_','')
    AND canonical.source_name<>'groq'
);
