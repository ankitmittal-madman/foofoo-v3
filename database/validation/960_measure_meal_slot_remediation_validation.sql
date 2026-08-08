DO $$
DECLARE
  v_report jsonb;
  v_active_dishes bigint;
  v_missing_slots bigint;
BEGIN
  IF to_regprocedure(
       're_engine.catalogue_meal_slot_remediation_report()'
     ) IS NULL THEN
    RAISE EXCEPTION 'catalogue meal-slot remediation report is missing';
  END IF;

  IF has_function_privilege(
       'anon', 're_engine.catalogue_meal_slot_remediation_report()', 'EXECUTE'
     ) OR has_function_privilege(
       'authenticated',
       're_engine.catalogue_meal_slot_remediation_report()', 'EXECUTE'
     ) THEN
    RAISE EXCEPTION 'catalogue meal-slot remediation report must remain service-only';
  END IF;

  SELECT re_engine.catalogue_meal_slot_remediation_report() INTO v_report;
  v_active_dishes := (v_report->>'active_dishes')::bigint;
  v_missing_slots := (v_report->>'missing_canonical_slot_dishes')::bigint;

  IF v_report->>'schema_version'
       <> 'recommendation-catalogue-meal-slot-remediation-v1' THEN
    RAISE EXCEPTION 'catalogue meal-slot remediation schema is invalid';
  END IF;

  IF (v_report->'policy'->>'identity_exposed')::boolean
     OR (v_report->'policy'->>'raw_source_text_exposed')::boolean
     OR NOT (v_report->'policy'->>'fixed_evidence_categories_only')::boolean
     OR (v_report->'policy'->>'automatic_proposal_acceptance_allowed')::boolean
     OR (v_report->'policy'->>'publication_gate_changed')::boolean
     OR NOT (v_report->'policy'->>'direct_slot_proposal_is_non_serving')::boolean THEN
    RAISE EXCEPTION 'catalogue meal-slot remediation policy is unsafe';
  END IF;

  IF (
    SELECT coalesce(sum(value::bigint), 0)
    FROM jsonb_each_text(v_report->'current_slot_state')
  ) <> v_active_dishes THEN
    RAISE EXCEPTION 'catalogue current slot states do not reconcile';
  END IF;

  IF (
    SELECT coalesce(sum(value::bigint), 0)
    FROM jsonb_each_text(v_report->'remediation_routes')
  ) <> v_missing_slots THEN
    RAISE EXCEPTION 'catalogue meal-slot remediation routes do not reconcile';
  END IF;

  IF (
    SELECT coalesce(sum(value::bigint), 0)
    FROM jsonb_each_text(v_report->'single_direct_slot_proposals')
  ) <> coalesce(
    (v_report->'remediation_routes'->>'single_direct_slot_proposal')::bigint,
    0
  ) THEN
    RAISE EXCEPTION 'catalogue direct meal-slot proposals do not reconcile';
  END IF;
END $$;
