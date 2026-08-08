-- Measure the safest ontology-status reclosure tranche without changing any dish.
--
-- The report narrows active rows that pass every publication requirement except
-- ontology_status, then applies the original seed-146 class/field policy plus stricter
-- confidence checks. It returns aggregate counts only and never exposes dish identity.

CREATE OR REPLACE FUNCTION re_engine.catalogue_enrichment_tranche_report()
RETURNS jsonb
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public, re_engine, ops, pg_temp
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
  latest_job AS (
    SELECT DISTINCT ON (j.dish_id) j.dish_id, j.status
    FROM public.dish_enrichment_jobs j
    WHERE j.dish_id IS NOT NULL
    ORDER BY j.dish_id, j.updated_at DESC, j.created_at DESC, j.id DESC
  ),
  candidates AS (
    SELECT
      d.ontology_status,
      d.ontology_confidence,
      coalesce(t.seed_required_field_count, 0) AS seed_required_field_count,
      t.seed_required_min_confidence,
      c.best_confidence AS class_best_confidence,
      i.min_confidence AS ingredient_min_confidence,
      coalesce(j.status, 'missing') AS external_job_status,
      coalesce(ai.status, 'missing') AS ai_job_status
    FROM public.dishes d
    JOIN taxonomy_quality t ON t.dish_id = d.id
    JOIN class_quality c ON c.dish_id = d.id
    JOIN ingredient_quality i ON i.dish_id = d.id
    LEFT JOIN latest_job j ON j.dish_id = d.id
    LEFT JOIN ops.ai_dish_enrichment_state ai ON ai.dish_id = d.id
    WHERE d.is_active
      AND d.ontology_status <> 'enriched'
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
      candidates.*,
      (
        seed_required_field_count = 13
        AND class_best_confidence >= 0.700
      ) AS meets_seed_146_policy,
      (
        seed_required_field_count = 13
        AND seed_required_min_confidence >= 0.800
        AND class_best_confidence >= 0.700
        AND ingredient_min_confidence >= 0.800
      ) AS strict_auto_reclose_ready
    FROM candidates
  )
  SELECT jsonb_build_object(
    'schema_version', 'recommendation-catalogue-enrichment-tranche-v1',
    'source', 'catalogue_enrichment_tranche_report',
    'candidate_definition', 'active_and_publishable_except_ontology_status',
    'candidate_count', count(*),
    'policy', jsonb_build_object(
      'seed_required_fields', 13,
      'seed_class_confidence_minimum', 0.700,
      'strict_taxonomy_confidence_minimum', 0.800,
      'strict_ingredient_confidence_minimum', 0.800
    ),
    'readiness', jsonb_build_object(
      'meets_seed_146_policy', count(*) FILTER (WHERE meets_seed_146_policy),
      'strict_auto_reclose_ready', count(*) FILTER (WHERE strict_auto_reclose_ready),
      'requires_review', count(*) FILTER (WHERE NOT strict_auto_reclose_ready)
    ),
    'ontology_status', coalesce((
      SELECT jsonb_object_agg(status_counts.ontology_status, status_counts.dish_count)
      FROM (
        SELECT ontology_status, count(*) AS dish_count
        FROM classified
        GROUP BY ontology_status
        ORDER BY ontology_status
      ) status_counts
    ), '{}'::jsonb),
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
    ),
    'external_job_status', coalesce((
      SELECT jsonb_object_agg(job_counts.external_job_status, job_counts.dish_count)
      FROM (
        SELECT external_job_status, count(*) AS dish_count
        FROM classified
        GROUP BY external_job_status
        ORDER BY external_job_status
      ) job_counts
    ), '{}'::jsonb),
    'ai_job_status', coalesce((
      SELECT jsonb_object_agg(job_counts.ai_job_status, job_counts.dish_count)
      FROM (
        SELECT ai_job_status, count(*) AS dish_count
        FROM classified
        GROUP BY ai_job_status
        ORDER BY ai_job_status
      ) job_counts
    ), '{}'::jsonb)
  )
  FROM classified;
$$;

REVOKE ALL ON FUNCTION re_engine.catalogue_enrichment_tranche_report()
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION re_engine.catalogue_enrichment_tranche_report() TO service_role;

COMMENT ON FUNCTION re_engine.catalogue_enrichment_tranche_report() IS
  'Returns aggregate confidence and queue evidence for dishes publishable except for ontology status; performs no promotion and exposes no identity.';
