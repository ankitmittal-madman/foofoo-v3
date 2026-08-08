-- Apply one explicitly approved contextual slot-set policy as a reversible, audited cohort.
--
-- Installation is additive and changes no dish or proposal. Application requires the exact
-- production proposal/evidence cohort, checked-in row manifest, candidate-policy hash, a durable
-- Product approval reference and actor provenance. Restore is atomic and fails when any applied
-- dish has since changed, preserving later human or system edits.

ALTER TABLE ops.dish_meal_slot_set_proposals
  DROP CONSTRAINT dish_meal_slot_set_proposals_proposal_status_check;
ALTER TABLE ops.dish_meal_slot_set_proposals
  ADD CONSTRAINT dish_meal_slot_set_proposals_proposal_status_check CHECK (
    proposal_status IN ('pending','in_review','approved','rejected','applied','rolled_back')
  );
ALTER TABLE ops.dish_meal_slot_set_proposals
  DROP CONSTRAINT dish_meal_slot_set_proposals_check;
ALTER TABLE ops.dish_meal_slot_set_proposals
  ADD CONSTRAINT dish_meal_slot_set_proposals_review_provenance_check CHECK (
    (proposal_status IN ('pending','in_review')
      AND reviewed_by IS NULL AND reviewed_at IS NULL)
    OR
    (proposal_status IN ('approved','rejected','applied','rolled_back')
      AND reviewed_by IS NOT NULL AND btrim(reviewed_by) <> ''
      AND reviewed_at IS NOT NULL)
  );

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
  IF OLD.proposal_status IN ('rejected','rolled_back')
     OR NOT (
       (OLD.proposal_status = 'pending'
         AND NEW.proposal_status IN ('in_review','approved','rejected'))
       OR (OLD.proposal_status = 'in_review'
         AND NEW.proposal_status IN ('approved','rejected'))
       OR (OLD.proposal_status = 'approved' AND NEW.proposal_status = 'applied')
       OR (OLD.proposal_status = 'applied' AND NEW.proposal_status = 'rolled_back')
     ) THEN
    RAISE EXCEPTION 'invalid contextual meal-slot proposal lifecycle transition';
  END IF;
  NEW.updated_at := now();
  RETURN NEW;
END;
$$;

CREATE TABLE ops.dish_meal_slot_set_applications (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  proposal_id uuid NOT NULL UNIQUE
    REFERENCES ops.dish_meal_slot_set_proposals(id) ON DELETE RESTRICT,
  dish_id uuid NOT NULL UNIQUE REFERENCES public.dishes(id) ON DELETE RESTRICT,
  previous_meal_occasion text[] NOT NULL,
  applied_meal_occasion text[] NOT NULL CHECK (
    applied_meal_occasion = ARRAY['breakfast','lunch']::text[]
    OR applied_meal_occasion = ARRAY['lunch','dinner']::text[]
  ),
  candidate_policy_version text NOT NULL CHECK (
    candidate_policy_version = 'contextual-import-course-slot-set-v1'
  ),
  candidate_policy_sha256 text NOT NULL CHECK (
    candidate_policy_sha256 =
      '5afca8a6da05a6070abc6678d0a4f73924cafad62835e9152916efe6e7596154'
  ),
  approval_reference text NOT NULL CHECK (
    approval_reference ~ '^[A-Za-z0-9][A-Za-z0-9._:/#-]{7,199}$'
  ),
  reviewed_by text NOT NULL CHECK (reviewed_by ~ '^[A-Za-z0-9][A-Za-z0-9._:@/-]{2,127}$'),
  applied_by text NOT NULL CHECK (applied_by ~ '^[A-Za-z0-9][A-Za-z0-9._:@/-]{2,127}$'),
  applied_by_workflow_run text NOT NULL CHECK (applied_by_workflow_run ~ '^[0-9]+$'),
  application_status text NOT NULL DEFAULT 'applied' CHECK (
    application_status IN ('applied','rolled_back')
  ),
  applied_at timestamptz NOT NULL DEFAULT now(),
  rolled_back_by text,
  rollback_reference text,
  rolled_back_by_workflow_run text,
  rolled_back_at timestamptz,
  CHECK (
    (application_status = 'applied'
      AND rolled_back_by IS NULL
      AND rollback_reference IS NULL
      AND rolled_back_by_workflow_run IS NULL
      AND rolled_back_at IS NULL)
    OR
    (application_status = 'rolled_back'
      AND rolled_back_by ~ '^[A-Za-z0-9][A-Za-z0-9._:@/-]{2,127}$'
      AND rollback_reference ~ '^[A-Za-z0-9][A-Za-z0-9._:/#-]{7,199}$'
      AND rolled_back_by_workflow_run ~ '^[0-9]+$'
      AND rolled_back_at IS NOT NULL)
  )
);

CREATE INDEX dish_meal_slot_set_applications_policy_status
  ON ops.dish_meal_slot_set_applications (
    candidate_policy_version, candidate_policy_sha256, application_status, dish_id
  );

ALTER TABLE ops.dish_meal_slot_set_applications ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON ops.dish_meal_slot_set_applications FROM PUBLIC, anon, authenticated;
REVOKE ALL ON ops.dish_meal_slot_set_applications FROM service_role;
GRANT SELECT ON ops.dish_meal_slot_set_applications TO service_role;

CREATE OR REPLACE FUNCTION ops.apply_contextual_meal_slot_set_policy(
  p_workflow_run_id text,
  p_expected_proposal_count integer,
  p_expected_evidence_link_count integer,
  p_expected_manifest_row_count integer,
  p_expected_source_name text,
  p_expected_source_checksum text,
  p_policy_version text,
  p_policy_sha256 text,
  p_approval_reference text,
  p_reviewed_by text,
  p_applied_by text
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ops, public, re_engine, pg_catalog, pg_temp
AS $$
DECLARE
  v_existing_count integer;
  v_changed_count integer;
  v_now timestamptz := clock_timestamp();
BEGIN
  IF p_workflow_run_id IS NULL OR p_workflow_run_id !~ '^[0-9]+$' THEN
    RAISE EXCEPTION 'workflow run id must be numeric';
  END IF;
  IF p_expected_proposal_count <> 775
     OR p_expected_evidence_link_count <> 3121
     OR p_expected_manifest_row_count <> 2003 THEN
    RAISE EXCEPTION 'approved contextual slot-set cohort counts are invalid';
  END IF;
  IF p_policy_version IS DISTINCT FROM 'contextual-import-course-slot-set-v1'
     OR p_policy_sha256 IS DISTINCT FROM
       '5afca8a6da05a6070abc6678d0a4f73924cafad62835e9152916efe6e7596154' THEN
    RAISE EXCEPTION 'contextual candidate policy identity is not accepted by this boundary';
  END IF;
  IF p_expected_source_name IS NULL
     OR p_expected_source_name <> btrim(p_expected_source_name)
     OR p_expected_source_name !~ '^[A-Za-z0-9._-]+$'
     OR p_expected_source_checksum !~ '^[0-9a-f]{64}$' THEN
    RAISE EXCEPTION 'expected contextual source identity is invalid';
  END IF;
  IF p_approval_reference IS NULL
     OR p_approval_reference !~ '^[A-Za-z0-9][A-Za-z0-9._:/#-]{7,199}$' THEN
    RAISE EXCEPTION 'an explicit Product approval reference is required';
  END IF;
  IF p_reviewed_by IS NULL OR p_reviewed_by !~ '^[A-Za-z0-9][A-Za-z0-9._:@/-]{2,127}$'
     OR p_applied_by IS NULL OR p_applied_by !~ '^[A-Za-z0-9][A-Za-z0-9._:@/-]{2,127}$' THEN
    RAISE EXCEPTION 'review and application actors must be explicit safe identifiers';
  END IF;
  IF to_regclass('pg_temp.expected_contextual_source_manifest') IS NULL THEN
    RAISE EXCEPTION 'expected contextual source manifest is missing';
  END IF;

  PERFORM pg_advisory_xact_lock(hashtext('foofoo-contextual-meal-slot-policy-application-v1'));

  SELECT count(*) INTO v_existing_count
  FROM ops.dish_meal_slot_set_applications a
  WHERE a.candidate_policy_version = p_policy_version
    AND a.candidate_policy_sha256 = p_policy_sha256;
  IF v_existing_count > 0 THEN
    IF v_existing_count = p_expected_proposal_count
       AND NOT EXISTS (
         SELECT 1
         FROM ops.dish_meal_slot_set_applications a
         JOIN ops.dish_meal_slot_set_proposals p ON p.id = a.proposal_id
         JOIN public.dishes d ON d.id = a.dish_id
         WHERE a.candidate_policy_version = p_policy_version
           AND a.candidate_policy_sha256 = p_policy_sha256
           AND (
             a.application_status <> 'applied'
             OR p.proposal_status <> 'applied'
             OR d.meal_occasion IS DISTINCT FROM a.applied_meal_occasion
           )
       ) THEN
      RETURN jsonb_build_object(
        'schema_version', 'contextual-meal-slot-policy-application-v1',
        'policy_version', p_policy_version,
        'policy_sha256', p_policy_sha256,
        'proposal_count', p_expected_proposal_count,
        'evidence_link_count', p_expected_evidence_link_count,
        'manifest_candidate_row_count', p_expected_manifest_row_count,
        'applied_count', 0,
        'existing_applied_count', v_existing_count,
        'status', 'already_applied',
        'publication_changed', false,
        'serving_changed', false
      );
    END IF;
    RAISE EXCEPTION 'existing contextual slot-set application state is partial or divergent';
  END IF;

  IF (SELECT count(*) FROM ops.dish_meal_slot_set_proposals p
      WHERE p.proposal_method = 'contextual_import_course_v1'
        AND p.proposal_version = 'meal-slot-set-proposal-v1') <> p_expected_proposal_count
     OR (SELECT count(*)
         FROM ops.dish_meal_slot_set_proposal_evidence e
         JOIN ops.dish_meal_slot_set_proposals p ON p.id = e.proposal_id
         WHERE p.proposal_method = 'contextual_import_course_v1'
           AND p.proposal_version = 'meal-slot-set-proposal-v1')
       <> p_expected_evidence_link_count
     OR (SELECT count(*) FROM pg_temp.expected_contextual_source_manifest)
       <> p_expected_manifest_row_count THEN
    RAISE EXCEPTION 'contextual proposal, evidence or manifest cohort drifted';
  END IF;
  IF (SELECT count(*) FROM ops.dish_meal_slot_set_proposals p
      WHERE p.proposal_method = 'contextual_import_course_v1'
        AND p.proposal_version = 'meal-slot-set-proposal-v1'
        AND p.proposed_slots = ARRAY['breakfast','lunch']::text[]) <> 2
     OR (SELECT count(*) FROM ops.dish_meal_slot_set_proposals p
      WHERE p.proposal_method = 'contextual_import_course_v1'
        AND p.proposal_version = 'meal-slot-set-proposal-v1'
        AND p.proposed_slots = ARRAY['lunch','dinner']::text[]) <> 773 THEN
    RAISE EXCEPTION 'contextual slot-set proposal distribution drifted';
  END IF;
  IF EXISTS (
    SELECT 1
    FROM ops.dish_meal_slot_set_proposal_evidence e
    JOIN ops.dish_meal_slot_set_proposals p ON p.id = e.proposal_id
    JOIN public.dish_source_rows s ON s.id = e.source_row_id
    JOIN public.import_runs r ON r.id = s.import_run_id
    LEFT JOIN pg_temp.expected_contextual_source_manifest m ON m.source_srno = s.source_srno
    WHERE p.proposal_method = 'contextual_import_course_v1'
      AND p.proposal_version = 'meal-slot-set-proposal-v1'
      AND (
        r.source_name IS DISTINCT FROM p_expected_source_name
        OR r.source_checksum IS DISTINCT FROM p_expected_source_checksum
        OR m.source_srno IS NULL
        OR m.row_fingerprint IS DISTINCT FROM s.row_fingerprint
        OR m.evidence_category IS DISTINCT FROM e.evidence_category
        OR m.proposed_slots_key IS DISTINCT FROM array_to_string(p.proposed_slots, ',')
      )
  ) THEN
    RAISE EXCEPTION 'contextual application evidence does not match checked-in manifest';
  END IF;

  PERFORM 1
  FROM ops.dish_meal_slot_set_proposals p
  JOIN public.dishes d ON d.id = p.dish_id
  WHERE p.proposal_method = 'contextual_import_course_v1'
    AND p.proposal_version = 'meal-slot-set-proposal-v1'
  ORDER BY p.id
  FOR UPDATE OF p, d;
  IF EXISTS (
    SELECT 1
    FROM ops.dish_meal_slot_set_proposals p
    JOIN public.dishes d ON d.id = p.dish_id
    WHERE p.proposal_method = 'contextual_import_course_v1'
      AND p.proposal_version = 'meal-slot-set-proposal-v1'
      AND (
        p.proposal_status NOT IN ('pending','in_review')
        OR NOT d.is_active
        OR EXISTS (
          SELECT 1 FROM unnest(d.meal_occasion) raw(raw_slot)
          WHERE re_engine.canonical_meal_slot(raw_slot) IS NOT NULL
        )
      )
  ) THEN
    RAISE EXCEPTION 'contextual cohort is no longer uniformly pending and slot-empty';
  END IF;

  INSERT INTO ops.dish_meal_slot_set_applications (
    proposal_id, dish_id, previous_meal_occasion, applied_meal_occasion,
    candidate_policy_version, candidate_policy_sha256, approval_reference,
    reviewed_by, applied_by, applied_by_workflow_run, applied_at
  )
  SELECT
    p.id, d.id, d.meal_occasion, p.proposed_slots,
    p_policy_version, p_policy_sha256, p_approval_reference,
    p_reviewed_by, p_applied_by, p_workflow_run_id, v_now
  FROM ops.dish_meal_slot_set_proposals p
  JOIN public.dishes d ON d.id = p.dish_id
  WHERE p.proposal_method = 'contextual_import_course_v1'
    AND p.proposal_version = 'meal-slot-set-proposal-v1';
  GET DIAGNOSTICS v_changed_count = ROW_COUNT;
  IF v_changed_count <> p_expected_proposal_count THEN
    RAISE EXCEPTION 'contextual application ledger count mismatch';
  END IF;

  UPDATE ops.dish_meal_slot_set_proposals p
  SET proposal_status = 'approved',
      reviewed_by = p_reviewed_by,
      reviewed_at = v_now,
      review_notes = 'Approved under ' || p_policy_version || ' / ' || p_approval_reference
  WHERE p.proposal_method = 'contextual_import_course_v1'
    AND p.proposal_version = 'meal-slot-set-proposal-v1'
    AND p.proposal_status IN ('pending','in_review');
  GET DIAGNOSTICS v_changed_count = ROW_COUNT;
  IF v_changed_count <> p_expected_proposal_count THEN
    RAISE EXCEPTION 'contextual proposal approval count mismatch';
  END IF;

  UPDATE public.dishes d
  SET meal_occasion = a.applied_meal_occasion
  FROM ops.dish_meal_slot_set_applications a
  WHERE a.dish_id = d.id
    AND a.candidate_policy_version = p_policy_version
    AND a.candidate_policy_sha256 = p_policy_sha256
    AND d.meal_occasion IS NOT DISTINCT FROM a.previous_meal_occasion;
  GET DIAGNOSTICS v_changed_count = ROW_COUNT;
  IF v_changed_count <> p_expected_proposal_count THEN
    RAISE EXCEPTION 'contextual dish update count mismatch';
  END IF;

  UPDATE ops.dish_meal_slot_set_proposals p
  SET proposal_status = 'applied'
  FROM ops.dish_meal_slot_set_applications a
  WHERE a.proposal_id = p.id
    AND a.candidate_policy_version = p_policy_version
    AND a.candidate_policy_sha256 = p_policy_sha256
    AND p.proposal_status = 'approved';
  GET DIAGNOSTICS v_changed_count = ROW_COUNT;
  IF v_changed_count <> p_expected_proposal_count THEN
    RAISE EXCEPTION 'contextual proposal application count mismatch';
  END IF;

  RETURN jsonb_build_object(
    'schema_version', 'contextual-meal-slot-policy-application-v1',
    'policy_version', p_policy_version,
    'policy_sha256', p_policy_sha256,
    'proposal_count', p_expected_proposal_count,
    'evidence_link_count', p_expected_evidence_link_count,
    'manifest_candidate_row_count', p_expected_manifest_row_count,
    'applied_count', p_expected_proposal_count,
    'existing_applied_count', 0,
    'status', 'applied',
    'slot_set_counts', jsonb_build_object('breakfast,lunch', 2, 'lunch,dinner', 773),
    'publication_changed', false,
    'serving_changed', false
  );
END;
$$;

CREATE OR REPLACE FUNCTION ops.rollback_contextual_meal_slot_set_policy(
  p_workflow_run_id text,
  p_expected_application_count integer,
  p_policy_version text,
  p_policy_sha256 text,
  p_rollback_reference text,
  p_rolled_back_by text
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ops, public, re_engine, pg_catalog, pg_temp
AS $$
DECLARE
  v_changed_count integer;
  v_now timestamptz := clock_timestamp();
BEGIN
  IF p_workflow_run_id IS NULL OR p_workflow_run_id !~ '^[0-9]+$' THEN
    RAISE EXCEPTION 'workflow run id must be numeric';
  END IF;
  IF p_expected_application_count <> 775
     OR p_policy_version IS DISTINCT FROM 'contextual-import-course-slot-set-v1'
     OR p_policy_sha256 IS DISTINCT FROM
       '5afca8a6da05a6070abc6678d0a4f73924cafad62835e9152916efe6e7596154' THEN
    RAISE EXCEPTION 'rollback does not identify the exact contextual cohort';
  END IF;
  IF p_rollback_reference IS NULL
     OR p_rollback_reference !~ '^[A-Za-z0-9][A-Za-z0-9._:/#-]{7,199}$'
     OR p_rolled_back_by IS NULL
     OR p_rolled_back_by !~ '^[A-Za-z0-9][A-Za-z0-9._:@/-]{2,127}$' THEN
    RAISE EXCEPTION 'rollback reference and actor are required';
  END IF;

  PERFORM pg_advisory_xact_lock(hashtext('foofoo-contextual-meal-slot-policy-application-v1'));
  PERFORM 1
  FROM ops.dish_meal_slot_set_applications a
  JOIN ops.dish_meal_slot_set_proposals p ON p.id = a.proposal_id
  JOIN public.dishes d ON d.id = a.dish_id
  WHERE a.candidate_policy_version = p_policy_version
    AND a.candidate_policy_sha256 = p_policy_sha256
  ORDER BY a.id
  FOR UPDATE OF a, p, d;

  IF (SELECT count(*) FROM ops.dish_meal_slot_set_applications a
      WHERE a.candidate_policy_version = p_policy_version
        AND a.candidate_policy_sha256 = p_policy_sha256)
       <> p_expected_application_count
     OR EXISTS (
       SELECT 1
       FROM ops.dish_meal_slot_set_applications a
       JOIN ops.dish_meal_slot_set_proposals p ON p.id = a.proposal_id
       JOIN public.dishes d ON d.id = a.dish_id
       WHERE a.candidate_policy_version = p_policy_version
         AND a.candidate_policy_sha256 = p_policy_sha256
         AND (
           a.application_status <> 'applied'
           OR p.proposal_status <> 'applied'
           OR d.meal_occasion IS DISTINCT FROM a.applied_meal_occasion
         )
     ) THEN
    RAISE EXCEPTION 'contextual rollback refused because current state is partial or changed';
  END IF;

  UPDATE public.dishes d
  SET meal_occasion = a.previous_meal_occasion
  FROM ops.dish_meal_slot_set_applications a
  WHERE a.dish_id = d.id
    AND a.candidate_policy_version = p_policy_version
    AND a.candidate_policy_sha256 = p_policy_sha256
    AND a.application_status = 'applied'
    AND d.meal_occasion IS NOT DISTINCT FROM a.applied_meal_occasion;
  GET DIAGNOSTICS v_changed_count = ROW_COUNT;
  IF v_changed_count <> p_expected_application_count THEN
    RAISE EXCEPTION 'contextual rollback dish count mismatch';
  END IF;

  UPDATE ops.dish_meal_slot_set_proposals p
  SET proposal_status = 'rolled_back'
  FROM ops.dish_meal_slot_set_applications a
  WHERE a.proposal_id = p.id
    AND a.candidate_policy_version = p_policy_version
    AND a.candidate_policy_sha256 = p_policy_sha256
    AND p.proposal_status = 'applied';
  GET DIAGNOSTICS v_changed_count = ROW_COUNT;
  IF v_changed_count <> p_expected_application_count THEN
    RAISE EXCEPTION 'contextual rollback proposal count mismatch';
  END IF;

  UPDATE ops.dish_meal_slot_set_applications a
  SET application_status = 'rolled_back',
      rolled_back_by = p_rolled_back_by,
      rollback_reference = p_rollback_reference,
      rolled_back_by_workflow_run = p_workflow_run_id,
      rolled_back_at = v_now
  WHERE a.candidate_policy_version = p_policy_version
    AND a.candidate_policy_sha256 = p_policy_sha256
    AND a.application_status = 'applied';
  GET DIAGNOSTICS v_changed_count = ROW_COUNT;
  IF v_changed_count <> p_expected_application_count THEN
    RAISE EXCEPTION 'contextual rollback ledger count mismatch';
  END IF;

  RETURN jsonb_build_object(
    'schema_version', 'contextual-meal-slot-policy-rollback-v1',
    'policy_version', p_policy_version,
    'policy_sha256', p_policy_sha256,
    'rolled_back_count', p_expected_application_count,
    'status', 'rolled_back',
    'proposal_history_retained', true,
    'publication_changed', false,
    'serving_changed', false
  );
END;
$$;

REVOKE ALL ON FUNCTION ops.apply_contextual_meal_slot_set_policy(
  text, integer, integer, integer, text, text, text, text, text, text, text
) FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION ops.rollback_contextual_meal_slot_set_policy(
  text, integer, text, text, text, text
) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION ops.apply_contextual_meal_slot_set_policy(
  text, integer, integer, integer, text, text, text, text, text, text, text
) TO service_role;
GRANT EXECUTE ON FUNCTION ops.rollback_contextual_meal_slot_set_policy(
  text, integer, text, text, text, text
) TO service_role;

COMMENT ON TABLE ops.dish_meal_slot_set_applications IS
  'Private before/after ledger for an explicitly approved contextual slot-set cohort; installation alone changes no dish.';
COMMENT ON FUNCTION ops.apply_contextual_meal_slot_set_policy(
  text, integer, integer, integer, text, text, text, text, text, text, text
) IS
  'Applies exactly 775 row-verified contextual proposals only after durable Product approval; records reversible dish state and does not publish or route serving.';
COMMENT ON FUNCTION ops.rollback_contextual_meal_slot_set_policy(
  text, integer, text, text, text, text
) IS
  'Restores all 775 dishes only when every current slot array and proposal still matches the recorded application; retains audit history.';
