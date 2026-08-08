-- Produce a bounded, deterministic review pack for governed direct meal-slot proposals.
--
-- The report is read-only. It exposes a small catalogue-name sample so a reviewer can judge the
-- proposed slots, but it never returns dish/source-row identifiers, raw import text or user data.

CREATE OR REPLACE FUNCTION re_engine.direct_meal_slot_proposal_review_report(
  p_sample_per_slot integer DEFAULT 10
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
  IF p_sample_per_slot IS NULL OR p_sample_per_slot < 1 OR p_sample_per_slot > 25 THEN
    RAISE EXCEPTION 'sample per slot must be between 1 and 25';
  END IF;

  WITH evidence_counts AS (
    SELECT e.proposal_id, count(*) AS evidence_link_count
    FROM ops.dish_meal_slot_proposal_evidence e
    GROUP BY e.proposal_id
  ),
  current_candidates AS (
    SELECT DISTINCT c.dish_id, c.proposed_slot
    FROM re_engine.direct_meal_slot_proposal_candidates() c
  ),
  proposals AS (
    SELECT
      p.id,
      p.dish_id,
      d.name AS dish_name,
      p.proposed_slot,
      p.evidence_category,
      p.confidence,
      p.proposal_status,
      coalesce(e.evidence_link_count, 0) AS evidence_link_count,
      (c.dish_id IS NOT NULL) AS still_matches_direct_evidence
    FROM ops.dish_meal_slot_proposals p
    JOIN public.dishes d ON d.id = p.dish_id
    LEFT JOIN evidence_counts e ON e.proposal_id = p.id
    LEFT JOIN current_candidates c ON c.dish_id = p.dish_id
      AND c.proposed_slot = p.proposed_slot
    WHERE p.proposal_method = 'exact_import_course_v1'
      AND p.proposal_version = 'meal-slot-proposal-v1'
  ),
  ranked_sample AS (
    SELECT
      p.*,
      row_number() OVER (
        PARTITION BY p.proposed_slot
        ORDER BY md5(p.dish_id::text || ':meal-slot-proposal-v1')
      ) AS sample_rank
    FROM proposals p
    WHERE p.proposal_status = 'pending'
  )
  SELECT jsonb_build_object(
    'schema_version', 'recommendation-meal-slot-proposal-review-v1',
    'proposal_count', (SELECT count(*) FROM proposals),
    'evidence_link_count', (
      SELECT coalesce(sum(p.evidence_link_count), 0) FROM proposals p
    ),
    'status_counts', coalesce((
      SELECT jsonb_object_agg(s.proposal_status, s.proposal_count)
      FROM (
        SELECT proposal_status, count(*) AS proposal_count
        FROM proposals
        GROUP BY proposal_status
        ORDER BY proposal_status
      ) s
    ), '{}'::jsonb),
    'slot_counts', coalesce((
      SELECT jsonb_object_agg(s.proposed_slot, s.proposal_count)
      FROM (
        SELECT proposed_slot, count(*) AS proposal_count
        FROM proposals
        GROUP BY proposed_slot
        ORDER BY proposed_slot
      ) s
    ), '{}'::jsonb),
    'freshness', jsonb_build_object(
      'current_candidate_count', (
        SELECT count(*) FROM proposals WHERE still_matches_direct_evidence
      ),
      'stale_proposal_count', (
        SELECT count(*) FROM proposals WHERE NOT still_matches_direct_evidence
      )
    ),
    'evidence_links_per_proposal', jsonb_build_object(
      'minimum', (SELECT min(evidence_link_count) FROM proposals),
      'maximum', (SELECT max(evidence_link_count) FROM proposals),
      'zero_link_proposals', (
        SELECT count(*) FROM proposals WHERE evidence_link_count = 0
      )
    ),
    'sample_per_slot', p_sample_per_slot,
    'sample', coalesce((
      SELECT jsonb_agg(
        jsonb_build_object(
          'dish_name', s.dish_name,
          'proposed_slot', s.proposed_slot,
          'evidence_category', s.evidence_category,
          'confidence', s.confidence,
          'evidence_link_count', s.evidence_link_count,
          'proposal_status', s.proposal_status,
          'still_matches_direct_evidence', s.still_matches_direct_evidence
        ) ORDER BY s.proposed_slot, s.sample_rank
      )
      FROM ranked_sample s
      WHERE s.sample_rank <= p_sample_per_slot
    ), '[]'::jsonb),
    'policy', jsonb_build_object(
      'read_only', true,
      'user_data_exposed', false,
      'raw_source_text_exposed', false,
      'catalogue_names_exposed_for_review', true,
      'automatic_acceptance_allowed', false,
      'serving_changed', false,
      'publication_changed', false
    )
  ) INTO v_report;

  RETURN v_report;
END;
$$;

REVOKE ALL ON FUNCTION re_engine.direct_meal_slot_proposal_review_report(integer)
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION re_engine.direct_meal_slot_proposal_review_report(integer)
  TO service_role;

COMMENT ON FUNCTION re_engine.direct_meal_slot_proposal_review_report(integer) IS
  'Returns a bounded deterministic catalogue-name sample and reconciled proposal aggregates; performs no write and exposes no raw import or user data.';
