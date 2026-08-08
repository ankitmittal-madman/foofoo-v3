DO $$
DECLARE
  v_report jsonb;
  v_eligible_count bigint;
  v_gap_report jsonb;
BEGIN
  IF to_regprocedure('re_engine.catalogue_published_quality_report()') IS NULL THEN
    RAISE EXCEPTION 'catalogue published quality report function is missing';
  END IF;

  IF has_function_privilege('anon', 're_engine.catalogue_published_quality_report()', 'EXECUTE')
     OR has_function_privilege(
       'authenticated', 're_engine.catalogue_published_quality_report()', 'EXECUTE'
     ) THEN
    RAISE EXCEPTION 'catalogue published quality report must remain service-only';
  END IF;

  SELECT re_engine.catalogue_published_quality_report() INTO v_report;
  SELECT re_engine.catalogue_publication_gap_report() INTO v_gap_report;
  v_eligible_count := (v_report->>'eligible_count')::bigint;

  IF v_report->>'schema_version' <> 'recommendation-catalogue-published-quality-v1' THEN
    RAISE EXCEPTION 'catalogue published quality report schema is invalid';
  END IF;

  IF v_eligible_count
       <> (v_gap_report->'serving_readiness'->>'publishable_dishes')::bigint THEN
    RAISE EXCEPTION 'catalogue published quality count does not match publication eligibility';
  END IF;

  IF (v_report->'readiness'->>'strict_quality_ready')::bigint
       + (v_report->'readiness'->>'quality_review_required')::bigint <> v_eligible_count THEN
    RAISE EXCEPTION 'catalogue published quality readiness does not reconcile';
  END IF;

  IF (
    SELECT coalesce(sum(value::bigint), 0)
    FROM jsonb_each_text(v_report->'ontology_confidence')
  ) <> v_eligible_count THEN
    RAISE EXCEPTION 'catalogue published ontology confidence does not reconcile';
  END IF;

  IF (
    SELECT coalesce(sum(value::bigint), 0)
    FROM jsonb_each_text(v_report->'class_confidence')
  ) <> v_eligible_count THEN
    RAISE EXCEPTION 'catalogue published class confidence does not reconcile';
  END IF;

  IF (
    SELECT coalesce(sum(value::bigint), 0)
    FROM jsonb_each_text(v_report->'taxonomy_min_confidence')
  ) <> v_eligible_count THEN
    RAISE EXCEPTION 'catalogue published taxonomy confidence does not reconcile';
  END IF;

  IF (
    SELECT coalesce(sum(value::bigint), 0)
    FROM jsonb_each_text(v_report->'ingredient_min_confidence')
  ) <> v_eligible_count THEN
    RAISE EXCEPTION 'catalogue published ingredient confidence does not reconcile';
  END IF;
END $$;
