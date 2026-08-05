DROP FUNCTION IF EXISTS ops.requeue_external_provider(text);
DROP FUNCTION IF EXISTS public.research_record_annotation(jsonb);
DROP FUNCTION IF EXISTS public.research_claim_annotation_items(uuid,text,integer);
DROP FUNCTION IF EXISTS public.research_queue_annotation_items(uuid,jsonb);
DROP FUNCTION IF EXISTS public.research_create_annotation_batch(jsonb);
DROP FUNCTION IF EXISTS public.research_submit_meal_diary(uuid,jsonb);
DROP FUNCTION IF EXISTS public.research_participation_status(uuid);
DROP FUNCTION IF EXISTS public.record_external_nutrient_assertion(uuid,text,text,text,numeric,text,uuid,numeric);
DROP INDEX IF EXISTS research.research_participants_study_user;
ALTER TABLE research.participants DROP COLUMN IF EXISTS user_id;

-- Restore the migration-060 implementation, which repairs missing jobs and expired leases but
-- does not reopen completed jobs on the refresh horizon introduced by migration 064.
CREATE OR REPLACE FUNCTION public.reconcile_dish_enrichment_jobs()
RETURNS integer
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE affected integer;
BEGIN
  INSERT INTO public.dish_enrichment_jobs (dish_id, missing_fields)
  SELECT d.id, ARRAY['external_evidence']::text[]
  FROM public.dishes d
  WHERE NOT EXISTS (SELECT 1 FROM public.dish_enrichment_jobs j WHERE j.dish_id = d.id)
  ON CONFLICT DO NOTHING;

  UPDATE public.dish_enrichment_jobs
  SET status = 'failed',
      last_error_code = 'lease_expired',
      next_attempt_at = now(),
      locked_at = NULL,
      locked_by = NULL,
      lease_expires_at = NULL,
      updated_at = now()
  WHERE lease_expires_at < now() AND locked_by IS NOT NULL;

  GET DIAGNOSTICS affected = ROW_COUNT;
  RETURN affected;
END;
$$;

REVOKE ALL ON FUNCTION public.reconcile_dish_enrichment_jobs() FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.reconcile_dish_enrichment_jobs() TO service_role;
