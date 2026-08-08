DO $validation$
DECLARE
  v_since timestamptz := statement_timestamp() - interval '7 days';
  v_report jsonb;
  v_labeled integer;
  v_route_total integer;
BEGIN
  IF to_regprocedure('ml.fresh_preference_attribution_report(timestamptz)') IS NULL THEN
    RAISE EXCEPTION 'fresh preference attribution report is missing';
  END IF;
  IF has_function_privilege(
       'anon', 'ml.fresh_preference_attribution_report(timestamptz)', 'EXECUTE'
     ) OR has_function_privilege(
       'authenticated', 'ml.fresh_preference_attribution_report(timestamptz)', 'EXECUTE'
     ) THEN
    RAISE EXCEPTION 'fresh preference attribution report must remain service-only';
  END IF;

  v_report := ml.fresh_preference_attribution_report(v_since);
  SELECT count(*) INTO v_labeled
  FROM public.feedback_events f
  WHERE f.data_source = 'real'
    AND f.created_at >= v_since
    AND f.event_type IN (
      'accept', 'like', 'make_this', 'cooked', 'completed',
      'dislike', 'never', 'regretted'
    );
  SELECT coalesce(sum(value::text::integer), 0) INTO v_route_total
  FROM jsonb_each(v_report->'route_counts');

  IF v_report->>'schema_version' <> 'fresh-preference-attribution-v1' THEN
    RAISE EXCEPTION 'fresh preference attribution schema version is invalid';
  END IF;
  IF (v_report->>'labeled_event_count')::integer <> v_labeled
     OR v_route_total <> v_labeled THEN
    RAISE EXCEPTION 'fresh preference attribution routes do not reconcile';
  END IF;
  IF (v_report->>'exact_event_count')::integer
       + (v_report->>'inexact_event_count')::integer <> v_labeled THEN
    RAISE EXCEPTION 'fresh preference attribution counts do not reconcile';
  END IF;
  IF v_report->'slo'->>'status' NOT IN ('insufficient_sample', 'pass', 'fail')
     OR (v_report->'slo'->>'minimum_sample_size')::integer <> 20
     OR (v_report->'slo'->>'target_exact_attribution_rate')::numeric <> 0.9500 THEN
    RAISE EXCEPTION 'fresh preference attribution SLO contract is invalid';
  END IF;
  IF v_report->'policy' <> jsonb_build_object(
       'identity_exposed', false,
       'event_identity_exposed', false,
       'raw_feedback_exposed', false,
       'bounded_window_days', 90,
       'point_in_time_features_required', true,
       'exact_served_item_required', true,
       'feedback_changed', false,
       'outcome_changed', false,
       'training_changed', false,
       'serving_changed', false
     ) THEN
    RAISE EXCEPTION 'fresh preference attribution policy is invalid';
  END IF;
END
$validation$;
