-- Preserve explicit preference outcomes with their true semantics. A like/dislike is valuable
-- supervised signal, but it is not evidence that a meal was cooked or regretted.

ALTER TABLE public.outcome_events
  DROP CONSTRAINT IF EXISTS outcome_events_outcome_type_check;

ALTER TABLE public.outcome_events
  ADD CONSTRAINT outcome_events_outcome_type_check CHECK (
    outcome_type IN (
      'chosen', 'locked', 'cooked', 'ordered', 'replaced', 'completed',
      'liked', 'disliked', 'enjoyed', 'regretted',
      'leftover_created', 'leftover_consumed', 'discarded'
    )
  );

COMMENT ON COLUMN public.outcome_events.outcome_type IS
  'Typed point-in-time outcome. liked/disliked preserve explicit preference without falsely implying execution.';

CREATE INDEX IF NOT EXISTS feedback_events_preference_training_signal
  ON public.feedback_events (household_id, event_type, created_at DESC)
  WHERE data_source = 'real'
    AND event_type IN ('accept', 'like', 'make_this', 'cooked', 'completed',
                       'dislike', 'never', 'regretted');

CREATE OR REPLACE FUNCTION ml.preference_training_readiness(
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
  is_ready boolean
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public, ml, pg_temp
AS $$
  WITH labeled AS (
    SELECT
      f.household_id,
      f.dish_id,
      f.event_type,
      CASE WHEN f.event_type IN ('accept', 'like', 'make_this', 'cooked', 'completed')
        THEN 1 ELSE 0 END AS label,
      EXISTS (
        SELECT 1
        FROM public.recommendation_events r
        JOIN public.slates s
          ON s.household_id = r.household_id AND s.request_id = r.request_id
        JOIN public.outcome_events o
          ON o.idempotency_key = f.id AND o.slate_id = s.id AND o.episode_hash IS NOT NULL
        JOIN public.slate_items i
          ON i.slate_id = s.id AND i.episode_hash = o.episode_hash
        JOIN public.recommendation_runs rr
          ON rr.slate_id = s.id AND rr.run_status = 'success'
        JOIN ml.feature_snapshots fs
          ON fs.id = rr.feature_snapshot_id
        WHERE r.id = f.recommendation_event_id
          AND jsonb_typeof(fs.values->'household') = 'object'
          AND fs.values->'household' <> '{}'::jsonb
      ) AS has_slate
    FROM public.feedback_events f
    WHERE f.data_source = 'real'
      AND f.event_type IN ('accept', 'like', 'make_this', 'cooked', 'completed',
                           'dislike', 'never', 'regretted')
  ), aggregate AS (
    SELECT
      count(*) AS n,
      count(*) FILTER (WHERE label = 1) AS positives,
      count(*) FILTER (WHERE label = 0) AS negatives,
      count(DISTINCT household_id) AS households,
      count(*) FILTER (WHERE dish_id IS NOT NULL) AS identities,
      count(*) FILTER (WHERE has_slate) AS attributed
    FROM labeled
  )
  SELECT
    n,
    positives,
    negatives,
    households,
    identities,
    attributed,
    CASE WHEN n = 0 THEN 0 ELSE round(identities::numeric / n, 4) END,
    CASE WHEN n = 0 THEN 0 ELSE round(attributed::numeric / n, 4) END,
    n >= greatest(p_min_real_events, 1)
      AND households >= greatest(p_min_households, 1)
      AND positives > 0
      AND negatives > 0
      AND identities = n
      AND attributed = n
  FROM aggregate;
$$;

REVOKE ALL ON FUNCTION ml.preference_training_readiness(integer, integer)
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION ml.preference_training_readiness(integer, integer) TO service_role;

COMMENT ON FUNCTION ml.preference_training_readiness(integer, integer) IS
  'Aggregate, non-user-identifying gate for preference-model volume, class balance, identity resolution and point-in-time slate attribution.';

-- Upgrade normalized lineage so future feature snapshots retain the exact, private household
-- feature input used at serving time. Historical rows are left unchanged rather than reconstructed
-- from today's profile, which would create training leakage and false point-in-time evidence.
CREATE OR REPLACE FUNCTION public.record_episode_recommendation_lineage(p_payload jsonb)
RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER
SET search_path=public,ml,food,pg_temp AS $$
DECLARE v_request_id text; v_household_id uuid; v_slate_id uuid; v_context_id uuid;
DECLARE v_feature_id uuid; v_run_id uuid; v_candidate jsonb; v_candidate_count integer;
BEGIN
  v_request_id:=nullif(btrim(p_payload->>'request_id'),'');
  v_household_id=(p_payload->>'household_id')::uuid;
  v_slate_id=(p_payload->>'slate_id')::uuid;
  IF v_request_id IS NULL OR v_household_id IS NULL OR v_slate_id IS NULL THEN
    RAISE EXCEPTION 'request_id, household_id and slate_id are required';
  END IF;
  v_candidate_count:=jsonb_array_length(coalesce(p_payload->'candidates','[]'::jsonb));

  INSERT INTO public.recommendation_requests(request_id,household_id,surface,meal_slot_code,
    request_payload,input_hash,request_status,requested_at,completed_at)
  VALUES(v_request_id,v_household_id,coalesce(p_payload->>'surface','today_meal_episode'),
    p_payload->>'meal_slot_code',coalesce(p_payload->'context','{}'),
    p_payload->>'household_snapshot_hash','completed',now(),now())
  ON CONFLICT(request_id) DO UPDATE SET request_status='completed',completed_at=now();

  INSERT INTO public.context_snapshots(request_id,household_id,snapshot_hash,values,source_times)
  VALUES(v_request_id,v_household_id,p_payload->>'context_snapshot_hash',
    coalesce(p_payload->'context','{}'),coalesce(p_payload->'context_source_times','{}'))
  ON CONFLICT(request_id) DO UPDATE SET snapshot_hash=excluded.snapshot_hash,
    values=excluded.values,source_times=excluded.source_times
  RETURNING id INTO v_context_id;

  INSERT INTO ml.feature_snapshots(request_id,household_id,feature_set_version,snapshot_hash,values,
    source_watermarks)
  VALUES(v_request_id,v_household_id,coalesce(p_payload->>'feature_set_version','episode-online-v1'),
    p_payload->>'feature_snapshot_hash',jsonb_build_object(
      'household',coalesce(p_payload->'household_snapshot','{}'),
      'candidates',coalesce(p_payload->'candidates','[]')
    ),coalesce(p_payload->'feature_source_watermarks','{}'))
  ON CONFLICT(request_id) DO UPDATE SET snapshot_hash=excluded.snapshot_hash,values=excluded.values,
    source_watermarks=excluded.source_watermarks
  RETURNING id INTO v_feature_id;

  INSERT INTO public.recommendation_runs(request_id,attempt_no,slate_id,context_snapshot_id,
    feature_snapshot_id,household_snapshot_hash,engine_version,model_version,config_version,
    catalog_version,policy_version,run_status,candidate_count,safe_candidate_count,latency_ms,trace_checksum)
  VALUES(v_request_id,1,v_slate_id,v_context_id,v_feature_id,p_payload->>'household_snapshot_hash',
    coalesce(p_payload->>'engine_version',p_payload->>'model_version','unknown'),
    coalesce(p_payload->>'model_version','unknown'),coalesce(p_payload->>'config_version','unknown'),
    p_payload->>'catalog_version',coalesce(p_payload->>'policy_version','unknown'),'success',
    v_candidate_count,v_candidate_count,(p_payload->>'latency_ms')::integer,p_payload->>'trace_checksum')
  ON CONFLICT(request_id,attempt_no) DO UPDATE SET slate_id=excluded.slate_id,
    context_snapshot_id=excluded.context_snapshot_id,feature_snapshot_id=excluded.feature_snapshot_id,
    candidate_count=excluded.candidate_count,safe_candidate_count=excluded.safe_candidate_count,
    latency_ms=excluded.latency_ms,trace_checksum=excluded.trace_checksum,run_status='success'
  RETURNING id INTO v_run_id;

  DELETE FROM public.recommendation_candidates WHERE recommendation_run_id=v_run_id;
  FOR v_candidate IN SELECT value FROM jsonb_array_elements(coalesce(p_payload->'candidates','[]')) LOOP
    INSERT INTO public.recommendation_candidates(recommendation_run_id,candidate_item_hash,episode_id,
      generator_codes,generator_scores)
    VALUES(v_run_id,v_candidate->>'candidate_item_hash',(v_candidate->>'episode_id')::uuid,
      ARRAY(SELECT jsonb_array_elements_text(coalesce(v_candidate->'generator_codes','[]'))),
      coalesce(v_candidate->'generator_scores','{}'));
    INSERT INTO public.recommendation_candidate_stages(recommendation_run_id,candidate_item_hash,
      stage_sequence,stage_code,is_eligible,reason_codes,score_contributions,rank_after_stage,
      safety_gate_result)
    VALUES(v_run_id,v_candidate->>'candidate_item_hash',1,'eligible_set',true,
      ARRAY(SELECT jsonb_array_elements_text(coalesce(v_candidate->'reason_codes','[]'))),
      coalesce(v_candidate->'generator_scores','{}'),(v_candidate->>'rank')::smallint,
      'passed_upstream');
  END LOOP;
  UPDATE public.slates SET recommendation_run_id=v_run_id WHERE id=v_slate_id;
  RETURN v_run_id;
END $$;

REVOKE ALL ON FUNCTION public.record_episode_recommendation_lineage(jsonb)
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.record_episode_recommendation_lineage(jsonb) TO service_role;

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

COMMENT ON FUNCTION ml.preference_training_export_rows() IS
  'Service-role-only, point-in-time JSON rows consumed by ghar_re_core.training; excludes unresolved, unattributed and legacy reconstructed events.';
