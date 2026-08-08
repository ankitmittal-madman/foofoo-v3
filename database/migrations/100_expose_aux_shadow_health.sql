-- Service-only aggregate health boundary for Aux shadow/canary decisions.

CREATE OR REPLACE FUNCTION re_engine.aux_shadow_health(
  p_since timestamptz,
  p_until timestamptz
)
RETURNS TABLE (
  observation_date date,
  mode text,
  publication_version text,
  event_count bigint,
  retrieved_count bigint,
  unavailable_count bigint,
  timeout_count bigint,
  comparable_event_count bigint,
  avg_candidate_count numeric,
  avg_aux_latency_ms numeric,
  p95_aux_latency_ms numeric,
  avg_served_candidate_coverage numeric
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = public, re_engine, pg_temp
AS $$
BEGIN
  IF p_since IS NULL OR p_until IS NULL OR p_since >= p_until THEN
    RAISE EXCEPTION 'A valid half-open observation window is required';
  END IF;
  IF p_until - p_since > interval '31 days' THEN
    RAISE EXCEPTION 'Aux shadow health window cannot exceed 31 days';
  END IF;

  RETURN QUERY
  SELECT
    (e.created_at AT TIME ZONE 'UTC')::date,
    e.aux_shadow_observation->>'mode',
    e.aux_shadow_observation->>'publication_version',
    count(*),
    count(*) FILTER (WHERE e.aux_shadow_observation->>'outcome' = 'retrieved'),
    count(*) FILTER (WHERE e.aux_shadow_observation->>'outcome' = 'unavailable'),
    count(*) FILTER (WHERE e.aux_shadow_observation->>'failure_reason' = 'timeout'),
    count(*) FILTER (
      WHERE (e.aux_shadow_observation->>'comparable_served_count')::integer > 0
    ),
    round(avg((e.aux_shadow_observation->>'candidate_count')::numeric), 2),
    round(avg((e.aux_shadow_observation->>'aux_latency_ms')::numeric), 2),
    percentile_disc(0.95) WITHIN GROUP (
      ORDER BY (e.aux_shadow_observation->>'aux_latency_ms')::numeric
    ),
    round(avg((e.aux_shadow_observation->>'served_candidate_coverage')::numeric), 4)
  FROM public.recommendation_events e
  WHERE e.created_at >= p_since
    AND e.created_at < p_until
    AND e.aux_shadow_observation IS NOT NULL
  GROUP BY 1, 2, 3
  ORDER BY 1, 2, 3;
END;
$$;

REVOKE ALL ON FUNCTION re_engine.aux_shadow_health(timestamptz, timestamptz)
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION re_engine.aux_shadow_health(timestamptz, timestamptz)
  TO service_role;

COMMENT ON FUNCTION re_engine.aux_shadow_health(timestamptz, timestamptz) IS
  'Returns UTC-day, mode and publication aggregate Aux availability, latency and canonical overlap for a bounded window; exposes no profile, household, request or dish identity.';
