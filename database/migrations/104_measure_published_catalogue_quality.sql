-- Measure confidence quality inside the currently publishable catalogue without exposing dishes.
--
-- Presence-based publication remains unchanged. This report shows how many eligible rows also
-- satisfy the stricter seed/class/taxonomy/ingredient confidence contract before republishing.

CREATE OR REPLACE FUNCTION re_engine.catalogue_published_quality_report()
RETURNS jsonb
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public, re_engine, pg_temp
AS $$
  WITH taxonomy_quality AS (
    SELECT
      cur.dish_id,
      count(DISTINCT cur.field_key) FILTER (
        WHERE cur.field_key = ANY (ARRAY[
          'cuisine', 'diet', 'cooking_method', 'spice_level', 'heaviness', 'texture',
          'richness', 'weather_affinity', 'meal_type', 'state_origin', 'hero_role',
          'jain_compatible', 'farali_compatible'
        ]::text[])
          AND a.review_status <> 'rejected'
      ) AS seed_required_field_count,
      min(a.confidence) FILTER (
        WHERE cur.field_key = ANY (ARRAY[
          'cuisine', 'diet', 'cooking_method', 'spice_level', 'heaviness', 'texture',
          'richness', 'weather_affinity', 'meal_type', 'state_origin', 'hero_role',
          'jain_compatible', 'farali_compatible'
        ]::text[])
          AND a.review_status <> 'rejected'
      ) AS seed_required_min_confidence,
      count(DISTINCT cur.field_key) FILTER (
        WHERE cur.field_key = ANY (ARRAY[
          'hero_role', 'spice_level', 'heaviness', 'cooking_method', 'texture',
          'richness', 'weather_affinity', 'meal_type'
        ]::text[])
          AND a.review_status <> 'rejected'
      ) AS publication_taxonomy_field_count
    FROM public.dish_taxonomy_current cur
    JOIN public.dish_taxonomy_assertions a ON a.id = cur.assertion_id
    GROUP BY cur.dish_id
  ),
  class_quality AS (
    SELECT
      m.dish_id,
      max(m.confidence) FILTER (WHERE m.review_status <> 'rejected') AS best_confidence,
      count(*) FILTER (WHERE m.review_status <> 'rejected') AS usable_mapping_count
    FROM public.dish_meal_class_mappings m
    GROUP BY m.dish_id
  ),
  ingredient_quality AS (
    SELECT
      di.dish_id,
      min(di.confidence) FILTER (WHERE di.review_status <> 'rejected') AS min_confidence,
      count(*) FILTER (WHERE di.review_status <> 'rejected') AS usable_ingredient_count
    FROM public.dish_ingredients di
    GROUP BY di.dish_id
  ),
  eligible AS (
    SELECT
      d.ontology_confidence,
      t.seed_required_field_count,
      t.seed_required_min_confidence,
      c.best_confidence AS class_best_confidence,
      i.min_confidence AS ingredient_min_confidence
    FROM public.dishes d
    JOIN taxonomy_quality t ON t.dish_id = d.id
    JOIN class_quality c ON c.dish_id = d.id
    JOIN ingredient_quality i ON i.dish_id = d.id
    WHERE d.is_active
      AND d.ontology_status = 'enriched'
      AND d.diet_type IS NOT NULL
      AND d.is_jain IS NOT NULL
      AND d.allergen_flags IS NOT NULL
      AND d.cuisine_id IS NOT NULL
      AND i.usable_ingredient_count > 0
      AND c.usable_mapping_count > 0
      AND t.publication_taxonomy_field_count = 8
  ),
  classified AS (
    SELECT
      eligible.*,
      (
        seed_required_field_count = 13
        AND seed_required_min_confidence >= 0.800
        AND class_best_confidence >= 0.700
        AND ingredient_min_confidence >= 0.800
        AND ontology_confidence >= 0.700
      ) AS strict_quality_ready
    FROM eligible
  )
  SELECT jsonb_build_object(
    'schema_version', 'recommendation-catalogue-published-quality-v1',
    'source', 'catalogue_published_quality_report',
    'eligible_count', count(*),
    'policy', jsonb_build_object(
      'seed_required_fields', 13,
      'ontology_confidence_minimum', 0.700,
      'class_confidence_minimum', 0.700,
      'taxonomy_confidence_minimum', 0.800,
      'ingredient_confidence_minimum', 0.800
    ),
    'readiness', jsonb_build_object(
      'strict_quality_ready', count(*) FILTER (WHERE strict_quality_ready),
      'quality_review_required', count(*) FILTER (WHERE NOT strict_quality_ready)
    ),
    'ontology_confidence', jsonb_build_object(
      'missing', count(*) FILTER (WHERE ontology_confidence IS NULL),
      'below_0_700', count(*) FILTER (WHERE ontology_confidence < 0.700),
      '0_700_to_below_0_800', count(*) FILTER (
        WHERE ontology_confidence >= 0.700 AND ontology_confidence < 0.800
      ),
      '0_800_plus', count(*) FILTER (WHERE ontology_confidence >= 0.800)
    ),
    'class_confidence', jsonb_build_object(
      'below_0_500', count(*) FILTER (WHERE class_best_confidence < 0.500),
      '0_500_to_below_0_700', count(*) FILTER (
        WHERE class_best_confidence >= 0.500 AND class_best_confidence < 0.700
      ),
      '0_700_to_below_0_800', count(*) FILTER (
        WHERE class_best_confidence >= 0.700 AND class_best_confidence < 0.800
      ),
      '0_800_plus', count(*) FILTER (WHERE class_best_confidence >= 0.800)
    ),
    'taxonomy_min_confidence', jsonb_build_object(
      'missing_seed_fields', count(*) FILTER (WHERE seed_required_field_count < 13),
      'below_0_800', count(*) FILTER (
        WHERE seed_required_field_count = 13 AND seed_required_min_confidence < 0.800
      ),
      '0_800_plus', count(*) FILTER (
        WHERE seed_required_field_count = 13 AND seed_required_min_confidence >= 0.800
      )
    ),
    'ingredient_min_confidence', jsonb_build_object(
      'below_0_800', count(*) FILTER (WHERE ingredient_min_confidence < 0.800),
      '0_800_plus', count(*) FILTER (WHERE ingredient_min_confidence >= 0.800)
    )
  )
  FROM classified;
$$;

REVOKE ALL ON FUNCTION re_engine.catalogue_published_quality_report()
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION re_engine.catalogue_published_quality_report() TO service_role;

COMMENT ON FUNCTION re_engine.catalogue_published_quality_report() IS
  'Returns aggregate confidence quality for presence-eligible catalogue rows; changes no eligibility and exposes no dish or user identity.';
