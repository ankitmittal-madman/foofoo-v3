DO $$
DECLARE
  v_report jsonb;
  v_version text := 'sha256:' || repeat('0', 64);
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'recommendation_events'
      AND column_name = 'production_guardrail_observation'
      AND data_type = 'jsonb'
  ) THEN
    RAISE EXCEPTION 'production guardrail observation column is missing';
  END IF;
  IF to_regprocedure(
    're_engine.production_guardrail_aggregate(timestamp with time zone,timestamp with time zone,text)'
  ) IS NULL THEN
    RAISE EXCEPTION 're_engine.production_guardrail_aggregate is missing';
  END IF;
  IF has_function_privilege(
    'anon',
    're_engine.production_guardrail_aggregate(timestamp with time zone,timestamp with time zone,text)',
    'EXECUTE'
  ) OR has_function_privilege(
    'authenticated',
    're_engine.production_guardrail_aggregate(timestamp with time zone,timestamp with time zone,text)',
    'EXECUTE'
  ) THEN
    RAISE EXCEPTION 'Production recommendation guardrails must remain service-only';
  END IF;

  v_report := re_engine.production_guardrail_aggregate(
    now() - interval '1 day', now(), v_version
  );
  IF v_report->>'schema_version' <> 'recommendation-guardrail-report-v1'
    OR v_report->>'source' <> 'production_guardrail_aggregate'
    OR v_report->>'measurement_status' <> 'unavailable'
    OR v_report->>'publication_version' <> v_version
    OR (v_report->'counts') IS NULL THEN
    RAISE EXCEPTION 'Production recommendation guardrail report shape is invalid';
  END IF;
END $$;
