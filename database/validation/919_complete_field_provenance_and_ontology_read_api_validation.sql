DO $$
DECLARE v_dish_id uuid; v_record jsonb;
BEGIN
  IF EXISTS (
    SELECT 1 FROM public.dish_ingredients
    WHERE source_name IS NULL OR source_type IS NULL OR confidence IS NULL
      OR review_status IS NULL OR extraction_method IS NULL OR last_verified_at IS NULL
  ) THEN RAISE EXCEPTION 'dish ingredient provenance is incomplete'; END IF;
  IF EXISTS (
    SELECT 1 FROM public.dish_taxonomy_assertions
    WHERE extraction_method IS NULL OR last_verified_at IS NULL
  ) THEN RAISE EXCEPTION 'taxonomy assertion provenance is incomplete'; END IF;
  IF EXISTS (
    SELECT 1 FROM public.dish_constraints
    WHERE extraction_method IS NULL OR last_verified_at IS NULL
  ) THEN RAISE EXCEPTION 'constraint provenance is incomplete'; END IF;
  IF EXISTS (
    SELECT 1 FROM public.dish_regional_affinities
    WHERE extraction_method IS NULL OR last_verified_at IS NULL
  ) THEN RAISE EXCEPTION 'regional-affinity provenance is incomplete'; END IF;

  SELECT id INTO v_dish_id FROM public.dishes ORDER BY name LIMIT 1;
  v_record := public.get_dish_ontology_record(v_dish_id, NULL);
  IF v_record IS NULL OR v_record->'dish'->>'id' <> v_dish_id::text THEN
    RAISE EXCEPTION 'ontology read model failed canonical dish resolution';
  END IF;
  IF jsonb_typeof(v_record->'ingredients') <> 'array'
     OR jsonb_typeof(v_record->'meal_classes') <> 'array'
     OR jsonb_typeof(v_record->'taxonomy') <> 'array'
     OR jsonb_typeof(v_record->'constraints') <> 'array'
     OR jsonb_typeof(v_record->'regional_affinities') <> 'array'
     OR jsonb_typeof(v_record->'nutrition') <> 'array'
     OR jsonb_typeof(v_record->'recipes') <> 'array'
     OR jsonb_typeof(v_record->'meal_episodes') <> 'array'
     OR jsonb_typeof(v_record->'relationships') <> 'array'
     OR jsonb_typeof(v_record->'evidence') <> 'array' THEN
    RAISE EXCEPTION 'ontology read model is missing a required collection';
  END IF;
END $$;

SELECT public.get_dish_ontology_record(id,NULL)->'dish'->>'name' AS sample_name
FROM public.dishes ORDER BY name LIMIT 1;
