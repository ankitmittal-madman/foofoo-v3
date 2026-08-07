-- Publish a bounded, safety-closed recommendation catalogue from production facts.
--
-- This is a read boundary, not a serving switch. It lets an offline publisher stream approved
-- rows without scanning public.dishes through a client API or copying user data. The current
-- immutable 810-dish bundle remains the production fallback until shadow parity is proven.

CREATE INDEX IF NOT EXISTS idx_dishes_catalogue_publication
  ON public.dishes (id)
  WHERE is_active
    AND ontology_status = 'enriched'
    AND diet_type IS NOT NULL
    AND is_jain IS NOT NULL
    AND allergen_flags IS NOT NULL;

CREATE OR REPLACE FUNCTION re_engine.catalogue_publication_coverage()
RETURNS TABLE (
  active_dishes bigint,
  enriched_dishes bigint,
  safety_closed_dishes bigint,
  class_mapped_dishes bigint,
  publishable_dishes bigint
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public, re_engine, pg_temp
AS $$
  SELECT
    count(*) FILTER (WHERE d.is_active),
    count(*) FILTER (WHERE d.is_active AND d.ontology_status = 'enriched'),
    count(*) FILTER (
      WHERE d.is_active
        AND d.ontology_status = 'enriched'
        AND d.diet_type IS NOT NULL
        AND d.is_jain IS NOT NULL
        AND d.allergen_flags IS NOT NULL
    ),
    count(*) FILTER (
      WHERE d.is_active
        AND EXISTS (
          SELECT 1
          FROM public.dish_meal_class_mappings m
          WHERE m.dish_id = d.id
            AND m.review_status <> 'rejected'
        )
    ),
    count(*) FILTER (
      WHERE d.is_active
        AND d.ontology_status = 'enriched'
        AND d.diet_type IS NOT NULL
        AND d.is_jain IS NOT NULL
        AND d.allergen_flags IS NOT NULL
        AND d.cuisine_id IS NOT NULL
        AND EXISTS (
          SELECT 1
          FROM public.dish_ingredients di
          WHERE di.dish_id = d.id
            AND di.review_status <> 'rejected'
        )
        AND EXISTS (
          SELECT 1
          FROM public.dish_meal_class_mappings m
          WHERE m.dish_id = d.id
            AND m.review_status <> 'rejected'
        )
        AND ARRAY[
          'hero_role', 'spice_level', 'heaviness', 'cooking_method', 'texture',
          'richness', 'weather_affinity', 'meal_type'
        ]::text[] <@ ARRAY(
          SELECT cur.field_key
          FROM public.dish_taxonomy_current cur
          JOIN public.dish_taxonomy_assertions a ON a.id = cur.assertion_id
          WHERE cur.dish_id = d.id
            AND a.review_status <> 'rejected'
        )
    )
  FROM public.dishes d;
$$;

CREATE OR REPLACE FUNCTION re_engine.catalogue_publication_rows(
  p_after uuid DEFAULT NULL,
  p_limit integer DEFAULT 500
)
RETURNS SETOF jsonb
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public, re_engine, pg_temp
AS $$
  SELECT jsonb_build_object(
    'schema_version', 'recommendation-catalogue-row-v1',
    'id', d.id,
    'name', d.name,
    'description', d.description,
    'meal_slots', d.meal_occasion,
    'cook_time_minutes', d.cook_time_minutes,
    'difficulty', d.difficulty,
    'diet_type', d.diet_type,
    'is_jain', d.is_jain,
    'allergen_flags', d.allergen_flags,
    'popularity_score', d.popularity_score,
    'acceptance_rate_7d', d.acceptance_rate_7d,
    'acceptance_rate_30d', d.acceptance_rate_30d,
    'calories', d.calories,
    'serving_size', d.serving_size,
    'food_dna_tier_1', d.food_dna_tier_1,
    'ontology_confidence', d.ontology_confidence,
    'catalogue_updated_at', d.updated_at,
    'cuisine', CASE WHEN c.id IS NULL THEN NULL ELSE jsonb_build_object(
      'name', c.name,
      'group', c.cuisine_group,
      'state_origin', c.state_origin
    ) END,
    'ingredients', coalesce((
      SELECT jsonb_agg(jsonb_build_object(
        'id', i.id,
        'name', i.name,
        'is_optional', di.is_optional,
        'is_main_ingredient', di.is_main_ingredient,
        'allergen_flags', i.allergen_flags,
        'is_veg', i.is_veg,
        'is_vegan', i.is_vegan,
        'is_jain_excluded', i.is_jain_excluded,
        'confidence', di.confidence,
        'review_status', di.review_status
      ) ORDER BY i.name, i.id)
      FROM public.dish_ingredients di
      JOIN public.ingredients i ON i.id = di.ingredient_id
      WHERE di.dish_id = d.id
        AND di.review_status <> 'rejected'
        AND i.is_active
    ), '[]'::jsonb),
    'meal_classes', coalesce((
      SELECT jsonb_agg(jsonb_build_object(
        'class_code', m.class_code,
        'slot', m.slot,
        'item_role', m.item_role,
        'confidence', m.confidence,
        'review_status', m.review_status
      ) ORDER BY m.slot, m.class_code, m.item_role)
      FROM public.dish_meal_class_mappings m
      WHERE m.dish_id = d.id
        AND m.review_status <> 'rejected'
    ), '[]'::jsonb),
    'aliases', coalesce((
      SELECT jsonb_agg(s.synonym ORDER BY s.confidence DESC NULLS LAST, s.synonym)
      FROM public.dish_name_synonyms s
      WHERE s.dish_id = d.id
        AND s.review_status <> 'rejected'
    ), '[]'::jsonb),
    'taxonomy', coalesce((
      SELECT jsonb_object_agg(
        a.field_key,
        CASE
          WHEN t.code IS NOT NULL THEN to_jsonb(t.code)
          WHEN a.value_text IS NOT NULL THEN to_jsonb(a.value_text)
          ELSE a.value_json
        END
      )
      FROM public.dish_taxonomy_current cur
      JOIN public.dish_taxonomy_assertions a ON a.id = cur.assertion_id
      LEFT JOIN public.taxonomy_terms t ON t.id = a.term_id
      WHERE cur.dish_id = d.id
        AND a.review_status <> 'rejected'
    ), '{}'::jsonb),
    'regional_affinities', coalesce((
      SELECT jsonb_agg(jsonb_build_object(
        'region_code', r.region_code,
        'affinity_score', r.affinity_score,
        'confidence', r.confidence,
        'review_status', r.review_status
      ) ORDER BY r.affinity_score DESC, r.region_code)
      FROM public.dish_regional_affinities r
      WHERE r.dish_id = d.id
        AND r.review_status <> 'rejected'
    ), '[]'::jsonb)
  )
  FROM public.dishes d
  LEFT JOIN public.cuisines c ON c.id = d.cuisine_id
  WHERE (p_after IS NULL OR d.id > p_after)
    AND d.is_active
    AND d.ontology_status = 'enriched'
    AND d.diet_type IS NOT NULL
    AND d.is_jain IS NOT NULL
    AND d.allergen_flags IS NOT NULL
    AND d.cuisine_id IS NOT NULL
    AND EXISTS (
      SELECT 1
      FROM public.dish_ingredients di
      WHERE di.dish_id = d.id
        AND di.review_status <> 'rejected'
    )
    AND EXISTS (
      SELECT 1
      FROM public.dish_meal_class_mappings m
      WHERE m.dish_id = d.id
        AND m.review_status <> 'rejected'
    )
    AND ARRAY[
      'hero_role', 'spice_level', 'heaviness', 'cooking_method', 'texture',
      'richness', 'weather_affinity', 'meal_type'
    ]::text[] <@ ARRAY(
      SELECT cur.field_key
      FROM public.dish_taxonomy_current cur
      JOIN public.dish_taxonomy_assertions a ON a.id = cur.assertion_id
      WHERE cur.dish_id = d.id
        AND a.review_status <> 'rejected'
    )
  ORDER BY d.id
  LIMIT least(greatest(coalesce(p_limit, 500), 1), 2000);
$$;

REVOKE ALL ON FUNCTION re_engine.catalogue_publication_coverage() FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION re_engine.catalogue_publication_rows(uuid, integer)
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION re_engine.catalogue_publication_coverage() TO service_role;
GRANT EXECUTE ON FUNCTION re_engine.catalogue_publication_rows(uuid, integer) TO service_role;

COMMENT ON FUNCTION re_engine.catalogue_publication_rows(uuid, integer) IS
  'Streams canonical, safety-closed, class-mapped dish rows in bounded UUID pages; contains no user data.';
