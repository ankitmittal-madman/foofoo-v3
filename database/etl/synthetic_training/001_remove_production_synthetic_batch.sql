-- Removes the verified synthetic-training batch from production after it has been copied to the
-- dedicated training project. Exact batch assertions prevent unrelated research records from
-- being removed; the raw table is exclusively this batch and can be truncated immediately.

SET TRANSACTION READ WRITE;

DO $$
DECLARE
  expected_batch constant uuid := '06a38fd3-ec53-54ab-ab0f-ef04bdf92c44';
  production_dishes_before bigint;
  production_profiles_before bigint;
  production_plans_before bigint;
  normalized_rows_removed bigint;
BEGIN
  PERFORM pg_advisory_xact_lock(hashtextextended(expected_batch::text, 0));

  SELECT count(*) INTO production_dishes_before FROM public.dishes;
  SELECT count(*) INTO production_profiles_before FROM public.profiles;
  SELECT count(*) INTO production_plans_before FROM public.week_plans;

  IF NOT EXISTS (
    SELECT 1
    FROM ml.training_import_batches
    WHERE id = expected_batch
      AND synthetic_only
      AND status = 'completed_with_rejections'
      AND source_row_count = 132586
      AND accepted_source_row_count = 132541
      AND rejected_source_row_count = 45
      AND normalized_record_count = 113868
  ) THEN
    RAISE EXCEPTION 'expected completed synthetic training batch is absent or has drifted';
  END IF;

  IF (SELECT count(*) FROM research.training_source_rows) <> 132586
     OR (SELECT count(*) FROM research.training_source_rows
         WHERE batch_id = expected_batch) <> 132586 THEN
    RAISE EXCEPTION 'raw training rows are not exclusively the expected batch';
  END IF;

  IF (SELECT count(*) FROM research.auto_training_records
      WHERE first_batch_id = expected_batch::text
        AND synthetic_only
        AND source_dataset_version = 'foofoo-training-v1'
        AND transformation_version = 'foofoo-training-db-v1') <> 113868 THEN
    RAISE EXCEPTION 'normalized records created by the expected batch have drifted';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM research.auto_training_records
    WHERE first_batch_id = expected_batch::text
      AND last_batch_id <> expected_batch::text
  ) THEN
    RAISE EXCEPTION 'a later batch updated records created by this batch; cleanup requires review';
  END IF;

  IF (SELECT count(*) FROM research.auto_training_records
      WHERE first_batch_id = expected_batch::text
        AND target_table = 'research.training_dishes') <> 86
     OR (SELECT count(*) FROM research.auto_training_records
         WHERE first_batch_id = expected_batch::text
           AND target_table = 'research.household_personas') <> 10000
     OR (SELECT count(*) FROM research.auto_training_records
         WHERE first_batch_id = expected_batch::text
           AND target_table = 'research.interactions') <> 64842
     OR (SELECT count(*) FROM research.auto_training_records
         WHERE first_batch_id = expected_batch::text
           AND target_table = 'research.weekly_signals') <> 10000
     OR (SELECT count(*) FROM research.auto_training_records
         WHERE first_batch_id = expected_batch::text
           AND target_table = 'research.household_preference_edges') <> 28940 THEN
    RAISE EXCEPTION 'normalized target counts have drifted';
  END IF;

  TRUNCATE TABLE research.training_source_rows RESTART IDENTITY;
  DELETE FROM research.auto_training_records
  WHERE first_batch_id = expected_batch::text;
  GET DIAGNOSTICS normalized_rows_removed = ROW_COUNT;

  IF normalized_rows_removed <> 113868 THEN
    RAISE EXCEPTION 'normalized delete count mismatch: %', normalized_rows_removed;
  END IF;

  UPDATE ml.training_import_batches
  SET load_summary = load_summary || jsonb_build_object(
        'production_cleanup', jsonb_build_object(
          'completed', true,
          'completed_at', now(),
          'raw_rows_removed', 132586,
          'normalized_rows_removed', 113868,
          'recovery_source', 'dedicated training project plus checked-in source artifacts'
        )
      )
  WHERE id = expected_batch;

  IF (SELECT count(*) FROM public.dishes) <> production_dishes_before
     OR (SELECT count(*) FROM public.profiles) <> production_profiles_before
     OR (SELECT count(*) FROM public.week_plans) <> production_plans_before THEN
    RAISE EXCEPTION 'production table counts changed during isolated training cleanup';
  END IF;
END $$;
