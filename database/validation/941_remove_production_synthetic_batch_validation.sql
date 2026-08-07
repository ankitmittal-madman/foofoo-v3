-- Confirms that only isolated training payloads were removed and the audit header was retained.

DO $$
DECLARE
  expected_batch constant uuid := '06a38fd3-ec53-54ab-ab0f-ef04bdf92c44';
BEGIN
  IF EXISTS (SELECT 1 FROM research.training_source_rows)
     OR EXISTS (SELECT 1 FROM research.auto_training_records) THEN
    RAISE EXCEPTION 'synthetic training payloads remain in production';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM ml.training_import_batches
    WHERE id = expected_batch
      AND synthetic_only
      AND load_summary #>> '{production_cleanup,completed}' = 'true'
      AND load_summary #>> '{production_cleanup,raw_rows_removed}' = '132586'
      AND load_summary #>> '{production_cleanup,normalized_rows_removed}' = '113868'
  ) THEN
    RAISE EXCEPTION 'production cleanup audit evidence is incomplete';
  END IF;
END $$;
