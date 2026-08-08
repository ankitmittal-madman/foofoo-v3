-- Apply one explicitly approved direct-course mapping policy as a reversible, audited cohort.
--
-- Installation is additive and changes no dish. The application function requires the exact
-- checked-in policy hash, exact proposal/evidence/manifest counts, an ephemeral row manifest,
-- a human approval reference and actor provenance. Rollback restores a dish only when its current
-- slot array still equals the value written by this cohort; immutable source and proposal history
-- is retained.

CREATE TABLE ops.dish_meal_slot_applications (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  proposal_id uuid NOT NULL UNIQUE
    REFERENCES ops.dish_meal_slot_proposals(id) ON DELETE RESTRICT,
  dish_id uuid NOT NULL REFERENCES public.dishes(id) ON DELETE RESTRICT,
  applied_slot text NOT NULL CHECK (
    applied_slot IN ('breakfast','lunch','dinner','snacks')
  ),
  previous_meal_occasion text[] NOT NULL,
  applied_meal_occasion text[] NOT NULL,
  mapping_policy_version text NOT NULL,
  mapping_policy_sha256 text NOT NULL CHECK (
    mapping_policy_sha256 ~ '^[0-9a-f]{64}$'
  ),
  approval_reference text NOT NULL CHECK (
    approval_reference ~ '^[A-Za-z0-9][A-Za-z0-9._:/#-]{7,199}$'
  ),
  reviewed_by text NOT NULL CHECK (btrim(reviewed_by) <> ''),
  applied_by text NOT NULL CHECK (btrim(applied_by) <> ''),
  applied_by_workflow_run text NOT NULL CHECK (
    applied_by_workflow_run ~ '^[0-9]+$'
  ),
  application_status text NOT NULL DEFAULT 'applied' CHECK (
    application_status IN ('applied','rolled_back')
  ),
  applied_at timestamptz NOT NULL DEFAULT now(),
  rolled_back_by text,
  rollback_reference text,
  rolled_back_by_workflow_run text,
  rolled_back_at timestamptz,
  CHECK (dish_id IS NOT NULL),
  CHECK (NOT applied_slot = ANY (previous_meal_occasion)),
  CHECK (applied_slot = ANY (applied_meal_occasion)),
  CHECK (
    (application_status = 'applied'
      AND rolled_back_by IS NULL
      AND rollback_reference IS NULL
      AND rolled_back_by_workflow_run IS NULL
      AND rolled_back_at IS NULL)
    OR
    (application_status = 'rolled_back'
      AND rolled_back_by IS NOT NULL AND btrim(rolled_back_by) <> ''
      AND rollback_reference ~ '^[A-Za-z0-9][A-Za-z0-9._:/#-]{7,199}$'
      AND rolled_back_by_workflow_run ~ '^[0-9]+$'
      AND rolled_back_at IS NOT NULL)
  )
);

CREATE INDEX dish_meal_slot_applications_policy_status
  ON ops.dish_meal_slot_applications (
    mapping_policy_version, mapping_policy_sha256, application_status, dish_id
  );

ALTER TABLE ops.dish_meal_slot_applications ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON ops.dish_meal_slot_applications FROM PUBLIC, anon, authenticated;
REVOKE ALL ON ops.dish_meal_slot_applications FROM service_role;
GRANT SELECT ON ops.dish_meal_slot_applications TO service_role;

CREATE OR REPLACE FUNCTION ops.apply_direct_meal_slot_mapping_policy(
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
  v_integrity jsonb;
  v_proposal_count integer;
  v_evidence_count integer;
  v_existing_application_count integer;
  v_changed_count integer;
  v_now timestamptz := clock_timestamp();
BEGIN
  IF p_workflow_run_id IS NULL OR p_workflow_run_id !~ '^[0-9]+$' THEN
    RAISE EXCEPTION 'workflow run id must be numeric';
  END IF;
  IF p_expected_proposal_count <> 1802
     OR p_expected_evidence_link_count <> 7222
     OR p_expected_manifest_row_count <> 4806 THEN
    RAISE EXCEPTION 'approved direct-slot cohort counts are invalid';
  END IF;
  IF p_policy_version IS DISTINCT FROM 'direct-import-course-slot-v1'
     OR p_policy_sha256 IS DISTINCT FROM
       '2dda4d35c8ab9314c89b6e56ab2d637eb9e7ba1fce9d3f113242813bdb01d3db' THEN
    RAISE EXCEPTION 'direct-slot mapping policy identity is not approved by this boundary';
  END IF;
  IF p_approval_reference IS NULL
     OR p_approval_reference !~ '^[A-Za-z0-9][A-Za-z0-9._:/#-]{7,199}$' THEN
    RAISE EXCEPTION 'an explicit approval reference is required';
  END IF;
  IF p_reviewed_by IS NULL OR p_reviewed_by !~ '^[A-Za-z0-9][A-Za-z0-9._:@/-]{2,127}$'
     OR p_applied_by IS NULL OR p_applied_by !~ '^[A-Za-z0-9][A-Za-z0-9._:@/-]{2,127}$' THEN
    RAISE EXCEPTION 'review and application actors must be explicit safe identifiers';
  END IF;
  IF to_regclass('pg_temp.expected_dish_source_manifest') IS NULL THEN
    RAISE EXCEPTION 'expected direct source manifest is missing';
  END IF;

  PERFORM pg_advisory_xact_lock(hashtext('foofoo-direct-meal-slot-policy-application-v1'));

  SELECT count(*) INTO v_existing_application_count
  FROM ops.dish_meal_slot_applications a
  WHERE a.mapping_policy_version = p_policy_version
    AND a.mapping_policy_sha256 = p_policy_sha256;
  IF v_existing_application_count > 0 THEN
    IF v_existing_application_count = p_expected_proposal_count
       AND NOT EXISTS (
         SELECT 1
         FROM ops.dish_meal_slot_applications a
         JOIN public.dishes d ON d.id = a.dish_id
         JOIN ops.dish_meal_slot_proposals p ON p.id = a.proposal_id
         WHERE a.mapping_policy_version = p_policy_version
           AND a.mapping_policy_sha256 = p_policy_sha256
           AND (
             a.application_status <> 'applied'
             OR p.proposal_status <> 'applied'
             OR d.meal_occasion IS DISTINCT FROM a.applied_meal_occasion
           )
       ) THEN
      RETURN jsonb_build_object(
        'schema_version', 'direct-meal-slot-policy-application-v1',
        'policy_version', p_policy_version,
        'policy_sha256', p_policy_sha256,
        'proposal_count', p_expected_proposal_count,
        'evidence_link_count', p_expected_evidence_link_count,
        'manifest_direct_row_count', p_expected_manifest_row_count,
        'applied_count', 0,
        'existing_applied_count', v_existing_application_count,
        'status', 'already_applied',
        'publication_changed', false,
        'serving_changed', false
      );
    END IF;
    RAISE EXCEPTION 'existing direct-slot application state is partial or divergent';
  END IF;

  SELECT count(*) INTO v_proposal_count
  FROM ops.dish_meal_slot_proposals p
  WHERE p.proposal_method = 'exact_import_course_v1'
    AND p.proposal_version = 'meal-slot-proposal-v1';
  SELECT count(*) INTO v_evidence_count
  FROM ops.dish_meal_slot_proposal_evidence e
  JOIN ops.dish_meal_slot_proposals p ON p.id = e.proposal_id
  WHERE p.proposal_method = 'exact_import_course_v1'
    AND p.proposal_version = 'meal-slot-proposal-v1';
  IF v_proposal_count <> p_expected_proposal_count
     OR v_evidence_count <> p_expected_evidence_link_count
     OR (SELECT count(*) FROM pg_temp.expected_dish_source_manifest)
       <> p_expected_manifest_row_count THEN
    RAISE EXCEPTION 'direct-slot proposal, evidence or manifest cohort drifted';
  END IF;
  IF (SELECT count(*) FROM ops.dish_meal_slot_proposals p
      WHERE p.proposal_method = 'exact_import_course_v1'
        AND p.proposal_version = 'meal-slot-proposal-v1'
        AND p.proposed_slot = 'breakfast') <> 275
     OR (SELECT count(*) FROM ops.dish_meal_slot_proposals p
      WHERE p.proposal_method = 'exact_import_course_v1'
        AND p.proposal_version = 'meal-slot-proposal-v1'
        AND p.proposed_slot = 'lunch') <> 667
     OR (SELECT count(*) FROM ops.dish_meal_slot_proposals p
      WHERE p.proposal_method = 'exact_import_course_v1'
        AND p.proposal_version = 'meal-slot-proposal-v1'
        AND p.proposed_slot = 'dinner') <> 294
     OR (SELECT count(*) FROM ops.dish_meal_slot_proposals p
      WHERE p.proposal_method = 'exact_import_course_v1'
        AND p.proposal_version = 'meal-slot-proposal-v1'
        AND p.proposed_slot = 'snacks') <> 566 THEN
    RAISE EXCEPTION 'direct-slot proposal distribution drifted from approved scope';
  END IF;

  v_integrity := re_engine.direct_meal_slot_proposal_row_manifest_report(
    p_expected_source_name, p_expected_source_checksum
  );
  IF (v_integrity->>'proposal_count')::integer <> p_expected_proposal_count
     OR (v_integrity->>'evidence_link_count')::integer <> p_expected_evidence_link_count
     OR (v_integrity->>'manifest_direct_row_count')::integer
       <> p_expected_manifest_row_count
     OR (v_integrity->'proposal_gate_counts'->>'passes_row_manifest_integrity')::integer
       <> p_expected_proposal_count
     OR (v_integrity->'proposal_gate_counts'->>'requires_row_integrity_review')::integer <> 0
     OR (v_integrity->'row_integrity_link_counts'->>'exact_checked_in_row')::integer
       <> p_expected_evidence_link_count THEN
    RAISE EXCEPTION 'direct-slot row-manifest integrity gate did not pass exactly';
  END IF;

  PERFORM 1
  FROM ops.dish_meal_slot_proposals p
  JOIN public.dishes d ON d.id = p.dish_id
  WHERE p.proposal_method = 'exact_import_course_v1'
    AND p.proposal_version = 'meal-slot-proposal-v1'
  ORDER BY p.id
  FOR UPDATE OF p, d;

  IF EXISTS (
    SELECT 1
    FROM ops.dish_meal_slot_proposals p
    JOIN public.dishes d ON d.id = p.dish_id
    WHERE p.proposal_method = 'exact_import_course_v1'
      AND p.proposal_version = 'meal-slot-proposal-v1'
      AND (
        p.proposal_status NOT IN ('pending','in_review')
        OR NOT d.is_active
        OR EXISTS (
          SELECT 1 FROM unnest(d.meal_occasion) raw(raw_slot)
          WHERE re_engine.canonical_meal_slot(raw_slot) IS NOT NULL
        )
      )
  ) THEN
    RAISE EXCEPTION 'direct-slot cohort is no longer uniformly pending and slot-empty';
  END IF;

  INSERT INTO ops.dish_meal_slot_applications (
    proposal_id, dish_id, applied_slot, previous_meal_occasion, applied_meal_occasion,
    mapping_policy_version, mapping_policy_sha256, approval_reference,
    reviewed_by, applied_by, applied_by_workflow_run, applied_at
  )
  SELECT
    p.id,
    d.id,
    p.proposed_slot,
    d.meal_occasion,
    array_append(d.meal_occasion, p.proposed_slot),
    p_policy_version,
    p_policy_sha256,
    p_approval_reference,
    p_reviewed_by,
    p_applied_by,
    p_workflow_run_id,
    v_now
  FROM ops.dish_meal_slot_proposals p
  JOIN public.dishes d ON d.id = p.dish_id
  WHERE p.proposal_method = 'exact_import_course_v1'
    AND p.proposal_version = 'meal-slot-proposal-v1';
  GET DIAGNOSTICS v_changed_count = ROW_COUNT;
  IF v_changed_count <> p_expected_proposal_count THEN
    RAISE EXCEPTION 'direct-slot application ledger count mismatch';
  END IF;

  UPDATE ops.dish_meal_slot_proposals p
  SET proposal_status = 'approved',
      reviewed_by = p_reviewed_by,
      reviewed_at = v_now,
      review_notes = 'Approved under ' || p_policy_version || ' / ' || p_approval_reference
  WHERE p.proposal_method = 'exact_import_course_v1'
    AND p.proposal_version = 'meal-slot-proposal-v1'
    AND p.proposal_status IN ('pending','in_review');
  GET DIAGNOSTICS v_changed_count = ROW_COUNT;
  IF v_changed_count <> p_expected_proposal_count THEN
    RAISE EXCEPTION 'direct-slot proposal approval count mismatch';
  END IF;

  UPDATE public.dishes d
  SET meal_occasion = a.applied_meal_occasion
  FROM ops.dish_meal_slot_applications a
  WHERE a.dish_id = d.id
    AND a.mapping_policy_version = p_policy_version
    AND a.mapping_policy_sha256 = p_policy_sha256
    AND d.meal_occasion IS NOT DISTINCT FROM a.previous_meal_occasion;
  GET DIAGNOSTICS v_changed_count = ROW_COUNT;
  IF v_changed_count <> p_expected_proposal_count THEN
    RAISE EXCEPTION 'direct-slot dish update count mismatch';
  END IF;

  UPDATE ops.dish_meal_slot_proposals p
  SET proposal_status = 'applied',
      applied_by = p_applied_by,
      applied_at = v_now
  FROM ops.dish_meal_slot_applications a
  WHERE a.proposal_id = p.id
    AND a.mapping_policy_version = p_policy_version
    AND a.mapping_policy_sha256 = p_policy_sha256
    AND p.proposal_status = 'approved';
  GET DIAGNOSTICS v_changed_count = ROW_COUNT;
  IF v_changed_count <> p_expected_proposal_count THEN
    RAISE EXCEPTION 'direct-slot proposal application count mismatch';
  END IF;

  RETURN jsonb_build_object(
    'schema_version', 'direct-meal-slot-policy-application-v1',
    'policy_version', p_policy_version,
    'policy_sha256', p_policy_sha256,
    'proposal_count', p_expected_proposal_count,
    'evidence_link_count', p_expected_evidence_link_count,
    'manifest_direct_row_count', p_expected_manifest_row_count,
    'applied_count', p_expected_proposal_count,
    'existing_applied_count', 0,
    'status', 'applied',
    'slot_counts', (
      SELECT jsonb_object_agg(counts.applied_slot, counts.dish_count)
      FROM (
        SELECT a.applied_slot, count(*) AS dish_count
        FROM ops.dish_meal_slot_applications a
        WHERE a.mapping_policy_version = p_policy_version
          AND a.mapping_policy_sha256 = p_policy_sha256
        GROUP BY a.applied_slot ORDER BY a.applied_slot
      ) counts
    ),
    'publication_changed', false,
    'serving_changed', false
  );
END;
$$;

CREATE OR REPLACE FUNCTION ops.rollback_direct_meal_slot_mapping_policy(
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
  IF p_expected_application_count <> 1802
     OR p_policy_version IS DISTINCT FROM 'direct-import-course-slot-v1'
     OR p_policy_sha256 IS DISTINCT FROM
       '2dda4d35c8ab9314c89b6e56ab2d637eb9e7ba1fce9d3f113242813bdb01d3db' THEN
    RAISE EXCEPTION 'rollback does not identify the exact governed cohort';
  END IF;
  IF p_rollback_reference IS NULL
     OR p_rollback_reference !~ '^[A-Za-z0-9][A-Za-z0-9._:/#-]{7,199}$'
     OR p_rolled_back_by IS NULL
     OR p_rolled_back_by !~ '^[A-Za-z0-9][A-Za-z0-9._:@/-]{2,127}$' THEN
    RAISE EXCEPTION 'rollback reference and actor are required';
  END IF;

  PERFORM pg_advisory_xact_lock(hashtext('foofoo-direct-meal-slot-policy-application-v1'));
  PERFORM 1
  FROM ops.dish_meal_slot_applications a
  JOIN public.dishes d ON d.id = a.dish_id
  WHERE a.mapping_policy_version = p_policy_version
    AND a.mapping_policy_sha256 = p_policy_sha256
  ORDER BY a.id
  FOR UPDATE OF a, d;

  IF (SELECT count(*) FROM ops.dish_meal_slot_applications a
      WHERE a.mapping_policy_version = p_policy_version
        AND a.mapping_policy_sha256 = p_policy_sha256)
       <> p_expected_application_count
     OR EXISTS (
       SELECT 1
       FROM ops.dish_meal_slot_applications a
       JOIN public.dishes d ON d.id = a.dish_id
       WHERE a.mapping_policy_version = p_policy_version
         AND a.mapping_policy_sha256 = p_policy_sha256
         AND (
           a.application_status <> 'applied'
           OR d.meal_occasion IS DISTINCT FROM a.applied_meal_occasion
         )
     ) THEN
    RAISE EXCEPTION 'direct-slot rollback refused because current state is partial or changed';
  END IF;

  UPDATE public.dishes d
  SET meal_occasion = a.previous_meal_occasion
  FROM ops.dish_meal_slot_applications a
  WHERE a.dish_id = d.id
    AND a.mapping_policy_version = p_policy_version
    AND a.mapping_policy_sha256 = p_policy_sha256
    AND a.application_status = 'applied'
    AND d.meal_occasion IS NOT DISTINCT FROM a.applied_meal_occasion;
  GET DIAGNOSTICS v_changed_count = ROW_COUNT;
  IF v_changed_count <> p_expected_application_count THEN
    RAISE EXCEPTION 'direct-slot rollback dish count mismatch';
  END IF;

  UPDATE ops.dish_meal_slot_applications a
  SET application_status = 'rolled_back',
      rolled_back_by = p_rolled_back_by,
      rollback_reference = p_rollback_reference,
      rolled_back_by_workflow_run = p_workflow_run_id,
      rolled_back_at = v_now
  WHERE a.mapping_policy_version = p_policy_version
    AND a.mapping_policy_sha256 = p_policy_sha256
    AND a.application_status = 'applied';
  GET DIAGNOSTICS v_changed_count = ROW_COUNT;
  IF v_changed_count <> p_expected_application_count THEN
    RAISE EXCEPTION 'direct-slot rollback ledger count mismatch';
  END IF;

  RETURN jsonb_build_object(
    'schema_version', 'direct-meal-slot-policy-rollback-v1',
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

REVOKE ALL ON FUNCTION ops.apply_direct_meal_slot_mapping_policy(
  text, integer, integer, integer, text, text, text, text, text, text, text
) FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION ops.rollback_direct_meal_slot_mapping_policy(
  text, integer, text, text, text, text
) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION ops.apply_direct_meal_slot_mapping_policy(
  text, integer, integer, integer, text, text, text, text, text, text, text
) TO service_role;
GRANT EXECUTE ON FUNCTION ops.rollback_direct_meal_slot_mapping_policy(
  text, integer, text, text, text, text
) TO service_role;

COMMENT ON TABLE ops.dish_meal_slot_applications IS
  'Immutable before/after ledger for one explicitly approved direct-slot cohort; rollback restores only unchanged applied arrays.';
COMMENT ON FUNCTION ops.apply_direct_meal_slot_mapping_policy(
  text, integer, integer, integer, text, text, text, text, text, text, text
) IS
  'Applies exactly 1,802 row-verified direct-slot proposals under one hash-pinned approval and records reversible before/after state; does not publish or route serving.';
COMMENT ON FUNCTION ops.rollback_direct_meal_slot_mapping_policy(
  text, integer, text, text, text, text
) IS
  'Restores the approved cohort only when every current slot array still equals its recorded applied value; retains proposal and application history.';
