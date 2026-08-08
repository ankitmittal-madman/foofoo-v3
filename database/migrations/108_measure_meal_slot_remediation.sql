-- Measure which missing meal slots can be proposed from exact import-course evidence and which
-- require food-domain review. Output categories are fixed and aggregate; raw source text, dish
-- identity and user data never leave the database. This function performs no write.

CREATE OR REPLACE FUNCTION re_engine.catalogue_meal_slot_remediation_report()
RETURNS jsonb
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public, re_engine, pg_temp
AS $$
  WITH active AS (
    SELECT d.id AS dish_id, d.meal_occasion
    FROM public.dishes d
    WHERE d.is_active
  ),
  slot_state AS (
    SELECT
      d.dish_id,
      cardinality(d.meal_occasion) AS raw_slot_count,
      count(DISTINCT re_engine.canonical_meal_slot(raw_slot)) FILTER (
        WHERE re_engine.canonical_meal_slot(raw_slot) IS NOT NULL
      ) AS canonical_slot_count,
      count(DISTINCT lower(btrim(raw_slot))) FILTER (
        WHERE re_engine.canonical_meal_slot(raw_slot) IS NULL
      ) AS unrecognized_slot_count
    FROM active d
    LEFT JOIN LATERAL unnest(d.meal_occasion) AS raw(raw_slot) ON true
    GROUP BY d.dish_id, d.meal_occasion
  ),
  missing_slot_dishes AS (
    SELECT dish_id
    FROM slot_state
    WHERE canonical_slot_count = 0
  ),
  source_course_rows AS (
    SELECT DISTINCT
      r.dish_id,
      CASE lower(btrim(s.normalized_payload->>'course_raw'))
        WHEN 'lunch' THEN 'lunch'
        WHEN 'dinner' THEN 'dinner'
        WHEN 'snack' THEN 'snacks'
        WHEN 'appetizer' THEN 'snacks'
        WHEN 'south indian breakfast' THEN 'breakfast'
        WHEN 'world breakfast' THEN 'breakfast'
        WHEN 'north indian breakfast' THEN 'breakfast'
        WHEN 'indian breakfast' THEN 'breakfast'
        ELSE NULL
      END AS direct_slot,
      CASE lower(btrim(s.normalized_payload->>'course_raw'))
        WHEN 'side dish' THEN 'side_dish_needs_meal_context'
        WHEN 'main course' THEN 'main_course_needs_lunch_or_dinner'
        WHEN 'one pot dish' THEN 'one_pot_needs_lunch_or_dinner'
        WHEN 'dessert' THEN 'dessert_needs_episode_context'
        WHEN 'brunch' THEN 'brunch_needs_breakfast_or_lunch'
        WHEN 'vegetarian' THEN 'diet_value_in_course_field'
        WHEN 'high protein vegetarian' THEN 'diet_value_in_course_field'
        WHEN 'vegan' THEN 'diet_value_in_course_field'
        WHEN 'non vegeterian' THEN 'diet_value_in_course_field'
        WHEN 'eggetarian' THEN 'diet_value_in_course_field'
        WHEN 'no onion no garlic (sattvic)' THEN 'diet_value_in_course_field'
        WHEN 'sugar free diet' THEN 'diet_value_in_course_field'
        WHEN '' THEN 'missing_source_course'
        ELSE CASE
          WHEN s.normalized_payload->>'course_raw' IS NULL THEN 'missing_source_course'
          WHEN lower(btrim(s.normalized_payload->>'course_raw')) IN (
            'lunch','dinner','snack','appetizer','south indian breakfast',
            'world breakfast','north indian breakfast','indian breakfast'
          ) THEN NULL
          ELSE 'unrecognized_source_course'
        END
      END AS review_category
    FROM missing_slot_dishes d
    JOIN public.import_row_results r ON r.dish_id = d.dish_id
      AND r.status IN ('matched_existing','created_new','merged_duplicate','routed_review')
    JOIN public.dish_source_rows s ON s.id = r.source_row_id
  ),
  source_by_dish AS (
    SELECT
      d.dish_id,
      array_remove(array_agg(DISTINCT s.direct_slot), NULL) AS direct_slots,
      array_remove(array_agg(DISTINCT s.review_category), NULL) AS review_categories,
      count(s.dish_id) AS source_evidence_rows
    FROM missing_slot_dishes d
    LEFT JOIN source_course_rows s ON s.dish_id = d.dish_id
    GROUP BY d.dish_id
  ),
  routed AS (
    SELECT
      *,
      CASE
        WHEN source_evidence_rows = 0 THEN 'missing_source_course_evidence'
        WHEN cardinality(direct_slots) = 1 AND cardinality(review_categories) = 0
          THEN 'single_direct_slot_proposal'
        WHEN cardinality(direct_slots) > 1 THEN 'conflicting_direct_slot_evidence'
        WHEN cardinality(direct_slots) = 0 AND cardinality(review_categories) > 0
          THEN 'contextual_course_review'
        WHEN cardinality(direct_slots) > 0 AND cardinality(review_categories) > 0
          THEN 'mixed_direct_and_contextual_evidence'
        ELSE 'unclassified_source_evidence'
      END AS remediation_route
    FROM source_by_dish
  )
  SELECT jsonb_build_object(
    'schema_version', 'recommendation-catalogue-meal-slot-remediation-v1',
    'source', 'catalogue_meal_slot_remediation_report',
    'active_dishes', (SELECT count(*) FROM active),
    'missing_canonical_slot_dishes', (SELECT count(*) FROM missing_slot_dishes),
    'policy', jsonb_build_object(
      'identity_exposed', false,
      'raw_source_text_exposed', false,
      'fixed_evidence_categories_only', true,
      'automatic_proposal_acceptance_allowed', false,
      'publication_gate_changed', false,
      'direct_slot_proposal_is_non_serving', true
    ),
    'current_slot_state', jsonb_build_object(
      'empty_meal_occasion', (
        SELECT count(*) FROM slot_state WHERE raw_slot_count = 0
      ),
      'canonical_only', (
        SELECT count(*) FROM slot_state
        WHERE canonical_slot_count > 0 AND unrecognized_slot_count = 0
      ),
      'canonical_and_unrecognized', (
        SELECT count(*) FROM slot_state
        WHERE canonical_slot_count > 0 AND unrecognized_slot_count > 0
      ),
      'unrecognized_only', (
        SELECT count(*) FROM slot_state
        WHERE canonical_slot_count = 0 AND unrecognized_slot_count > 0
      )
    ),
    'remediation_routes', coalesce((
      SELECT jsonb_object_agg(route_counts.remediation_route, route_counts.dish_count)
      FROM (
        SELECT remediation_route, count(*) AS dish_count
        FROM routed
        GROUP BY remediation_route
        ORDER BY remediation_route
      ) route_counts
    ), '{}'::jsonb),
    'single_direct_slot_proposals', coalesce((
      SELECT jsonb_object_agg(slot_counts.direct_slot, slot_counts.dish_count)
      FROM (
        SELECT direct_slots[1] AS direct_slot, count(*) AS dish_count
        FROM routed
        WHERE remediation_route = 'single_direct_slot_proposal'
        GROUP BY direct_slots[1]
        ORDER BY direct_slots[1]
      ) slot_counts
    ), '{}'::jsonb),
    'contextual_review_categories', coalesce((
      SELECT jsonb_object_agg(category_counts.review_category, category_counts.dish_count)
      FROM (
        SELECT review_category, count(DISTINCT r.dish_id) AS dish_count
        FROM routed r
        CROSS JOIN LATERAL unnest(r.review_categories) review_category
        GROUP BY review_category
        ORDER BY review_category
      ) category_counts
    ), '{}'::jsonb)
  );
$$;

REVOKE ALL ON FUNCTION re_engine.catalogue_meal_slot_remediation_report()
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION re_engine.catalogue_meal_slot_remediation_report()
  TO service_role;

COMMENT ON FUNCTION re_engine.catalogue_meal_slot_remediation_report() IS
  'Returns fixed-category aggregate evidence for missing canonical meal slots; exposes no raw text or identity and performs no write.';
