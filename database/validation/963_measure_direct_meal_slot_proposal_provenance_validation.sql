DO $$
DECLARE
  v_report jsonb;
  v_proposals integer;
  v_links integer;
  v_route_total integer;
  v_mode_total integer;
BEGIN
  IF to_regprocedure(
       're_engine.direct_meal_slot_proposal_provenance_report()'
     ) IS NULL THEN
    RAISE EXCEPTION 'direct meal-slot proposal provenance report is missing';
  END IF;
  IF has_function_privilege(
       'anon', 're_engine.direct_meal_slot_proposal_provenance_report()', 'EXECUTE'
     ) OR has_function_privilege(
       'authenticated',
       're_engine.direct_meal_slot_proposal_provenance_report()',
       'EXECUTE'
     ) THEN
    RAISE EXCEPTION 'direct meal-slot proposal provenance report must remain service-only';
  END IF;

  v_report := re_engine.direct_meal_slot_proposal_provenance_report();
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
  FROM jsonb_each(v_report->'provenance_routes');
  SELECT coalesce(sum(value::text::integer), 0) INTO v_mode_total
  FROM jsonb_each(v_report->'run_mode_link_counts');

  IF v_report->>'schema_version'
       <> 'recommendation-meal-slot-proposal-provenance-v1' THEN
    RAISE EXCEPTION 'direct meal-slot proposal provenance schema version is invalid';
  END IF;
  IF (v_report->>'proposal_count')::integer <> v_proposals
     OR v_route_total <> v_proposals THEN
    RAISE EXCEPTION 'direct meal-slot proposal provenance routes do not reconcile';
  END IF;
  IF (v_report->>'evidence_link_count')::integer <> v_links
     OR v_mode_total <> v_links THEN
    RAISE EXCEPTION 'direct meal-slot proposal provenance links do not reconcile';
  END IF;
  IF v_report->'policy' <> jsonb_build_object(
       'identity_exposed', false,
       'source_name_exposed', false,
       'source_checksum_exposed', false,
       'raw_source_text_exposed', false,
       'evidence_link_is_independent_source_proof', false,
       'automatic_confidence_upgrade_allowed', false,
       'proposal_changed', false,
       'serving_changed', false,
       'publication_changed', false
     ) THEN
    RAISE EXCEPTION 'direct meal-slot proposal provenance policy is invalid';
  END IF;
END $$;
