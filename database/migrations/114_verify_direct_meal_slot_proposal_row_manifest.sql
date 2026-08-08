-- Verify each proposal evidence row against a manifest regenerated from the checked-in CSV.
--
-- The caller loads a temporary pg_temp.expected_dish_source_manifest table containing only
-- source_srno, row_fingerprint and a fixed direct slot. The function returns aggregate counts,
-- exposes no manifest value or source identity, and changes no proposal or serving fact.

CREATE OR REPLACE FUNCTION re_engine.direct_meal_slot_proposal_row_manifest_report(
  p_expected_source_name text,
  p_expected_source_checksum text
)
RETURNS jsonb
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = ops, public, re_engine, pg_catalog, pg_temp
AS $$
DECLARE
  v_report jsonb;
BEGIN
  IF p_expected_source_name IS NULL
     OR btrim(p_expected_source_name) = ''
     OR p_expected_source_name <> btrim(p_expected_source_name)
     OR position('/' IN p_expected_source_name) > 0
     OR position(chr(92) IN p_expected_source_name) > 0 THEN
    RAISE EXCEPTION 'expected source name must be one basename';
  END IF;
  IF p_expected_source_checksum IS NULL
     OR p_expected_source_checksum !~ '^[0-9a-f]{64}$' THEN
    RAISE EXCEPTION 'expected source checksum must be lowercase sha256';
  END IF;
  IF to_regclass('pg_temp.expected_dish_source_manifest') IS NULL THEN
    RAISE EXCEPTION 'expected direct source manifest is missing';
  END IF;

  WITH proposal_lineage AS (
    SELECT
      p.id AS proposal_id,
      count(e.source_row_id) AS evidence_link_count,
      count(e.source_row_id) FILTER (
        WHERE e.source_row_id IS NOT NULL AND r.id IS NULL
      ) AS missing_import_lineage_count,
      count(e.source_row_id) FILTER (
        WHERE r.id IS NOT NULL
          AND (
            r.source_name IS DISTINCT FROM p_expected_source_name
            OR r.source_checksum IS DISTINCT FROM p_expected_source_checksum
          )
      ) AS unexpected_source_link_count,
      count(e.source_row_id) FILTER (
        WHERE r.source_name = p_expected_source_name
          AND r.source_checksum = p_expected_source_checksum
          AND m.source_srno IS NULL
      ) AS missing_manifest_row_count,
      count(e.source_row_id) FILTER (
        WHERE r.source_name = p_expected_source_name
          AND r.source_checksum = p_expected_source_checksum
          AND m.source_srno IS NOT NULL
          AND m.row_fingerprint IS DISTINCT FROM s.row_fingerprint
      ) AS fingerprint_mismatch_count,
      count(e.source_row_id) FILTER (
        WHERE r.source_name = p_expected_source_name
          AND r.source_checksum = p_expected_source_checksum
          AND m.source_srno IS NOT NULL
          AND m.row_fingerprint = s.row_fingerprint
          AND m.direct_slot IS DISTINCT FROM p.proposed_slot
      ) AS direct_slot_mismatch_count,
      count(e.source_row_id) FILTER (
        WHERE r.source_name = p_expected_source_name
          AND r.source_checksum = p_expected_source_checksum
          AND m.source_srno IS NOT NULL
          AND m.row_fingerprint = s.row_fingerprint
          AND m.direct_slot = p.proposed_slot
      ) AS exact_manifest_link_count,
      count(e.source_row_id) FILTER (WHERE r.status = 'completed') AS completed_link_count,
      count(e.source_row_id) FILTER (WHERE r.status = 'running') AS running_link_count,
      count(e.source_row_id) FILTER (WHERE r.status = 'failed') AS failed_link_count,
      count(e.source_row_id) FILTER (WHERE r.id IS NULL) AS missing_status_link_count
    FROM ops.dish_meal_slot_proposals p
    LEFT JOIN ops.dish_meal_slot_proposal_evidence e ON e.proposal_id = p.id
    LEFT JOIN public.dish_source_rows s ON s.id = e.source_row_id
    LEFT JOIN public.import_runs r ON r.id = s.import_run_id
    LEFT JOIN pg_temp.expected_dish_source_manifest m ON m.source_srno = s.source_srno
    WHERE p.proposal_method = 'exact_import_course_v1'
      AND p.proposal_version = 'meal-slot-proposal-v1'
    GROUP BY p.id
  ),
  classified AS (
    SELECT
      p.*,
      CASE
        WHEN p.evidence_link_count = 0 THEN 'no_evidence'
        WHEN p.missing_import_lineage_count > 0 THEN 'missing_import_lineage'
        WHEN p.unexpected_source_link_count > 0 THEN 'unexpected_source_identity'
        WHEN p.missing_manifest_row_count > 0 THEN 'missing_checked_in_manifest_row'
        WHEN p.fingerprint_mismatch_count > 0 THEN 'checked_in_fingerprint_mismatch'
        WHEN p.direct_slot_mismatch_count > 0 THEN 'checked_in_direct_slot_mismatch'
        WHEN p.exact_manifest_link_count = p.evidence_link_count
          THEN 'exact_checked_in_row_only'
        ELSE 'unclassified_row_manifest_integrity'
      END AS integrity_route,
      p.evidence_link_count > 0
        AND p.exact_manifest_link_count = p.evidence_link_count
        AS passes_row_manifest_gate
    FROM proposal_lineage p
  )
  SELECT jsonb_build_object(
    'schema_version', 'recommendation-meal-slot-proposal-row-manifest-v1',
    'manifest_direct_row_count', (
      SELECT count(*) FROM pg_temp.expected_dish_source_manifest
    ),
    'proposal_count', (SELECT count(*) FROM classified),
    'evidence_link_count', (
      SELECT coalesce(sum(evidence_link_count), 0) FROM classified
    ),
    'row_integrity_link_counts', jsonb_build_object(
      'exact_checked_in_row', (
        SELECT coalesce(sum(exact_manifest_link_count), 0) FROM classified
      ),
      'missing_import_lineage', (
        SELECT coalesce(sum(missing_import_lineage_count), 0) FROM classified
      ),
      'unexpected_source_identity', (
        SELECT coalesce(sum(unexpected_source_link_count), 0) FROM classified
      ),
      'missing_manifest_row', (
        SELECT coalesce(sum(missing_manifest_row_count), 0) FROM classified
      ),
      'fingerprint_mismatch', (
        SELECT coalesce(sum(fingerprint_mismatch_count), 0) FROM classified
      ),
      'direct_slot_mismatch', (
        SELECT coalesce(sum(direct_slot_mismatch_count), 0) FROM classified
      )
    ),
    'run_status_link_counts', jsonb_build_object(
      'completed', (SELECT coalesce(sum(completed_link_count), 0) FROM classified),
      'running', (SELECT coalesce(sum(running_link_count), 0) FROM classified),
      'failed', (SELECT coalesce(sum(failed_link_count), 0) FROM classified),
      'missing', (SELECT coalesce(sum(missing_status_link_count), 0) FROM classified)
    ),
    'integrity_routes', coalesce((
      SELECT jsonb_object_agg(routes.integrity_route, routes.proposal_count)
      FROM (
        SELECT integrity_route, count(*) AS proposal_count
        FROM classified
        GROUP BY integrity_route
        ORDER BY integrity_route
      ) routes
    ), '{}'::jsonb),
    'proposal_gate_counts', jsonb_build_object(
      'passes_row_manifest_integrity', (
        SELECT count(*) FROM classified WHERE passes_row_manifest_gate
      ),
      'requires_row_integrity_review', (
        SELECT count(*) FROM classified WHERE NOT passes_row_manifest_gate
      )
    ),
    'proposal_issue_counts', jsonb_build_object(
      'missing_import_lineage', (
        SELECT count(*) FROM classified WHERE missing_import_lineage_count > 0
      ),
      'unexpected_source_identity', (
        SELECT count(*) FROM classified WHERE unexpected_source_link_count > 0
      ),
      'missing_manifest_row', (
        SELECT count(*) FROM classified WHERE missing_manifest_row_count > 0
      ),
      'fingerprint_mismatch', (
        SELECT count(*) FROM classified WHERE fingerprint_mismatch_count > 0
      ),
      'direct_slot_mismatch', (
        SELECT count(*) FROM classified WHERE direct_slot_mismatch_count > 0
      )
    ),
    'policy', jsonb_build_object(
      'identity_exposed', false,
      'source_name_exposed', false,
      'source_checksum_exposed', false,
      'manifest_values_exposed', false,
      'raw_source_text_exposed', false,
      'row_level_integrity_independent_of_run_completion', true,
      'run_completion_required_for_import_health', true,
      'row_manifest_gate_is_approval', false,
      'automatic_acceptance_allowed', false,
      'proposal_changed', false,
      'serving_changed', false,
      'publication_changed', false
    )
  ) INTO v_report;

  RETURN v_report;
END;
$$;

REVOKE ALL ON FUNCTION
  re_engine.direct_meal_slot_proposal_row_manifest_report(text, text)
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION
  re_engine.direct_meal_slot_proposal_row_manifest_report(text, text)
  TO service_role;

COMMENT ON FUNCTION
  re_engine.direct_meal_slot_proposal_row_manifest_report(text, text) IS
  'Returns aggregate per-row checked-in manifest integrity for direct slot proposals; run health remains separate and no identity or row value is exposed.';
