-- Deterministic, Groq-independent meal_class/cuisine classifier. Migration 128 only used
-- meal_classes.embedding/cuisines.embedding to shrink the Groq prompt -- the actual class/cuisine
-- decision still required an LLM call, so it was still fully blocked by Groq's rate limit (76% of
-- dishes still pending after that change). meal_classes and cuisines are CLOSED, DB-governed
-- vocabularies (not open text) -- there is no reason a nearest-embedding lookup against them needs
-- an LLM in the loop at all. This adds that lookup as a second, independent evidence source and
-- feeds it through the SAME confidence-gated promotion function Groq already uses
-- (record_ai_low_risk_enrichment, migration 126) rather than duplicating publish logic.
--
-- What this does NOT replace: taxonomy (cooking_method, spice_level, ...), aliases, and
-- regional_affinities are open-ended/generative, not closed-vocabulary lookups -- there is no
-- "nearest embedding" answer for those, so they remain Groq-only and will keep lagging behind
-- meal_class/cuisine coverage until the Groq rate limit is separately resolved.
--
-- Correctness fix required first: record_ai_low_risk_enrichment hardcoded source_name='groq' on
-- every insert it makes (aliases, taxonomy, regional_affinities, cuisine_candidate, meal_class
-- mappings), and its policy-enforcement trigger (072's enforce_groq_ontology_field_policy) only
-- applies its confidence-threshold checks when source_name='groq' -- calling it unmodified for
-- embedding evidence would both mislabel provenance as Groq AND let the embedding path skip the
-- 0.65/0.80 field-policy gate entirely (the trigger RETURNs NEW immediately for any other
-- source_name). Fixed by parameterizing source_name/extraction_method (same DROP-then-CREATE
-- pattern as migrations 127/129, defaulted to preserve existing Groq call sites unchanged) and by
-- widening the trigger's gate from source_name='groq' to source_type='ml_model' -- the trigger's
-- actual intent ("govern low-risk AI/model-sourced fields"), not "govern Groq specifically".
-- external_api-sourced rows (FoodOn) are untouched since their source_type is 'external_api'.

ALTER TABLE public.food_source_records DROP CONSTRAINT IF EXISTS food_source_records_provider_check;
ALTER TABLE public.food_source_records
  ADD CONSTRAINT food_source_records_provider_check
  CHECK (provider IN ('foodon_ols', 'usda_fdc', 'ifct', 'agrovoc', 'groq', 'embedding_classifier'));

CREATE OR REPLACE FUNCTION public.enforce_groq_ontology_field_policy()
RETURNS trigger LANGUAGE plpgsql SET search_path=public,food,pg_temp AS $$
DECLARE v_policy food.ontology_field_policies%ROWTYPE;
BEGIN
  IF NEW.source_type<>'ml_model' THEN RETURN NEW; END IF;
  SELECT * INTO v_policy FROM food.ontology_field_policies
  WHERE policy_version='groq-low-risk-v1' AND field_key=NEW.field_key
    AND effective_from<=now() AND effective_until IS NULL;
  IF NOT FOUND THEN RAISE EXCEPTION 'ml_model field is not allowlisted: %',NEW.field_key; END IF;
  IF v_policy.is_safety_field THEN RAISE EXCEPTION 'ml_model source cannot assert safety field: %',NEW.field_key; END IF;
  IF NEW.confidence<v_policy.candidate_threshold THEN
    RAISE EXCEPTION 'ml_model candidate below field policy threshold';
  END IF;
  IF NEW.review_status='accepted' AND (
    v_policy.auto_publish_threshold IS NULL OR NEW.confidence<v_policy.auto_publish_threshold
  ) THEN RAISE EXCEPTION 'ml_model accepted assertion below auto-publish threshold'; END IF;
  RETURN NEW;
END $$;

COMMENT ON FUNCTION public.enforce_groq_ontology_field_policy() IS
  'Field-policy gate for low-risk ml_model-sourced ontology assertions (food.ontology_field_policies, '
  'migration 072). Widened in migration 130 from source_name=''groq'' to source_type=''ml_model'' so '
  'the embedding classifier (migration 130) is governed by the same 0.65/0.80 thresholds Groq always '
  'was, instead of silently bypassing the trigger under a different source_name. Function name kept '
  'for compatibility; trigger wiring (dish_taxonomy_assertions_groq_field_policy) is unchanged.';

DROP FUNCTION IF EXISTS public.record_ai_low_risk_enrichment(uuid, uuid, text, jsonb, numeric, numeric);

CREATE OR REPLACE FUNCTION public.record_ai_low_risk_enrichment(
  p_dish_id uuid, p_source_record_id uuid, p_model text, p_payload jsonb,
  p_min_confidence numeric DEFAULT 0.65, p_direct_confidence numeric DEFAULT 0.80,
  p_source_name text DEFAULT 'groq', p_extraction_method text DEFAULT 'groq_structured_output'
)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=public,ops,ml,pg_temp AS $$
DECLARE item jsonb; v_conf numeric; v_term_id uuid; v_assertion_id uuid;
DECLARE v_candidates integer:=0; v_published integer:=0; v_run_id uuid;
DECLARE v_class_code text; v_slot text; v_cuisine_id uuid;
BEGIN
  IF p_min_confidence<0.5 OR p_direct_confidence<p_min_confidence OR p_direct_confidence>1 THEN
    RAISE EXCEPTION 'invalid confidence policy';
  END IF;

  FOR item IN SELECT value FROM jsonb_array_elements(coalesce(p_payload->'aliases','[]'::jsonb)) LOOP
    v_conf:=coalesce((item->>'confidence')::numeric,0);
    IF v_conf>=p_min_confidence AND length(btrim(item->>'name')) BETWEEN 2 AND 160 THEN
      INSERT INTO public.dish_taxonomy_assertions(dish_id,field_key,value_json,confidence,source_name,
        source_type,source_record_id,model_name,model_version,review_status,extraction_method,source_version)
      VALUES(p_dish_id,'alias_candidate',item,v_conf,p_source_name,'ml_model',p_source_record_id,
        p_model,p_model,CASE WHEN v_conf>=p_direct_confidence THEN 'accepted' ELSE 'provisional' END,
        p_extraction_method,p_model);
      v_candidates:=v_candidates+1;
      IF v_conf>=p_direct_confidence THEN
        INSERT INTO public.dish_name_synonyms(dish_id,synonym,data_source,alias_type,region,language,
          source_url,confidence,source_record_id,extraction_method,source_version,review_status,last_verified_at)
        VALUES(p_dish_id,btrim(item->>'name'),'ai_generated',item->>'alias_type',nullif(btrim(item->>'region'),''),
          lower(btrim(item->>'language')),NULL,v_conf,p_source_record_id,p_extraction_method,p_model,
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
      VALUES(p_dish_id,item->>'dimension',v_term_id,v_conf,p_source_name,'ml_model',p_source_record_id,
        p_model,p_model,CASE WHEN v_conf>=p_direct_confidence THEN 'accepted' ELSE 'provisional' END,
        p_extraction_method,p_model) RETURNING id INTO v_assertion_id;
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
      VALUES(p_dish_id,'regional_affinity_candidate',item,v_conf,p_source_name,'ml_model',p_source_record_id,
        p_model,p_model,CASE WHEN v_conf>=p_direct_confidence THEN 'accepted' ELSE 'provisional' END,
        p_extraction_method,p_model);
      v_candidates:=v_candidates+1;
      IF v_conf>=p_direct_confidence THEN
        INSERT INTO public.dish_regional_affinities(dish_id,region_code,affinity_score,confidence,
          source_name,source_type,review_status,source_record_id,extraction_method,model_name,model_version,last_verified_at)
        VALUES(p_dish_id,item->>'region_code',least(1,greatest(0,(item->>'affinity_score')::numeric)),v_conf,
          p_source_name,'ml_model','accepted',p_source_record_id,p_extraction_method,p_model,p_model,now())
        ON CONFLICT(dish_id,region_code) DO UPDATE SET
          affinity_score=excluded.affinity_score,confidence=greatest(public.dish_regional_affinities.confidence,excluded.confidence),
          source_name=excluded.source_name,source_type='ml_model',review_status='accepted',source_record_id=excluded.source_record_id,
          extraction_method=excluded.extraction_method,model_name=excluded.model_name,model_version=excluded.model_version,
          last_verified_at=now(),updated_at=now()
        WHERE public.dish_regional_affinities.review_status<>'accepted'
          AND public.dish_regional_affinities.confidence<=excluded.confidence;
        v_published:=v_published+1;
      END IF;
    END IF;
  END LOOP;

  FOR item IN SELECT value FROM jsonb_array_elements(coalesce(p_payload->'meal_class','[]'::jsonb)) LOOP
    v_conf:=coalesce((item->>'confidence')::numeric,0);
    v_class_code:=item->>'class_code';
    v_slot:=item->>'slot';
    IF v_conf>=p_min_confidence AND v_slot IN ('breakfast','lunch','dinner','snack')
      AND EXISTS (
        SELECT 1 FROM public.meal_classes m
        WHERE m.class_code=v_class_code AND m.is_active AND v_slot=ANY(m.slot)
      )
    THEN
      v_candidates:=v_candidates+1;
      IF v_conf>=p_direct_confidence THEN
        INSERT INTO public.dish_meal_class_mappings(dish_id,class_code,slot,item_role,confidence,
          source_name,classification_method,source_type,model_name,model_version,review_status,source_record_id)
        VALUES(p_dish_id,v_class_code,v_slot,'primary',v_conf,p_source_name,p_extraction_method,'ml_model',
          p_model,p_model,'accepted',p_source_record_id)
        ON CONFLICT(dish_id,class_code,slot) DO UPDATE SET
          confidence=greatest(public.dish_meal_class_mappings.confidence,excluded.confidence),
          review_status='accepted',source_record_id=excluded.source_record_id,updated_at=now()
        WHERE public.dish_meal_class_mappings.review_status<>'accepted';
        v_published:=v_published+1;
      END IF;
    END IF;
  END LOOP;

  IF p_payload ? 'cuisine' AND jsonb_typeof(p_payload->'cuisine')='object' THEN
    item:=p_payload->'cuisine';
    v_conf:=coalesce((item->>'confidence')::numeric,0);
    IF v_conf>=p_min_confidence THEN
      SELECT id INTO v_cuisine_id FROM public.cuisines WHERE lower(name)=lower(item->>'cuisine_name');
      IF v_cuisine_id IS NOT NULL THEN
        INSERT INTO public.dish_taxonomy_assertions(dish_id,field_key,value_json,confidence,source_name,
          source_type,source_record_id,model_name,model_version,review_status,extraction_method,source_version)
        VALUES(p_dish_id,'cuisine_candidate',item,v_conf,p_source_name,'ml_model',p_source_record_id,
          p_model,p_model,CASE WHEN v_conf>=p_direct_confidence THEN 'accepted' ELSE 'provisional' END,
          p_extraction_method,p_model);
        v_candidates:=v_candidates+1;
        IF v_conf>=p_direct_confidence THEN
          UPDATE public.dishes SET cuisine_id=v_cuisine_id
          WHERE id=p_dish_id AND cuisine_id IS NULL;
          IF FOUND THEN v_published:=v_published+1; END IF;
        END IF;
      END IF;
    END IF;
  END IF;

  INSERT INTO ops.ai_generation_runs(model_name,model_version,prompt_version,input_source_ids,
    parameters,output_artifact_uri,validator_result,status)
  VALUES('dish_ontology',p_model,'groq-low-risk-v2',ARRAY[p_source_record_id],
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

COMMENT ON FUNCTION public.record_ai_low_risk_enrichment(uuid,uuid,text,jsonb,numeric,numeric,text,text) IS
  'Publishes only non-safety ontology fields at founder thresholds; nutrition/constraints are '
  'absent by design. p_source_name/p_extraction_method (migration 130) default to groq/'
  'groq_structured_output for compatibility with existing Groq call sites; the embedding classifier '
  'passes embedding_classifier/embedding_gte_small_cosine_similarity instead so provenance is never '
  'mislabeled.';

REVOKE ALL ON FUNCTION public.record_ai_low_risk_enrichment(uuid,uuid,text,jsonb,numeric,numeric,text,text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.record_ai_low_risk_enrichment(uuid,uuid,text,jsonb,numeric,numeric,text,text) TO service_role;

CREATE OR REPLACE FUNCTION public.nearest_meal_class_by_embedding(p_embedding extensions.vector(384))
RETURNS TABLE (class_code text, slot text[], similarity numeric)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path=public,extensions,pg_temp
AS $$
  SELECT m.class_code, m.slot, (1 - (m.embedding <=> p_embedding))::numeric
  FROM public.meal_classes m
  WHERE m.is_active AND m.embedding IS NOT NULL
  ORDER BY m.embedding <=> p_embedding
  LIMIT 1;
$$;

COMMENT ON FUNCTION public.nearest_meal_class_by_embedding(extensions.vector) IS
  'Nearest active meal_classes row by gte-small cosine similarity (1 - cosine distance). Returns '
  'zero rows if no meal_classes have an embedding yet (backfill not run) -- callers must treat '
  'that as "no answer available", not an error.';

REVOKE ALL ON FUNCTION public.nearest_meal_class_by_embedding(extensions.vector) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.nearest_meal_class_by_embedding(extensions.vector) TO service_role;

CREATE OR REPLACE FUNCTION public.nearest_cuisine_by_embedding(p_embedding extensions.vector(384))
RETURNS TABLE (cuisine_name text, similarity numeric)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path=public,extensions,pg_temp
AS $$
  SELECT c.name, (1 - (c.embedding <=> p_embedding))::numeric
  FROM public.cuisines c
  WHERE c.embedding IS NOT NULL
  ORDER BY c.embedding <=> p_embedding
  LIMIT 1;
$$;

COMMENT ON FUNCTION public.nearest_cuisine_by_embedding(extensions.vector) IS
  'Nearest cuisines row by gte-small cosine similarity. Returns zero rows if no cuisines have an '
  'embedding yet.';

REVOKE ALL ON FUNCTION public.nearest_cuisine_by_embedding(extensions.vector) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.nearest_cuisine_by_embedding(extensions.vector) TO service_role;

CREATE OR REPLACE FUNCTION public.classify_dish_by_embedding(
  p_dish_id uuid,
  p_query_embedding extensions.vector(384),
  p_source_record_id uuid,
  p_min_confidence numeric DEFAULT 0.55,
  p_direct_confidence numeric DEFAULT 0.80
)
RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path=public,ops,ml,pg_temp
AS $$
DECLARE
  v_class record;
  v_cuisine record;
  v_payload jsonb := jsonb_build_object(
    'aliases', '[]'::jsonb, 'taxonomy', '[]'::jsonb, 'regional_affinities', '[]'::jsonb
  );
  v_meal_class jsonb := '[]'::jsonb;
BEGIN
  SELECT * INTO v_class FROM public.nearest_meal_class_by_embedding(p_query_embedding);
  IF FOUND AND v_class.similarity >= p_min_confidence THEN
    SELECT jsonb_agg(jsonb_build_object(
      'class_code', v_class.class_code, 'slot', slot_value, 'confidence', v_class.similarity
    ))
    INTO v_meal_class
    FROM unnest(v_class.slot) AS slot_value;
  END IF;
  v_payload := v_payload || jsonb_build_object('meal_class', coalesce(v_meal_class, '[]'::jsonb));

  SELECT * INTO v_cuisine FROM public.nearest_cuisine_by_embedding(p_query_embedding);
  IF FOUND AND v_cuisine.similarity >= p_min_confidence THEN
    v_payload := v_payload || jsonb_build_object(
      'cuisine', jsonb_build_object('cuisine_name', v_cuisine.cuisine_name, 'confidence', v_cuisine.similarity)
    );
  ELSE
    v_payload := v_payload || jsonb_build_object('cuisine', NULL);
  END IF;

  RETURN public.record_ai_low_risk_enrichment(
    p_dish_id, p_source_record_id, 'embedding-gte-small', v_payload, p_min_confidence, p_direct_confidence,
    'embedding_classifier', 'embedding_gte_small_cosine_similarity'
  );
END;
$$;

COMMENT ON FUNCTION public.classify_dish_by_embedding(uuid, extensions.vector, uuid, numeric, numeric) IS
  'Groq-independent meal_class/cuisine classifier: builds a Groq-shaped payload from nearest-'
  'embedding lookups and passes it through the SAME confidence-gated promotion function '
  '(record_ai_low_risk_enrichment) Groq output uses, tagged with its own source_name so provenance '
  'is never mislabeled as Groq. p_min_confidence defaults to 0.55 (looser than Groq''s 0.65) since '
  'raw cosine similarity between a short dish name and a short class/cuisine label runs lower than '
  'a model''s own stated confidence for the same judgement; still gated by the same field policy '
  '(migration 072/130), still requires 0.80 to auto-publish rather than stay a review candidate.';

REVOKE ALL ON FUNCTION public.classify_dish_by_embedding(uuid, extensions.vector, uuid, numeric, numeric) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.classify_dish_by_embedding(uuid, extensions.vector, uuid, numeric, numeric) TO service_role;

-- cron-embedding-classifier's second selection pass: dishes with no dish_meal_class_mappings row
-- at all yet. Kept as its own RPC (rather than inline in the worker's query builder call) since
-- "no matching child row exists" isn't expressible through a single supabase-js filter chain.
CREATE OR REPLACE FUNCTION public.dishes_missing_meal_class(p_limit integer DEFAULT 30)
RETURNS TABLE (id uuid, name text)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path=public,pg_temp
AS $$
  SELECT d.id, d.name
  FROM public.dishes d
  WHERE NOT EXISTS (
    SELECT 1 FROM public.dish_meal_class_mappings m WHERE m.dish_id = d.id
  )
  LIMIT p_limit;
$$;

COMMENT ON FUNCTION public.dishes_missing_meal_class(integer) IS
  'Dishes with zero dish_meal_class_mappings rows -- feeds cron-embedding-classifier''s batch '
  'selection alongside its direct cuisine_id IS NULL query.';

REVOKE ALL ON FUNCTION public.dishes_missing_meal_class(integer) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.dishes_missing_meal_class(integer) TO service_role;
