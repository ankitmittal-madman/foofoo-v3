-- Restore the queue ordering and explicit region mapping introduced by migrations 066 and 068.

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
    ORDER BY s.next_attempt_at,s.created_at FOR UPDATE SKIP LOCKED
    LIMIT greatest(1,least(coalesce(p_batch_size,2),12))
  ), claimed AS (
    UPDATE ops.ai_dish_enrichment_state s SET status='running',attempts=s.attempts+1,
      locked_at=now(),locked_by=p_worker_id,lease_expires_at=now()+interval '5 minutes',updated_at=now()
    FROM due WHERE s.dish_id=due.dish_id RETURNING s.*
  )
  SELECT c.dish_id,d.name,c.attempts FROM claimed c JOIN public.dishes d ON d.id=c.dish_id;
END $$;

CREATE OR REPLACE FUNCTION public.normalize_groq_region_code()
RETURNS trigger LANGUAGE plpgsql SET search_path=public,pg_temp AS $$
BEGIN
  IF NEW.source_name='groq' THEN
    NEW.region_code:=CASE NEW.region_code
      WHEN 'in_rajasthan' THEN 'rajasthan' WHEN 'in_punjab' THEN 'punjab'
      WHEN 'in_maharashtra' THEN 'maharashtra' WHEN 'in_gujarat' THEN 'gujarat'
      WHEN 'in_kerala' THEN 'kerala' WHEN 'in_karnataka' THEN 'karnataka'
      WHEN 'in_tamil_nadu' THEN 'tamil_nadu' WHEN 'in_west_bengal' THEN 'west_bengal'
      WHEN 'in_uttar_pradesh' THEN 'uttar_pradesh' WHEN 'in_north_india' THEN 'north_india'
      WHEN 'in_south_india' THEN 'south_india' WHEN 'in_east_india' THEN 'east_india'
      WHEN 'in_west_india' THEN 'west_india' WHEN 'it' THEN 'italy'
      ELSE NEW.region_code END;
  END IF;
  RETURN NEW;
END $$;
