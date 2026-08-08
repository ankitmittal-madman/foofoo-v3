DO $$
DECLARE
  v_report jsonb;
  v_labeled integer;
  v_route_total integer;
BEGIN
  IF to_regprocedure('ml.preference_attribution_recovery_report()') IS NULL THEN
    RAISE EXCEPTION 'preference attribution recovery report is missing';
  END IF;
  IF has_function_privilege('anon', 'ml.preference_attribution_recovery_report()', 'EXECUTE')
     OR has_function_privilege(
       'authenticated', 'ml.preference_attribution_recovery_report()', 'EXECUTE'
     ) THEN
    RAISE EXCEPTION 'preference attribution recovery report must remain service-only';
  END IF;

  v_report := ml.preference_attribution_recovery_report();
  SELECT count(*) INTO v_labeled
  FROM public.feedback_events f
  WHERE f.data_source = 'real'
    AND f.event_type IN (
      'accept', 'like', 'make_this', 'cooked', 'completed',
      'dislike', 'never', 'regretted'
    );
  SELECT coalesce(sum(value::text::integer), 0) INTO v_route_total
  FROM jsonb_each(v_report->'route_counts');

  IF v_report->>'schema_version' <> 'preference-attribution-recovery-v1' THEN
    RAISE EXCEPTION 'preference attribution recovery schema version is invalid';
  END IF;
  IF (v_report->>'labeled_event_count')::integer <> v_labeled
     OR v_route_total <> v_labeled THEN
    RAISE EXCEPTION 'preference attribution recovery routes do not reconcile';
  END IF;
  IF (v_report->>'already_exact_event_count')::integer
       + (v_report->>'recoverable_event_count')::integer
       + (v_report->>'unrecoverable_event_count')::integer <> v_labeled THEN
    RAISE EXCEPTION 'preference attribution recovery outcome counts do not reconcile';
  END IF;
  IF v_report->'policy' <> jsonb_build_object(
       'identity_exposed', false,
       'event_identity_exposed', false,
       'raw_feedback_exposed', false,
       'point_in_time_features_required', true,
       'unique_served_item_required', true,
       'automatic_recovery_allowed', false,
       'feedback_changed', false,
       'outcome_changed', false,
       'training_changed', false,
       'serving_changed', false
     ) THEN
    RAISE EXCEPTION 'preference attribution recovery policy is invalid';
  END IF;
END $$;
