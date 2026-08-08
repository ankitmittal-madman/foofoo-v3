-- Reconcile primary/component readiness across every active dish, including expanded-inventory
-- dishes that have no canonical meal slot yet.
--
-- The v1 slot report intentionally counted valid dish-slot combinations. Its first protected run
-- proved that 2,600 active dishes currently produce no canonical slot and therefore do not enter
-- a slot-only denominator. This additive v2 report preserves the v1 evidence and adds a dish-level
-- route that accounts for the complete active inventory. It performs no write and changes no
-- publication or recommendation behavior.

CREATE OR REPLACE FUNCTION re_engine.catalogue_serving_role_readiness_report_v2()
RETURNS jsonb
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public, food, ops, re_engine, pg_temp
AS $$
  WITH active AS (
    SELECT d.id AS dish_id, d.meal_occasion
    FROM public.dishes d
    WHERE d.is_active
  ),
  hero_role AS (
    SELECT
      d.dish_id,
      max(coalesce(t.code, a.value_text, a.value_json #>> '{}')) FILTER (
        WHERE cur.field_key = 'hero_role' AND a.review_status <> 'rejected'
      ) AS hero_role
    FROM active d
    LEFT JOIN public.dish_taxonomy_current cur ON cur.dish_id = d.dish_id
      AND cur.field_key = 'hero_role'
    LEFT JOIN public.dish_taxonomy_assertions a ON a.id = cur.assertion_id
    LEFT JOIN public.taxonomy_terms t ON t.id = a.term_id
    GROUP BY d.dish_id
  ),
  canonical_slots AS (
    SELECT DISTINCT
      d.dish_id,
      re_engine.canonical_meal_slot(raw_slot) AS meal_slot
    FROM active d
    CROSS JOIN LATERAL unnest(d.meal_occasion) AS raw(raw_slot)
    WHERE re_engine.canonical_meal_slot(raw_slot) IS NOT NULL
  ),
  slot_classified AS (
    SELECT
      s.dish_id,
      s.meal_slot,
      h.hero_role,
      EXISTS (
        SELECT 1
        FROM public.dish_meal_class_mappings m
        WHERE m.dish_id = s.dish_id
          AND re_engine.canonical_meal_slot(m.slot) = s.meal_slot
          AND m.review_status <> 'rejected'
          AND m.confidence >= 0.700
      ) AS primary_mapping_ready,
      EXISTS (
        SELECT 1
        FROM food.dish_component_compatibility c
        JOIN food.plate_grammars g ON g.id = c.grammar_id
        WHERE c.dish_id = s.dish_id
          AND c.meal_slot = s.meal_slot
          AND c.review_status = 'accepted'
          AND c.confidence >= 0.800
          AND g.review_status = 'published'
      ) AS component_compatibility_ready
    FROM canonical_slots s
    JOIN hero_role h ON h.dish_id = s.dish_id
  ),
  slot_routed AS (
    SELECT
      *,
      CASE
        WHEN hero_role IS NULL THEN 'missing_hero_role'
        WHEN hero_role = 'support' AND component_compatibility_ready
          THEN 'component_ready'
        WHEN hero_role = 'support' THEN 'component_review_required'
        WHEN hero_role IN ('dry','liquid','single','standalone') AND primary_mapping_ready
          THEN 'primary_ready'
        WHEN hero_role IN ('dry','liquid','single','standalone')
          THEN 'primary_class_review_required'
        ELSE 'invalid_hero_role'
      END AS serving_route
    FROM slot_classified
  ),
  dish_summary AS (
    SELECT
      d.dish_id,
      h.hero_role,
      count(s.meal_slot) AS canonical_slot_count,
      count(*) FILTER (
        WHERE s.serving_route IN ('primary_ready','component_ready')
      ) AS ready_slot_count
    FROM active d
    JOIN hero_role h ON h.dish_id = d.dish_id
    LEFT JOIN slot_routed s ON s.dish_id = d.dish_id
    GROUP BY d.dish_id, h.hero_role
  ),
  dish_routed AS (
    SELECT
      *,
      CASE
        WHEN canonical_slot_count = 0 THEN 'missing_canonical_meal_slot'
        WHEN hero_role IS NULL THEN 'missing_hero_role'
        WHEN hero_role = 'support' AND ready_slot_count = canonical_slot_count
          THEN 'component_ready_all_slots'
        WHEN hero_role = 'support' AND ready_slot_count > 0
          THEN 'component_partially_ready'
        WHEN hero_role = 'support' THEN 'component_review_required'
        WHEN hero_role IN ('dry','liquid','single','standalone')
             AND ready_slot_count = canonical_slot_count
          THEN 'primary_ready_all_slots'
        WHEN hero_role IN ('dry','liquid','single','standalone')
             AND ready_slot_count > 0
          THEN 'primary_partially_ready'
        WHEN hero_role IN ('dry','liquid','single','standalone')
          THEN 'primary_class_review_required'
        ELSE 'invalid_hero_role'
      END AS dish_route
    FROM dish_summary
  )
  SELECT jsonb_build_object(
    'schema_version', 'recommendation-catalogue-serving-role-readiness-v2',
    'source', 'catalogue_serving_role_readiness_report_v2',
    'active_dishes', (SELECT count(*) FROM active),
    'active_dishes_with_canonical_slot', (
      SELECT count(*) FROM dish_summary WHERE canonical_slot_count > 0
    ),
    'active_dishes_without_canonical_slot', (
      SELECT count(*) FROM dish_summary WHERE canonical_slot_count = 0
    ),
    'active_dish_slots', (SELECT count(*) FROM slot_routed),
    'active_dishes_with_unrecognized_slot', (
      SELECT count(*)
      FROM active d
      WHERE EXISTS (
        SELECT 1
        FROM unnest(d.meal_occasion) raw_slot
        WHERE re_engine.canonical_meal_slot(raw_slot) IS NULL
      )
    ),
    'policy', jsonb_build_object(
      'coverage_unit', 'active_dish_and_canonical_dish_slot',
      'all_active_dishes_reconciled', true,
      'canonical_meal_slots', jsonb_build_array('breakfast','lunch','dinner','snacks'),
      'snack_alias_normalized_to', 'snacks',
      'primary_class_confidence_minimum', 0.700,
      'component_confidence_minimum', 0.800,
      'identity_exposed', false,
      'automatic_proposal_acceptance_allowed', false,
      'publication_gate_changed', false
    ),
    'dish_routes', coalesce((
      SELECT jsonb_object_agg(route_counts.dish_route, route_counts.dish_count)
      FROM (
        SELECT dish_route, count(*) AS dish_count
        FROM dish_routed
        GROUP BY dish_route
        ORDER BY dish_route
      ) route_counts
    ), '{}'::jsonb),
    'slot_routes', coalesce((
      SELECT jsonb_object_agg(route_counts.serving_route, route_counts.slot_count)
      FROM (
        SELECT serving_route, count(*) AS slot_count
        FROM slot_routed
        GROUP BY serving_route
        ORDER BY serving_route
      ) route_counts
    ), '{}'::jsonb),
    'hero_roles', coalesce((
      SELECT jsonb_object_agg(role_counts.role_key, role_counts.dish_count)
      FROM (
        SELECT coalesce(hero_role, 'missing') AS role_key, count(*) AS dish_count
        FROM dish_summary
        GROUP BY coalesce(hero_role, 'missing')
        ORDER BY coalesce(hero_role, 'missing')
      ) role_counts
    ), '{}'::jsonb),
    'component_governance', jsonb_build_object(
      'accepted_assertions', (
        SELECT count(*) FROM food.dish_component_compatibility
        WHERE review_status = 'accepted'
      ),
      'pending_proposals', (
        SELECT count(*) FROM ops.dish_component_compatibility_proposals
        WHERE proposal_status IN ('pending','in_review')
      ),
      'approved_not_applied', (
        SELECT count(*) FROM ops.dish_component_compatibility_proposals
        WHERE proposal_status = 'approved'
      ),
      'applied_proposals', (
        SELECT count(*) FROM ops.dish_component_compatibility_proposals
        WHERE proposal_status = 'applied'
      )
    )
  );
$$;

REVOKE ALL ON FUNCTION re_engine.catalogue_serving_role_readiness_report_v2()
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION re_engine.catalogue_serving_role_readiness_report_v2()
  TO service_role;

COMMENT ON FUNCTION re_engine.catalogue_serving_role_readiness_report_v2() IS
  'Reconciles every active dish plus every canonical dish-slot into aggregate primary/component readiness without changing serving.';
