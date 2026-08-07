DO $$
BEGIN
  IF to_regclass('ml.training_import_batches') IS NULL
     OR to_regclass('research.training_source_rows') IS NULL THEN
    RAISE EXCEPTION 'training ingestion lineage tables are incomplete';
  END IF;

  IF has_table_privilege('anon', 'research.training_source_rows', 'SELECT')
     OR has_table_privilege('authenticated', 'research.training_source_rows', 'SELECT')
     OR has_table_privilege('anon', 'ml.training_import_batches', 'SELECT')
     OR has_table_privilege('authenticated', 'ml.training_import_batches', 'SELECT') THEN
    RAISE EXCEPTION 'training ingestion lineage must not be exposed to client roles';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='research' AND table_name='auto_training_records'
      AND column_name='source_lineage'
  ) THEN
    RAISE EXCEPTION 'auto-training source lineage column is missing';
  END IF;

  BEGIN
    INSERT INTO ml.training_import_batches(
      id, import_key, source_bundle_sha256, source_dataset_version, generation_version,
      transformation_version, synthetic_only, source_files
    ) VALUES (
      gen_random_uuid(), 'validation:unsafe', repeat('0',64), 'validation', 'validation',
      'validation', false, '[]'
    );
    RAISE EXCEPTION 'synthetic-only constraint accepted an unsafe batch';
  EXCEPTION WHEN check_violation THEN
    NULL;
  END;
END $$;

