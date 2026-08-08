-- Explain the provenance of low-confidence meal-class mappings without exposing dish identity.
--
-- The legacy classifier covered the immutable bundle, but confidence alone cannot distinguish
-- curated truth from a weak rule-derived guess. This report isolates otherwise publication-ready
-- dishes whose best class confidence is below 0.700 and shows which evidence path must remediate
-- them. It is aggregate, service-only and read-only.

CREATE OR REPLACE FUNCTION re_engine.catalogue_meal_class_remediation_report()
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
          'hero_role', 'spice_level', 'heaviness', 'cooking_method', 'texture',
          'richness', 'weather_affinity', 'meal_type'
        ]::text[])
          AND a.review_status <> 'rejected'
      ) AS publication_taxonomy_field_count
    FROM public.dish_taxonomy_current cur
    JOIN public.dish_taxonomy_assertions a ON a.id = cur.assertion_id
    GROUP BY cur.dish_id
  ),
  ingredient_quality AS (
    SELECT
      di.dish_id,
      count(*) FILTER (WHERE di.review_status <> 'rejected') AS usable_ingredient_count
    FROM public.dish_ingredients di
    GROUP BY di.dish_id
  ),
  mapping_summary AS (
    SELECT
      m.dish_id,
      count(*) FILTER (WHERE m.review_status <> 'rejected') AS usable_mapping_count,
      bool_or(
        m.classification_method = 'curated_exact' AND m.review_status <> 'rejected'
      ) AS has_curated_exact,
      bool_or(
        m.source_type = 'human_review' AND m.review_status <> 'rejected'
      ) AS has_human_review,
      bool_or(m.review_status = 'accepted') AS has_accepted_mapping
    FROM public.dish_meal_class_mappings m
    GROUP BY m.dish_id
  ),
  best_mapping AS (
    SELECT DISTINCT ON (m.dish_id)
      m.dish_id,
      m.confidence,
      m.classification_method,
      m.source_type,
      m.review_status
    FROM public.dish_meal_class_mappings m
    WHERE m.review_status <> 'rejected'
    ORDER BY
      m.dish_id,
      m.confidence DESC,
      (m.review_status = 'accepted') DESC,
      (m.source_type = 'human_review') DESC,
      m.class_code,
      m.slot
  ),
  candidates AS (
    SELECT
      CASE
        WHEN d.ontology_status = 'enriched' THEN 'published_quality_review'
        ELSE 'status_not_enriched'
      END AS remediation_cohort,
      d.ontology_status,
      b.confidence,
      b.classification_method,
      b.source_type,
      b.review_status,
      m.usable_mapping_count,
      m.has_curated_exact,
      m.has_human_review,
      m.has_accepted_mapping
    FROM public.dishes d
    JOIN taxonomy_quality t ON t.dish_id = d.id
    JOIN ingredient_quality i ON i.dish_id = d.id
    JOIN mapping_summary m ON m.dish_id = d.id
    JOIN best_mapping b ON b.dish_id = d.id
    WHERE d.is_active
      AND b.confidence < 0.700
      AND d.diet_type IS NOT NULL
      AND d.is_jain IS NOT NULL
      AND d.allergen_flags IS NOT NULL
      AND d.cuisine_id IS NOT NULL
      AND i.usable_ingredient_count > 0
      AND m.usable_mapping_count > 0
      AND t.publication_taxonomy_field_count = 8
  )
  SELECT jsonb_build_object(
    'schema_version', 'recommendation-catalogue-meal-class-remediation-v1',
    'source', 'catalogue_meal_class_remediation_report',
    'candidate_definition',
      'otherwise_publication_ready_with_best_meal_class_confidence_below_0_700',
    'candidate_count', count(*),
    'policy', jsonb_build_object(
      'class_confidence_minimum', 0.700,
      'identity_exposed', false,
      'automatic_confidence_upgrade_allowed', false
    ),
    'cohorts', coalesce((
      SELECT jsonb_object_agg(cohort_counts.remediation_cohort, cohort_counts.dish_count)
      FROM (
        SELECT remediation_cohort, count(*) AS dish_count
        FROM candidates
        GROUP BY remediation_cohort
        ORDER BY remediation_cohort
      ) cohort_counts
    ), '{}'::jsonb),
    'ontology_status', coalesce((
      SELECT jsonb_object_agg(status_counts.ontology_status, status_counts.dish_count)
      FROM (
        SELECT ontology_status, count(*) AS dish_count
        FROM candidates
        GROUP BY ontology_status
        ORDER BY ontology_status
      ) status_counts
    ), '{}'::jsonb),
    'classification_method', coalesce((
      SELECT jsonb_object_agg(method_counts.classification_method, method_counts.dish_count)
      FROM (
        SELECT classification_method, count(*) AS dish_count
        FROM candidates
        GROUP BY classification_method
        ORDER BY classification_method
      ) method_counts
    ), '{}'::jsonb),
    'source_type', coalesce((
      SELECT jsonb_object_agg(source_counts.source_type, source_counts.dish_count)
      FROM (
        SELECT source_type, count(*) AS dish_count
        FROM candidates
        GROUP BY source_type
        ORDER BY source_type
      ) source_counts
    ), '{}'::jsonb),
    'review_status', coalesce((
      SELECT jsonb_object_agg(review_counts.review_status, review_counts.dish_count)
      FROM (
        SELECT review_status, count(*) AS dish_count
        FROM candidates
        GROUP BY review_status
        ORDER BY review_status
      ) review_counts
    ), '{}'::jsonb),
    'evidence', jsonb_build_object(
      'has_curated_exact', count(*) FILTER (WHERE has_curated_exact),
      'has_human_review', count(*) FILTER (WHERE has_human_review),
      'has_accepted_mapping', count(*) FILTER (WHERE has_accepted_mapping),
      'single_usable_mapping', count(*) FILTER (WHERE usable_mapping_count = 1),
      'multiple_usable_mappings', count(*) FILTER (WHERE usable_mapping_count > 1)
    ),
    'confidence', jsonb_build_object(
      'below_0_500', count(*) FILTER (WHERE confidence < 0.500),
      '0_500_to_below_0_700', count(*) FILTER (
        WHERE confidence >= 0.500 AND confidence < 0.700
      )
    )
  )
  FROM candidates;
$$;

REVOKE ALL ON FUNCTION re_engine.catalogue_meal_class_remediation_report()
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION re_engine.catalogue_meal_class_remediation_report() TO service_role;

COMMENT ON FUNCTION re_engine.catalogue_meal_class_remediation_report() IS
  'Returns aggregate provenance for otherwise-ready dishes blocked by meal-class confidence; performs no write and exposes no dish or user identity.';
