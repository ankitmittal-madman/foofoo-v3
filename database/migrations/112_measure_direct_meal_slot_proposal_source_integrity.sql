-- Verify proposal evidence against one expected checked-in source and completed apply runs.
--
-- The expected source identity is supplied at audit time and is never returned. This report
-- emits aggregate counts only and performs no proposal, dish, publication or serving write.

CREATE OR REPLACE FUNCTION re_engine.direct_meal_slot_proposal_source_integrity_report(
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

  WITH proposal_lineage AS (
    SELECT
      p.id AS proposal_id,
      count(e.source_row_id) AS evidence_link_count,
      count(e.source_row_id) FILTER (
        WHERE r.id IS NOT NULL
          AND r.source_name = p_expected_source_name
          AND r.source_checksum = p_expected_source_checksum
      ) AS expected_source_link_count,
      count(e.source_row_id) FILTER (
        WHERE r.id IS NOT NULL
          AND (
            r.source_name IS DISTINCT FROM p_expected_source_name
            OR r.source_checksum IS DISTINCT FROM p_expected_source_checksum
          )
      ) AS unexpected_source_link_count,
      count(e.source_row_id) FILTER (
        WHERE e.source_row_id IS NOT NULL AND r.id IS NULL
      ) AS missing_import_lineage_count,
      count(e.source_row_id) FILTER (WHERE r.run_mode = 'apply') AS apply_link_count,
      count(e.source_row_id) FILTER (WHERE r.run_mode = 'dry_run') AS dry_run_link_count,
      count(e.source_row_id) FILTER (WHERE r.id IS NULL) AS missing_run_mode_link_count,
      count(e.source_row_id) FILTER (WHERE r.status = 'completed') AS completed_link_count,
      count(e.source_row_id) FILTER (WHERE r.status = 'running') AS running_link_count,
      count(e.source_row_id) FILTER (WHERE r.status = 'failed') AS failed_link_count,
      count(e.source_row_id) FILTER (WHERE r.id IS NULL) AS missing_run_status_link_count,
      count(e.source_row_id) FILTER (
        WHERE r.source_name = p_expected_source_name
          AND r.source_checksum = p_expected_source_checksum
          AND r.run_mode IS DISTINCT FROM 'apply'
      ) AS expected_source_non_apply_count,
      count(e.source_row_id) FILTER (
        WHERE r.source_name = p_expected_source_name
          AND r.source_checksum = p_expected_source_checksum
          AND r.status IS DISTINCT FROM 'completed'
      ) AS expected_source_non_completed_count,
      count(e.source_row_id) FILTER (
        WHERE r.source_name = p_expected_source_name
          AND r.source_checksum = p_expected_source_checksum
          AND r.run_mode = 'apply'
          AND r.status = 'completed'
      ) AS expected_completed_apply_link_count
    FROM ops.dish_meal_slot_proposals p
    LEFT JOIN ops.dish_meal_slot_proposal_evidence e ON e.proposal_id = p.id
    LEFT JOIN public.dish_source_rows s ON s.id = e.source_row_id
    LEFT JOIN public.import_runs r ON r.id = s.import_run_id
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
        WHEN p.expected_source_non_apply_count > 0 THEN 'expected_source_non_apply'
        WHEN p.expected_source_non_completed_count > 0 THEN 'expected_source_incomplete_run'
        WHEN p.expected_completed_apply_link_count = p.evidence_link_count
          THEN 'expected_completed_apply_only'
        ELSE 'unclassified_source_integrity'
      END AS integrity_route,
      p.evidence_link_count > 0
        AND p.expected_completed_apply_link_count = p.evidence_link_count
        AS passes_source_integrity_gate
    FROM proposal_lineage p
  )
  SELECT jsonb_build_object(
    'schema_version', 'recommendation-meal-slot-proposal-source-integrity-v1',
    'proposal_count', (SELECT count(*) FROM classified),
    'evidence_link_count', (
      SELECT coalesce(sum(evidence_link_count), 0) FROM classified
    ),
    'source_identity_link_counts', jsonb_build_object(
      'expected', (SELECT coalesce(sum(expected_source_link_count), 0) FROM classified),
      'unexpected', (SELECT coalesce(sum(unexpected_source_link_count), 0) FROM classified),
      'missing_lineage', (
        SELECT coalesce(sum(missing_import_lineage_count), 0) FROM classified
      )
    ),
    'run_mode_link_counts', jsonb_build_object(
      'apply', (SELECT coalesce(sum(apply_link_count), 0) FROM classified),
      'dry_run', (SELECT coalesce(sum(dry_run_link_count), 0) FROM classified),
      'missing', (
        SELECT coalesce(sum(missing_run_mode_link_count), 0) FROM classified
      )
    ),
    'run_status_link_counts', jsonb_build_object(
      'completed', (SELECT coalesce(sum(completed_link_count), 0) FROM classified),
      'running', (SELECT coalesce(sum(running_link_count), 0) FROM classified),
      'failed', (SELECT coalesce(sum(failed_link_count), 0) FROM classified),
      'missing', (
        SELECT coalesce(sum(missing_run_status_link_count), 0) FROM classified
      )
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
      'passes_source_integrity', (
        SELECT count(*) FROM classified WHERE passes_source_integrity_gate
      ),
      'requires_source_review', (
        SELECT count(*) FROM classified WHERE NOT passes_source_integrity_gate
      )
    ),
    'proposal_issue_counts', jsonb_build_object(
      'missing_import_lineage', (
        SELECT count(*) FROM classified WHERE missing_import_lineage_count > 0
      ),
      'unexpected_source_identity', (
        SELECT count(*) FROM classified WHERE unexpected_source_link_count > 0
      ),
      'expected_source_non_apply', (
        SELECT count(*) FROM classified WHERE expected_source_non_apply_count > 0
      ),
      'expected_source_non_completed', (
        SELECT count(*) FROM classified WHERE expected_source_non_completed_count > 0
      )
    ),
    'policy', jsonb_build_object(
      'identity_exposed', false,
      'expected_source_name_exposed', false,
      'expected_source_checksum_exposed', false,
      'raw_source_text_exposed', false,
      'expected_source_supplied_at_runtime', true,
      'source_integrity_gate_is_approval', false,
      'automatic_acceptance_allowed', false,
      'proposal_changed', false,
      'serving_changed', false,
      'publication_changed', false
    )
  ) INTO v_report;

  RETURN v_report;
END;
$$;

REVOKE ALL ON FUNCTION re_engine.direct_meal_slot_proposal_source_integrity_report(text, text)
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION
  re_engine.direct_meal_slot_proposal_source_integrity_report(text, text)
  TO service_role;

COMMENT ON FUNCTION
  re_engine.direct_meal_slot_proposal_source_integrity_report(text, text) IS
  'Returns aggregate source-identity, run-mode and completion integrity for direct slot proposals; expected source identity and row data are never exposed.';
