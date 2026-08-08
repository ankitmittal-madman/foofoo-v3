-- Materialize coarse import-course evidence as pending multi-slot proposals.
--
-- Side dish, main course, one-pot, dessert and brunch describe possible meal contexts rather than
-- one exact meal moment. This boundary therefore records review-only slot sets. It never changes
-- public.dishes, publication eligibility, either recommendation engine or Aux routing.

CREATE OR REPLACE FUNCTION re_engine.contextual_slot_set_from_import_course(p_course text)
RETURNS text[]
LANGUAGE sql
IMMUTABLE
STRICT
PARALLEL SAFE
SET search_path = pg_catalog, pg_temp
AS $$
  SELECT CASE lower(btrim(p_course))
    WHEN 'brunch' THEN ARRAY['breakfast','lunch']::text[]
    WHEN 'dessert' THEN ARRAY['lunch','dinner']::text[]
    WHEN 'main course' THEN ARRAY['lunch','dinner']::text[]
    WHEN 'one pot dish' THEN ARRAY['lunch','dinner']::text[]
    WHEN 'side dish' THEN ARRAY['lunch','dinner']::text[]
    ELSE NULL
  END;
$$;

CREATE OR REPLACE FUNCTION re_engine.contextual_course_evidence_category(p_course text)
RETURNS text
LANGUAGE sql
IMMUTABLE
STRICT
PARALLEL SAFE
SET search_path = pg_catalog, pg_temp
AS $$
  SELECT CASE lower(btrim(p_course))
    WHEN 'brunch' THEN 'brunch_candidate'
    WHEN 'dessert' THEN 'dessert_candidate'
    WHEN 'main course' THEN 'main_course_candidate'
    WHEN 'one pot dish' THEN 'one_pot_candidate'
    WHEN 'side dish' THEN 'side_dish_candidate'
    ELSE NULL
  END;
$$;

CREATE TABLE ops.dish_meal_slot_set_proposals (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  dish_id uuid NOT NULL REFERENCES public.dishes(id) ON DELETE RESTRICT,
  proposed_slots text[] NOT NULL CHECK (
    proposed_slots = ARRAY['breakfast','lunch']::text[]
    OR proposed_slots = ARRAY['lunch','dinner']::text[]
  ),
  confidence numeric(4,3) NOT NULL CHECK (confidence BETWEEN 0.700 AND 0.899),
  proposal_method text NOT NULL CHECK (
    proposal_method = 'contextual_import_course_v1'
  ),
  proposal_version text NOT NULL CHECK (
    proposal_version = 'meal-slot-set-proposal-v1'
  ),
  candidate_policy_version text NOT NULL CHECK (
    candidate_policy_version = 'contextual-import-course-slot-set-v1'
  ),
  candidate_policy_sha256 text NOT NULL CHECK (
    candidate_policy_sha256 =
      '5afca8a6da05a6070abc6678d0a4f73924cafad62835e9152916efe6e7596154'
  ),
  proposal_status text NOT NULL DEFAULT 'pending' CHECK (
    proposal_status IN ('pending','in_review','approved','rejected')
  ),
  created_by_workflow_run text NOT NULL CHECK (created_by_workflow_run ~ '^[0-9]+$'),
  reviewed_by text,
  reviewed_at timestamptz,
  review_notes text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CHECK (
    (proposal_status IN ('pending','in_review')
      AND reviewed_by IS NULL AND reviewed_at IS NULL)
    OR
    (proposal_status IN ('approved','rejected')
      AND reviewed_by IS NOT NULL AND btrim(reviewed_by) <> ''
      AND reviewed_at IS NOT NULL)
  ),
  UNIQUE (dish_id, proposal_method, proposal_version)
);

CREATE TABLE ops.dish_meal_slot_set_proposal_evidence (
  proposal_id uuid NOT NULL REFERENCES ops.dish_meal_slot_set_proposals(id)
    ON DELETE RESTRICT,
  source_row_id uuid NOT NULL REFERENCES public.dish_source_rows(id) ON DELETE RESTRICT,
  evidence_category text NOT NULL CHECK (
    evidence_category IN (
      'brunch_candidate','dessert_candidate','main_course_candidate',
      'one_pot_candidate','side_dish_candidate'
    )
  ),
  evidence_role text NOT NULL DEFAULT 'contextual_course' CHECK (
    evidence_role = 'contextual_course'
  ),
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (proposal_id, source_row_id)
);

CREATE INDEX dish_meal_slot_set_proposals_review_queue
  ON ops.dish_meal_slot_set_proposals (
    proposal_status, proposed_slots, confidence DESC, created_at, id
  );
CREATE INDEX dish_meal_slot_set_evidence_source
  ON ops.dish_meal_slot_set_proposal_evidence (source_row_id, proposal_id);

CREATE OR REPLACE FUNCTION re_engine.contextual_meal_slot_set_candidate_evidence()
RETURNS TABLE (
  dish_id uuid,
  proposed_slots text[],
  source_row_id uuid,
  evidence_category text
)
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
        SELECT 1 FROM unnest(d.meal_occasion) AS raw(raw_slot)
        WHERE re_engine.canonical_meal_slot(raw_slot) IS NOT NULL
      )
  ),
  evidence AS (
    SELECT DISTINCT
      d.dish_id,
      s.id AS source_row_id,
      re_engine.direct_slot_from_import_course(
        s.normalized_payload->>'course_raw'
      ) AS direct_slot,
      re_engine.contextual_slot_set_from_import_course(
        s.normalized_payload->>'course_raw'
      ) AS contextual_slots,
      re_engine.contextual_course_evidence_category(
        s.normalized_payload->>'course_raw'
      ) AS evidence_category
    FROM missing_slot_dishes d
    JOIN public.import_row_results r ON r.dish_id = d.dish_id
      AND r.status IN ('matched_existing','created_new','merged_duplicate','routed_review')
    JOIN public.dish_source_rows s ON s.id = r.source_row_id
  ),
  eligible AS (
    SELECT
      e.dish_id,
      min(array_to_string(e.contextual_slots, ',')) FILTER (
        WHERE e.contextual_slots IS NOT NULL
      ) AS slot_key
    FROM evidence e
    GROUP BY e.dish_id
    HAVING count(DISTINCT e.direct_slot) FILTER (WHERE e.direct_slot IS NOT NULL) = 0
      AND count(*) FILTER (WHERE e.contextual_slots IS NULL) = 0
      AND count(DISTINCT array_to_string(e.contextual_slots, ',')) = 1
  )
  SELECT
    e.dish_id,
    string_to_array(c.slot_key, ','),
    e.source_row_id,
    e.evidence_category
  FROM eligible c
  JOIN evidence e ON e.dish_id = c.dish_id
    AND array_to_string(e.contextual_slots, ',') = c.slot_key
  ORDER BY e.dish_id, e.source_row_id;
$$;

CREATE OR REPLACE FUNCTION ops.validate_meal_slot_set_proposal_evidence()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ops, public, re_engine, pg_catalog, pg_temp
AS $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM ops.dish_meal_slot_set_proposals p
    JOIN public.import_row_results r ON r.dish_id = p.dish_id
      AND r.source_row_id = NEW.source_row_id
      AND r.status IN ('matched_existing','created_new','merged_duplicate','routed_review')
    JOIN public.dish_source_rows s ON s.id = r.source_row_id
    WHERE p.id = NEW.proposal_id
      AND re_engine.contextual_slot_set_from_import_course(
        s.normalized_payload->>'course_raw'
      ) = p.proposed_slots
      AND re_engine.contextual_course_evidence_category(
        s.normalized_payload->>'course_raw'
      ) = NEW.evidence_category
  ) THEN
    RAISE EXCEPTION 'contextual meal-slot proposal evidence does not match its dish and slot set';
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER dish_meal_slot_set_proposal_evidence_guard
BEFORE INSERT OR UPDATE ON ops.dish_meal_slot_set_proposal_evidence
FOR EACH ROW EXECUTE FUNCTION ops.validate_meal_slot_set_proposal_evidence();

CREATE OR REPLACE FUNCTION ops.require_meal_slot_set_proposal_evidence()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ops, pg_catalog, pg_temp
AS $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM ops.dish_meal_slot_set_proposal_evidence e
    WHERE e.proposal_id = NEW.id
  ) THEN
    RAISE EXCEPTION 'contextual meal-slot proposal requires source-row evidence';
  END IF;
  RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER dish_meal_slot_set_proposal_evidence_required
AFTER INSERT ON ops.dish_meal_slot_set_proposals
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION ops.require_meal_slot_set_proposal_evidence();

CREATE OR REPLACE FUNCTION ops.protect_meal_slot_set_proposal_lifecycle()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ops, pg_catalog, pg_temp
AS $$
BEGIN
  IF ROW(
       NEW.dish_id, NEW.proposed_slots, NEW.confidence, NEW.proposal_method,
       NEW.proposal_version, NEW.candidate_policy_version,
       NEW.candidate_policy_sha256, NEW.created_by_workflow_run, NEW.created_at
     ) IS DISTINCT FROM ROW(
       OLD.dish_id, OLD.proposed_slots, OLD.confidence, OLD.proposal_method,
       OLD.proposal_version, OLD.candidate_policy_version,
       OLD.candidate_policy_sha256, OLD.created_by_workflow_run, OLD.created_at
     ) THEN
    RAISE EXCEPTION 'contextual meal-slot proposal identity and policy are immutable';
  END IF;
  IF OLD.proposal_status IN ('approved','rejected')
     OR NOT (
       (OLD.proposal_status = 'pending'
         AND NEW.proposal_status IN ('in_review','approved','rejected'))
       OR (OLD.proposal_status = 'in_review'
         AND NEW.proposal_status IN ('approved','rejected'))
     ) THEN
    RAISE EXCEPTION 'invalid contextual meal-slot proposal lifecycle transition';
  END IF;
  NEW.updated_at := now();
  RETURN NEW;
END;
$$;

CREATE TRIGGER dish_meal_slot_set_proposal_lifecycle_guard
BEFORE UPDATE ON ops.dish_meal_slot_set_proposals
FOR EACH ROW EXECUTE FUNCTION ops.protect_meal_slot_set_proposal_lifecycle();

ALTER TABLE ops.dish_meal_slot_set_proposals ENABLE ROW LEVEL SECURITY;
ALTER TABLE ops.dish_meal_slot_set_proposal_evidence ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON ops.dish_meal_slot_set_proposals FROM PUBLIC, anon, authenticated;
REVOKE ALL ON ops.dish_meal_slot_set_proposal_evidence FROM PUBLIC, anon, authenticated;
REVOKE ALL ON ops.dish_meal_slot_set_proposals FROM service_role;
REVOKE ALL ON ops.dish_meal_slot_set_proposal_evidence FROM service_role;
GRANT SELECT ON ops.dish_meal_slot_set_proposals TO service_role;
GRANT SELECT ON ops.dish_meal_slot_set_proposal_evidence TO service_role;

CREATE OR REPLACE FUNCTION ops.generate_contextual_meal_slot_set_proposals(
  p_workflow_run_id text,
  p_expected_candidate_count integer,
  p_expected_manifest_row_count integer,
  p_expected_source_name text,
  p_expected_source_checksum text,
  p_policy_version text,
  p_policy_sha256 text
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
  v_evidence_total integer;
  v_total_versioned integer;
BEGIN
  IF p_workflow_run_id IS NULL OR p_workflow_run_id !~ '^[0-9]+$' THEN
    RAISE EXCEPTION 'workflow run id must be numeric';
  END IF;
  IF p_expected_candidate_count <> 775 OR p_expected_manifest_row_count <> 2003 THEN
    RAISE EXCEPTION 'contextual meal-slot candidate scope is invalid';
  END IF;
  IF p_expected_source_name IS NULL
     OR p_expected_source_name <> btrim(p_expected_source_name)
     OR p_expected_source_name !~ '^[A-Za-z0-9._-]+$'
     OR p_expected_source_checksum !~ '^[0-9a-f]{64}$' THEN
    RAISE EXCEPTION 'expected contextual source identity is invalid';
  END IF;
  IF p_policy_version IS DISTINCT FROM 'contextual-import-course-slot-set-v1'
     OR p_policy_sha256 IS DISTINCT FROM
       '5afca8a6da05a6070abc6678d0a4f73924cafad62835e9152916efe6e7596154' THEN
    RAISE EXCEPTION 'contextual meal-slot candidate policy identity is invalid';
  END IF;
  IF to_regclass('pg_temp.expected_contextual_source_manifest') IS NULL THEN
    RAISE EXCEPTION 'expected contextual source manifest is missing';
  END IF;
  IF (SELECT count(*) FROM pg_temp.expected_contextual_source_manifest)
       <> p_expected_manifest_row_count THEN
    RAISE EXCEPTION 'contextual source manifest row count drifted';
  END IF;

  PERFORM pg_advisory_xact_lock(hashtext('foofoo-contextual-meal-slot-proposals-v1'));

  CREATE TEMP TABLE contextual_candidate_evidence_snapshot ON COMMIT DROP AS
  SELECT * FROM re_engine.contextual_meal_slot_set_candidate_evidence();

  SELECT count(DISTINCT c.dish_id) INTO v_candidate_count
  FROM contextual_candidate_evidence_snapshot c;
  IF v_candidate_count <> p_expected_candidate_count THEN
    RAISE EXCEPTION 'contextual meal-slot candidate count drift: expected %, found %',
      p_expected_candidate_count, v_candidate_count;
  END IF;
  IF (SELECT count(DISTINCT dish_id) FROM contextual_candidate_evidence_snapshot
      WHERE proposed_slots = ARRAY['breakfast','lunch']::text[]) <> 2
     OR (SELECT count(DISTINCT dish_id) FROM contextual_candidate_evidence_snapshot
      WHERE proposed_slots = ARRAY['lunch','dinner']::text[]) <> 773 THEN
    RAISE EXCEPTION 'contextual meal-slot candidate slot-set distribution drifted';
  END IF;
  IF (SELECT count(DISTINCT dish_id) FROM contextual_candidate_evidence_snapshot
      WHERE evidence_category = 'brunch_candidate') <> 2
     OR (SELECT count(DISTINCT dish_id) FROM contextual_candidate_evidence_snapshot
      WHERE evidence_category = 'dessert_candidate') <> 247
     OR (SELECT count(DISTINCT dish_id) FROM contextual_candidate_evidence_snapshot
      WHERE evidence_category = 'main_course_candidate') <> 120
     OR (SELECT count(DISTINCT dish_id) FROM contextual_candidate_evidence_snapshot
      WHERE evidence_category = 'one_pot_candidate') <> 12
     OR (SELECT count(DISTINCT dish_id) FROM contextual_candidate_evidence_snapshot
      WHERE evidence_category = 'side_dish_candidate') <> 394 THEN
    RAISE EXCEPTION 'contextual meal-slot candidate category distribution drifted';
  END IF;
  IF EXISTS (
    SELECT 1
    FROM contextual_candidate_evidence_snapshot c
    JOIN public.dish_source_rows s ON s.id = c.source_row_id
    JOIN public.import_runs r ON r.id = s.import_run_id
    LEFT JOIN pg_temp.expected_contextual_source_manifest m
      ON m.source_srno = s.source_srno
    WHERE r.source_name IS DISTINCT FROM p_expected_source_name
      OR r.source_checksum IS DISTINCT FROM p_expected_source_checksum
      OR m.source_srno IS NULL
      OR m.row_fingerprint IS DISTINCT FROM s.row_fingerprint
      OR m.evidence_category IS DISTINCT FROM c.evidence_category
      OR m.proposed_slots_key IS DISTINCT FROM array_to_string(c.proposed_slots, ',')
  ) THEN
    RAISE EXCEPTION 'contextual proposal evidence does not match the checked-in row manifest';
  END IF;

  INSERT INTO ops.dish_meal_slot_set_proposals (
    dish_id, proposed_slots, confidence, proposal_method, proposal_version,
    candidate_policy_version, candidate_policy_sha256, created_by_workflow_run
  )
  SELECT DISTINCT
    c.dish_id,
    c.proposed_slots,
    0.750,
    'contextual_import_course_v1',
    'meal-slot-set-proposal-v1',
    p_policy_version,
    p_policy_sha256,
    p_workflow_run_id
  FROM contextual_candidate_evidence_snapshot c
  ON CONFLICT (dish_id, proposal_method, proposal_version) DO NOTHING;
  GET DIAGNOSTICS v_inserted_count = ROW_COUNT;

  INSERT INTO ops.dish_meal_slot_set_proposal_evidence (
    proposal_id, source_row_id, evidence_category
  )
  SELECT p.id, c.source_row_id, c.evidence_category
  FROM contextual_candidate_evidence_snapshot c
  JOIN ops.dish_meal_slot_set_proposals p ON p.dish_id = c.dish_id
    AND p.proposal_method = 'contextual_import_course_v1'
    AND p.proposal_version = 'meal-slot-set-proposal-v1'
    AND p.proposed_slots = c.proposed_slots
  ON CONFLICT (proposal_id, source_row_id) DO NOTHING;
  GET DIAGNOSTICS v_evidence_inserted = ROW_COUNT;

  SELECT count(*) INTO v_total_versioned
  FROM ops.dish_meal_slot_set_proposals p
  WHERE p.proposal_method = 'contextual_import_course_v1'
    AND p.proposal_version = 'meal-slot-set-proposal-v1';
  SELECT count(*) INTO v_evidence_total
  FROM ops.dish_meal_slot_set_proposal_evidence e
  JOIN ops.dish_meal_slot_set_proposals p ON p.id = e.proposal_id
  WHERE p.proposal_method = 'contextual_import_course_v1'
    AND p.proposal_version = 'meal-slot-set-proposal-v1';
  IF v_total_versioned <> v_candidate_count THEN
    RAISE EXCEPTION 'materialized contextual proposals do not match candidate count';
  END IF;
  IF EXISTS (
    SELECT 1 FROM ops.dish_meal_slot_set_proposals p
    WHERE p.proposal_method = 'contextual_import_course_v1'
      AND p.proposal_version = 'meal-slot-set-proposal-v1'
      AND NOT EXISTS (
        SELECT 1 FROM ops.dish_meal_slot_set_proposal_evidence e
        WHERE e.proposal_id = p.id
      )
  ) THEN
    RAISE EXCEPTION 'materialized contextual proposal is missing evidence';
  END IF;

  RETURN jsonb_build_object(
    'schema_version', 'contextual-meal-slot-set-proposal-generation-v1',
    'policy_version', p_policy_version,
    'policy_sha256', p_policy_sha256,
    'candidate_count', v_candidate_count,
    'inserted_count', v_inserted_count,
    'existing_count', v_candidate_count - v_inserted_count,
    'evidence_links_inserted', v_evidence_inserted,
    'evidence_link_count', v_evidence_total,
    'manifest_candidate_row_count', p_expected_manifest_row_count,
    'total_versioned_proposals', v_total_versioned,
    'status', 'pending_review',
    'slot_set_counts', jsonb_build_object(
      'breakfast,lunch', 2,
      'lunch,dinner', 773
    ),
    'category_counts', jsonb_build_object(
      'brunch', 2,
      'dessert', 247,
      'main course', 120,
      'one pot dish', 12,
      'side dish', 394
    ),
    'deferred_dish_counts', jsonb_build_object(
      'diet_value_in_course_field', 22,
      'conflicting_direct_evidence', 1
    ),
    'policy', jsonb_build_object(
      'proposal_only', true,
      'requires_explicit_approval_before_apply', true,
      'identity_exposed', false,
      'raw_source_text_exposed', false,
      'dishes_changed', false,
      'publication_changed', false,
      'serving_changed', false
    )
  );
END;
$$;

REVOKE ALL ON FUNCTION re_engine.contextual_slot_set_from_import_course(text)
  FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION re_engine.contextual_course_evidence_category(text)
  FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION re_engine.contextual_meal_slot_set_candidate_evidence()
  FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION ops.generate_contextual_meal_slot_set_proposals(
  text, integer, integer, text, text, text, text
) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION re_engine.contextual_slot_set_from_import_course(text)
  TO service_role;
GRANT EXECUTE ON FUNCTION re_engine.contextual_course_evidence_category(text)
  TO service_role;
GRANT EXECUTE ON FUNCTION re_engine.contextual_meal_slot_set_candidate_evidence()
  TO service_role;
GRANT EXECUTE ON FUNCTION ops.generate_contextual_meal_slot_set_proposals(
  text, integer, integer, text, text, text, text
) TO service_role;

COMMENT ON TABLE ops.dish_meal_slot_set_proposals IS
  'Service-only review queue for coarse multi-slot candidates; no proposal is a dish fact or serving input.';
COMMENT ON TABLE ops.dish_meal_slot_set_proposal_evidence IS
  'Immutable source-row lineage for one contextual multi-slot proposal.';
COMMENT ON FUNCTION ops.generate_contextual_meal_slot_set_proposals(
  text, integer, integer, text, text, text, text
) IS
  'Creates exactly 775 pending row-verified multi-slot proposals under a hash-pinned candidate policy; changes no dish, publication or serving state.';
