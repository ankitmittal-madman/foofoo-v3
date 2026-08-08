-- Measure whether newly written real feedback is accumulating exact point-in-time attribution.
-- This is an operational SLO, not a legacy backfill: it reports aggregate routes for a bounded
-- caller-supplied window and never changes feedback, outcomes, training data or serving state.

CREATE OR REPLACE FUNCTION ml.fresh_preference_attribution_report(p_since timestamptz)
RETURNS jsonb
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = public, ml, pg_catalog, pg_temp
AS $function$
DECLARE
  v_report jsonb;
BEGIN
  IF p_since IS NULL
     OR p_since > statement_timestamp()
     OR p_since < statement_timestamp() - interval '90 days' THEN
    RAISE EXCEPTION 'attribution SLO window must begin within the last 90 days';
  END IF;

  WITH labeled AS (
    SELECT f.id, f.household_id, f.dish_id, f.recommendation_event_id
    FROM public.feedback_events f
    WHERE f.data_source = 'real'
      AND f.created_at >= p_since
      AND f.event_type IN (
        'accept', 'like', 'make_this', 'cooked', 'completed',
        'dislike', 'never', 'regretted'
      )
  ), linked AS (
    SELECT
      l.*,
      r.id AS resolved_recommendation_event_id,
      s.id AS slate_id,
      EXISTS (
        SELECT 1
        FROM public.recommendation_runs rr
        JOIN ml.feature_snapshots fs ON fs.id = rr.feature_snapshot_id
        JOIN public.context_snapshots cs ON cs.id = rr.context_snapshot_id
        WHERE rr.slate_id = s.id
          AND rr.run_status = 'success'
          AND jsonb_typeof(fs.values->'household') = 'object'
          AND fs.values->'household' <> '{}'::jsonb
      ) AS has_point_in_time_run,
      o.id IS NOT NULL AS has_outcome,
      o.slate_id AS outcome_slate_id,
      o.episode_hash,
      coalesce(items.match_count, 0) AS served_item_match_count
    FROM labeled l
    LEFT JOIN public.recommendation_events r
      ON r.id = l.recommendation_event_id
      AND r.household_id = l.household_id
    LEFT JOIN public.slates s
      ON s.household_id = r.household_id
      AND s.request_id = r.request_id
    LEFT JOIN public.outcome_events o ON o.idempotency_key = l.id
    LEFT JOIN LATERAL (
      SELECT count(*)::integer AS match_count
      FROM public.slate_items si
      WHERE si.slate_id = s.id
        AND si.episode_hash = o.episode_hash
    ) items ON true
  ), classified AS (
    SELECT CASE
      WHEN dish_id IS NULL THEN 'missing_canonical_identity'
      WHEN resolved_recommendation_event_id IS NULL THEN 'missing_recommendation_event'
      WHEN slate_id IS NULL THEN 'missing_slate'
      WHEN NOT has_point_in_time_run THEN 'missing_point_in_time_run'
      WHEN NOT has_outcome THEN 'missing_outcome'
      WHEN outcome_slate_id IS DISTINCT FROM slate_id THEN 'mismatched_outcome_slate'
      WHEN episode_hash IS NULL THEN 'missing_episode_identity'
      WHEN served_item_match_count = 0 THEN 'no_served_item_match'
      WHEN served_item_match_count > 1 THEN 'ambiguous_served_item_match'
      ELSE 'exact'
    END AS attribution_route
    FROM linked
  ), summary AS (
    SELECT
      count(*) AS labeled_event_count,
      count(*) FILTER (WHERE attribution_route = 'exact') AS exact_event_count
    FROM classified
  )
  SELECT jsonb_build_object(
    'schema_version', 'fresh-preference-attribution-v1',
    'window_started_at', p_since,
    'window_ended_at', statement_timestamp(),
    'labeled_event_count', summary.labeled_event_count,
    'exact_event_count', summary.exact_event_count,
    'inexact_event_count', summary.labeled_event_count - summary.exact_event_count,
    'exact_attribution_rate', CASE
      WHEN summary.labeled_event_count = 0 THEN 0
      ELSE round(summary.exact_event_count::numeric / summary.labeled_event_count, 4)
    END,
    'route_counts', coalesce((
      SELECT jsonb_object_agg(attribution_route, event_count ORDER BY attribution_route)
      FROM (
        SELECT attribution_route, count(*) AS event_count
        FROM classified
        GROUP BY attribution_route
      ) routes
    ), '{}'::jsonb),
    'slo', jsonb_build_object(
      'minimum_sample_size', 20,
      'target_exact_attribution_rate', 0.9500,
      'status', CASE
        WHEN summary.labeled_event_count < 20 THEN 'insufficient_sample'
        WHEN summary.exact_event_count::numeric / summary.labeled_event_count >= 0.95 THEN 'pass'
        ELSE 'fail'
      END
    ),
    'policy', jsonb_build_object(
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
    )
  )
  INTO v_report
  FROM summary;

  RETURN v_report;
END;
$function$;

REVOKE ALL ON FUNCTION ml.fresh_preference_attribution_report(timestamptz)
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION ml.fresh_preference_attribution_report(timestamptz) TO service_role;

COMMENT ON FUNCTION ml.fresh_preference_attribution_report(timestamptz) IS
  'Returns aggregate exact-attribution SLO routes for recent real feedback; bounded to 90 days and changes no feedback, outcome, training or serving state.';
