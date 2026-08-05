DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM public.dishes d
    WHERE NOT EXISTS (SELECT 1 FROM public.dish_enrichment_jobs j WHERE j.dish_id = d.id)
  ) THEN
    RAISE EXCEPTION 'FAIL: canonical dish without enrichment job';
  END IF;
  IF EXISTS (
    SELECT 1 FROM public.dish_enrichment_jobs
    WHERE locked_by IS NOT NULL AND lease_expires_at IS NULL
  ) THEN
    RAISE EXCEPTION 'FAIL: claimed job without lease expiry';
  END IF;
END $$;

SELECT status, count(*) AS jobs
FROM public.dish_enrichment_jobs
GROUP BY status
ORDER BY status;
