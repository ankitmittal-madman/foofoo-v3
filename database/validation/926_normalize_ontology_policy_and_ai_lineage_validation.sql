DO $$ BEGIN
  IF to_regclass('ops.ai_generation_run_inputs') IS NULL OR
     to_regclass('ops.assertion_sources') IS NULL OR
     to_regclass('ops.assertion_ai_runs') IS NULL OR
     to_regclass('food.ontology_field_policies') IS NULL OR
     to_regclass('food.ontology_review_decisions') IS NULL THEN
    RAISE EXCEPTION 'normalized ontology governance tables missing';
  END IF;
  IF (SELECT count(*) FROM food.ontology_field_policies
    WHERE policy_version='groq-low-risk-v1' AND auto_publish_threshold=0.80)<>8 THEN
    RAISE EXCEPTION 'Groq low-risk field policy incomplete';
  END IF;
  IF EXISTS (SELECT 1 FROM food.ontology_field_policies
    WHERE is_safety_field AND auto_publish_threshold IS NOT NULL) THEN
    RAISE EXCEPTION 'safety field has automatic publication authority';
  END IF;
  IF EXISTS (SELECT 1 FROM ops.ai_generation_runs r WHERE cardinality(r.input_source_ids)>0
    AND NOT EXISTS (SELECT 1 FROM ops.ai_generation_run_inputs i
      WHERE i.ai_generation_run_id=r.id)) THEN
    RAISE EXCEPTION 'AI run input array lacks normalized rows';
  END IF;
  IF EXISTS (SELECT 1 FROM public.dish_taxonomy_assertions a WHERE a.source_record_id IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM ops.assertion_sources s
      WHERE s.assertion_type_code='dish_taxonomy_assertion' AND s.assertion_id=a.id)) THEN
    RAISE EXCEPTION 'taxonomy assertion lacks normalized source evidence';
  END IF;
  IF has_table_privilege('authenticated','food.ontology_field_policies','SELECT') THEN
    RAISE EXCEPTION 'ontology field policy leaked to authenticated role'; END IF;
END $$;
