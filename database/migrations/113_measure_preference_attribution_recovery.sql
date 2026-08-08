-- Measure whether legacy real feedback can be recovered into exact point-in-time preference
-- evidence. This report is read-only and aggregate: it never guesses a served item, exposes a
-- household identity, or changes feedback/outcome/training state.

CREATE OR REPLACE FUNCTION ml.preference_attribution_recovery_report()
RETURNS jsonb
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public, ml, pg_catalog, pg_temp
AS $$
  WITH labeled AS (
    SELECT f.id, f.household_id, f.dish_id, f.recommendation_event_id, d.name AS canonical_name
    FROM public.feedback_events f
    LEFT JOIN public.dishes d ON d.id = f.dish_id
    WHERE f.data_source = 'real'
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
      ) AS has_point_in_time_run
    FROM labeled l
    LEFT JOIN public.recommendation_events r
      ON r.id = l.recommendation_event_id
      AND r.household_id = l.household_id
    LEFT JOIN public.slates s
      ON s.household_id = r.household_id
      AND s.request_id = r.request_id
  ), matched AS (
    SELECT
      l.*,
      coalesce(m.match_count, 0) AS match_count,
      m.matched_episode_hash,
      EXISTS (
        SELECT 1
        FROM public.outcome_events o
        WHERE o.idempotency_key = l.id
      ) AS has_existing_outcome,
      EXISTS (
        SELECT 1
        FROM public.outcome_events o
        WHERE o.idempotency_key = l.id
          AND o.slate_id = l.slate_id
          AND o.episode_hash = m.matched_episode_hash
          AND m.match_count = 1
      ) AS is_already_exact
    FROM linked l
    LEFT JOIN LATERAL (
      SELECT
        count(*)::integer AS match_count,
        min(si.episode_hash) AS matched_episode_hash
      FROM public.slate_items si
      WHERE si.slate_id = l.slate_id
        AND (
          si.decision_trace #>> '{dish_snapshot,id}' = l.dish_id::text
          OR lower(si.decision_trace #>> '{dish_snapshot,name}') = lower(l.canonical_name)
          OR lower(si.decision_trace->>'dish_name') = lower(l.canonical_name)
          OR EXISTS (
            SELECT 1
            FROM jsonb_array_elements(
              coalesce(si.decision_trace #> '{episode_snapshot,components}', '[]'::jsonb)
            ) component
            WHERE component->>'dish_id' = l.dish_id::text
              OR lower(component->>'dish_name') = lower(l.canonical_name)
          )
        )
    ) m ON true
  ), classified AS (
    SELECT
      CASE
        WHEN dish_id IS NULL OR canonical_name IS NULL THEN 'missing_canonical_identity'
        WHEN resolved_recommendation_event_id IS NULL THEN 'missing_recommendation_event'
        WHEN slate_id IS NULL THEN 'missing_slate'
        WHEN NOT has_point_in_time_run THEN 'missing_point_in_time_run'
        WHEN match_count = 0 THEN 'no_served_item_match'
        WHEN match_count > 1 THEN 'ambiguous_served_item_match'
        WHEN is_already_exact THEN 'already_exact'
        WHEN has_existing_outcome THEN 'recoverable_incomplete_outcome'
        ELSE 'recoverable_missing_outcome'
      END AS recovery_route
    FROM matched
  )
  SELECT jsonb_build_object(
    'schema_version', 'preference-attribution-recovery-v1',
    'labeled_event_count', (SELECT count(*) FROM classified),
    'route_counts', coalesce((
      SELECT jsonb_object_agg(recovery_route, event_count ORDER BY recovery_route)
      FROM (
        SELECT recovery_route, count(*) AS event_count
        FROM classified
        GROUP BY recovery_route
      ) routes
    ), '{}'::jsonb),
    'already_exact_event_count', (
      SELECT count(*) FROM classified WHERE recovery_route = 'already_exact'
    ),
    'recoverable_event_count', (
      SELECT count(*) FROM classified
      WHERE recovery_route IN ('recoverable_incomplete_outcome', 'recoverable_missing_outcome')
    ),
    'unrecoverable_event_count', (
      SELECT count(*) FROM classified
      WHERE recovery_route NOT IN (
        'already_exact', 'recoverable_incomplete_outcome', 'recoverable_missing_outcome'
      )
    ),
    'policy', jsonb_build_object(
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
    )
  );
$$;

REVOKE ALL ON FUNCTION ml.preference_attribution_recovery_report()
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION ml.preference_attribution_recovery_report() TO service_role;

COMMENT ON FUNCTION ml.preference_attribution_recovery_report() IS
  'Returns aggregate routes for exact legacy preference-attribution recovery; exposes no user/event identity and performs no recovery write.';
