DO $$
DECLARE job_id bigint;
BEGIN
  FOR job_id IN SELECT jobid FROM cron.job
    WHERE jobname IN ('foofoo-dish-ontology-worker', 'foofoo-dish-ontology-reconcile')
  LOOP
    PERFORM cron.unschedule(job_id);
  END LOOP;
END $$;
DROP FUNCTION IF EXISTS ops.configure_dish_ontology_schedules(text);
DROP FUNCTION IF EXISTS public.reconcile_dish_enrichment_jobs();
DROP FUNCTION IF EXISTS public.claim_dish_enrichment_jobs(text, integer);
DROP INDEX IF EXISTS public.dish_enrichment_jobs_due;
ALTER TABLE public.dish_enrichment_jobs
  DROP COLUMN IF EXISTS completed_at,
  DROP COLUMN IF EXISTS source_refresh_after,
  DROP COLUMN IF EXISTS external_enriched_at,
  DROP COLUMN IF EXISTS lease_expires_at,
  DROP COLUMN IF EXISTS next_attempt_at;
