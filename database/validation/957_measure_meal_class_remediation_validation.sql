DO $$
DECLARE
  v_report jsonb;
  v_candidate_count bigint;
BEGIN
  IF to_regprocedure('re_engine.catalogue_meal_class_remediation_report()') IS NULL THEN
    RAISE EXCEPTION 'catalogue meal-class remediation report function is missing';
  END IF;

  IF has_function_privilege(
       'anon', 're_engine.catalogue_meal_class_remediation_report()', 'EXECUTE'
     ) OR has_function_privilege(
       'authenticated', 're_engine.catalogue_meal_class_remediation_report()', 'EXECUTE'
     ) THEN
    RAISE EXCEPTION 'catalogue meal-class remediation report must remain service-only';
  END IF;

  SELECT re_engine.catalogue_meal_class_remediation_report() INTO v_report;
  v_candidate_count := (v_report->>'candidate_count')::bigint;

  IF v_report->>'schema_version'
       <> 'recommendation-catalogue-meal-class-remediation-v1' THEN
    RAISE EXCEPTION 'catalogue meal-class remediation report schema is invalid';
  END IF;

  IF (v_report->'policy'->>'identity_exposed')::boolean
     OR (v_report->'policy'->>'automatic_confidence_upgrade_allowed')::boolean THEN
    RAISE EXCEPTION 'catalogue meal-class remediation policy is unsafe';
  END IF;

  IF (
    SELECT coalesce(sum(value::bigint), 0)
    FROM jsonb_each_text(v_report->'cohorts')
  ) <> v_candidate_count THEN
    RAISE EXCEPTION 'catalogue meal-class remediation cohorts do not reconcile';
  END IF;

  IF (
    SELECT coalesce(sum(value::bigint), 0)
    FROM jsonb_each_text(v_report->'ontology_status')
  ) <> v_candidate_count THEN
    RAISE EXCEPTION 'catalogue meal-class remediation ontology states do not reconcile';
  END IF;

  IF (
    SELECT coalesce(sum(value::bigint), 0)
    FROM jsonb_each_text(v_report->'classification_method')
  ) <> v_candidate_count THEN
    RAISE EXCEPTION 'catalogue meal-class remediation methods do not reconcile';
  END IF;

  IF (
    SELECT coalesce(sum(value::bigint), 0)
    FROM jsonb_each_text(v_report->'source_type')
  ) <> v_candidate_count THEN
    RAISE EXCEPTION 'catalogue meal-class remediation sources do not reconcile';
  END IF;

  IF (
    SELECT coalesce(sum(value::bigint), 0)
    FROM jsonb_each_text(v_report->'review_status')
  ) <> v_candidate_count THEN
    RAISE EXCEPTION 'catalogue meal-class remediation review states do not reconcile';
  END IF;

  IF (
    SELECT coalesce(sum(value::bigint), 0)
    FROM jsonb_each_text(v_report->'confidence')
  ) <> v_candidate_count THEN
    RAISE EXCEPTION 'catalogue meal-class remediation confidence does not reconcile';
  END IF;

  IF (v_report->'evidence'->>'single_usable_mapping')::bigint
       + (v_report->'evidence'->>'multiple_usable_mappings')::bigint
       <> v_candidate_count THEN
    RAISE EXCEPTION 'catalogue meal-class remediation mapping cardinality does not reconcile';
  END IF;
END $$;
