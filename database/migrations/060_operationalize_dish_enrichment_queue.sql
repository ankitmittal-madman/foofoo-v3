-- Migration: 060_operationalize_dish_enrichment_queue.sql
-- Turns migration 056's durable job records into a safely claimable background queue.
-- Existing accepted taxonomy remains authoritative; external refresh only appends evidence.

ALTER TABLE public.dish_enrichment_jobs
  ADD COLUMN next_attempt_at timestamptz NOT NULL DEFAULT now(),
  ADD COLUMN lease_expires_at timestamptz,
  ADD COLUMN external_enriched_at timestamptz,
  ADD COLUMN source_refresh_after timestamptz,
  ADD COLUMN completed_at timestamptz;

CREATE INDEX dish_enrichment_jobs_due
  ON public.dish_enrichment_jobs (next_attempt_at, created_at)
  WHERE status IN ('pending_external', 'failed');

-- One controlled backfill: every canonical dish gets external research at least once. Terminal
-- seed jobs are reopened without changing dish ontology truth or review status.
UPDATE public.dish_enrichment_jobs
SET status = 'pending_external',
    next_attempt_at = now(),
    last_error_code = NULL,
    updated_at = now()
WHERE dish_id IS NOT NULL AND external_enriched_at IS NULL;

CREATE OR REPLACE FUNCTION public.claim_dish_enrichment_jobs(
  p_worker_id text,
  p_batch_size integer DEFAULT 20
)
RETURNS TABLE (
  job_id uuid,
  dish_id uuid,
  submission_id uuid,
  query_text text,
  attempts smallint
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
BEGIN
  IF p_worker_id IS NULL OR length(btrim(p_worker_id)) < 3 THEN
    RAISE EXCEPTION 'worker id required';
  END IF;

  RETURN QUERY
  WITH due AS (
    SELECT j.id
    FROM public.dish_enrichment_jobs j
    WHERE j.status IN ('pending_external', 'failed')
      AND j.next_attempt_at <= now()
      AND (j.lease_expires_at IS NULL OR j.lease_expires_at < now())
      AND j.attempts < 8
    ORDER BY j.next_attempt_at, j.created_at
    FOR UPDATE SKIP LOCKED
    LIMIT greatest(1, least(coalesce(p_batch_size, 20), 100))
  ), claimed AS (
    UPDATE public.dish_enrichment_jobs j
    SET status = 'pending_external',
        locked_by = p_worker_id,
        locked_at = now(),
        lease_expires_at = now() + interval '5 minutes',
        attempts = j.attempts + 1,
        updated_at = now()
    FROM due
    WHERE j.id = due.id
    RETURNING j.*
  )
  SELECT c.id, c.dish_id, c.submission_id,
         coalesce(d.name, s.entered_name) AS query_text, c.attempts
  FROM claimed c
  LEFT JOIN public.dishes d ON d.id = c.dish_id
  LEFT JOIN public.dish_submissions s ON s.id = c.submission_id;
END;
$$;

REVOKE ALL ON FUNCTION public.claim_dish_enrichment_jobs(text, integer) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.claim_dish_enrichment_jobs(text, integer) TO service_role;

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

-- Operator-called after the Edge Function exists. The scheduled command resolves the Vault secret
-- at execution time, so the credential itself is never embedded in migration text or cron.job.
CREATE OR REPLACE FUNCTION ops.configure_dish_ontology_schedules(p_function_url text)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ops, public, cron, pg_temp
AS $$
DECLARE existing_id bigint;
BEGIN
  IF p_function_url !~ '^https://[a-z0-9-]+\.supabase\.co/functions/v1/cron-dish-ontology$' THEN
    RAISE EXCEPTION 'invalid dish ontology worker URL';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM vault.decrypted_secrets WHERE name = 'service_role_key') THEN
    RAISE EXCEPTION 'Vault secret service_role_key is required';
  END IF;

  FOR existing_id IN SELECT jobid FROM cron.job
    WHERE jobname IN ('foofoo-dish-ontology-worker', 'foofoo-dish-ontology-reconcile')
  LOOP
    PERFORM cron.unschedule(existing_id);
  END LOOP;

  PERFORM cron.schedule(
    'foofoo-dish-ontology-worker',
    '*/10 * * * *',
    format(
      $command$SELECT net.http_post(
        url := %L,
        headers := jsonb_build_object(
          'Content-Type', 'application/json',
          'Authorization', 'Bearer ' || (
            SELECT decrypted_secret FROM vault.decrypted_secrets
            WHERE name = 'service_role_key' LIMIT 1
          )
        ),
        body := '{"source":"pg_cron"}'::jsonb,
        timeout_milliseconds := 55000
      );$command$,
      p_function_url
    )
  );

  PERFORM cron.schedule(
    'foofoo-dish-ontology-reconcile',
    '25 1 * * *',
    'SELECT public.reconcile_dish_enrichment_jobs();'
  );
END;
$$;

REVOKE ALL ON FUNCTION ops.configure_dish_ontology_schedules(text) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION ops.configure_dish_ontology_schedules(text) TO service_role;
