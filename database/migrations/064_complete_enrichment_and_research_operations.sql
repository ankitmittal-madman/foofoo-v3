-- Complete refresh/requeue controls and bind consented research participants to users.

ALTER TABLE research.participants ADD COLUMN user_id uuid REFERENCES auth.users(id) ON DELETE SET NULL;
CREATE UNIQUE INDEX research_participants_study_user ON research.participants(study_id,user_id) WHERE user_id IS NOT NULL;

CREATE OR REPLACE FUNCTION public.record_external_nutrient_assertion(
  p_dish_id uuid,p_nutrient_code text,p_display_name text,p_unit_code text,p_expected_value numeric,
  p_serving_basis text,p_source_record_id uuid,p_confidence numeric
)
RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=public,food,pg_temp AS $$
DECLARE v_nutrient_id uuid; v_assertion_id uuid;
BEGIN
  INSERT INTO food.nutrients(nutrient_code,display_name,unit_code,source_name)
  VALUES(p_nutrient_code,p_display_name,p_unit_code,'usda_fdc')
  ON CONFLICT(nutrient_code) DO UPDATE SET display_name=excluded.display_name
  RETURNING id INTO v_nutrient_id;
  INSERT INTO food.nutrient_assertions(dish_id,nutrient_id,expected_value,serving_basis,method_code,
    source_name,source_record_id,confidence,review_status)
  VALUES(p_dish_id,v_nutrient_id,p_expected_value,p_serving_basis,'usda_search_top_match','usda_fdc',
    p_source_record_id,p_confidence,'provisional') RETURNING id INTO v_assertion_id;
  RETURN v_assertion_id;
END $$;
REVOKE ALL ON FUNCTION public.record_external_nutrient_assertion(uuid,text,text,text,numeric,text,uuid,numeric) FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.record_external_nutrient_assertion(uuid,text,text,text,numeric,text,uuid,numeric) TO service_role;

CREATE OR REPLACE FUNCTION public.reconcile_dish_enrichment_jobs()
RETURNS integer
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp
AS $$
DECLARE affected integer;
BEGIN
  INSERT INTO public.dish_enrichment_jobs (dish_id, missing_fields)
  SELECT d.id, ARRAY['external_evidence']::text[] FROM public.dishes d
  WHERE NOT EXISTS (SELECT 1 FROM public.dish_enrichment_jobs j WHERE j.dish_id=d.id)
  ON CONFLICT DO NOTHING;

  UPDATE public.dish_enrichment_jobs SET status='pending_external',next_attempt_at=now(),
    completed_at=NULL,last_error_code=NULL,updated_at=now()
  WHERE status='complete' AND source_refresh_after<=now();

  UPDATE public.dish_enrichment_jobs SET status='failed',last_error_code='lease_expired',
    next_attempt_at=now(),locked_at=NULL,locked_by=NULL,lease_expires_at=NULL,updated_at=now()
  WHERE lease_expires_at<now() AND locked_by IS NOT NULL;
  GET DIAGNOSTICS affected = ROW_COUNT;
  RETURN affected;
END;
$$;

CREATE OR REPLACE FUNCTION ops.requeue_external_provider(p_provider text)
RETURNS integer
LANGUAGE plpgsql SECURITY DEFINER SET search_path = ops, public, pg_temp
AS $$
DECLARE affected integer;
BEGIN
  IF p_provider NOT IN ('foodon_ols','usda_fdc') THEN RAISE EXCEPTION 'unsupported provider'; END IF;
  UPDATE public.dish_enrichment_jobs j SET status='pending_external',attempts=0,next_attempt_at=now(),
    completed_at=NULL,last_error_code=NULL,locked_at=NULL,locked_by=NULL,lease_expires_at=NULL,updated_at=now()
  WHERE j.dish_id IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM public.food_source_records r WHERE r.dish_id=j.dish_id AND r.provider=p_provider
  );
  GET DIAGNOSTICS affected=ROW_COUNT;
  RETURN affected;
END;
$$;
REVOKE ALL ON FUNCTION ops.requeue_external_provider(text) FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION ops.requeue_external_provider(text) TO service_role;

DO $$ BEGIN
  GRANT SELECT,INSERT,UPDATE ON research.participants,research.meal_diaries TO service_role;
EXCEPTION WHEN undefined_object THEN NULL;
END $$;

CREATE OR REPLACE FUNCTION public.research_participation_status(p_user_id uuid)
RETURNS jsonb LANGUAGE sql STABLE SECURITY DEFINER SET search_path=research,public,pg_temp AS $$
  SELECT coalesce(jsonb_agg(jsonb_build_object('study_id',p.study_id,'participant_id',p.participant_id,
    'enrolled_at',p.enrolled_at,'study_code',s.study_code,'purpose_text',s.purpose_text,'study_status',s.study_status)), '[]')
  FROM research.participants p JOIN research.studies s ON s.id=p.study_id
  WHERE p.user_id=p_user_id AND p.withdrawn_at IS NULL;
$$;
REVOKE ALL ON FUNCTION public.research_participation_status(uuid) FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.research_participation_status(uuid) TO service_role;

CREATE OR REPLACE FUNCTION public.research_submit_meal_diary(p_user_id uuid,p_payload jsonb)
RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=research,public,pg_temp AS $$
DECLARE v_participant research.participants%ROWTYPE; v_id uuid;
BEGIN
  SELECT * INTO v_participant FROM research.participants WHERE user_id=p_user_id
    AND study_id=(p_payload->>'study_id')::uuid AND withdrawn_at IS NULL;
  IF NOT FOUND THEN RAISE EXCEPTION 'research_enrollment_required'; END IF;
  INSERT INTO research.meal_diaries(study_id,participant_id,occurred_at,meal_slot_code,
    planned_episode_hash,actual_components,portions,cook_effort,pantry_evidence,leftover_result,
    satisfaction,media_uri)
  VALUES(v_participant.study_id,v_participant.participant_id,
    coalesce((p_payload->>'occurred_at')::timestamptz,now()),p_payload->>'meal_slot_code',
    p_payload->>'planned_episode_hash',coalesce(p_payload->'actual_components','[]'),
    coalesce(p_payload->'portions','{}'),coalesce(p_payload->'cook_effort','{}'),
    coalesce(p_payload->'pantry_evidence','{}'),coalesce(p_payload->'leftover_result','{}'),
    coalesce(p_payload->'satisfaction','{}'),p_payload->>'media_uri') RETURNING id INTO v_id;
  RETURN v_id;
END $$;
REVOKE ALL ON FUNCTION public.research_submit_meal_diary(uuid,jsonb) FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.research_submit_meal_diary(uuid,jsonb) TO service_role;

CREATE OR REPLACE FUNCTION public.research_create_annotation_batch(p_payload jsonb)
RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=research,pg_temp AS $$
DECLARE v_id uuid; BEGIN
  INSERT INTO research.annotation_batches(corpus_version,handbook_version,task_type_code,
    sampling_method_code,required_reviewers,agreement_threshold,batch_status)
  VALUES(p_payload->>'corpus_version',p_payload->>'handbook_version',p_payload->>'task_type_code',
    coalesce(p_payload->>'sampling_method_code','manual'),greatest(1,coalesce((p_payload->>'required_reviewers')::smallint,2)),
    coalesce((p_payload->>'agreement_threshold')::numeric,0.8),'active') RETURNING id INTO v_id;
  RETURN v_id;
END $$;
CREATE OR REPLACE FUNCTION public.research_queue_annotation_items(p_batch_id uuid,p_items jsonb)
RETURNS integer LANGUAGE plpgsql SECURITY DEFINER SET search_path=research,pg_temp AS $$
DECLARE affected integer; BEGIN
  INSERT INTO research.annotation_items(batch_id,item_key,subject_type,subject_id,evidence_payload,priority)
  SELECT p_batch_id,coalesce(x.item_key,x.subject_id),coalesce(x.subject_type,'dish'),x.subject_id,
    coalesce(x.evidence_payload,'{}'),coalesce(x.priority,0)
  FROM jsonb_to_recordset(p_items) x(item_key text,subject_type text,subject_id text,evidence_payload jsonb,priority smallint)
  ON CONFLICT(batch_id,item_key) DO UPDATE SET evidence_payload=excluded.evidence_payload,priority=excluded.priority;
  GET DIAGNOSTICS affected=ROW_COUNT; RETURN affected;
END $$;
CREATE OR REPLACE FUNCTION public.research_record_annotation(p_payload jsonb)
RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=research,pg_temp AS $$
DECLARE v_item research.annotation_items%ROWTYPE; v_id uuid; BEGIN
  SELECT * INTO v_item FROM research.annotation_items WHERE id=(p_payload->>'annotation_item_id')::uuid
    AND locked_by=p_payload->>'annotator_token' FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'annotation_lease_required'; END IF;
  INSERT INTO research.annotations(batch_id,item_id,annotation_item_id,annotator_token,labels,confidence)
  VALUES(v_item.batch_id,v_item.item_key,v_item.id,p_payload->>'annotator_token',coalesce(p_payload->'labels','{}'),
    (p_payload->>'confidence')::numeric)
  ON CONFLICT(batch_id,item_id,annotator_token) DO UPDATE SET labels=excluded.labels,confidence=excluded.confidence,submitted_at=now()
  RETURNING id INTO v_id;
  UPDATE research.annotation_items SET item_status='submitted',lease_expires_at=NULL WHERE id=v_item.id;
  RETURN v_id;
END $$;
CREATE OR REPLACE FUNCTION public.research_claim_annotation_items(p_batch_id uuid,p_annotator_token text,p_limit integer DEFAULT 10)
RETURNS jsonb LANGUAGE sql SECURITY DEFINER SET search_path=research,pg_temp AS $$
  SELECT coalesce(jsonb_agg(to_jsonb(x)), '[]') FROM research.claim_annotation_items(p_batch_id,p_annotator_token,p_limit) x;
$$;
REVOKE ALL ON FUNCTION public.research_create_annotation_batch(jsonb),public.research_queue_annotation_items(uuid,jsonb),public.research_record_annotation(jsonb),public.research_claim_annotation_items(uuid,text,integer) FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.research_create_annotation_batch(jsonb),public.research_queue_annotation_items(uuid,jsonb),public.research_record_annotation(jsonb),public.research_claim_annotation_items(uuid,text,integer) TO service_role;
