DO $validation$
DECLARE
  v_report jsonb;
BEGIN
  IF to_regclass('ml.preference_attribution_slo_control') IS NULL THEN
    RAISE EXCEPTION 'fresh preference attribution SLO control is missing';
  END IF;
  IF (SELECT count(*) FROM ml.preference_attribution_slo_control WHERE singleton) <> 1 THEN
    RAISE EXCEPTION 'fresh preference attribution SLO control is not a singleton';
  END IF;
  IF has_function_privilege(
       'anon', 'ml.fresh_preference_attribution_report(timestamptz)', 'EXECUTE'
     ) OR has_function_privilege(
       'authenticated', 'ml.fresh_preference_attribution_report(timestamptz)', 'EXECUTE'
     ) THEN
    RAISE EXCEPTION 'fresh preference attribution SLO is exposed to application roles';
  END IF;

  v_report := ml.fresh_preference_attribution_report(statement_timestamp() - interval '24 hours');
  IF v_report->>'schema_version' <> 'fresh-preference-attribution-v2'
     OR v_report #>> '{policy,cutover_aware}' <> 'true'
     OR v_report #>> '{policy,dish_preference_targets_only}' <> 'true' THEN
    RAISE EXCEPTION 'fresh preference attribution SLO scope contract is invalid';
  END IF;
  IF (v_report->>'labeled_event_count')::bigint < 0
     OR (v_report->>'excluded_non_dish_event_count')::bigint < 0
     OR (v_report->>'labeled_event_count')::bigint < (v_report->>'exact_event_count')::bigint THEN
    RAISE EXCEPTION 'fresh preference attribution SLO counts are invalid';
  END IF;
  IF (v_report->>'labeled_event_count')::bigint < 20
     AND v_report #>> '{slo,status}' <> 'insufficient_sample' THEN
    RAISE EXCEPTION 'fresh preference attribution SLO insufficient-sample contract is invalid';
  END IF;
END;
$validation$;
