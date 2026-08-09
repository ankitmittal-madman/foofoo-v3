-- Rollback for 130_embedding_meal_class_cuisine_classifier.sql

DROP FUNCTION IF EXISTS public.dishes_missing_meal_class(integer);
DROP FUNCTION IF EXISTS public.classify_dish_by_embedding(uuid, extensions.vector, uuid, numeric, numeric);
DROP FUNCTION IF EXISTS public.nearest_cuisine_by_embedding(extensions.vector);
DROP FUNCTION IF EXISTS public.nearest_meal_class_by_embedding(extensions.vector);

DROP FUNCTION IF EXISTS public.record_ai_low_risk_enrichment(uuid,uuid,text,jsonb,numeric,numeric,text,text);

CREATE OR REPLACE FUNCTION public.record_ai_low_risk_enrichment(
  p_dish_id uuid,p_source_record_id uuid,p_model text,p_payload jsonb,
  p_min_confidence numeric DEFAULT 0.65,p_direct_confidence numeric DEFAULT 0.80
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
        VALUES(p_dish_id,v_class_code,v_slot,'primary',v_conf,'groq','groq_structured_output','ml_model',
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
        VALUES(p_dish_id,'cuisine_candidate',item,v_conf,'groq','ml_model',p_source_record_id,
          p_model,p_model,CASE WHEN v_conf>=p_direct_confidence THEN 'accepted' ELSE 'provisional' END,
          'groq_structured_output',p_model);
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

REVOKE ALL ON FUNCTION public.record_ai_low_risk_enrichment(uuid,uuid,text,jsonb,numeric,numeric) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.record_ai_low_risk_enrichment(uuid,uuid,text,jsonb,numeric,numeric) TO service_role;

CREATE OR REPLACE FUNCTION public.enforce_groq_ontology_field_policy()
RETURNS trigger LANGUAGE plpgsql SET search_path=public,food,pg_temp AS $$
DECLARE v_policy food.ontology_field_policies%ROWTYPE;
BEGIN
  IF NEW.source_name<>'groq' THEN RETURN NEW; END IF;
  SELECT * INTO v_policy FROM food.ontology_field_policies
  WHERE policy_version='groq-low-risk-v1' AND field_key=NEW.field_key
    AND effective_from<=now() AND effective_until IS NULL;
  IF NOT FOUND THEN RAISE EXCEPTION 'groq field is not allowlisted: %',NEW.field_key; END IF;
  IF v_policy.is_safety_field THEN RAISE EXCEPTION 'groq cannot assert safety field: %',NEW.field_key; END IF;
  IF NEW.confidence<v_policy.candidate_threshold THEN
    RAISE EXCEPTION 'groq candidate below field policy threshold';
  END IF;
  IF NEW.review_status='accepted' AND (
    v_policy.auto_publish_threshold IS NULL OR NEW.confidence<v_policy.auto_publish_threshold
  ) THEN RAISE EXCEPTION 'groq accepted assertion below auto-publish threshold'; END IF;
  RETURN NEW;
END $$;

ALTER TABLE public.food_source_records DROP CONSTRAINT IF EXISTS food_source_records_provider_check;
ALTER TABLE public.food_source_records
  ADD CONSTRAINT food_source_records_provider_check
  CHECK (provider IN ('foodon_ols', 'usda_fdc', 'ifct', 'agrovoc', 'groq'));
