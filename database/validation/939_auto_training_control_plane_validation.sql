DO $$
BEGIN
  IF to_regclass('ml.auto_training_runs') IS NULL
     OR to_regclass('ml.auto_training_table_audits') IS NULL
     OR to_regclass('research.auto_training_records') IS NULL
     OR to_regclass('ml.auto_training_seed_counts') IS NULL
     OR to_regclass('ml.auto_training_model_runs') IS NULL THEN
    RAISE EXCEPTION 'auto-training control-plane tables are incomplete';
  END IF;

  IF has_table_privilege('authenticated', 'research.auto_training_records', 'SELECT') THEN
    RAISE EXCEPTION 'synthetic training staging must not be exposed to authenticated clients';
  END IF;

  BEGIN
    INSERT INTO research.auto_training_records(
      target_table, record_key, payload, payload_sha256, generation_method, confidence,
      confidence_band, ontology_mapping_status, ontology_version, first_batch_id, last_batch_id
    ) VALUES ('validation', 'invalid-confidence', '{}', repeat('0', 64), 'validation', 1.1,
      'high', 'mapped', 'validation', 'validation', 'validation');
    RAISE EXCEPTION 'confidence constraint did not reject invalid value';
  EXCEPTION WHEN check_violation THEN
    NULL;
  END;
END $$;
