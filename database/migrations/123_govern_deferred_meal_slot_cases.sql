-- Migration 123: materialize the final deferred meal-slot denominator as private pending-review cases.
--
-- The source audit proved 23 active dishes remain outside the direct/contextual proposal cohorts:
-- five have exact shifted-field candidates, 17 need food-role review and one has conflicting direct
-- slots. This migration preserves those cases and their exact source-row evidence without changing
-- dishes, proposals, catalogue publication, recommendation serving or Aux routing.

CREATE TABLE ops.deferred_meal_slot_cases (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  dish_id uuid NOT NULL REFERENCES public.dishes(id) ON DELETE RESTRICT,
  recovery_route text NOT NULL CHECK (recovery_route IN (
    'shifted_direct_slot_candidate',
    'shifted_contextual_slot_candidate',
    'requires_food_role_review',
    'conflicting_direct_slots'
  )),
  proposed_slots text[],
  case_status text NOT NULL DEFAULT 'pending_review' CHECK (case_status IN (
    'pending_review','candidate_approved','candidate_rejected','resolved_no_mapping'
  )),
  source_name text NOT NULL,
  source_checksum text NOT NULL CHECK (source_checksum ~ '^[0-9a-f]{64}$'),
  source_audit_policy_version text NOT NULL CHECK (
    source_audit_policy_version = 'deferred-course-shifted-field-audit-v1'
  ),
  source_audit_policy_sha256 text NOT NULL CHECK (
    source_audit_policy_sha256 =
      '94d5f198bbb1244d631a23c5dc95200a6be860d6609dfc6a6bb0c1a7cb5717ac'
  ),
  case_policy_version text NOT NULL CHECK (
    case_policy_version = 'deferred-meal-slot-case-generation-v1'
  ),
  case_policy_sha256 text NOT NULL CHECK (
    case_policy_sha256 =
      '339916734763f073080cec4079f51401955da7af5df996076c1cc851b92b68da'
  ),
  created_by_workflow_run text NOT NULL CHECK (created_by_workflow_run ~ '^[0-9]+$'),
  reviewed_by text,
  reviewed_at timestamptz,
  review_reference text,
  review_notes text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CHECK (
    (recovery_route = 'shifted_direct_slot_candidate'
      AND cardinality(proposed_slots) = 1
      AND proposed_slots[1] IN ('breakfast','lunch','dinner','snacks'))
    OR (recovery_route = 'shifted_contextual_slot_candidate'
      AND proposed_slots = ARRAY['lunch','dinner']::text[])
    OR (recovery_route IN ('requires_food_role_review','conflicting_direct_slots')
      AND proposed_slots IS NULL)
  ),
  CHECK (
    (case_status = 'pending_review'
      AND reviewed_by IS NULL AND reviewed_at IS NULL
      AND review_reference IS NULL AND review_notes IS NULL)
    OR (case_status IN ('candidate_approved','candidate_rejected','resolved_no_mapping')
      AND reviewed_by IS NOT NULL AND btrim(reviewed_by) <> ''
      AND reviewed_at IS NOT NULL
      AND review_reference IS NOT NULL AND btrim(review_reference) <> ''
      AND review_notes IS NOT NULL AND btrim(review_notes) <> '')
  ),
  CHECK (
    case_status = 'pending_review'
    OR (recovery_route LIKE 'shifted_%'
      AND case_status IN ('candidate_approved','candidate_rejected'))
    OR (recovery_route IN ('requires_food_role_review','conflicting_direct_slots')
      AND case_status = 'resolved_no_mapping')
  ),
  UNIQUE (dish_id, case_policy_version)
);

CREATE TABLE ops.deferred_meal_slot_case_evidence (
  case_id uuid NOT NULL REFERENCES ops.deferred_meal_slot_cases(id) ON DELETE RESTRICT,
  source_row_id uuid NOT NULL REFERENCES public.dish_source_rows(id) ON DELETE RESTRICT,
  evidence_role text NOT NULL CHECK (evidence_role IN (
    'shifted_manifest','direct_conflict'
  )),
  row_fingerprint text NOT NULL CHECK (row_fingerprint ~ '^[0-9a-f]{64}$'),
  canonical_slot_key text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (case_id, source_row_id)
);

CREATE INDEX deferred_meal_slot_cases_review_queue
  ON ops.deferred_meal_slot_cases (case_status, recovery_route, created_at, id);
CREATE INDEX deferred_meal_slot_case_evidence_source
  ON ops.deferred_meal_slot_case_evidence (source_row_id, case_id);

CREATE OR REPLACE FUNCTION ops.protect_deferred_meal_slot_case_lifecycle()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ops, pg_catalog, pg_temp
AS $$
BEGIN
  IF ROW(
       NEW.dish_id, NEW.recovery_route, NEW.proposed_slots,
       NEW.source_name, NEW.source_checksum,
       NEW.source_audit_policy_version, NEW.source_audit_policy_sha256,
       NEW.case_policy_version, NEW.case_policy_sha256,
       NEW.created_by_workflow_run, NEW.created_at
     ) IS DISTINCT FROM ROW(
       OLD.dish_id, OLD.recovery_route, OLD.proposed_slots,
       OLD.source_name, OLD.source_checksum,
       OLD.source_audit_policy_version, OLD.source_audit_policy_sha256,
       OLD.case_policy_version, OLD.case_policy_sha256,
       OLD.created_by_workflow_run, OLD.created_at
     ) THEN
    RAISE EXCEPTION 'deferred meal-slot case identity and evidence are immutable';
  END IF;
  IF OLD.case_status <> 'pending_review'
     OR NEW.case_status = 'pending_review' THEN
    RAISE EXCEPTION 'deferred meal-slot case decisions are forward-only';
  END IF;
  NEW.updated_at := now();
  RETURN NEW;
END;
$$;

CREATE TRIGGER deferred_meal_slot_case_lifecycle_guard
BEFORE UPDATE ON ops.deferred_meal_slot_cases
FOR EACH ROW EXECUTE FUNCTION ops.protect_deferred_meal_slot_case_lifecycle();

CREATE OR REPLACE FUNCTION ops.protect_deferred_meal_slot_case_evidence()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
BEGIN
  RAISE EXCEPTION 'deferred meal-slot case evidence is immutable';
END;
$$;

CREATE TRIGGER deferred_meal_slot_case_evidence_immutable
BEFORE UPDATE OR DELETE ON ops.deferred_meal_slot_case_evidence
FOR EACH ROW EXECUTE FUNCTION ops.protect_deferred_meal_slot_case_evidence();

ALTER TABLE ops.deferred_meal_slot_cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE ops.deferred_meal_slot_case_evidence ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON ops.deferred_meal_slot_cases FROM PUBLIC, anon, authenticated;
REVOKE ALL ON ops.deferred_meal_slot_case_evidence FROM PUBLIC, anon, authenticated;
GRANT SELECT ON ops.deferred_meal_slot_cases TO service_role;
GRANT SELECT ON ops.deferred_meal_slot_case_evidence TO service_role;

CREATE OR REPLACE FUNCTION ops.generate_deferred_meal_slot_cases(
  p_workflow_run_id text,
  p_expected_source_name text,
  p_expected_source_checksum text,
  p_source_audit_policy_sha256 text,
  p_case_policy_sha256 text,
  p_expected_manifest_row_count integer,
  p_expected_case_count integer,
  p_expected_diet_evidence_link_count integer
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ops, public, re_engine, pg_catalog, pg_temp
AS $$
DECLARE
  v_cases_created integer;
  v_evidence_created integer;
  v_conflict_evidence_count integer;
  v_total_evidence_count integer;
BEGIN
  IF p_workflow_run_id !~ '^[0-9]+$'
     OR p_expected_source_name IS NULL
     OR p_expected_source_name <> btrim(p_expected_source_name)
     OR p_expected_source_name !~ '^[A-Za-z0-9._-]+$'
     OR p_expected_source_checksum !~ '^[0-9a-f]{64}$' THEN
    RAISE EXCEPTION 'deferred case workflow or source identity is invalid';
  END IF;
  IF p_source_audit_policy_sha256 IS DISTINCT FROM
       '94d5f198bbb1244d631a23c5dc95200a6be860d6609dfc6a6bb0c1a7cb5717ac'
     OR p_case_policy_sha256 IS DISTINCT FROM
       '339916734763f073080cec4079f51401955da7af5df996076c1cc851b92b68da' THEN
    RAISE EXCEPTION 'deferred case policy identity is invalid';
  END IF;
  IF p_expected_manifest_row_count <> 62
     OR p_expected_case_count <> 23
     OR p_expected_diet_evidence_link_count <> 88 THEN
    RAISE EXCEPTION 'deferred case generation scope is invalid';
  END IF;
  IF to_regclass('pg_temp.expected_deferred_course_manifest') IS NULL
     OR (SELECT count(*) FROM pg_temp.expected_deferred_course_manifest) <> 62 THEN
    RAISE EXCEPTION 'deferred case manifest is missing or drifted';
  END IF;
  IF to_regclass('pg_temp.generated_deferred_case_evidence') IS NOT NULL THEN
    RAISE EXCEPTION 'deferred case generation temporary state already exists';
  END IF;

  CREATE TEMP TABLE generated_deferred_case_evidence ON COMMIT DROP AS
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
      e.row_fingerprint,
      e.source_name,
      e.source_checksum,
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
      count(*) FILTER (WHERE l.repair_route = 'unresolved_food_role')
        AS unresolved_link_count,
      count(DISTINCT l.proposed_slots_key) FILTER (WHERE l.proposed_slots_key <> '')
        AS proposed_slot_set_count,
      min(l.proposed_slots_key) FILTER (WHERE l.proposed_slots_key <> '')
        AS proposed_slots_key,
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
  ),
  diet_case_evidence AS (
    SELECT
      l.dish_id,
      l.source_row_id,
      r.recovery_route,
      CASE WHEN r.proposed_slot_set_count = 1
        THEN string_to_array(r.proposed_slots_key, ',') ELSE NULL END AS proposed_slots,
      'shifted_manifest'::text AS evidence_role,
      l.row_fingerprint,
      coalesce(l.proposed_slots_key, '') AS canonical_slot_key,
      l.source_name,
      l.source_checksum,
      l.exact_manifest_link
    FROM routed_diet r
    JOIN diet_links l ON l.dish_id = r.dish_id
  ),
  conflict_case_evidence AS (
    SELECT
      c.dish_id,
      e.source_row_id,
      'conflicting_direct_slots'::text AS recovery_route,
      NULL::text[] AS proposed_slots,
      'direct_conflict'::text AS evidence_role,
      e.row_fingerprint,
      e.direct_slot AS canonical_slot_key,
      e.source_name,
      e.source_checksum,
      true AS exact_manifest_link
    FROM direct_conflicts c
    JOIN evidence e ON e.dish_id = c.dish_id AND e.direct_slot IS NOT NULL
  )
  SELECT * FROM diet_case_evidence
  UNION ALL
  SELECT * FROM conflict_case_evidence;

  IF (SELECT count(DISTINCT dish_id) FROM generated_deferred_case_evidence) <> 23
     OR (SELECT count(DISTINCT dish_id) FROM generated_deferred_case_evidence
         WHERE recovery_route = 'shifted_direct_slot_candidate') <> 3
     OR (SELECT count(DISTINCT dish_id) FROM generated_deferred_case_evidence
         WHERE recovery_route = 'shifted_contextual_slot_candidate') <> 2
     OR (SELECT count(DISTINCT dish_id) FROM generated_deferred_case_evidence
         WHERE recovery_route = 'requires_food_role_review') <> 17
     OR (SELECT count(DISTINCT dish_id) FROM generated_deferred_case_evidence
         WHERE recovery_route = 'conflicting_direct_slots') <> 1 THEN
    RAISE EXCEPTION 'deferred case recovery-route scope drifted';
  END IF;
  IF (SELECT count(DISTINCT dish_id) FROM generated_deferred_case_evidence
      WHERE array_to_string(proposed_slots, ',') = 'breakfast') <> 2
     OR (SELECT count(DISTINCT dish_id) FROM generated_deferred_case_evidence
         WHERE array_to_string(proposed_slots, ',') = 'dinner') <> 1
     OR (SELECT count(DISTINCT dish_id) FROM generated_deferred_case_evidence
         WHERE array_to_string(proposed_slots, ',') = 'lunch,dinner') <> 2 THEN
    RAISE EXCEPTION 'deferred case candidate slot distribution drifted';
  END IF;
  IF (SELECT count(*) FROM generated_deferred_case_evidence
      WHERE evidence_role = 'shifted_manifest') <> 88
     OR EXISTS (
       SELECT 1 FROM generated_deferred_case_evidence WHERE NOT exact_manifest_link
     )
     OR EXISTS (
       SELECT 1 FROM generated_deferred_case_evidence
       WHERE source_name <> p_expected_source_name
          OR source_checksum <> p_expected_source_checksum
     ) THEN
    RAISE EXCEPTION 'deferred case source evidence integrity failed';
  END IF;
  SELECT count(*) INTO v_conflict_evidence_count
  FROM generated_deferred_case_evidence WHERE evidence_role = 'direct_conflict';
  IF v_conflict_evidence_count < 2
     OR (SELECT string_agg(DISTINCT canonical_slot_key, ',' ORDER BY canonical_slot_key)
         FROM generated_deferred_case_evidence
         WHERE evidence_role = 'direct_conflict') <> 'dinner,snacks' THEN
    RAISE EXCEPTION 'deferred direct-conflict evidence drifted';
  END IF;

  INSERT INTO ops.deferred_meal_slot_cases (
    dish_id, recovery_route, proposed_slots,
    source_name, source_checksum,
    source_audit_policy_version, source_audit_policy_sha256,
    case_policy_version, case_policy_sha256, created_by_workflow_run
  )
  SELECT DISTINCT
    dish_id, recovery_route, proposed_slots,
    p_expected_source_name, p_expected_source_checksum,
    'deferred-course-shifted-field-audit-v1', p_source_audit_policy_sha256,
    'deferred-meal-slot-case-generation-v1', p_case_policy_sha256,
    p_workflow_run_id
  FROM generated_deferred_case_evidence
  ON CONFLICT (dish_id, case_policy_version) DO NOTHING;
  GET DIAGNOSTICS v_cases_created = ROW_COUNT;

  INSERT INTO ops.deferred_meal_slot_case_evidence (
    case_id, source_row_id, evidence_role, row_fingerprint, canonical_slot_key
  )
  SELECT
    c.id, e.source_row_id, e.evidence_role, e.row_fingerprint, e.canonical_slot_key
  FROM generated_deferred_case_evidence e
  JOIN ops.deferred_meal_slot_cases c ON c.dish_id = e.dish_id
    AND c.case_policy_version = 'deferred-meal-slot-case-generation-v1'
  ON CONFLICT (case_id, source_row_id) DO NOTHING;
  GET DIAGNOSTICS v_evidence_created = ROW_COUNT;

  IF (SELECT count(*) FROM ops.deferred_meal_slot_cases
      WHERE case_policy_version = 'deferred-meal-slot-case-generation-v1') <> 23
     OR (SELECT count(*) FROM ops.deferred_meal_slot_cases
         WHERE case_policy_version = 'deferred-meal-slot-case-generation-v1'
           AND case_status = 'pending_review') <> 23
     OR EXISTS (
       SELECT 1
       FROM generated_deferred_case_evidence e
       FULL JOIN ops.deferred_meal_slot_cases c ON c.dish_id = e.dish_id
         AND c.case_policy_version = 'deferred-meal-slot-case-generation-v1'
       WHERE e.dish_id IS NULL OR c.dish_id IS NULL
          OR c.recovery_route <> e.recovery_route
          OR c.proposed_slots IS DISTINCT FROM e.proposed_slots
     ) THEN
    RAISE EXCEPTION 'stored deferred cases do not exactly match generated evidence';
  END IF;
  SELECT count(*) INTO v_total_evidence_count
  FROM ops.deferred_meal_slot_case_evidence e
  JOIN ops.deferred_meal_slot_cases c ON c.id = e.case_id
  WHERE c.case_policy_version = 'deferred-meal-slot-case-generation-v1';
  IF v_total_evidence_count <> 88 + v_conflict_evidence_count
     OR EXISTS (
       SELECT 1
       FROM generated_deferred_case_evidence g
       JOIN ops.deferred_meal_slot_cases c ON c.dish_id = g.dish_id
         AND c.case_policy_version = 'deferred-meal-slot-case-generation-v1'
       FULL JOIN ops.deferred_meal_slot_case_evidence e
         ON e.case_id = c.id AND e.source_row_id = g.source_row_id
       WHERE g.source_row_id IS NULL OR e.source_row_id IS NULL
          OR e.evidence_role <> g.evidence_role
          OR e.row_fingerprint <> g.row_fingerprint
          OR e.canonical_slot_key <> g.canonical_slot_key
     ) THEN
    RAISE EXCEPTION 'stored deferred case evidence does not exactly match generated evidence';
  END IF;

  RETURN jsonb_build_object(
    'schema_version', 'deferred-meal-slot-case-generation-result-v1',
    'policy_version', 'deferred-meal-slot-case-generation-v1',
    'policy_sha256', p_case_policy_sha256,
    'outcome', CASE WHEN v_cases_created = 0 AND v_evidence_created = 0
      THEN 'already_generated' ELSE 'generated' END,
    'cases_created', v_cases_created,
    'evidence_links_created', v_evidence_created,
    'total_cases', 23,
    'total_evidence_links', v_total_evidence_count,
    'diet_evidence_links', 88,
    'conflict_evidence_links', v_conflict_evidence_count,
    'route_counts', jsonb_build_object(
      'shifted_direct_slot_candidate', 3,
      'shifted_contextual_slot_candidate', 2,
      'requires_food_role_review', 17,
      'conflicting_direct_slots', 1
    ),
    'candidate_slot_set_counts', jsonb_build_object(
      'breakfast', 2, 'dinner', 1, 'lunch,dinner', 2
    ),
    'case_status', 'pending_review',
    'automatic_acceptance_allowed', false,
    'dish_changed', false,
    'proposal_changed', false,
    'publication_changed', false,
    'serving_changed', false
  );
END;
$$;

REVOKE ALL ON FUNCTION ops.generate_deferred_meal_slot_cases(
  text,text,text,text,text,integer,integer,integer
) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION ops.generate_deferred_meal_slot_cases(
  text,text,text,text,text,integer,integer,integer
) TO service_role;

COMMENT ON TABLE ops.deferred_meal_slot_cases IS
  'Private pending-review ledger for the exact final 23 meal-slot cases; never a serving fact.';
COMMENT ON TABLE ops.deferred_meal_slot_case_evidence IS
  'Immutable source-row evidence for deferred meal-slot cases; service-role only.';
COMMENT ON FUNCTION ops.generate_deferred_meal_slot_cases(
  text,text,text,text,text,integer,integer,integer
) IS
  'Generates the exact 23-case private review cohort from checked-in evidence without changing dishes, publication or serving.';
