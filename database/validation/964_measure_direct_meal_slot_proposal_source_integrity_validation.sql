DO $$
DECLARE
  v_report jsonb;
  v_proposals integer;
  v_links integer;
  v_route_total integer;
  v_gate_total integer;
  v_identity_total integer;
  v_mode_total integer;
  v_status_total integer;
BEGIN
  IF to_regprocedure(
       're_engine.direct_meal_slot_proposal_source_integrity_report(text,text)'
     ) IS NULL THEN
    RAISE EXCEPTION 'direct meal-slot proposal source-integrity report is missing';
  END IF;
  IF has_function_privilege(
       'anon',
       're_engine.direct_meal_slot_proposal_source_integrity_report(text,text)',
       'EXECUTE'
     ) OR has_function_privilege(
       'authenticated',
       're_engine.direct_meal_slot_proposal_source_integrity_report(text,text)',
       'EXECUTE'
     ) THEN
    RAISE EXCEPTION 'direct meal-slot proposal source-integrity report must remain service-only';
  END IF;

  v_report := re_engine.direct_meal_slot_proposal_source_integrity_report(
    'validation-source.csv', repeat('0', 64)
  );
  SELECT count(*) INTO v_proposals
  FROM ops.dish_meal_slot_proposals p
  WHERE p.proposal_method = 'exact_import_course_v1'
    AND p.proposal_version = 'meal-slot-proposal-v1';
  SELECT count(*) INTO v_links
  FROM ops.dish_meal_slot_proposal_evidence e
  JOIN ops.dish_meal_slot_proposals p ON p.id = e.proposal_id
  WHERE p.proposal_method = 'exact_import_course_v1'
    AND p.proposal_version = 'meal-slot-proposal-v1';
  SELECT coalesce(sum(value::text::integer), 0) INTO v_route_total
  FROM jsonb_each(v_report->'integrity_routes');
  SELECT coalesce(sum(value::text::integer), 0) INTO v_gate_total
  FROM jsonb_each(v_report->'proposal_gate_counts');
  SELECT coalesce(sum(value::text::integer), 0) INTO v_identity_total
  FROM jsonb_each(v_report->'source_identity_link_counts');
  SELECT coalesce(sum(value::text::integer), 0) INTO v_mode_total
  FROM jsonb_each(v_report->'run_mode_link_counts');
  SELECT coalesce(sum(value::text::integer), 0) INTO v_status_total
  FROM jsonb_each(v_report->'run_status_link_counts');

  IF v_report->>'schema_version'
       <> 'recommendation-meal-slot-proposal-source-integrity-v1' THEN
    RAISE EXCEPTION 'direct meal-slot proposal source-integrity schema version is invalid';
  END IF;
  IF (v_report->>'proposal_count')::integer <> v_proposals
     OR v_route_total <> v_proposals
     OR v_gate_total <> v_proposals THEN
    RAISE EXCEPTION 'direct meal-slot proposal source-integrity routes do not reconcile';
  END IF;
  IF (v_report->>'evidence_link_count')::integer <> v_links
     OR v_identity_total <> v_links
     OR v_mode_total <> v_links
     OR v_status_total <> v_links THEN
    RAISE EXCEPTION 'direct meal-slot proposal source-integrity links do not reconcile';
  END IF;
  IF v_report->'policy' <> jsonb_build_object(
       'identity_exposed', false,
       'expected_source_name_exposed', false,
       'expected_source_checksum_exposed', false,
       'raw_source_text_exposed', false,
       'expected_source_supplied_at_runtime', true,
       'source_integrity_gate_is_approval', false,
       'automatic_acceptance_allowed', false,
       'proposal_changed', false,
       'serving_changed', false,
       'publication_changed', false
     ) THEN
    RAISE EXCEPTION 'direct meal-slot proposal source-integrity policy is invalid';
  END IF;
END $$;
