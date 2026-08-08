-- Count-only production serving guardrails for governed Aux rollout decisions.

ALTER TABLE public.recommendation_events
  ADD COLUMN IF NOT EXISTS production_guardrail_observation jsonb;

ALTER TABLE public.recommendation_events
  DROP CONSTRAINT IF EXISTS recommendation_events_production_guardrail_observation_shape;

ALTER TABLE public.recommendation_events
  ADD CONSTRAINT recommendation_events_production_guardrail_observation_shape CHECK (
    production_guardrail_observation IS NULL OR (
      jsonb_typeof(production_guardrail_observation) = 'object'
      AND production_guardrail_observation ?& ARRAY[
        'schema_version', 'measurement_status', 'mode', 'publication_version',
        'served_dish_count', 'hard_constraint_violations',
        'catalogue_version_mismatches', 'canonical_identity_failures',
        'intended_date_integrity_failures', 'ghar_fallback_failures'
      ]
      AND (
        production_guardrail_observation - ARRAY[
          'schema_version', 'measurement_status', 'mode', 'publication_version',
          'served_dish_count', 'hard_constraint_violations',
          'catalogue_version_mismatches', 'canonical_identity_failures',
          'intended_date_integrity_failures', 'ghar_fallback_failures'
        ]
      ) = '{}'::jsonb
      AND production_guardrail_observation->>'schema_version'
        = 'recommendation-serving-guardrail-observation-v1'
      AND production_guardrail_observation->>'measurement_status' IN ('measured','unavailable')
      AND production_guardrail_observation->>'mode' IN ('shadow','active')
      AND production_guardrail_observation->>'publication_version' ~ '^sha256:[0-9a-f]{64}$'
      AND (production_guardrail_observation->>'served_dish_count')::integer >= 0
      AND (production_guardrail_observation->>'hard_constraint_violations')::integer >= 0
      AND (production_guardrail_observation->>'catalogue_version_mismatches')::integer >= 0
      AND (production_guardrail_observation->>'canonical_identity_failures')::integer >= 0
      AND (production_guardrail_observation->>'intended_date_integrity_failures')::integer >= 0
      AND (production_guardrail_observation->>'ghar_fallback_failures')::integer >= 0
    )
  );

CREATE INDEX IF NOT EXISTS recommendation_events_guardrail_version_time_idx
  ON public.recommendation_events (
    (production_guardrail_observation->>'publication_version'), created_at
  )
  WHERE production_guardrail_observation IS NOT NULL;

COMMENT ON COLUMN public.recommendation_events.production_guardrail_observation IS
  'Strict count-only post-serving safety, catalogue identity, intended-date and Ghar fallback evidence; contains no dish, candidate, request-context or user identity.';

CREATE OR REPLACE FUNCTION re_engine.production_guardrail_aggregate(
  p_since timestamptz,
  p_until timestamptz,
  p_publication_version text
)
RETURNS jsonb
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = public, re_engine, pg_temp
AS $$
DECLARE
  v_event_count bigint;
  v_unavailable_count bigint;
  v_counts jsonb;
BEGIN
  IF p_since IS NULL OR p_until IS NULL OR p_since >= p_until THEN
    RAISE EXCEPTION 'A valid half-open observation window is required';
  END IF;
  IF p_until - p_since > interval '31 days' THEN
    RAISE EXCEPTION 'Production guardrail window cannot exceed 31 days';
  END IF;
  IF p_publication_version !~ '^sha256:[0-9a-f]{64}$' THEN
    RAISE EXCEPTION 'A full recommendation catalogue publication hash is required';
  END IF;

  SELECT
    count(*),
    count(*) FILTER (
      WHERE e.production_guardrail_observation->>'measurement_status' = 'unavailable'
    ),
    jsonb_build_object(
      'hard_constraint_violations', coalesce(sum(
        (e.production_guardrail_observation->>'hard_constraint_violations')::bigint
      ), 0),
      'catalogue_version_mismatches', coalesce(sum(
        (e.production_guardrail_observation->>'catalogue_version_mismatches')::bigint
      ), 0),
      'canonical_identity_failures', coalesce(sum(
        (e.production_guardrail_observation->>'canonical_identity_failures')::bigint
      ), 0),
      'intended_date_integrity_failures', coalesce(sum(
        (e.production_guardrail_observation->>'intended_date_integrity_failures')::bigint
      ), 0),
      'ghar_fallback_failures', coalesce(sum(
        (e.production_guardrail_observation->>'ghar_fallback_failures')::bigint
      ), 0)
    )
  INTO v_event_count, v_unavailable_count, v_counts
  FROM public.recommendation_events e
  WHERE e.created_at >= p_since
    AND e.created_at < p_until
    AND e.production_guardrail_observation->>'publication_version' = p_publication_version;

  RETURN jsonb_build_object(
    'schema_version', 'recommendation-guardrail-report-v1',
    'source', 'production_guardrail_aggregate',
    'measurement_status', CASE
      WHEN v_event_count > 0 AND v_unavailable_count = 0 THEN 'measured'
      ELSE 'unavailable'
    END,
    'window', jsonb_build_object(
      'since', to_char(p_since AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
      'until', to_char(p_until AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"')
    ),
    'publication_version', p_publication_version,
    'counts', v_counts
  );
END;
$$;

REVOKE ALL ON FUNCTION re_engine.production_guardrail_aggregate(timestamptz, timestamptz, text)
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION re_engine.production_guardrail_aggregate(timestamptz, timestamptz, text)
  TO service_role;

COMMENT ON FUNCTION re_engine.production_guardrail_aggregate(timestamptz, timestamptz, text) IS
  'Returns one privacy-safe, publication-bound rollout guardrail report. Any missing final Ghar audit makes measurement_status unavailable; no unavailable evidence is converted to zero.';
