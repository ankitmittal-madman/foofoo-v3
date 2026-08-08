DO $$
DECLARE
  v_report jsonb;
  v_proposal_count integer;
  v_evidence_count integer;
  v_status_total integer;
  v_slot_total integer;
BEGIN
  IF to_regprocedure(
       're_engine.direct_meal_slot_proposal_review_report(integer)'
     ) IS NULL THEN
    RAISE EXCEPTION 'direct meal-slot proposal review report is missing';
  END IF;

  IF has_function_privilege(
       'anon',
       're_engine.direct_meal_slot_proposal_review_report(integer)',
       'EXECUTE'
     ) OR has_function_privilege(
       'authenticated',
       're_engine.direct_meal_slot_proposal_review_report(integer)',
       'EXECUTE'
     ) THEN
    RAISE EXCEPTION 'direct meal-slot proposal review report must remain service-only';
  END IF;

  v_report := re_engine.direct_meal_slot_proposal_review_report(1);
  SELECT count(*) INTO v_proposal_count
  FROM ops.dish_meal_slot_proposals p
  WHERE p.proposal_method = 'exact_import_course_v1'
    AND p.proposal_version = 'meal-slot-proposal-v1';
  SELECT count(*) INTO v_evidence_count
  FROM ops.dish_meal_slot_proposal_evidence e
  JOIN ops.dish_meal_slot_proposals p ON p.id = e.proposal_id
  WHERE p.proposal_method = 'exact_import_course_v1'
    AND p.proposal_version = 'meal-slot-proposal-v1';
  SELECT coalesce(sum(value::text::integer), 0) INTO v_status_total
  FROM jsonb_each(v_report->'status_counts');
  SELECT coalesce(sum(value::text::integer), 0) INTO v_slot_total
  FROM jsonb_each(v_report->'slot_counts');

  IF v_report->>'schema_version'
       <> 'recommendation-meal-slot-proposal-review-v1' THEN
    RAISE EXCEPTION 'direct meal-slot proposal review schema version is invalid';
  END IF;
  IF (v_report->>'proposal_count')::integer <> v_proposal_count
     OR v_status_total <> v_proposal_count
     OR v_slot_total <> v_proposal_count THEN
    RAISE EXCEPTION 'direct meal-slot proposal review counts do not reconcile';
  END IF;
  IF (v_report->>'evidence_link_count')::integer <> v_evidence_count
     OR (v_report->'evidence_links_per_proposal'->>'zero_link_proposals')::integer <> 0 THEN
    RAISE EXCEPTION 'direct meal-slot proposal review evidence does not reconcile';
  END IF;
  IF jsonb_array_length(v_report->'sample') > 4 THEN
    RAISE EXCEPTION 'direct meal-slot proposal review sample exceeds its bound';
  END IF;
  IF EXISTS (
    SELECT 1
    FROM jsonb_array_elements(v_report->'sample') sample_row
    CROSS JOIN LATERAL jsonb_object_keys(sample_row) sample_key
    WHERE sample_key NOT IN (
      'dish_name', 'proposed_slot', 'evidence_category', 'confidence',
      'evidence_link_count', 'proposal_status', 'still_matches_direct_evidence'
    )
  ) THEN
    RAISE EXCEPTION 'direct meal-slot proposal review sample exposes an unapproved field';
  END IF;
  IF v_report->'policy' <> jsonb_build_object(
       'read_only', true,
       'user_data_exposed', false,
       'raw_source_text_exposed', false,
       'catalogue_names_exposed_for_review', true,
       'automatic_acceptance_allowed', false,
       'serving_changed', false,
       'publication_changed', false
     ) THEN
    RAISE EXCEPTION 'direct meal-slot proposal review policy is invalid';
  END IF;
END $$;
