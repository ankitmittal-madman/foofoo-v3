-- Let trustworthy future evidence unlock preference training without pretending legacy feedback
-- has point-in-time lineage. The v1 gate required attributed_events = all_historical_events,
-- which can never become true once an unattributed legacy event exists.

CREATE OR REPLACE FUNCTION ml.preference_training_readiness_v2(
  p_min_real_events integer DEFAULT 10000,
  p_min_households integer DEFAULT 500
)
RETURNS TABLE (
  real_labeled_events bigint,
  positive_events bigint,
  negative_events bigint,
  distinct_households bigint,
  identity_resolved_events bigint,
  attributed_to_slate_events bigint,
  identity_coverage numeric,
  slate_attribution_coverage numeric,
  eligible_training_events bigint,
  eligible_training_households bigint,
  eligible_positive_events bigint,
  eligible_negative_events bigint,
  is_ready boolean
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public, ml, pg_temp
AS $$
  WITH labeled AS (
    SELECT
      f.id,
      f.household_id,
      f.dish_id,
      f.event_type,
      CASE WHEN f.event_type IN ('accept', 'like', 'make_this', 'cooked', 'completed')
        THEN 1 ELSE 0 END AS label
    FROM public.feedback_events f
    WHERE f.data_source = 'real'
      AND f.event_type IN ('accept', 'like', 'make_this', 'cooked', 'completed',
                           'dislike', 'never', 'regretted')
  ), eligible AS (
    -- Keep this join topology aligned with ml.preference_training_export_rows(). Only rows with
    -- canonical identity, exact served item, successful run and point-in-time features qualify.
    SELECT l.id, l.household_id, l.label
    FROM labeled l
    JOIN public.feedback_events f ON f.id = l.id AND f.dish_id IS NOT NULL
    JOIN public.recommendation_events r ON r.id = f.recommendation_event_id
    JOIN public.slates s
      ON s.household_id = r.household_id AND s.request_id = r.request_id
    JOIN public.recommendation_runs rr ON rr.slate_id = s.id AND rr.run_status = 'success'
    JOIN ml.feature_snapshots fs
      ON fs.id = rr.feature_snapshot_id
      AND jsonb_typeof(fs.values->'household') = 'object'
      AND fs.values->'household' <> '{}'::jsonb
    JOIN public.context_snapshots cs ON cs.id = rr.context_snapshot_id
    JOIN public.outcome_events o
      ON o.idempotency_key = f.id AND o.slate_id = s.id AND o.episode_hash IS NOT NULL
    JOIN public.slate_items i
      ON i.slate_id = s.id AND i.episode_hash = o.episode_hash
    JOIN public.dishes d ON d.id = f.dish_id
  ), all_aggregate AS (
    SELECT
      count(*) AS total,
      count(*) FILTER (WHERE label = 1) AS positives,
      count(*) FILTER (WHERE label = 0) AS negatives,
      count(DISTINCT household_id) AS households,
      count(*) FILTER (WHERE dish_id IS NOT NULL) AS identities
    FROM labeled
  ), eligible_aggregate AS (
    SELECT
      count(*) AS eligible,
      count(DISTINCT household_id) AS households,
      count(*) FILTER (WHERE label = 1) AS positives,
      count(*) FILTER (WHERE label = 0) AS negatives
    FROM eligible
  )
  SELECT
    a.total,
    a.positives,
    a.negatives,
    a.households,
    a.identities,
    e.eligible,
    CASE WHEN a.total = 0 THEN 0 ELSE round(a.identities::numeric / a.total, 4) END,
    CASE WHEN a.total = 0 THEN 0 ELSE round(e.eligible::numeric / a.total, 4) END,
    e.eligible,
    e.households,
    e.positives,
    e.negatives,
    e.eligible >= greatest(p_min_real_events, 1)
      AND e.households >= greatest(p_min_households, 1)
      AND e.positives > 0
      AND e.negatives > 0
  FROM all_aggregate a CROSS JOIN eligible_aggregate e;
$$;

REVOKE ALL ON FUNCTION ml.preference_training_readiness_v2(integer, integer)
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION ml.preference_training_readiness_v2(integer, integer) TO service_role;

COMMENT ON FUNCTION ml.preference_training_readiness_v2(integer, integer) IS
  'Reports overall real-feedback coverage while gating only on exact, export-eligible point-in-time examples; legacy gaps never become fabricated training rows or a permanent accrual deadlock.';
