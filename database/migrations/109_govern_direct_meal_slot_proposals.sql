-- Materialize exact import-course evidence as pending, non-serving meal-slot proposals.
--
-- This does not update dishes.meal_occasion, ontology state, publication eligibility or either
-- recommendation engine. Proposals require evidence rows, are immutable apart from a forward-only
-- review lifecycle, and cannot be applied automatically.

CREATE TABLE ops.dish_meal_slot_proposals (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  dish_id uuid NOT NULL REFERENCES public.dishes(id) ON DELETE RESTRICT,
  proposed_slot text NOT NULL CHECK (
    proposed_slot IN ('breakfast','lunch','dinner','snacks')
  ),
  evidence_category text NOT NULL CHECK (
    evidence_category IN (
      'exact_breakfast_course','exact_lunch_course',
      'exact_dinner_course','exact_snacks_course'
    )
  ),
  confidence numeric(4,3) NOT NULL CHECK (confidence BETWEEN 0.900 AND 1.000),
  proposal_method text NOT NULL CHECK (proposal_method = 'exact_import_course_v1'),
  proposal_version text NOT NULL CHECK (proposal_version = 'meal-slot-proposal-v1'),
  proposal_status text NOT NULL DEFAULT 'pending' CHECK (
    proposal_status IN ('pending','in_review','approved','rejected','applied')
  ),
  created_by_workflow_run text NOT NULL CHECK (
    created_by_workflow_run ~ '^[0-9]+$'
  ),
  reviewed_by text,
  reviewed_at timestamptz,
  review_notes text,
  applied_by text,
  applied_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CHECK (
    (proposed_slot = 'breakfast' AND evidence_category = 'exact_breakfast_course')
    OR (proposed_slot = 'lunch' AND evidence_category = 'exact_lunch_course')
    OR (proposed_slot = 'dinner' AND evidence_category = 'exact_dinner_course')
    OR (proposed_slot = 'snacks' AND evidence_category = 'exact_snacks_course')
  ),
  CHECK (
    (proposal_status IN ('pending','in_review') AND reviewed_by IS NULL
      AND reviewed_at IS NULL AND applied_by IS NULL AND applied_at IS NULL)
    OR
    (proposal_status IN ('approved','rejected') AND reviewed_by IS NOT NULL
      AND btrim(reviewed_by) <> '' AND reviewed_at IS NOT NULL
      AND applied_by IS NULL AND applied_at IS NULL)
    OR
    (proposal_status = 'applied' AND reviewed_by IS NOT NULL
      AND btrim(reviewed_by) <> '' AND reviewed_at IS NOT NULL
      AND applied_by IS NOT NULL AND btrim(applied_by) <> '' AND applied_at IS NOT NULL)
  ),
  UNIQUE (dish_id, proposed_slot, proposal_method, proposal_version)
);

CREATE TABLE ops.dish_meal_slot_proposal_evidence (
  proposal_id uuid NOT NULL REFERENCES ops.dish_meal_slot_proposals(id) ON DELETE RESTRICT,
  source_row_id uuid NOT NULL REFERENCES public.dish_source_rows(id) ON DELETE RESTRICT,
  evidence_role text NOT NULL DEFAULT 'direct_course' CHECK (
    evidence_role = 'direct_course'
  ),
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (proposal_id, source_row_id)
);

CREATE INDEX dish_meal_slot_proposals_review_queue
  ON ops.dish_meal_slot_proposals (
    proposal_status, proposed_slot, confidence DESC, created_at, id
  );
CREATE INDEX dish_meal_slot_proposal_evidence_source
  ON ops.dish_meal_slot_proposal_evidence (source_row_id, proposal_id);

CREATE OR REPLACE FUNCTION re_engine.direct_slot_from_import_course(p_course text)
RETURNS text
LANGUAGE sql
IMMUTABLE
STRICT
PARALLEL SAFE
SET search_path = pg_catalog, pg_temp
AS $$
  SELECT CASE lower(btrim(p_course))
    WHEN 'lunch' THEN 'lunch'
    WHEN 'dinner' THEN 'dinner'
    WHEN 'snack' THEN 'snacks'
    WHEN 'appetizer' THEN 'snacks'
    WHEN 'south indian breakfast' THEN 'breakfast'
    WHEN 'world breakfast' THEN 'breakfast'
    WHEN 'north indian breakfast' THEN 'breakfast'
    WHEN 'indian breakfast' THEN 'breakfast'
    ELSE NULL
  END;
$$;

CREATE OR REPLACE FUNCTION re_engine.direct_meal_slot_proposal_candidates()
RETURNS TABLE (dish_id uuid, proposed_slot text, source_row_id uuid)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public, re_engine, pg_temp
AS $$
  WITH missing_slot_dishes AS (
    SELECT d.id AS dish_id
    FROM public.dishes d
    WHERE d.is_active
      AND NOT EXISTS (
        SELECT 1
        FROM unnest(d.meal_occasion) AS raw(raw_slot)
        WHERE re_engine.canonical_meal_slot(raw_slot) IS NOT NULL
      )
  ),
  evidence AS (
    SELECT DISTINCT
      d.dish_id,
      s.id AS source_row_id,
      re_engine.direct_slot_from_import_course(
        s.normalized_payload->>'course_raw'
      ) AS direct_slot
    FROM missing_slot_dishes d
    JOIN public.import_row_results r ON r.dish_id = d.dish_id
      AND r.status IN ('matched_existing','created_new','merged_duplicate','routed_review')
    JOIN public.dish_source_rows s ON s.id = r.source_row_id
  ),
  eligible AS (
    SELECT
      dish_id,
      min(direct_slot) FILTER (WHERE direct_slot IS NOT NULL) AS proposed_slot
    FROM evidence
    GROUP BY dish_id
    HAVING count(DISTINCT direct_slot) FILTER (WHERE direct_slot IS NOT NULL) = 1
      AND count(*) FILTER (WHERE direct_slot IS NULL) = 0
  )
  SELECT e.dish_id, c.proposed_slot, e.source_row_id
  FROM eligible c
  JOIN evidence e ON e.dish_id = c.dish_id AND e.direct_slot = c.proposed_slot
  ORDER BY e.dish_id, e.source_row_id;
$$;

CREATE OR REPLACE FUNCTION ops.validate_meal_slot_proposal_evidence()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ops, public, re_engine, pg_catalog, pg_temp
AS $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM ops.dish_meal_slot_proposals p
    JOIN public.import_row_results r ON r.dish_id = p.dish_id
      AND r.source_row_id = NEW.source_row_id
      AND r.status IN ('matched_existing','created_new','merged_duplicate','routed_review')
    JOIN public.dish_source_rows s ON s.id = r.source_row_id
    WHERE p.id = NEW.proposal_id
      AND re_engine.direct_slot_from_import_course(
        s.normalized_payload->>'course_raw'
      ) = p.proposed_slot
  ) THEN
    RAISE EXCEPTION 'meal-slot proposal evidence must match its dish and direct slot';
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER dish_meal_slot_proposal_evidence_guard
BEFORE INSERT OR UPDATE ON ops.dish_meal_slot_proposal_evidence
FOR EACH ROW EXECUTE FUNCTION ops.validate_meal_slot_proposal_evidence();

CREATE OR REPLACE FUNCTION ops.require_meal_slot_proposal_evidence()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ops, pg_catalog, pg_temp
AS $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM ops.dish_meal_slot_proposal_evidence e
    WHERE e.proposal_id = NEW.id
  ) THEN
    RAISE EXCEPTION 'meal-slot proposal requires at least one direct evidence row';
  END IF;
  RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER dish_meal_slot_proposal_evidence_required
AFTER INSERT ON ops.dish_meal_slot_proposals
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION ops.require_meal_slot_proposal_evidence();

CREATE OR REPLACE FUNCTION ops.protect_meal_slot_proposal_lifecycle()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ops, pg_catalog, pg_temp
AS $$
BEGIN
  IF ROW(
       NEW.dish_id, NEW.proposed_slot, NEW.evidence_category, NEW.confidence,
       NEW.proposal_method, NEW.proposal_version, NEW.created_by_workflow_run,
       NEW.created_at
     ) IS DISTINCT FROM ROW(
       OLD.dish_id, OLD.proposed_slot, OLD.evidence_category, OLD.confidence,
       OLD.proposal_method, OLD.proposal_version, OLD.created_by_workflow_run,
       OLD.created_at
     ) THEN
    RAISE EXCEPTION 'meal-slot proposal identity and evidence are immutable';
  END IF;
  IF OLD.proposal_status IN ('rejected','applied')
     OR NOT (
       (OLD.proposal_status = 'pending'
         AND NEW.proposal_status IN ('in_review','approved','rejected'))
       OR (OLD.proposal_status = 'in_review'
         AND NEW.proposal_status IN ('approved','rejected'))
       OR (OLD.proposal_status = 'approved' AND NEW.proposal_status = 'applied')
     ) THEN
    RAISE EXCEPTION 'invalid meal-slot proposal lifecycle transition';
  END IF;
  NEW.updated_at := now();
  RETURN NEW;
END;
$$;

CREATE TRIGGER dish_meal_slot_proposal_lifecycle_guard
BEFORE UPDATE ON ops.dish_meal_slot_proposals
FOR EACH ROW EXECUTE FUNCTION ops.protect_meal_slot_proposal_lifecycle();

ALTER TABLE ops.dish_meal_slot_proposals ENABLE ROW LEVEL SECURITY;
ALTER TABLE ops.dish_meal_slot_proposal_evidence ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON ops.dish_meal_slot_proposals FROM PUBLIC, anon, authenticated;
REVOKE ALL ON ops.dish_meal_slot_proposal_evidence FROM PUBLIC, anon, authenticated;
GRANT SELECT ON ops.dish_meal_slot_proposals TO service_role;
GRANT SELECT ON ops.dish_meal_slot_proposal_evidence TO service_role;

CREATE OR REPLACE FUNCTION ops.generate_direct_meal_slot_proposals(
  p_workflow_run_id text,
  p_expected_candidate_count integer
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ops, public, re_engine, pg_catalog, pg_temp
AS $$
DECLARE
  v_candidate_count integer;
  v_inserted_count integer;
  v_evidence_inserted integer;
  v_total_versioned integer;
BEGIN
  IF p_workflow_run_id IS NULL OR p_workflow_run_id !~ '^[0-9]+$' THEN
    RAISE EXCEPTION 'workflow run id must be numeric';
  END IF;
  IF p_expected_candidate_count IS NULL OR p_expected_candidate_count < 1 THEN
    RAISE EXCEPTION 'expected candidate count must be positive';
  END IF;

  PERFORM pg_advisory_xact_lock(hashtext('foofoo-direct-meal-slot-proposals-v1'));

  SELECT count(DISTINCT c.dish_id) INTO v_candidate_count
  FROM re_engine.direct_meal_slot_proposal_candidates() c;
  IF v_candidate_count <> p_expected_candidate_count THEN
    RAISE EXCEPTION 'direct meal-slot candidate count drift: expected %, found %',
      p_expected_candidate_count, v_candidate_count;
  END IF;

  INSERT INTO ops.dish_meal_slot_proposals (
    dish_id, proposed_slot, evidence_category, confidence,
    proposal_method, proposal_version, created_by_workflow_run
  )
  SELECT DISTINCT
    c.dish_id,
    c.proposed_slot,
    CASE c.proposed_slot
      WHEN 'breakfast' THEN 'exact_breakfast_course'
      WHEN 'lunch' THEN 'exact_lunch_course'
      WHEN 'dinner' THEN 'exact_dinner_course'
      WHEN 'snacks' THEN 'exact_snacks_course'
    END,
    0.950,
    'exact_import_course_v1',
    'meal-slot-proposal-v1',
    p_workflow_run_id
  FROM re_engine.direct_meal_slot_proposal_candidates() c
  ON CONFLICT (dish_id, proposed_slot, proposal_method, proposal_version) DO NOTHING;
  GET DIAGNOSTICS v_inserted_count = ROW_COUNT;

  INSERT INTO ops.dish_meal_slot_proposal_evidence (proposal_id, source_row_id)
  SELECT p.id, c.source_row_id
  FROM re_engine.direct_meal_slot_proposal_candidates() c
  JOIN ops.dish_meal_slot_proposals p ON p.dish_id = c.dish_id
    AND p.proposed_slot = c.proposed_slot
    AND p.proposal_method = 'exact_import_course_v1'
    AND p.proposal_version = 'meal-slot-proposal-v1'
  ON CONFLICT (proposal_id, source_row_id) DO NOTHING;
  GET DIAGNOSTICS v_evidence_inserted = ROW_COUNT;

  SELECT count(*) INTO v_total_versioned
  FROM ops.dish_meal_slot_proposals p
  WHERE p.proposal_method = 'exact_import_course_v1'
    AND p.proposal_version = 'meal-slot-proposal-v1';
  IF v_total_versioned <> v_candidate_count THEN
    RAISE EXCEPTION 'materialized meal-slot proposals do not match candidate count';
  END IF;
  IF EXISTS (
    SELECT 1
    FROM ops.dish_meal_slot_proposals p
    WHERE p.proposal_method = 'exact_import_course_v1'
      AND p.proposal_version = 'meal-slot-proposal-v1'
      AND NOT EXISTS (
        SELECT 1 FROM ops.dish_meal_slot_proposal_evidence e
        WHERE e.proposal_id = p.id
      )
  ) THEN
    RAISE EXCEPTION 'materialized meal-slot proposal is missing evidence';
  END IF;

  RETURN jsonb_build_object(
    'schema_version', 'recommendation-meal-slot-proposal-generation-v1',
    'candidate_count', v_candidate_count,
    'inserted_count', v_inserted_count,
    'existing_count', v_candidate_count - v_inserted_count,
    'evidence_links_inserted', v_evidence_inserted,
    'total_versioned_proposals', v_total_versioned,
    'status', 'pending_review',
    'policy', jsonb_build_object(
      'identity_exposed', false,
      'raw_source_text_exposed', false,
      'automatic_acceptance_allowed', false,
      'serving_changed', false,
      'publication_changed', false
    ),
    'slot_counts', (
      SELECT jsonb_object_agg(slot_counts.proposed_slot, slot_counts.proposal_count)
      FROM (
        SELECT p.proposed_slot, count(*) AS proposal_count
        FROM ops.dish_meal_slot_proposals p
        WHERE p.proposal_method = 'exact_import_course_v1'
          AND p.proposal_version = 'meal-slot-proposal-v1'
        GROUP BY p.proposed_slot
        ORDER BY p.proposed_slot
      ) slot_counts
    )
  );
END;
$$;

REVOKE ALL ON FUNCTION re_engine.direct_slot_from_import_course(text)
  FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION re_engine.direct_meal_slot_proposal_candidates()
  FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION ops.generate_direct_meal_slot_proposals(text, integer)
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION re_engine.direct_slot_from_import_course(text) TO service_role;
GRANT EXECUTE ON FUNCTION re_engine.direct_meal_slot_proposal_candidates() TO service_role;
GRANT EXECUTE ON FUNCTION ops.generate_direct_meal_slot_proposals(text, integer)
  TO service_role;

COMMENT ON TABLE ops.dish_meal_slot_proposals IS
  'Service-only, evidence-linked pending meal-slot proposals; no row affects serving until separately reviewed and applied.';
COMMENT ON TABLE ops.dish_meal_slot_proposal_evidence IS
  'Immutable import source-row lineage for one governed meal-slot proposal.';
COMMENT ON FUNCTION ops.generate_direct_meal_slot_proposals(text, integer) IS
  'Idempotently creates only pending direct-course proposals after an exact expected-count check; performs no catalogue or serving write.';
