DO $$
DECLARE
  v_report jsonb;
  v_candidate_count bigint;
BEGIN
  IF to_regprocedure('re_engine.catalogue_enrichment_tranche_report()') IS NULL THEN
    RAISE EXCEPTION 'catalogue enrichment tranche report function is missing';
  END IF;

  IF has_function_privilege('anon', 're_engine.catalogue_enrichment_tranche_report()', 'EXECUTE')
     OR has_function_privilege(
       'authenticated', 're_engine.catalogue_enrichment_tranche_report()', 'EXECUTE'
     ) THEN
    RAISE EXCEPTION 'catalogue enrichment tranche report must remain service-only';
  END IF;

  SELECT re_engine.catalogue_enrichment_tranche_report() INTO v_report;
  v_candidate_count := (v_report->>'candidate_count')::bigint;

  IF v_report->>'schema_version' <> 'recommendation-catalogue-enrichment-tranche-v1' THEN
    RAISE EXCEPTION 'catalogue enrichment tranche report schema is invalid';
  END IF;

  IF (v_report->'readiness'->>'strict_auto_reclose_ready')::bigint
       + (v_report->'readiness'->>'requires_review')::bigint <> v_candidate_count THEN
    RAISE EXCEPTION 'catalogue enrichment tranche readiness does not reconcile';
  END IF;

  IF (v_report->'readiness'->>'meets_seed_146_policy')::bigint > v_candidate_count
     OR (v_report->'readiness'->>'strict_auto_reclose_ready')::bigint > v_candidate_count THEN
    RAISE EXCEPTION 'catalogue enrichment tranche policy count exceeds candidates';
  END IF;

  IF (
    SELECT coalesce(sum(value::bigint), 0)
    FROM jsonb_each_text(v_report->'ontology_status')
  ) <> v_candidate_count THEN
    RAISE EXCEPTION 'catalogue enrichment tranche status counts do not reconcile';
  END IF;

  IF (
    SELECT coalesce(sum(value::bigint), 0)
    FROM jsonb_each_text(v_report->'class_confidence')
  ) <> v_candidate_count THEN
    RAISE EXCEPTION 'catalogue enrichment tranche class confidence does not reconcile';
  END IF;

  IF (
    SELECT coalesce(sum(value::bigint), 0)
    FROM jsonb_each_text(v_report->'taxonomy_min_confidence')
  ) <> v_candidate_count THEN
    RAISE EXCEPTION 'catalogue enrichment tranche taxonomy confidence does not reconcile';
  END IF;

  IF (
    SELECT coalesce(sum(value::bigint), 0)
    FROM jsonb_each_text(v_report->'ingredient_min_confidence')
  ) <> v_candidate_count THEN
    RAISE EXCEPTION 'catalogue enrichment tranche ingredient confidence does not reconcile';
  END IF;
END $$;
