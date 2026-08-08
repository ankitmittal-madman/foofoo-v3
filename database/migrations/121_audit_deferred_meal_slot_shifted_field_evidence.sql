-- Audit the final malformed meal-slot source cohort using exact adjacent-field evidence.
--
-- The checked-in source has 62 rows where Course contains a diet value. This report verifies an
-- ephemeral row manifest, intersects those rows with the 22 still-unclassified active dishes and
-- classifies only aggregate recovery routes. It also summarizes the one direct-slot conflict.
-- No identity, raw source value, proposal, dish, catalogue or serving state is returned or changed.

CREATE OR REPLACE FUNCTION re_engine.deferred_meal_slot_shifted_field_report(
  p_expected_source_name text,
  p_expected_source_checksum text,
  p_policy_version text,
  p_policy_sha256 text,
  p_expected_manifest_row_count integer,
  p_expected_diet_deferred_dish_count integer,
  p_expected_direct_conflict_dish_count integer
)
RETURNS jsonb
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = public, re_engine, pg_catalog, pg_temp
AS $$
DECLARE
  v_report jsonb;
  v_diet_dish_count integer;
  v_conflict_dish_count integer;
BEGIN
  IF p_expected_source_name IS NULL
     OR p_expected_source_name <> btrim(p_expected_source_name)
     OR p_expected_source_name !~ '^[A-Za-z0-9._-]+$'
     OR p_expected_source_checksum !~ '^[0-9a-f]{64}$' THEN
    RAISE EXCEPTION 'expected deferred source identity is invalid';
  END IF;
  IF p_policy_version IS DISTINCT FROM 'deferred-course-shifted-field-audit-v1'
     OR p_policy_sha256 IS DISTINCT FROM
       '94d5f198bbb1244d631a23c5dc95200a6be860d6609dfc6a6bb0c1a7cb5717ac' THEN
    RAISE EXCEPTION 'deferred shifted-field policy identity is invalid';
  END IF;
  IF p_expected_manifest_row_count <> 62
     OR p_expected_diet_deferred_dish_count <> 22
     OR p_expected_direct_conflict_dish_count <> 1 THEN
    RAISE EXCEPTION 'deferred meal-slot audit scope is invalid';
  END IF;
  IF to_regclass('pg_temp.expected_deferred_course_manifest') IS NULL THEN
    RAISE EXCEPTION 'expected deferred course manifest is missing';
  END IF;
  IF (SELECT count(*) FROM pg_temp.expected_deferred_course_manifest)
       <> p_expected_manifest_row_count THEN
    RAISE EXCEPTION 'deferred course manifest row count drifted';
  END IF;

  WITH missing_slot_dishes AS (
    SELECT d.id AS dish_id
    FROM public.dishes d
    WHERE d.is_active
      AND NOT EXISTS (
        SELECT 1 FROM unnest(d.meal_occasion) raw(raw_slot)
        WHERE re_engine.canonical_meal_slot(raw_slot) IS NOT NULL
      )
  ),
  evidence AS (
    SELECT DISTINCT
      d.dish_id,
      s.id AS source_row_id,
      s.source_srno,
      s.row_fingerprint,
      r.source_name,
      r.source_checksum,
      re_engine.direct_slot_from_import_course(s.normalized_payload->>'course_raw')
        AS direct_slot,
      re_engine.contextual_slot_set_from_import_course(s.normalized_payload->>'course_raw')
        AS contextual_slots,
      lower(btrim(s.normalized_payload->>'course_raw')) IN (
        'eggetarian','high protein vegetarian','no onion no garlic (sattvic)',
        'non vegeterian','sugar free diet','vegan','vegetarian'
      ) AS diet_in_course
    FROM missing_slot_dishes d
    JOIN public.import_row_results rr ON rr.dish_id = d.dish_id
      AND rr.status IN ('matched_existing','created_new','merged_duplicate','routed_review')
    JOIN public.dish_source_rows s ON s.id = rr.source_row_id
    JOIN public.import_runs r ON r.id = s.import_run_id
  ),
  dish_scope AS (
    SELECT
      e.dish_id,
      count(DISTINCT e.direct_slot) FILTER (WHERE e.direct_slot IS NOT NULL)
        AS direct_slot_count,
      count(DISTINCT array_to_string(e.contextual_slots, ',')) FILTER (
        WHERE e.contextual_slots IS NOT NULL
      ) AS contextual_slot_count,
      count(*) FILTER (WHERE e.diet_in_course) AS diet_evidence_count
    FROM evidence e
    GROUP BY e.dish_id
  ),
  diet_deferred AS (
    SELECT s.dish_id
    FROM dish_scope s
    WHERE s.direct_slot_count = 0
      AND s.contextual_slot_count = 0
      AND s.diet_evidence_count > 0
  ),
  diet_links AS (
    SELECT
      d.dish_id,
      e.source_row_id,
      m.repair_route,
      m.proposed_slots_key,
      (
        e.source_name = p_expected_source_name
        AND e.source_checksum = p_expected_source_checksum
        AND m.source_srno IS NOT NULL
        AND m.row_fingerprint = e.row_fingerprint
      ) AS exact_manifest_link
    FROM diet_deferred d
    JOIN evidence e ON e.dish_id = d.dish_id AND e.diet_in_course
    LEFT JOIN pg_temp.expected_deferred_course_manifest m ON m.source_srno = e.source_srno
  ),
  classified_diet AS (
    SELECT
      l.dish_id,
      bool_and(l.exact_manifest_link) AS exact_manifest_only,
      count(*) AS evidence_link_count,
      count(*) FILTER (WHERE l.repair_route = 'unresolved_food_role') AS unresolved_link_count,
      count(DISTINCT l.proposed_slots_key) FILTER (WHERE l.proposed_slots_key <> '')
        AS proposed_slot_set_count,
      min(l.proposed_slots_key) FILTER (WHERE l.proposed_slots_key <> '') AS proposed_slots_key,
      bool_or(l.repair_route LIKE 'shifted_direct:%') AS has_shifted_direct,
      bool_or(l.repair_route LIKE 'shifted_contextual:%') AS has_shifted_contextual
    FROM diet_links l
    GROUP BY l.dish_id
  ),
  routed_diet AS (
    SELECT
      c.*,
      CASE
        WHEN NOT c.exact_manifest_only THEN 'manifest_integrity_failure'
        WHEN c.proposed_slot_set_count > 1 THEN 'conflicting_shifted_slot_sets'
        WHEN c.proposed_slot_set_count = 1 AND c.unresolved_link_count > 0
          THEN 'mixed_shifted_and_unresolved_evidence'
        WHEN c.proposed_slot_set_count = 1 AND c.has_shifted_direct
          THEN 'shifted_direct_slot_candidate'
        WHEN c.proposed_slot_set_count = 1 AND c.has_shifted_contextual
          THEN 'shifted_contextual_slot_candidate'
        WHEN c.proposed_slot_set_count = 0 AND c.unresolved_link_count = c.evidence_link_count
          THEN 'requires_food_role_review'
        ELSE 'unclassified_deferred_evidence'
      END AS recovery_route
    FROM classified_diet c
  ),
  direct_conflicts AS (
    SELECT
      e.dish_id,
      array_to_string(array_agg(DISTINCT e.direct_slot ORDER BY e.direct_slot), ',')
        AS direct_slot_key
    FROM evidence e
    WHERE e.direct_slot IS NOT NULL
    GROUP BY e.dish_id
    HAVING count(DISTINCT e.direct_slot) > 1
  )
  SELECT
    (SELECT count(*) FROM routed_diet),
    (SELECT count(*) FROM direct_conflicts),
    jsonb_build_object(
      'schema_version', 'deferred-meal-slot-shifted-field-report-v1',
      'policy_version', p_policy_version,
      'policy_sha256', p_policy_sha256,
      'manifest_row_count', p_expected_manifest_row_count,
      'diet_deferred_dish_count', (SELECT count(*) FROM routed_diet),
      'direct_conflict_dish_count', (SELECT count(*) FROM direct_conflicts),
      'diet_recovery_routes', coalesce((
        SELECT jsonb_object_agg(x.recovery_route, x.dish_count)
        FROM (
          SELECT recovery_route, count(*) AS dish_count
          FROM routed_diet GROUP BY recovery_route ORDER BY recovery_route
        ) x
      ), '{}'::jsonb),
      'candidate_slot_sets', coalesce((
        SELECT jsonb_object_agg(x.proposed_slots_key, x.dish_count)
        FROM (
          SELECT proposed_slots_key, count(*) AS dish_count
          FROM routed_diet
          WHERE proposed_slot_set_count = 1
          GROUP BY proposed_slots_key ORDER BY proposed_slots_key
        ) x
      ), '{}'::jsonb),
      'direct_conflict_slot_sets', coalesce((
        SELECT jsonb_object_agg(x.direct_slot_key, x.dish_count)
        FROM (
          SELECT direct_slot_key, count(*) AS dish_count
          FROM direct_conflicts GROUP BY direct_slot_key ORDER BY direct_slot_key
        ) x
      ), '{}'::jsonb),
      'evidence_link_counts', jsonb_build_object(
        'total', (SELECT coalesce(sum(evidence_link_count), 0) FROM routed_diet),
        'exact_manifest', (
          SELECT count(*) FROM diet_links WHERE exact_manifest_link
        ),
        'manifest_failure', (
          SELECT count(*) FROM diet_links WHERE NOT exact_manifest_link
        )
      ),
      'policy', jsonb_build_object(
        'report_only', true,
        'identity_exposed', false,
        'raw_source_text_exposed', false,
        'name_inference_used', false,
        'automatic_acceptance_allowed', false,
        'proposal_changed', false,
        'dish_changed', false,
        'publication_changed', false,
        'serving_changed', false
      )
    )
  INTO v_diet_dish_count, v_conflict_dish_count, v_report;

  IF v_diet_dish_count <> p_expected_diet_deferred_dish_count
     OR v_conflict_dish_count <> p_expected_direct_conflict_dish_count THEN
    RAISE EXCEPTION 'deferred production dish scope drifted';
  END IF;
  IF (v_report->'evidence_link_counts'->>'manifest_failure')::integer <> 0 THEN
    RAISE EXCEPTION 'deferred production evidence failed checked-in manifest integrity';
  END IF;
  RETURN v_report;
END;
$$;

REVOKE ALL ON FUNCTION re_engine.deferred_meal_slot_shifted_field_report(
  text, text, text, text, integer, integer, integer
) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION re_engine.deferred_meal_slot_shifted_field_report(
  text, text, text, text, integer, integer, integer
) TO service_role;

COMMENT ON FUNCTION re_engine.deferred_meal_slot_shifted_field_report(
  text, text, text, text, integer, integer, integer
) IS
  'Returns aggregate checked-in adjacent-field recovery evidence for the final 22 diet-field and one conflicting-slot dishes; exposes no identity and changes no serving fact.';
