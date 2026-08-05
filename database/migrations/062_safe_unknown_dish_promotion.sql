-- Conservative automatic promotion for user-submitted dishes.
-- Exact external identity plus fully known ingredients may create a canonical draft. Safety,
-- class and AI-inferred fields remain governed and cannot be bypassed by this function.

CREATE OR REPLACE FUNCTION public.promote_submission_if_safe(p_submission_id uuid)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
  v_submission public.dish_submissions%ROWTYPE;
  v_dish_id uuid;
  v_slots text[];
  v_ingredient_names text[];
  v_cook_minutes integer;
  v_difficulty text;
  v_cuisine_id uuid;
  v_requested_count integer;
  v_known_count integer;
BEGIN
  SELECT * INTO v_submission
  FROM public.dish_submissions
  WHERE id = p_submission_id
  FOR UPDATE;
  IF NOT FOUND THEN RETURN NULL; END IF;
  IF v_submission.canonical_dish_id IS NOT NULL THEN RETURN v_submission.canonical_dish_id; END IF;

  SELECT coalesce(array_agg(j.value), '{}') INTO v_slots
  FROM jsonb_array_elements_text(coalesce(v_submission.submitted_metadata->'meal_slots', '[]')) AS j(value)
  WHERE j.value IN ('breakfast','lunch','dinner','snack');
  SELECT coalesce(array_agg(DISTINCT lower(btrim(j.value))), '{}') INTO v_ingredient_names
  FROM jsonb_array_elements_text(coalesce(v_submission.submitted_metadata->'ingredients', '[]')) AS j(value)
  WHERE btrim(j.value) <> '';
  v_requested_count := cardinality(v_ingredient_names);
  SELECT count(DISTINCT lower(i.name)) INTO v_known_count
  FROM public.ingredients i
  WHERE lower(i.name) IN (SELECT lower(j.value) FROM unnest(v_ingredient_names) AS j(value))
    AND i.is_active;

  -- An exact provider match proves identity, not safety. Known ingredients are mandatory.
  IF cardinality(v_slots) = 0 OR v_requested_count = 0 OR v_known_count <> v_requested_count THEN
    RETURN NULL;
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM public.food_source_records r
    WHERE r.submission_id = p_submission_id AND (
      (r.provider = 'foodon_ols' AND lower(r.source_payload#>>'{response,docs,0,label}') = lower(v_submission.entered_name))
      OR
      (r.provider = 'usda_fdc' AND lower(r.source_payload#>>'{foods,0,description}') = lower(v_submission.entered_name))
    )
  ) THEN RETURN NULL; END IF;

  SELECT id INTO v_cuisine_id FROM public.cuisines
  WHERE lower(name) = lower(v_submission.submitted_metadata->>'cuisine')
     OR lower(display_name) = lower(v_submission.submitted_metadata->>'cuisine')
  ORDER BY is_active DESC LIMIT 1;
  v_cook_minutes := greatest(1, least(480,
    coalesce(nullif(v_submission.submitted_metadata->>'cook_time_minutes', '')::integer, 30)));
  v_difficulty := CASE v_submission.submitted_metadata->>'difficulty'
    WHEN 'intermediate' THEN 'intermediate' WHEN 'advanced' THEN 'advanced' ELSE 'beginner' END;

  SELECT id INTO v_dish_id FROM public.dishes WHERE lower(name) = lower(v_submission.entered_name);
  IF v_dish_id IS NULL THEN
    INSERT INTO public.dishes (
      name, name_regional, description, meal_occasion, cook_time_minutes, difficulty, cuisine_id,
      ontology_status, ontology_confidence, ontology_last_reviewed_at
    ) VALUES (
      v_submission.entered_name,
      nullif(v_submission.submitted_metadata->>'regional_name', ''),
      nullif(v_submission.submitted_metadata->>'notes', ''),
      v_slots, v_cook_minutes, v_difficulty, v_cuisine_id,
      'enriched', 0.900, now()
    ) RETURNING id INTO v_dish_id;

    INSERT INTO public.dish_ingredients (dish_id, ingredient_id, is_optional)
    SELECT v_dish_id, i.id, false FROM public.ingredients i
    WHERE lower(i.name) IN (SELECT lower(j.value) FROM unnest(v_ingredient_names) AS j(value))
    ON CONFLICT DO NOTHING;

    INSERT INTO public.dish_name_synonyms (
      dish_id, synonym, data_source, alias_type, language, region, confidence
    )
    SELECT v_dish_id, btrim(j.alias), 'ai_generated', 'common_name', 'en',
           nullif(v_submission.submitted_metadata->>'region', ''), 0.800
    FROM jsonb_array_elements_text(coalesce(v_submission.submitted_metadata->'aliases', '[]')) AS j(alias)
    WHERE btrim(j.alias) <> ''
    ON CONFLICT DO NOTHING;
  END IF;

  UPDATE public.dish_submissions
  SET canonical_dish_id = v_dish_id, status = 'resolved', updated_at = now()
  WHERE id = p_submission_id;
  UPDATE public.dishes
  SET ontology_status = 'enriched', ontology_confidence = 0.900,
      ontology_last_reviewed_at = now(), updated_at = now()
  WHERE id = v_dish_id;
  UPDATE public.dish_enrichment_jobs
  SET status = 'complete', completed_at = now(), external_enriched_at = coalesce(external_enriched_at, now()),
      locked_at = NULL, locked_by = NULL, lease_expires_at = NULL, updated_at = now()
  WHERE submission_id = p_submission_id;
  RETURN v_dish_id;
EXCEPTION WHEN invalid_text_representation THEN
  RETURN NULL;
END;
$$;

REVOKE ALL ON FUNCTION public.promote_submission_if_safe(uuid) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.promote_submission_if_safe(uuid) TO service_role;
