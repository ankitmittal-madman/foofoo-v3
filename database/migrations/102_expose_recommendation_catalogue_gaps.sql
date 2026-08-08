-- Explain, with aggregate counts only, why active dishes are excluded from publication.
--
-- This function is an operational read boundary. It mirrors every gate used by
-- re_engine.catalogue_publication_rows without exposing dish identity or user data.

CREATE OR REPLACE FUNCTION re_engine.catalogue_publication_gap_report()
RETURNS jsonb
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public, re_engine, pg_temp
AS $$
  WITH accepted_ingredients AS (
    SELECT DISTINCT di.dish_id
    FROM public.dish_ingredients di
    WHERE di.review_status <> 'rejected'
  ),
  accepted_classes AS (
    SELECT DISTINCT m.dish_id
    FROM public.dish_meal_class_mappings m
    WHERE m.review_status <> 'rejected'
  ),
  accepted_taxonomy AS (
    SELECT
      cur.dish_id,
      array_agg(DISTINCT cur.field_key) AS field_keys
    FROM public.dish_taxonomy_current cur
    JOIN public.dish_taxonomy_assertions a ON a.id = cur.assertion_id
    WHERE a.review_status <> 'rejected'
    GROUP BY cur.dish_id
  ),
  requirements AS (
    SELECT
      d.is_active,
      coalesce(d.ontology_status = 'enriched', false) AS has_enrichment,
      d.diet_type IS NOT NULL AS has_diet_type,
      d.is_jain IS NOT NULL AS has_jain_status,
      d.allergen_flags IS NOT NULL AS has_allergen_flags,
      d.cuisine_id IS NOT NULL AS has_cuisine,
      ai.dish_id IS NOT NULL AS has_ingredient,
      ac.dish_id IS NOT NULL AS has_meal_class,
      coalesce('hero_role' = ANY (tax.field_keys), false) AS has_hero_role,
      coalesce('spice_level' = ANY (tax.field_keys), false) AS has_spice_level,
      coalesce('heaviness' = ANY (tax.field_keys), false) AS has_heaviness,
      coalesce('cooking_method' = ANY (tax.field_keys), false) AS has_cooking_method,
      coalesce('texture' = ANY (tax.field_keys), false) AS has_texture,
      coalesce('richness' = ANY (tax.field_keys), false) AS has_richness,
      coalesce('weather_affinity' = ANY (tax.field_keys), false) AS has_weather_affinity,
      coalesce('meal_type' = ANY (tax.field_keys), false) AS has_meal_type
    FROM public.dishes d
    LEFT JOIN accepted_ingredients ai ON ai.dish_id = d.id
    LEFT JOIN accepted_classes ac ON ac.dish_id = d.id
    LEFT JOIN accepted_taxonomy tax ON tax.dish_id = d.id
  ),
  scored AS (
    SELECT
      requirements.*,
      (
        (NOT has_enrichment)::integer
        + (NOT has_diet_type)::integer
        + (NOT has_jain_status)::integer
        + (NOT has_allergen_flags)::integer
        + (NOT has_cuisine)::integer
        + (NOT has_ingredient)::integer
        + (NOT has_meal_class)::integer
        + (NOT has_hero_role)::integer
        + (NOT has_spice_level)::integer
        + (NOT has_heaviness)::integer
        + (NOT has_cooking_method)::integer
        + (NOT has_texture)::integer
        + (NOT has_richness)::integer
        + (NOT has_weather_affinity)::integer
        + (NOT has_meal_type)::integer
      ) AS missing_gate_count,
      (
        is_active
        AND has_enrichment
        AND has_diet_type
        AND has_jain_status
        AND has_allergen_flags
        AND has_cuisine
        AND has_ingredient
        AND has_meal_class
        AND has_hero_role
        AND has_spice_level
        AND has_heaviness
        AND has_cooking_method
        AND has_texture
        AND has_richness
        AND has_weather_affinity
        AND has_meal_type
      ) AS is_publishable
    FROM requirements
  ),
  counts AS (
    SELECT
      count(*) AS stored_dishes,
      count(*) FILTER (WHERE is_active) AS active_dishes,
      count(*) FILTER (WHERE NOT is_active) AS inactive_dishes,
      count(*) FILTER (WHERE is_publishable) AS publishable_dishes,
      count(*) FILTER (WHERE is_active AND NOT is_publishable) AS active_not_publishable,
      count(*) FILTER (WHERE is_active AND has_enrichment) AS funnel_enriched,
      count(*) FILTER (
        WHERE is_active AND has_enrichment AND has_diet_type
          AND has_jain_status AND has_allergen_flags
      ) AS funnel_safety_closed,
      count(*) FILTER (
        WHERE is_active AND has_enrichment AND has_diet_type
          AND has_jain_status AND has_allergen_flags AND has_cuisine
      ) AS funnel_cuisine_complete,
      count(*) FILTER (
        WHERE is_active AND has_enrichment AND has_diet_type
          AND has_jain_status AND has_allergen_flags AND has_cuisine AND has_ingredient
      ) AS funnel_ingredients_complete,
      count(*) FILTER (
        WHERE is_active AND has_enrichment AND has_diet_type
          AND has_jain_status AND has_allergen_flags AND has_cuisine
          AND has_ingredient AND has_meal_class
      ) AS funnel_class_mapped,
      count(*) FILTER (WHERE is_active AND NOT has_enrichment) AS missing_enrichment,
      count(*) FILTER (WHERE is_active AND NOT has_diet_type) AS missing_diet_type,
      count(*) FILTER (WHERE is_active AND NOT has_jain_status) AS missing_jain_status,
      count(*) FILTER (WHERE is_active AND NOT has_allergen_flags) AS missing_allergen_flags,
      count(*) FILTER (WHERE is_active AND NOT has_cuisine) AS missing_cuisine,
      count(*) FILTER (WHERE is_active AND NOT has_ingredient) AS missing_ingredient,
      count(*) FILTER (WHERE is_active AND NOT has_meal_class) AS missing_meal_class,
      count(*) FILTER (WHERE is_active AND NOT has_hero_role) AS missing_hero_role,
      count(*) FILTER (WHERE is_active AND NOT has_spice_level) AS missing_spice_level,
      count(*) FILTER (WHERE is_active AND NOT has_heaviness) AS missing_heaviness,
      count(*) FILTER (WHERE is_active AND NOT has_cooking_method) AS missing_cooking_method,
      count(*) FILTER (WHERE is_active AND NOT has_texture) AS missing_texture,
      count(*) FILTER (WHERE is_active AND NOT has_richness) AS missing_richness,
      count(*) FILTER (WHERE is_active AND NOT has_weather_affinity) AS missing_weather_affinity,
      count(*) FILTER (WHERE is_active AND NOT has_meal_type) AS missing_meal_type
    FROM scored
  ),
  gap_distribution AS (
    SELECT missing_gate_count, count(*) AS dish_count
    FROM scored
    WHERE is_active
    GROUP BY missing_gate_count
  )
  SELECT jsonb_build_object(
    'schema_version', 'recommendation-catalogue-gap-report-v1',
    'source', 'catalogue_publication_gap_report',
    'inventory', jsonb_build_object(
      'stored_dishes', c.stored_dishes,
      'active_dishes', c.active_dishes,
      'inactive_dishes', c.inactive_dishes
    ),
    'serving_readiness', jsonb_build_object(
      'publishable_dishes', c.publishable_dishes,
      'active_not_publishable', c.active_not_publishable,
      'requirements_per_active_dish', 15
    ),
    'ordered_funnel', jsonb_build_object(
      'active', c.active_dishes,
      'enriched', c.funnel_enriched,
      'safety_closed', c.funnel_safety_closed,
      'cuisine_complete', c.funnel_cuisine_complete,
      'ingredients_complete', c.funnel_ingredients_complete,
      'class_mapped', c.funnel_class_mapped,
      'taxonomy_complete_publishable', c.publishable_dishes
    ),
    'missing_gates', jsonb_build_object(
      'enrichment', c.missing_enrichment,
      'diet_type', c.missing_diet_type,
      'jain_status', c.missing_jain_status,
      'allergen_flags', c.missing_allergen_flags,
      'cuisine', c.missing_cuisine,
      'ingredient', c.missing_ingredient,
      'meal_class', c.missing_meal_class,
      'taxonomy', jsonb_build_object(
        'hero_role', c.missing_hero_role,
        'spice_level', c.missing_spice_level,
        'heaviness', c.missing_heaviness,
        'cooking_method', c.missing_cooking_method,
        'texture', c.missing_texture,
        'richness', c.missing_richness,
        'weather_affinity', c.missing_weather_affinity,
        'meal_type', c.missing_meal_type
      )
    ),
    'missing_gate_distribution', coalesce((
      SELECT jsonb_object_agg(
        distribution.missing_gate_count::text,
        distribution.dish_count
        ORDER BY distribution.missing_gate_count
      )
      FROM gap_distribution distribution
    ), '{}'::jsonb)
  )
  FROM counts c;
$$;

REVOKE ALL ON FUNCTION re_engine.catalogue_publication_gap_report()
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION re_engine.catalogue_publication_gap_report() TO service_role;

COMMENT ON FUNCTION re_engine.catalogue_publication_gap_report() IS
  'Returns only aggregate catalogue exclusion and readiness counts; exposes no dish or user identity.';
