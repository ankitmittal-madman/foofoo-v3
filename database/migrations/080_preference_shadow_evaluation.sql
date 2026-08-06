-- Aggregate, service-role-only evidence for shadow-model calibration. No household-level rows
-- are exposed. Exact item attribution and point-in-time snapshots remain prerequisites.

CREATE OR REPLACE FUNCTION ml.preference_shadow_evaluation()
RETURNS TABLE (
  model_version text,
  observations bigint,
  positive_events bigint,
  negative_events bigint,
  brier_score numeric,
  log_loss numeric,
  mean_positive_prediction numeric,
  mean_negative_prediction numeric
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public, ml, pg_temp
AS $$
  WITH attributed AS (
    SELECT
      coalesce(
        i.decision_trace #>> '{dish_snapshot,shadow_preference_model_version}',
        i.decision_trace #>> '{episode_snapshot,components,0,shadow_preference_model_version}'
      ) AS version,
      least(0.999999, greatest(0.000001, coalesce(
        (i.decision_trace #>> '{dish_snapshot,shadow_preference_score}')::numeric,
        (i.decision_trace #>> '{episode_snapshot,shadow_preference_mean}')::numeric
      ))) AS prediction,
      CASE WHEN f.event_type IN ('accept', 'like', 'make_this', 'cooked', 'completed')
        THEN 1 ELSE 0 END AS label
    FROM public.feedback_events f
    JOIN public.recommendation_events r ON r.id = f.recommendation_event_id
    JOIN public.slates s
      ON s.household_id = r.household_id AND s.request_id = r.request_id
    JOIN public.recommendation_runs rr ON rr.slate_id = s.id AND rr.run_status = 'success'
    JOIN ml.feature_snapshots fs ON fs.id = rr.feature_snapshot_id
    JOIN public.outcome_events o
      ON o.idempotency_key = f.id AND o.slate_id = s.id AND o.episode_hash IS NOT NULL
    JOIN public.slate_items i
      ON i.slate_id = s.id AND i.episode_hash = o.episode_hash
    WHERE f.data_source = 'real'
      AND f.event_type IN ('accept', 'like', 'make_this', 'cooked', 'completed',
                           'dislike', 'never', 'regretted')
      AND jsonb_typeof(fs.values->'household') = 'object'
      AND fs.values->'household' <> '{}'::jsonb
  )
  SELECT
    version,
    count(*),
    count(*) FILTER (WHERE label = 1),
    count(*) FILTER (WHERE label = 0),
    round(avg(power(prediction - label, 2)), 6),
    round(avg(-(label * ln(prediction) + (1 - label) * ln(1 - prediction))), 6),
    round(avg(prediction) FILTER (WHERE label = 1), 6),
    round(avg(prediction) FILTER (WHERE label = 0), 6)
  FROM attributed
  WHERE version IS NOT NULL AND prediction IS NOT NULL
  GROUP BY version
  ORDER BY version;
$$;

REVOKE ALL ON FUNCTION ml.preference_shadow_evaluation()
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION ml.preference_shadow_evaluation() TO service_role;

COMMENT ON FUNCTION ml.preference_shadow_evaluation() IS
  'Aggregate online calibration evidence by immutable shadow model version; service role only.';

CREATE OR REPLACE FUNCTION ml.preference_training_export_rows()
RETURNS SETOF jsonb
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public, ml, pg_temp
AS $$
  SELECT jsonb_build_object(
    'household', fs.values->'household',
    'ctx', cs.values,
    'dish_name', d.name,
    'event_type', f.event_type,
    'data_source', f.data_source,
    'household_id', f.household_id::text,
    'request_id', r.request_id,
    'slate_id', s.id::text,
    'candidate_item_hash', i.episode_hash,
    'served_point_score', i.point_score,
    'shadow_preference_score', coalesce(
      (i.decision_trace #>> '{dish_snapshot,shadow_preference_score}')::numeric,
      (i.decision_trace #>> '{episode_snapshot,shadow_preference_mean}')::numeric
    ),
    'shadow_preference_model_version', coalesce(
      i.decision_trace #>> '{dish_snapshot,shadow_preference_model_version}',
      i.decision_trace #>> '{episode_snapshot,components,0,shadow_preference_model_version}'
    ),
    'occurred_at', f.created_at
  )
  FROM public.feedback_events f
  JOIN public.recommendation_events r ON r.id = f.recommendation_event_id
  JOIN public.slates s
    ON s.household_id = r.household_id AND s.request_id = r.request_id
  JOIN public.recommendation_runs rr ON rr.slate_id = s.id AND rr.run_status = 'success'
  JOIN ml.feature_snapshots fs ON fs.id = rr.feature_snapshot_id
  JOIN public.context_snapshots cs ON cs.id = rr.context_snapshot_id
  JOIN public.outcome_events o
    ON o.idempotency_key = f.id AND o.slate_id = s.id AND o.episode_hash IS NOT NULL
  JOIN public.slate_items i
    ON i.slate_id = s.id AND i.episode_hash = o.episode_hash
  JOIN public.dishes d ON d.id = f.dish_id
  WHERE f.data_source = 'real'
    AND f.event_type IN ('accept', 'like', 'make_this', 'cooked', 'completed',
                         'dislike', 'never', 'regretted')
    AND jsonb_typeof(fs.values->'household') = 'object'
    AND fs.values->'household' <> '{}'::jsonb
  ORDER BY f.created_at, f.id;
$$;

REVOKE ALL ON FUNCTION ml.preference_training_export_rows()
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION ml.preference_training_export_rows() TO service_role;
