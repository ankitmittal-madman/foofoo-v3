-- Measure whether proposal evidence is repeated import lineage or distinct applied source data.
--
-- Evidence-link count is not treated as source independence. This report emits fixed aggregate
-- categories only and performs no proposal, dish, publication or serving write.

CREATE OR REPLACE FUNCTION re_engine.direct_meal_slot_proposal_provenance_report()
RETURNS jsonb
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ops, public, re_engine, pg_catalog, pg_temp
AS $$
  WITH proposal_lineage AS (
    SELECT
      p.id AS proposal_id,
      count(e.source_row_id) AS evidence_link_count,
      count(e.source_row_id) FILTER (WHERE r.run_mode = 'apply') AS apply_link_count,
      count(e.source_row_id) FILTER (WHERE r.run_mode = 'dry_run') AS dry_run_link_count,
      count(DISTINCT s.row_fingerprint) FILTER (
        WHERE r.run_mode = 'apply'
      ) AS distinct_apply_row_fingerprints,
      count(DISTINCT (r.source_name, r.source_checksum)) FILTER (
        WHERE r.run_mode = 'apply'
      ) AS distinct_apply_source_files,
      count(DISTINCT r.source_name) FILTER (
        WHERE r.run_mode = 'apply'
      ) AS distinct_apply_source_names,
      count(DISTINCT r.id) FILTER (
        WHERE r.run_mode = 'apply'
      ) AS distinct_apply_runs
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
        WHEN p.apply_link_count = 0 THEN 'no_applied_source_evidence'
        WHEN p.distinct_apply_row_fingerprints = 1
          AND p.distinct_apply_source_files = 1
          THEN 'repeated_same_logical_source_row'
        WHEN p.distinct_apply_source_files = 1
          THEN 'multiple_rows_same_applied_source_file'
        WHEN p.distinct_apply_source_files > 1
          AND p.distinct_apply_source_names = 1
          THEN 'multiple_versions_same_source_name'
        WHEN p.distinct_apply_source_names > 1
          THEN 'multiple_source_names_not_independence_proof'
        ELSE 'unclassified_applied_lineage'
      END AS provenance_route
    FROM proposal_lineage p
  )
  SELECT jsonb_build_object(
    'schema_version', 'recommendation-meal-slot-proposal-provenance-v1',
    'proposal_count', (SELECT count(*) FROM classified),
    'evidence_link_count', (
      SELECT coalesce(sum(evidence_link_count), 0) FROM classified
    ),
    'run_mode_link_counts', jsonb_build_object(
      'apply', (SELECT coalesce(sum(apply_link_count), 0) FROM classified),
      'dry_run', (SELECT coalesce(sum(dry_run_link_count), 0) FROM classified)
    ),
    'provenance_routes', coalesce((
      SELECT jsonb_object_agg(routes.provenance_route, routes.proposal_count)
      FROM (
        SELECT provenance_route, count(*) AS proposal_count
        FROM classified
        GROUP BY provenance_route
        ORDER BY provenance_route
      ) routes
    ), '{}'::jsonb),
    'applied_lineage_ranges', jsonb_build_object(
      'apply_links_minimum', (SELECT min(apply_link_count) FROM classified),
      'apply_links_maximum', (SELECT max(apply_link_count) FROM classified),
      'distinct_row_fingerprints_minimum', (
        SELECT min(distinct_apply_row_fingerprints) FROM classified
      ),
      'distinct_row_fingerprints_maximum', (
        SELECT max(distinct_apply_row_fingerprints) FROM classified
      ),
      'distinct_source_files_minimum', (
        SELECT min(distinct_apply_source_files) FROM classified
      ),
      'distinct_source_files_maximum', (
        SELECT max(distinct_apply_source_files) FROM classified
      ),
      'distinct_source_names_minimum', (
        SELECT min(distinct_apply_source_names) FROM classified
      ),
      'distinct_source_names_maximum', (
        SELECT max(distinct_apply_source_names) FROM classified
      ),
      'distinct_apply_runs_minimum', (
        SELECT min(distinct_apply_runs) FROM classified
      ),
      'distinct_apply_runs_maximum', (
        SELECT max(distinct_apply_runs) FROM classified
      )
    ),
    'policy', jsonb_build_object(
      'identity_exposed', false,
      'source_name_exposed', false,
      'source_checksum_exposed', false,
      'raw_source_text_exposed', false,
      'evidence_link_is_independent_source_proof', false,
      'automatic_confidence_upgrade_allowed', false,
      'proposal_changed', false,
      'serving_changed', false,
      'publication_changed', false
    )
  );
$$;

REVOKE ALL ON FUNCTION re_engine.direct_meal_slot_proposal_provenance_report()
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION re_engine.direct_meal_slot_proposal_provenance_report()
  TO service_role;

COMMENT ON FUNCTION re_engine.direct_meal_slot_proposal_provenance_report() IS
  'Returns fixed aggregate import-lineage multiplicity for direct slot proposals; link count never implies independent evidence and no source identity is exposed.';
