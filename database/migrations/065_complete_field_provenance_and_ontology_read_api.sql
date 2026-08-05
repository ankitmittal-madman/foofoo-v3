-- Complete field-level provenance and expose one governed ontology read model to the Edge API.

ALTER TABLE public.dish_taxonomy_assertions
  ADD COLUMN extraction_method text NOT NULL DEFAULT 'unspecified',
  ADD COLUMN source_version text,
  ADD COLUMN last_verified_at timestamptz NOT NULL DEFAULT now();

ALTER TABLE public.dish_meal_class_mappings
  ADD COLUMN source_record_id uuid REFERENCES public.food_source_records(id) ON DELETE SET NULL,
  ADD COLUMN last_verified_at timestamptz NOT NULL DEFAULT now();

ALTER TABLE public.dish_constraints
  ADD COLUMN source_record_id uuid REFERENCES public.food_source_records(id) ON DELETE SET NULL,
  ADD COLUMN source_url text,
  ADD COLUMN extraction_method text NOT NULL DEFAULT 'unspecified',
  ADD COLUMN model_name text,
  ADD COLUMN model_version text,
  ADD COLUMN last_verified_at timestamptz NOT NULL DEFAULT now(),
  ADD CONSTRAINT dish_constraints_ml_model_name CHECK (source_type <> 'ml_model' OR model_name IS NOT NULL);

ALTER TABLE public.dish_regional_affinities
  ADD COLUMN source_record_id uuid REFERENCES public.food_source_records(id) ON DELETE SET NULL,
  ADD COLUMN source_url text,
  ADD COLUMN extraction_method text NOT NULL DEFAULT 'unspecified',
  ADD COLUMN model_name text,
  ADD COLUMN model_version text,
  ADD COLUMN last_verified_at timestamptz NOT NULL DEFAULT now(),
  ADD CONSTRAINT dish_regional_affinities_ml_model_name CHECK (source_type <> 'ml_model' OR model_name IS NOT NULL);

ALTER TABLE public.dish_ingredients
  ADD COLUMN source_name text NOT NULL DEFAULT 'foofoo_catalogue_v1',
  ADD COLUMN source_type text NOT NULL DEFAULT 'internal_research' CHECK (
    source_type IN ('user','internal_research','external_api','rules','ml_model','human_review')
  ),
  ADD COLUMN source_record_id uuid REFERENCES public.food_source_records(id) ON DELETE SET NULL,
  ADD COLUMN source_url text,
  ADD COLUMN extraction_method text NOT NULL DEFAULT 'catalogue_import',
  ADD COLUMN model_name text,
  ADD COLUMN model_version text,
  ADD COLUMN confidence numeric(4,3) NOT NULL DEFAULT 0.850 CHECK (confidence BETWEEN 0 AND 1),
  ADD COLUMN review_status text NOT NULL DEFAULT 'provisional' CHECK (
    review_status IN ('provisional','accepted','rejected')
  ),
  ADD COLUMN last_verified_at timestamptz NOT NULL DEFAULT now(),
  ADD COLUMN updated_at timestamptz NOT NULL DEFAULT now(),
  ADD CONSTRAINT dish_ingredients_ml_model_name CHECK (source_type <> 'ml_model' OR model_name IS NOT NULL);

ALTER TABLE public.dish_name_synonyms
  ADD COLUMN source_record_id uuid REFERENCES public.food_source_records(id) ON DELETE SET NULL,
  ADD COLUMN extraction_method text NOT NULL DEFAULT 'catalogue_import',
  ADD COLUMN source_version text,
  ADD COLUMN review_status text NOT NULL DEFAULT 'provisional' CHECK (
    review_status IN ('provisional','accepted','rejected')
  ),
  ADD COLUMN last_verified_at timestamptz NOT NULL DEFAULT now(),
  ADD COLUMN created_at timestamptz NOT NULL DEFAULT now(),
  ADD COLUMN updated_at timestamptz NOT NULL DEFAULT now();

ALTER TABLE food.nutrient_assertions
  ADD COLUMN last_verified_at timestamptz NOT NULL DEFAULT now();

CREATE INDEX dish_ingredients_source_record ON public.dish_ingredients(source_record_id)
  WHERE source_record_id IS NOT NULL;
CREATE INDEX dish_constraints_source_record ON public.dish_constraints(source_record_id)
  WHERE source_record_id IS NOT NULL;
CREATE INDEX dish_regional_affinities_source_record ON public.dish_regional_affinities(source_record_id)
  WHERE source_record_id IS NOT NULL;

CREATE OR REPLACE FUNCTION public.get_dish_ontology_record(
  p_dish_id uuid DEFAULT NULL,
  p_name text DEFAULT NULL
)
RETURNS jsonb
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = public, food, pg_temp
AS $$
DECLARE
  v_dish_id uuid;
  v_record jsonb;
BEGIN
  IF p_dish_id IS NULL AND nullif(btrim(p_name), '') IS NULL THEN
    RAISE EXCEPTION 'dish_id_or_name_required';
  END IF;

  SELECT d.id INTO v_dish_id
  FROM public.dishes d
  WHERE (p_dish_id IS NOT NULL AND d.id = p_dish_id)
     OR (p_dish_id IS NULL AND lower(d.name) = lower(btrim(p_name)))
  ORDER BY (d.id = p_dish_id) DESC
  LIMIT 1;

  IF v_dish_id IS NULL AND nullif(btrim(p_name), '') IS NOT NULL THEN
    SELECT s.dish_id INTO v_dish_id
    FROM public.dish_name_synonyms s
    WHERE lower(s.synonym) = lower(btrim(p_name))
      AND s.review_status <> 'rejected'
    ORDER BY s.confidence DESC NULLS LAST, s.dish_id
    LIMIT 1;
  END IF;

  IF v_dish_id IS NULL THEN RETURN NULL; END IF;

  SELECT jsonb_build_object(
    'schema_version', '1',
    'dish', to_jsonb(d) || jsonb_build_object('cuisine', c.name),
    'aliases', coalesce((
      SELECT jsonb_agg(to_jsonb(s) - 'dish_id' ORDER BY s.confidence DESC NULLS LAST, s.synonym)
      FROM public.dish_name_synonyms s WHERE s.dish_id = v_dish_id
    ), '[]'::jsonb),
    'ingredients', coalesce((
      SELECT jsonb_agg(
        (to_jsonb(di) - 'dish_id' - 'ingredient_id') || jsonb_build_object(
          'ingredient_id', i.id, 'name', i.name, 'allergen_flags', i.allergen_flags,
          'is_veg', i.is_veg, 'is_vegan', i.is_vegan, 'is_jain_excluded', i.is_jain_excluded
        ) ORDER BY i.name
      )
      FROM public.dish_ingredients di JOIN public.ingredients i ON i.id = di.ingredient_id
      WHERE di.dish_id = v_dish_id AND di.review_status <> 'rejected'
    ), '[]'::jsonb),
    'meal_classes', coalesce((
      SELECT jsonb_agg(to_jsonb(m) - 'dish_id' ORDER BY m.slot, m.class_code)
      FROM public.dish_meal_class_mappings m
      WHERE m.dish_id = v_dish_id AND m.review_status <> 'rejected'
    ), '[]'::jsonb),
    'taxonomy', coalesce((
      SELECT jsonb_agg(
        (to_jsonb(a) - 'dish_id' - 'submission_id') || jsonb_build_object(
          'selected_at', cur.selected_at, 'selected_by', cur.selected_by,
          'term', CASE WHEN t.id IS NULL THEN NULL ELSE jsonb_build_object(
            'id', t.id, 'dimension', t.dimension, 'code', t.code, 'name', t.display_name
          ) END
        ) ORDER BY a.field_key
      )
      FROM public.dish_taxonomy_current cur
      JOIN public.dish_taxonomy_assertions a ON a.id = cur.assertion_id
      LEFT JOIN public.taxonomy_terms t ON t.id = a.term_id
      WHERE cur.dish_id = v_dish_id
    ), '[]'::jsonb),
    'constraints', coalesce((
      SELECT jsonb_agg(to_jsonb(x) - 'dish_id' ORDER BY x.constraint_code)
      FROM public.dish_constraints x
      WHERE x.dish_id = v_dish_id AND x.review_status <> 'rejected'
    ), '[]'::jsonb),
    'regional_affinities', coalesce((
      SELECT jsonb_agg(to_jsonb(r) - 'dish_id' ORDER BY r.affinity_score DESC, r.region_code)
      FROM public.dish_regional_affinities r
      WHERE r.dish_id = v_dish_id AND r.review_status <> 'rejected'
    ), '[]'::jsonb),
    'nutrition', coalesce((
      SELECT jsonb_agg(
        (to_jsonb(n) - 'dish_id' - 'ingredient_id' - 'recipe_id' - 'nutrient_id') ||
        jsonb_build_object('nutrient_code', u.nutrient_code, 'display_name', u.display_name,
          'unit_code', u.unit_code)
        ORDER BY u.nutrient_code, n.version DESC
      )
      FROM food.nutrient_assertions n JOIN food.nutrients u ON u.id = n.nutrient_id
      WHERE n.dish_id = v_dish_id AND n.review_status <> 'rejected'
    ), '[]'::jsonb),
    'recipes', coalesce((
      SELECT jsonb_agg(
        (to_jsonb(r) - 'dish_id') || jsonb_build_object(
          'steps', coalesce((SELECT jsonb_agg(to_jsonb(rs) - 'recipe_id' ORDER BY rs.step_number)
            FROM food.recipe_steps rs WHERE rs.recipe_id = r.id), '[]'::jsonb),
          'ingredients', coalesce((SELECT jsonb_agg(
            (to_jsonb(ri) - 'recipe_id' - 'ingredient_id') ||
            jsonb_build_object('ingredient_id', i.id, 'name', i.name) ORDER BY i.name)
            FROM food.recipe_ingredients ri JOIN public.ingredients i ON i.id = ri.ingredient_id
            WHERE ri.recipe_id = r.id), '[]'::jsonb)
        ) ORDER BY r.locale, r.version DESC
      ) FROM food.recipes r WHERE r.dish_id = v_dish_id AND r.review_status <> 'rejected'
    ), '[]'::jsonb),
    'meal_episodes', coalesce((
      SELECT jsonb_agg(
        (to_jsonb(e) - 'shared_base_dish_id') || jsonb_build_object(
          'components', coalesce((SELECT jsonb_agg(
            (to_jsonb(ec) - 'episode_id' - 'dish_id' - 'recipe_id') ||
            jsonb_build_object('dish_id', cd.id, 'dish_name', cd.name, 'recipe_id', ec.recipe_id)
            ORDER BY ec.sequence, ec.component_role)
            FROM food.meal_episode_components ec JOIN public.dishes cd ON cd.id = ec.dish_id
            WHERE ec.episode_id = e.id), '[]'::jsonb)
        ) ORDER BY e.version DESC, e.episode_code
      )
      FROM food.meal_episodes e
      WHERE e.shared_base_dish_id = v_dish_id OR EXISTS (
        SELECT 1 FROM food.meal_episode_components ec
        WHERE ec.episode_id = e.id AND ec.dish_id = v_dish_id
      )
    ), '[]'::jsonb),
    'relationships', coalesce((
      SELECT jsonb_agg(rel.payload ORDER BY rel.predicate_code, rel.other_label)
      FROM (
        SELECT e.predicate_code, o.label AS other_label,
          jsonb_build_object('direction','outgoing','predicate',e.predicate_code,
            'other_node',to_jsonb(o),'weight',e.weight,'confidence',e.confidence,
            'source_name',e.source_name,'source_version',e.source_version,
            'review_status',e.review_status,'effective_from',e.effective_from,
            'effective_to',e.effective_to) AS payload
        FROM food.ontology_nodes s JOIN food.ontology_edges e ON e.subject_node_id = s.id
        JOIN food.ontology_nodes o ON o.id = e.object_node_id
        WHERE s.node_type = 'dish' AND s.canonical_entity_id = v_dish_id
          AND e.review_status <> 'rejected' AND o.status <> 'retired'
        UNION ALL
        SELECT e.predicate_code, s.label AS other_label,
          jsonb_build_object('direction','incoming','predicate',e.predicate_code,
            'other_node',to_jsonb(s),'weight',e.weight,'confidence',e.confidence,
            'source_name',e.source_name,'source_version',e.source_version,
            'review_status',e.review_status,'effective_from',e.effective_from,
            'effective_to',e.effective_to) AS payload
        FROM food.ontology_nodes o JOIN food.ontology_edges e ON e.object_node_id = o.id
        JOIN food.ontology_nodes s ON s.id = e.subject_node_id
        WHERE o.node_type = 'dish' AND o.canonical_entity_id = v_dish_id
          AND e.review_status <> 'rejected' AND s.status <> 'retired'
      ) rel
    ), '[]'::jsonb),
    'evidence', coalesce((
      SELECT jsonb_agg(jsonb_build_object(
        'id', f.id, 'provider', f.provider, 'provider_record_id', f.provider_record_id,
        'query_text', f.query_text, 'source_url', f.source_url,
        'payload_sha256', f.payload_sha256, 'fetched_at', f.fetched_at
      ) ORDER BY f.fetched_at DESC)
      FROM public.food_source_records f WHERE f.dish_id = v_dish_id
    ), '[]'::jsonb)
  ) INTO v_record
  FROM public.dishes d LEFT JOIN public.cuisines c ON c.id = d.cuisine_id
  WHERE d.id = v_dish_id;

  RETURN v_record;
END;
$$;

REVOKE ALL ON FUNCTION public.get_dish_ontology_record(uuid,text) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.get_dish_ontology_record(uuid,text) TO service_role;

COMMENT ON FUNCTION public.get_dish_ontology_record(uuid,text) IS
  'Service-only governed dish read model: canonical data, field provenance, recipes, episodes, graph and evidence metadata.';
