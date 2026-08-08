-- Start a truthful forward-only SLO for exact dish-preference attribution.
--
-- Migration 117 proved that the historical seven-day window is dominated by events created
-- before durable dish-slate lineage was enforced. Preserve that evidence, but do not let it mask
-- whether the repaired writer is healthy. Direct meal-class actions are learned by the separate
-- class-affinity path and are intentionally outside the dish-preference model denominator.

CREATE TABLE IF NOT EXISTS ml.preference_attribution_slo_control (
  singleton boolean PRIMARY KEY DEFAULT true CHECK (singleton),
  monitoring_started_at timestamptz NOT NULL DEFAULT statement_timestamp(),
  schema_version text NOT NULL DEFAULT 'fresh-preference-attribution-v2'
    CHECK (schema_version = 'fresh-preference-attribution-v2')
);

INSERT INTO ml.preference_attribution_slo_control (singleton)
VALUES (true)
ON CONFLICT (singleton) DO NOTHING;

REVOKE ALL ON ml.preference_attribution_slo_control FROM PUBLIC, anon, authenticated;
GRANT SELECT ON ml.preference_attribution_slo_control TO service_role;

COMMENT ON TABLE ml.preference_attribution_slo_control IS
  'Singleton cutover for forward-only exact dish-preference attribution monitoring.';

CREATE OR REPLACE FUNCTION ml.fresh_preference_attribution_report(p_since timestamptz)
RETURNS jsonb
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = public, ml, pg_catalog, pg_temp
AS $function$
DECLARE
  v_report jsonb;
  v_monitoring_started_at timestamptz;
  v_effective_since timestamptz;
BEGIN
  IF p_since IS NULL
     OR p_since > statement_timestamp()
     OR p_since < statement_timestamp() - interval '90 days' THEN
    RAISE EXCEPTION 'attribution SLO window must begin within the last 90 days';
  END IF;

  SELECT monitoring_started_at INTO STRICT v_monitoring_started_at
  FROM ml.preference_attribution_slo_control
  WHERE singleton;
  v_effective_since := greatest(p_since, v_monitoring_started_at);

  WITH labeled AS (
    SELECT f.id, f.household_id, f.dish_id, f.recommendation_event_id
    FROM public.feedback_events f
    WHERE f.data_source = 'real'
      AND f.created_at >= v_effective_since
      AND f.event_type IN (
        'accept', 'like', 'make_this', 'cooked', 'completed',
        'dislike', 'never', 'regretted'
      )
      AND (
        f.target_type = 'dish'
        OR (
          f.target_type IS NULL
          AND (f.dish_id IS NOT NULL OR nullif(f.detail->>'dish_name', '') IS NOT NULL)
        )
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
  ), excluded AS (
    SELECT count(*) AS event_count
    FROM public.feedback_events f
    WHERE f.data_source = 'real'
      AND f.created_at >= v_effective_since
      AND f.event_type IN (
        'accept', 'like', 'make_this', 'cooked', 'completed',
        'dislike', 'never', 'regretted'
      )
      AND NOT (
        f.target_type = 'dish'
        OR (
          f.target_type IS NULL
          AND (f.dish_id IS NOT NULL OR nullif(f.detail->>'dish_name', '') IS NOT NULL)
        )
      )
  )
  SELECT jsonb_build_object(
    'schema_version', 'fresh-preference-attribution-v2',
    'requested_window_started_at', p_since,
    'monitoring_started_at', v_monitoring_started_at,
    'effective_window_started_at', v_effective_since,
    'window_ended_at', statement_timestamp(),
    'labeled_event_count', summary.labeled_event_count,
    'excluded_non_dish_event_count', excluded.event_count,
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
      'cutover_aware', true,
      'dish_preference_targets_only', true,
      'point_in_time_features_required', true,
      'exact_served_item_required', true,
      'feedback_changed', false,
      'outcome_changed', false,
      'training_changed', false,
      'serving_changed', false
    )
  )
  INTO v_report
  FROM summary CROSS JOIN excluded;

  RETURN v_report;
END;
$function$;

REVOKE ALL ON FUNCTION ml.fresh_preference_attribution_report(timestamptz)
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION ml.fresh_preference_attribution_report(timestamptz) TO service_role;

COMMENT ON FUNCTION ml.fresh_preference_attribution_report(timestamptz) IS
  'Returns aggregate forward-only exact-attribution SLO routes for real dish feedback after the governed monitoring cutover.';
