-- Extends public.record_ai_low_risk_enrichment (066) to promote meal_class and cuisine
-- candidates from supabase/functions/dish-ontology/ai.ts's extended Groq schema.
--
-- Why this was needed: migration 125's audit found the safety fields were wrong on many dishes,
-- but a separate investigation (2026-08-08) found the *structural* blocker for the largest gap
-- bucket (1,683 dishes missing meal-class mapping, per ops/recommendation/catalogue_gap_report.py)
-- is that this AI pipeline's schema never had meal_class or cuisine fields at all — every one of
-- the 4,720 rows in public.dish_enrichment_jobs already shows status='complete', yet those dishes
-- remain unmapped, because the pipeline was never built to produce that data, independent of how
-- many times it runs. This migration closes that gap the same way aliases/taxonomy/regional
-- affinities are already handled: below p_min_confidence -> recorded as an audit-only candidate
-- (dish_taxonomy_assertions), at/above p_direct_confidence -> published to the real table.
--
-- meal_class and cuisine are CLOSED, foreign-keyed vocabularies (public.meal_classes,
-- public.cuisines), unlike taxonomy_terms' open/growing vocabulary — so unlike the taxonomy branch
-- below, this function never inserts a new meal_classes or cuisines row. A class_code/cuisine_name
-- that doesn't match an existing active row is silently dropped (not published, not even recorded
-- as a candidate) rather than invented into the schema. The model is also given the real code list
-- in its prompt (ai.ts's ClosedVocabulary), so this should be a rare fallback, not the common case.
--
-- Safety posture unchanged: meal_class/cuisine are structural/geographic facts, not diet, Jain, or
-- allergen data — the "generative AI is structurally unable to write nutrition, allergens,
-- constraints or clinical facts" comment from migration 066 still holds.

-- food.ontology_field_policies (072) allowlists which field_key values ml_model-sourced rows may
-- write to dish_taxonomy_assertions (enforced by the dish_taxonomy_assertions_groq_field_policy
-- trigger). 'cuisine_candidate' is new in this migration and needs its own policy row at the same
-- low-risk 0.65/0.80 thresholds as alias_candidate/regional_affinity_candidate — otherwise every
-- cuisine candidate insert below fails with "groq field is not allowlisted", as confirmed by a
-- live test call against production before this row was added.
INSERT INTO food.ontology_field_policies(policy_version,field_key,risk_tier,
  required_source_types,candidate_threshold,auto_publish_threshold,human_review_count,
  is_safety_field,is_primary_required,approved_by,policy_checksum)
VALUES('groq-low-risk-v1','cuisine_candidate','low',ARRAY['ml_model'],0.65,0.80,0,false,false,
  'ankit-mittal-session-2026-08-08','groq-low-risk-v1-065-080-safety-excluded')
ON CONFLICT DO NOTHING;

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

  -- meal_class: closed vocabulary (public.meal_classes). Unlike taxonomy_terms, never invents a
  -- new class_code — a code/slot combination that isn't an active meal_classes row (with that slot
  -- in its own slot array) is dropped entirely, not even recorded as a candidate, since there is no
  -- taxonomy_assertions-equivalent staging table for meal-class membership and inventing an
  -- unvalidated candidate row would misrepresent it as reviewable evidence.
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

  -- cuisine: closed vocabulary (public.cuisines), single FK field on public.dishes (not a
  -- multi-row table like the others above). Only ever fills a NULL cuisine_id — never overwrites
  -- an existing value, whether that value came from a human, the original ETL import, or an
  -- earlier AI run. Below p_direct_confidence, the guess is recorded as a candidate assertion for
  -- future human review rather than silently discarded.
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

COMMENT ON FUNCTION public.record_ai_low_risk_enrichment(uuid,uuid,text,jsonb,numeric,numeric) IS
  'Publishes only non-safety ontology fields at founder thresholds; nutrition/constraints are '
  'absent by design. Extended in migration 126 to also promote meal_class (public.meal_classes, '
  'closed vocabulary, never invents a new class_code) and cuisine (public.cuisines, closed '
  'vocabulary, only ever fills a NULL dishes.cuisine_id, never overwrites).';

-- Read-only helper for the cron worker to fetch the current closed vocabulary once per invocation
-- and pass it into every generateGroqDishEnrichment() call, instead of hardcoding it in ai.ts
-- where it would silently drift from the live tables.
CREATE OR REPLACE FUNCTION public.ai_enrichment_closed_vocabulary()
RETURNS jsonb
LANGUAGE sql STABLE SECURITY DEFINER SET search_path=public,pg_temp
AS $$
  SELECT jsonb_build_object(
    'class_codes', coalesce((SELECT jsonb_agg(class_code ORDER BY class_code) FROM public.meal_classes WHERE is_active), '[]'::jsonb),
    'cuisine_names', coalesce((SELECT jsonb_agg(name ORDER BY name) FROM public.cuisines), '[]'::jsonb)
  );
$$;

COMMENT ON FUNCTION public.ai_enrichment_closed_vocabulary() IS
  'Live class_code/cuisine name lists for the dish-ontology Groq prompt (ai.ts ClosedVocabulary). '
  'Always reflects the current public.meal_classes/public.cuisines rows — never hardcoded in '
  'application code, since those tables can gain or lose rows independently of a deploy.';

REVOKE ALL ON FUNCTION public.ai_enrichment_closed_vocabulary() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.ai_enrichment_closed_vocabulary() TO service_role;
