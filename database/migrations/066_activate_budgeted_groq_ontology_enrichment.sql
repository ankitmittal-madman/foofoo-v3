-- Migration: 066_activate_budgeted_groq_ontology_enrichment.sql
-- Adds a provider-independent AI queue, atomic free-tier budgets and governed low-risk publication.
-- Generative AI is structurally unable to write nutrition, allergens, constraints or clinical facts.

CREATE TABLE ops.ai_provider_usage_daily (
  provider text NOT NULL,
  usage_date date NOT NULL DEFAULT current_date,
  requests_used integer NOT NULL DEFAULT 0 CHECK (requests_used >= 0),
  tokens_used bigint NOT NULL DEFAULT 0 CHECK (tokens_used >= 0),
  tokens_reserved bigint NOT NULL DEFAULT 0 CHECK (tokens_reserved >= 0),
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (provider, usage_date)
);

CREATE TABLE ops.ai_dish_enrichment_state (
  dish_id uuid PRIMARY KEY REFERENCES public.dishes(id) ON DELETE CASCADE,
  status text NOT NULL DEFAULT 'pending' CHECK (
    status IN ('pending','running','budget_deferred','complete','failed')
  ),
  attempts smallint NOT NULL DEFAULT 0 CHECK (attempts >= 0),
  next_attempt_at timestamptz NOT NULL DEFAULT now(),
  locked_at timestamptz,
  locked_by text,
  lease_expires_at timestamptz,
  last_error_code text,
  model_name text,
  ai_enriched_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ai_dish_enrichment_due ON ops.ai_dish_enrichment_state(next_attempt_at,created_at)
  WHERE status IN ('pending','budget_deferred','failed');

INSERT INTO ops.ai_dish_enrichment_state(dish_id)
SELECT id FROM public.dishes
ON CONFLICT(dish_id) DO NOTHING;

CREATE OR REPLACE FUNCTION ops.enqueue_ai_dish_enrichment()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path=ops,public,pg_temp AS $$
BEGIN
  INSERT INTO ops.ai_dish_enrichment_state(dish_id,status,next_attempt_at)
  VALUES(NEW.id,'pending',now())
  ON CONFLICT(dish_id) DO UPDATE SET status='pending',attempts=0,next_attempt_at=now(),
    locked_at=NULL,locked_by=NULL,lease_expires_at=NULL,last_error_code=NULL,updated_at=now();
  RETURN NEW;
END $$;
CREATE TRIGGER dishes_queue_ai_ontology_enrichment
AFTER INSERT OR UPDATE OF name,description,meal_occasion,cuisine_id ON public.dishes
FOR EACH ROW EXECUTE FUNCTION ops.enqueue_ai_dish_enrichment();

CREATE OR REPLACE FUNCTION ops.claim_ai_dish_enrichment(
  p_worker_id text,p_batch_size integer DEFAULT 2
)
RETURNS TABLE(dish_id uuid,query_text text,attempts smallint)
LANGUAGE plpgsql SECURITY DEFINER SET search_path=ops,public,pg_temp AS $$
BEGIN
  IF p_worker_id IS NULL OR length(btrim(p_worker_id))<3 THEN RAISE EXCEPTION 'worker id required'; END IF;
  RETURN QUERY
  WITH due AS (
    SELECT s.dish_id FROM ops.ai_dish_enrichment_state s
    WHERE s.status IN ('pending','budget_deferred','failed') AND s.next_attempt_at<=now()
      AND (s.lease_expires_at IS NULL OR s.lease_expires_at<now()) AND s.attempts<8
    ORDER BY s.next_attempt_at,s.created_at FOR UPDATE SKIP LOCKED
    LIMIT greatest(1,least(coalesce(p_batch_size,2),12))
  ), claimed AS (
    UPDATE ops.ai_dish_enrichment_state s SET status='running',attempts=s.attempts+1,
      locked_at=now(),locked_by=p_worker_id,lease_expires_at=now()+interval '5 minutes',updated_at=now()
    FROM due WHERE s.dish_id=due.dish_id RETURNING s.*
  )
  SELECT c.dish_id,d.name,c.attempts FROM claimed c JOIN public.dishes d ON d.id=c.dish_id;
END $$;

CREATE OR REPLACE FUNCTION ops.reserve_ai_provider_budget(
  p_provider text,p_request_limit integer,p_token_limit bigint,p_reserve_tokens bigint
)
RETURNS boolean LANGUAGE plpgsql SECURITY DEFINER SET search_path=ops,pg_temp AS $$
DECLARE affected integer;
BEGIN
  IF p_request_limit<1 OR p_token_limit<1 OR p_reserve_tokens<1 THEN
    RAISE EXCEPTION 'positive AI budgets required';
  END IF;
  INSERT INTO ops.ai_provider_usage_daily(provider,usage_date) VALUES(p_provider,current_date)
  ON CONFLICT(provider,usage_date) DO NOTHING;
  UPDATE ops.ai_provider_usage_daily SET requests_used=requests_used+1,
    tokens_reserved=tokens_reserved+p_reserve_tokens,updated_at=now()
  WHERE provider=p_provider AND usage_date=current_date
    AND requests_used<p_request_limit
    AND tokens_used+tokens_reserved+p_reserve_tokens<=p_token_limit;
  GET DIAGNOSTICS affected=ROW_COUNT;
  RETURN affected=1;
END $$;

CREATE OR REPLACE FUNCTION ops.settle_ai_provider_budget(
  p_provider text,p_reserved_tokens bigint,p_actual_tokens bigint
)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=ops,pg_temp AS $$
BEGIN
  UPDATE ops.ai_provider_usage_daily
  SET tokens_reserved=greatest(0,tokens_reserved-greatest(0,p_reserved_tokens)),
      tokens_used=tokens_used+greatest(0,p_actual_tokens),updated_at=now()
  WHERE provider=p_provider AND usage_date=current_date;
END $$;

CREATE OR REPLACE FUNCTION ops.finish_ai_dish_enrichment(
  p_dish_id uuid,p_worker_id text,p_model_name text,p_status text,p_error text DEFAULT NULL
)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=ops,pg_temp AS $$
BEGIN
  IF p_status NOT IN ('complete','failed','budget_deferred') THEN RAISE EXCEPTION 'invalid AI state'; END IF;
  UPDATE ops.ai_dish_enrichment_state SET status=p_status,model_name=p_model_name,
    ai_enriched_at=CASE WHEN p_status='complete' THEN now() ELSE ai_enriched_at END,
    next_attempt_at=CASE
      WHEN p_status='budget_deferred' THEN date_trunc('day',now())+interval '1 day 5 minutes'
      WHEN p_status='failed' THEN now()+least(interval '1 day',interval '1 minute'*power(2,attempts))
      ELSE next_attempt_at END,
    last_error_code=left(p_error,120),locked_at=NULL,locked_by=NULL,lease_expires_at=NULL,updated_at=now()
  WHERE dish_id=p_dish_id AND locked_by=p_worker_id;
END $$;

CREATE OR REPLACE FUNCTION public.record_ai_low_risk_enrichment(
  p_dish_id uuid,p_source_record_id uuid,p_model text,p_payload jsonb,
  p_min_confidence numeric DEFAULT 0.65,p_direct_confidence numeric DEFAULT 0.80
)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=public,ops,ml,pg_temp AS $$
DECLARE item jsonb; v_conf numeric; v_term_id uuid; v_assertion_id uuid;
DECLARE v_candidates integer:=0; v_published integer:=0; v_run_id uuid;
BEGIN
  IF p_min_confidence<0.5 OR p_direct_confidence<p_min_confidence OR p_direct_confidence>1 THEN
    RAISE EXCEPTION 'invalid confidence policy';
  END IF;

  FOR item IN SELECT value FROM jsonb_array_elements(coalesce(p_payload->'aliases','[]'::jsonb)) LOOP
    v_conf:=coalesce((item->>'confidence')::numeric,0);
    IF v_conf>=p_min_confidence AND length(btrim(item->>'name')) BETWEEN 2 AND 160 THEN
      INSERT INTO public.dish_taxonomy_assertions(dish_id,field_key,value_json,confidence,source_name,
        source_type,source_record_id,model_name,model_version,review_status,extraction_method,source_version)
      VALUES(p_dish_id,'alias_candidate',item,v_conf,'groq','ml_model',p_source_record_id,
        p_model,p_model,CASE WHEN v_conf>=p_direct_confidence THEN 'accepted' ELSE 'provisional' END,
        'groq_structured_output',p_model);
      v_candidates:=v_candidates+1;
      IF v_conf>=p_direct_confidence THEN
        INSERT INTO public.dish_name_synonyms(dish_id,synonym,data_source,alias_type,region,language,
          source_url,confidence,source_record_id,extraction_method,source_version,review_status,last_verified_at)
        VALUES(p_dish_id,btrim(item->>'name'),'ai_generated',item->>'alias_type',nullif(btrim(item->>'region'),''),
          lower(btrim(item->>'language')),NULL,v_conf,p_source_record_id,'groq_structured_output',p_model,
          'accepted',now())
        ON CONFLICT(dish_id,synonym) DO UPDATE SET confidence=greatest(public.dish_name_synonyms.confidence,excluded.confidence),
          source_record_id=excluded.source_record_id,source_version=excluded.source_version,
          last_verified_at=now(),updated_at=now()
        WHERE public.dish_name_synonyms.data_source='ai_generated';
        v_published:=v_published+1;
      END IF;
    END IF;
  END LOOP;

  FOR item IN SELECT value FROM jsonb_array_elements(coalesce(p_payload->'taxonomy','[]'::jsonb)) LOOP
    v_conf:=coalesce((item->>'confidence')::numeric,0);
    IF v_conf>=p_min_confidence AND item->>'dimension' IN
      ('cooking_method','spice_level','heaviness','texture','richness','weather_affinity')
      AND item->>'code' ~ '^[a-z0-9]+(_[a-z0-9]+)*$' THEN
      v_term_id:=NULL;
      INSERT INTO public.taxonomy_terms(dimension,code,display_name)
      VALUES(item->>'dimension',item->>'code',item->>'label')
      ON CONFLICT(dimension,code) DO NOTHING
      RETURNING id INTO v_term_id;
      IF v_term_id IS NULL THEN
        SELECT id INTO v_term_id FROM public.taxonomy_terms
        WHERE dimension=item->>'dimension' AND code=item->>'code';
      END IF;
      INSERT INTO public.dish_taxonomy_assertions(dish_id,field_key,term_id,confidence,source_name,
        source_type,source_record_id,model_name,model_version,review_status,extraction_method,source_version)
      VALUES(p_dish_id,item->>'dimension',v_term_id,v_conf,'groq','ml_model',p_source_record_id,
        p_model,p_model,CASE WHEN v_conf>=p_direct_confidence THEN 'accepted' ELSE 'provisional' END,
        'groq_structured_output',p_model) RETURNING id INTO v_assertion_id;
      v_candidates:=v_candidates+1;
      IF v_conf>=p_direct_confidence AND NOT EXISTS (
        SELECT 1 FROM public.dish_taxonomy_current c
        JOIN public.dish_taxonomy_assertions a ON a.id=c.assertion_id
        WHERE c.dish_id=p_dish_id AND c.field_key=item->>'dimension'
          AND (a.review_status='accepted' OR a.confidence>v_conf)
      ) THEN
        INSERT INTO public.dish_taxonomy_current(dish_id,field_key,assertion_id,selected_by)
        VALUES(p_dish_id,item->>'dimension',v_assertion_id,'ai_auto_confidence_policy')
        ON CONFLICT(dish_id,field_key) DO UPDATE SET assertion_id=excluded.assertion_id,
          selected_at=now(),selected_by=excluded.selected_by;
        v_published:=v_published+1;
      END IF;
    END IF;
  END LOOP;

  FOR item IN SELECT value FROM jsonb_array_elements(coalesce(p_payload->'regional_affinities','[]'::jsonb)) LOOP
    v_conf:=coalesce((item->>'confidence')::numeric,0);
    IF v_conf>=p_min_confidence AND item->>'region_code' ~ '^[a-z0-9]+(_[a-z0-9]+)*$' THEN
      INSERT INTO public.dish_taxonomy_assertions(dish_id,field_key,value_json,confidence,source_name,
        source_type,source_record_id,model_name,model_version,review_status,extraction_method,source_version)
      VALUES(p_dish_id,'regional_affinity_candidate',item,v_conf,'groq','ml_model',p_source_record_id,
        p_model,p_model,CASE WHEN v_conf>=p_direct_confidence THEN 'accepted' ELSE 'provisional' END,
        'groq_structured_output',p_model);
      v_candidates:=v_candidates+1;
      IF v_conf>=p_direct_confidence THEN
        INSERT INTO public.dish_regional_affinities(dish_id,region_code,affinity_score,confidence,
          source_name,source_type,review_status,source_record_id,extraction_method,model_name,model_version,last_verified_at)
        VALUES(p_dish_id,item->>'region_code',least(1,greatest(0,(item->>'affinity_score')::numeric)),v_conf,
          'groq','ml_model','accepted',p_source_record_id,'groq_structured_output',p_model,p_model,now())
        ON CONFLICT(dish_id,region_code) DO UPDATE SET
          affinity_score=excluded.affinity_score,confidence=greatest(public.dish_regional_affinities.confidence,excluded.confidence),
          source_name='groq',source_type='ml_model',review_status='accepted',source_record_id=excluded.source_record_id,
          extraction_method=excluded.extraction_method,model_name=excluded.model_name,model_version=excluded.model_version,
          last_verified_at=now(),updated_at=now()
        WHERE public.dish_regional_affinities.review_status<>'accepted'
          AND public.dish_regional_affinities.confidence<=excluded.confidence;
        v_published:=v_published+1;
      END IF;
    END IF;
  END LOOP;

  INSERT INTO ops.ai_generation_runs(model_name,model_version,prompt_version,input_source_ids,
    parameters,output_artifact_uri,validator_result,status)
  VALUES('dish_ontology',p_model,'groq-low-risk-v1',ARRAY[p_source_record_id],
    jsonb_build_object('min_confidence',p_min_confidence,'direct_confidence',p_direct_confidence),
    'food-source-record://' || p_source_record_id,
    jsonb_build_object('candidate_count',v_candidates,'published_count',v_published,
      'safety_fields_allowed',false),CASE WHEN v_published>0 THEN 'published' ELSE 'validated' END)
  RETURNING id INTO v_run_id;

  IF v_published>0 THEN
    UPDATE public.dishes SET ontology_status='enriched',
      ontology_confidence=greatest(coalesce(ontology_confidence,0),p_direct_confidence),
      ontology_last_reviewed_at=now() WHERE id=p_dish_id;
  END IF;
  RETURN jsonb_build_object('run_id',v_run_id,'candidates',v_candidates,'published',v_published);
END $$;

INSERT INTO ops.data_sources(source_code,owner_name,license_code,source_uri,permitted_uses)
VALUES('groq_free','GroqCloud / selected open model','provider-and-model-terms',
  'https://console.groq.com/docs','{ontology_proposals,low_risk_publication,evaluation}')
ON CONFLICT(source_code) DO UPDATE SET source_uri=excluded.source_uri,permitted_uses=excluded.permitted_uses;

INSERT INTO ml.model_registry(model_name,model_version,objective,training_dataset_uri,artifact_uri,
  artifact_checksum,metrics,slice_metrics,stage,approved_by,activated_at)
VALUES('dish_ontology','openai/gpt-oss-120b','low-risk food ontology enrichment only',
  'none://provider-foundation-model','groq://openai/gpt-oss-120b','groq-openai-gpt-oss-120b',
  '{"confidence_policy":{"usable":0.65,"direct":0.80},"safety_fields_allowed":false}',
  '{}','production','founder-decision-2026-08-05',now())
ON CONFLICT(model_name,model_version) DO UPDATE SET stage='production',activated_at=now(),
  metrics=excluded.metrics,approved_by=excluded.approved_by;

REVOKE ALL ON FUNCTION ops.claim_ai_dish_enrichment(text,integer) FROM PUBLIC,anon,authenticated;
REVOKE ALL ON FUNCTION ops.reserve_ai_provider_budget(text,integer,bigint,bigint) FROM PUBLIC,anon,authenticated;
REVOKE ALL ON FUNCTION ops.settle_ai_provider_budget(text,bigint,bigint) FROM PUBLIC,anon,authenticated;
REVOKE ALL ON FUNCTION ops.finish_ai_dish_enrichment(uuid,text,text,text,text) FROM PUBLIC,anon,authenticated;
REVOKE ALL ON FUNCTION public.record_ai_low_risk_enrichment(uuid,uuid,text,jsonb,numeric,numeric) FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION ops.claim_ai_dish_enrichment(text,integer) TO service_role;
GRANT EXECUTE ON FUNCTION ops.reserve_ai_provider_budget(text,integer,bigint,bigint) TO service_role;
GRANT EXECUTE ON FUNCTION ops.settle_ai_provider_budget(text,bigint,bigint) TO service_role;
GRANT EXECUTE ON FUNCTION ops.finish_ai_dish_enrichment(uuid,text,text,text,text) TO service_role;
GRANT EXECUTE ON FUNCTION public.record_ai_low_risk_enrichment(uuid,uuid,text,jsonb,numeric,numeric) TO service_role;
GRANT SELECT,INSERT,UPDATE ON ops.ai_provider_usage_daily,ops.ai_dish_enrichment_state TO service_role;

COMMENT ON TABLE ops.ai_provider_usage_daily IS
  'Atomic request/token guard for free AI providers; reservations prevent concurrent workers overspending.';
COMMENT ON TABLE ops.ai_dish_enrichment_state IS
  'Independent canonical-dish AI queue; external FoodOn/USDA jobs are never repeated just to run AI.';
COMMENT ON FUNCTION public.record_ai_low_risk_enrichment(uuid,uuid,text,jsonb,numeric,numeric) IS
  'Publishes only non-safety ontology fields at founder thresholds; nutrition/constraints are absent by design.';
