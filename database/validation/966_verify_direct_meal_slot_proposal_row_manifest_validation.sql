CREATE TEMP TABLE expected_dish_source_manifest (
  source_srno integer PRIMARY KEY,
  row_fingerprint text NOT NULL CHECK (row_fingerprint ~ '^[0-9a-f]{64}$'),
  direct_slot text NOT NULL CHECK (direct_slot IN ('breakfast','lunch','dinner','snacks'))
) ON COMMIT DROP;

DO $$
DECLARE
  v_report jsonb;
  v_proposals integer;
  v_links integer;
  v_route_total integer;
  v_gate_total integer;
  v_integrity_total integer;
  v_status_total integer;
BEGIN
  IF to_regprocedure(
       're_engine.direct_meal_slot_proposal_row_manifest_report(text,text)'
     ) IS NULL THEN
    RAISE EXCEPTION 'direct meal-slot proposal row-manifest report is missing';
  END IF;
  IF has_function_privilege(
       'anon',
       're_engine.direct_meal_slot_proposal_row_manifest_report(text,text)',
       'EXECUTE'
     ) OR has_function_privilege(
       'authenticated',
       're_engine.direct_meal_slot_proposal_row_manifest_report(text,text)',
       'EXECUTE'
     ) THEN
    RAISE EXCEPTION 'direct meal-slot proposal row-manifest report must remain service-only';
  END IF;

  v_report := re_engine.direct_meal_slot_proposal_row_manifest_report(
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
  SELECT coalesce(sum(value::text::integer), 0) INTO v_integrity_total
  FROM jsonb_each(v_report->'row_integrity_link_counts');
  SELECT coalesce(sum(value::text::integer), 0) INTO v_status_total
  FROM jsonb_each(v_report->'run_status_link_counts');

  IF v_report->>'schema_version'
       <> 'recommendation-meal-slot-proposal-row-manifest-v1' THEN
    RAISE EXCEPTION 'direct meal-slot proposal row-manifest schema version is invalid';
  END IF;
  IF (v_report->>'proposal_count')::integer <> v_proposals
     OR v_route_total <> v_proposals
     OR v_gate_total <> v_proposals THEN
    RAISE EXCEPTION 'direct meal-slot proposal row-manifest routes do not reconcile';
  END IF;
  IF (v_report->>'evidence_link_count')::integer <> v_links
     OR v_integrity_total <> v_links
     OR v_status_total <> v_links THEN
    RAISE EXCEPTION 'direct meal-slot proposal row-manifest links do not reconcile';
  END IF;
  IF v_report->'policy' <> jsonb_build_object(
       'identity_exposed', false,
       'source_name_exposed', false,
       'source_checksum_exposed', false,
       'manifest_values_exposed', false,
       'raw_source_text_exposed', false,
       'row_level_integrity_independent_of_run_completion', true,
       'run_completion_required_for_import_health', true,
       'row_manifest_gate_is_approval', false,
       'automatic_acceptance_allowed', false,
       'proposal_changed', false,
       'serving_changed', false,
       'publication_changed', false
     ) THEN
    RAISE EXCEPTION 'direct meal-slot proposal row-manifest policy is invalid';
  END IF;
END $$;
