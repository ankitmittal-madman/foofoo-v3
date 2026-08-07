-- This data-removal operation cannot be reversed from production alone.
-- Recovery is deterministic: rerun the governed loader from the checked-in, checksummed source
-- artifacts or copy the normalized batch from the verified dedicated training project.

DO $$
BEGIN
  RAISE EXCEPTION
    'restore requires governed re-ingestion from the dedicated training project or source artifacts';
END $$;
