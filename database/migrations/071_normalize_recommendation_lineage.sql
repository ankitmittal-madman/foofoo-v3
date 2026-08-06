-- Migration: 071_normalize_recommendation_lineage.sql
-- Normalizes the live episode-serving trace into request, context, feature, run, candidate and
-- stage facts. Existing slates are losslessly backfilled from fields already persisted; no
-- historical score, filter reason or context value is invented.

CREATE TABLE public.recommendation_requests (
  request_id text PRIMARY KEY,
  household_id uuid NOT NULL REFERENCES public.households(id) ON DELETE CASCADE,
  surface text NOT NULL,
  meal_slot_code text,
  request_payload jsonb NOT NULL DEFAULT '{}',
  input_hash text NOT NULL,
  request_status text NOT NULL DEFAULT 'completed' CHECK (
    request_status IN ('received','running','completed','failed','timed_out')
  ),
  requested_at timestamptz NOT NULL DEFAULT now(),
  completed_at timestamptz
);
CREATE INDEX recommendation_requests_household_time
  ON public.recommendation_requests(household_id,requested_at DESC);

CREATE TABLE public.context_snapshots (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  request_id text NOT NULL UNIQUE REFERENCES public.recommendation_requests(request_id) ON DELETE CASCADE,
  household_id uuid NOT NULL REFERENCES public.households(id) ON DELETE CASCADE,
  snapshot_hash text NOT NULL,
  values jsonb NOT NULL DEFAULT '{}',
  source_times jsonb NOT NULL DEFAULT '{}',
  captured_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX context_snapshots_household_time ON public.context_snapshots(household_id,captured_at DESC);

CREATE TABLE ml.feature_snapshots (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  request_id text NOT NULL UNIQUE REFERENCES public.recommendation_requests(request_id) ON DELETE CASCADE,
  household_id uuid NOT NULL REFERENCES public.households(id) ON DELETE CASCADE,
  feature_set_version text NOT NULL,
  snapshot_hash text NOT NULL,
  values jsonb NOT NULL DEFAULT '{}',
  source_watermarks jsonb NOT NULL DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX feature_snapshots_household_time ON ml.feature_snapshots(household_id,created_at DESC);

CREATE TABLE public.recommendation_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  request_id text NOT NULL REFERENCES public.recommendation_requests(request_id) ON DELETE CASCADE,
  attempt_no smallint NOT NULL DEFAULT 1 CHECK (attempt_no>0),
  slate_id uuid UNIQUE REFERENCES public.slates(id) ON DELETE SET NULL,
  context_snapshot_id uuid REFERENCES public.context_snapshots(id) ON DELETE RESTRICT,
  feature_snapshot_id uuid REFERENCES ml.feature_snapshots(id) ON DELETE RESTRICT,
  household_snapshot_hash text NOT NULL,
  engine_version text NOT NULL,
  model_version text NOT NULL,
  config_version text NOT NULL,
  catalog_version text,
  policy_version text NOT NULL,
  run_status text NOT NULL CHECK (run_status IN ('running','success','failed','timed_out')),
  candidate_count integer NOT NULL DEFAULT 0 CHECK (candidate_count>=0),
  safe_candidate_count integer NOT NULL DEFAULT 0 CHECK (safe_candidate_count>=0),
  latency_ms integer CHECK (latency_ms IS NULL OR latency_ms>=0),
  trace_checksum text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(request_id,attempt_no)
);

CREATE TABLE public.recommendation_candidates (
  recommendation_run_id uuid NOT NULL REFERENCES public.recommendation_runs(id) ON DELETE CASCADE,
  candidate_item_hash text NOT NULL,
  episode_id uuid REFERENCES food.meal_episodes(id) ON DELETE SET NULL,
  generator_codes text[] NOT NULL DEFAULT '{}',
  generator_scores jsonb NOT NULL DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY(recommendation_run_id,candidate_item_hash)
);

CREATE TABLE public.recommendation_candidate_stages (
  recommendation_run_id uuid NOT NULL,
  candidate_item_hash text NOT NULL,
  stage_sequence smallint NOT NULL CHECK(stage_sequence>0),
  stage_code text NOT NULL,
  is_eligible boolean NOT NULL,
  reason_codes text[] NOT NULL DEFAULT '{}',
  score_contributions jsonb NOT NULL DEFAULT '{}',
  rank_after_stage smallint CHECK(rank_after_stage IS NULL OR rank_after_stage>0),
  safety_gate_result text,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY(recommendation_run_id,candidate_item_hash,stage_sequence),
  FOREIGN KEY(recommendation_run_id,candidate_item_hash)
    REFERENCES public.recommendation_candidates(recommendation_run_id,candidate_item_hash)
    ON DELETE CASCADE
);
CREATE INDEX recommendation_candidate_stages_run_stage
  ON public.recommendation_candidate_stages(recommendation_run_id,stage_code,rank_after_stage);

ALTER TABLE public.slates ADD COLUMN recommendation_run_id uuid UNIQUE
  REFERENCES public.recommendation_runs(id) ON DELETE SET NULL;

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
    ),
    coalesce(p_payload->'feature_source_watermarks','{}'))
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

-- Backfill only facts already present in slates and slate_items.
INSERT INTO public.recommendation_requests(request_id,household_id,surface,meal_slot_code,
  request_payload,input_hash,request_status,requested_at,completed_at)
SELECT s.request_id,s.household_id,s.surface,s.context_snapshot->>'slot',s.context_snapshot,
  coalesce(s.household_snapshot_hash,s.eligible_set_hash,s.id::text),'completed',s.created_at,s.created_at
FROM public.slates s ON CONFLICT(request_id) DO NOTHING;

INSERT INTO public.context_snapshots(request_id,household_id,snapshot_hash,values,captured_at)
SELECT s.request_id,s.household_id,coalesce(s.eligible_set_hash,s.id::text),s.context_snapshot,s.created_at
FROM public.slates s ON CONFLICT(request_id) DO NOTHING;

INSERT INTO ml.feature_snapshots(request_id,household_id,feature_set_version,snapshot_hash,values,created_at)
SELECT s.request_id,s.household_id,'legacy-slate-v1',coalesce(s.eligible_set_hash,s.id::text),
  jsonb_build_object('source','slate_items','available_only',true),s.created_at
FROM public.slates s ON CONFLICT(request_id) DO NOTHING;

INSERT INTO public.recommendation_runs(request_id,attempt_no,slate_id,context_snapshot_id,
  feature_snapshot_id,household_snapshot_hash,engine_version,model_version,config_version,
  catalog_version,policy_version,run_status,candidate_count,safe_candidate_count,trace_checksum,created_at)
SELECT s.request_id,1,s.id,c.id,f.id,coalesce(s.household_snapshot_hash,s.id::text),s.model_version,
  s.model_version,s.config_version,s.catalog_version,s.policy_code,'success',
  (SELECT count(*) FROM public.slate_items i WHERE i.slate_id=s.id),
  (SELECT count(*) FROM public.slate_items i WHERE i.slate_id=s.id),
  coalesce(s.eligible_set_hash,s.id::text),s.created_at
FROM public.slates s JOIN public.context_snapshots c ON c.request_id=s.request_id
JOIN ml.feature_snapshots f ON f.request_id=s.request_id
ON CONFLICT(request_id,attempt_no) DO NOTHING;

INSERT INTO public.recommendation_candidates(recommendation_run_id,candidate_item_hash,episode_id,
  generator_codes,generator_scores,created_at)
SELECT r.id,i.episode_hash,i.episode_id,i.generator_codes,
  jsonb_build_object('point_score',i.point_score,'rerank_score',i.rerank_score,
    'predicted_choose',i.predicted_choose,'predicted_execute',i.predicted_execute,
    'predicted_regret',i.predicted_regret),s.created_at
FROM public.recommendation_runs r JOIN public.slates s ON s.id=r.slate_id
JOIN public.slate_items i ON i.slate_id=s.id ON CONFLICT DO NOTHING;

INSERT INTO public.recommendation_candidate_stages(recommendation_run_id,candidate_item_hash,
  stage_sequence,stage_code,is_eligible,reason_codes,score_contributions,rank_after_stage,
  safety_gate_result,created_at)
SELECT r.id,i.episode_hash,1,'served_rank',true,i.reason_tags,
  jsonb_build_object('point_score',i.point_score,'rerank_score',i.rerank_score),i.rank,
  'passed_upstream',s.created_at
FROM public.recommendation_runs r JOIN public.slates s ON s.id=r.slate_id
JOIN public.slate_items i ON i.slate_id=s.id ON CONFLICT DO NOTHING;

UPDATE public.slates s SET recommendation_run_id=r.id FROM public.recommendation_runs r
WHERE r.slate_id=s.id AND s.recommendation_run_id IS NULL;

ALTER TABLE public.recommendation_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.context_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.recommendation_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.recommendation_candidates ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.recommendation_candidate_stages ENABLE ROW LEVEL SECURITY;
ALTER TABLE ml.feature_snapshots ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.recommendation_requests,public.context_snapshots,public.recommendation_runs,
  public.recommendation_candidates,public.recommendation_candidate_stages FROM PUBLIC,anon,authenticated;
REVOKE ALL ON ml.feature_snapshots FROM PUBLIC,anon,authenticated;
GRANT SELECT,INSERT,UPDATE,DELETE ON public.recommendation_requests,public.context_snapshots,
  public.recommendation_runs,public.recommendation_candidates,
  public.recommendation_candidate_stages,ml.feature_snapshots TO service_role;
REVOKE ALL ON FUNCTION public.record_episode_recommendation_lineage(jsonb) FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.record_episode_recommendation_lineage(jsonb) TO service_role;

COMMENT ON FUNCTION public.record_episode_recommendation_lineage(jsonb) IS
  'Atomically persists normalized request/run/snapshot/candidate-stage evidence before serving an episode slate.';
