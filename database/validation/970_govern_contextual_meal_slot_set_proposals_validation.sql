DO $$
BEGIN
  IF to_regclass('ops.dish_meal_slot_set_proposals') IS NULL
     OR to_regclass('ops.dish_meal_slot_set_proposal_evidence') IS NULL THEN
    RAISE EXCEPTION 'contextual meal-slot proposal tables are missing';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'ops' AND c.relname = 'dish_meal_slot_set_proposals'
      AND c.relrowsecurity
  ) OR NOT EXISTS (
    SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'ops' AND c.relname = 'dish_meal_slot_set_proposal_evidence'
      AND c.relrowsecurity
  ) THEN
    RAISE EXCEPTION 'contextual meal-slot proposal tables must enforce RLS';
  END IF;
  IF has_table_privilege('anon', 'ops.dish_meal_slot_set_proposals', 'SELECT')
     OR has_table_privilege('authenticated', 'ops.dish_meal_slot_set_proposals', 'SELECT')
     OR has_table_privilege('anon', 'ops.dish_meal_slot_set_proposal_evidence', 'SELECT')
     OR has_table_privilege('authenticated', 'ops.dish_meal_slot_set_proposal_evidence', 'SELECT')
     OR has_table_privilege('service_role', 'ops.dish_meal_slot_set_proposals', 'INSERT')
     OR has_table_privilege('service_role', 'ops.dish_meal_slot_set_proposals', 'UPDATE')
     OR has_table_privilege('service_role', 'ops.dish_meal_slot_set_proposal_evidence', 'INSERT')
     OR has_table_privilege('service_role', 'ops.dish_meal_slot_set_proposal_evidence', 'UPDATE') THEN
    RAISE EXCEPTION 'contextual proposal reads and writes are not service/function gated';
  END IF;
  IF to_regprocedure(
       'ops.generate_contextual_meal_slot_set_proposals(text,integer,integer,text,text,text,text)'
     ) IS NULL
     OR to_regprocedure(
       're_engine.contextual_meal_slot_set_candidate_evidence()'
     ) IS NULL THEN
    RAISE EXCEPTION 'contextual proposal candidate or generator function is missing';
  END IF;
  IF has_function_privilege(
       'anon',
       'ops.generate_contextual_meal_slot_set_proposals(text,integer,integer,text,text,text,text)',
       'EXECUTE'
     ) OR has_function_privilege(
       'authenticated',
       'ops.generate_contextual_meal_slot_set_proposals(text,integer,integer,text,text,text,text)',
       'EXECUTE'
     ) THEN
    RAISE EXCEPTION 'contextual proposal generator must remain service-only';
  END IF;
  IF EXISTS (
    SELECT 1 FROM ops.dish_meal_slot_set_proposals p
    WHERE p.proposal_method <> 'contextual_import_course_v1'
      OR p.proposal_version <> 'meal-slot-set-proposal-v1'
      OR p.candidate_policy_version <> 'contextual-import-course-slot-set-v1'
      OR p.candidate_policy_sha256 <>
        '5afca8a6da05a6070abc6678d0a4f73924cafad62835e9152916efe6e7596154'
      OR NOT EXISTS (
        SELECT 1 FROM ops.dish_meal_slot_set_proposal_evidence e
        WHERE e.proposal_id = p.id
      )
  ) THEN
    RAISE EXCEPTION 'contextual proposal identity, policy or evidence is incomplete';
  END IF;
  IF EXISTS (
    SELECT 1
    FROM ops.dish_meal_slot_set_proposal_evidence e
    JOIN ops.dish_meal_slot_set_proposals p ON p.id = e.proposal_id
    JOIN public.dish_source_rows s ON s.id = e.source_row_id
    WHERE re_engine.contextual_slot_set_from_import_course(
            s.normalized_payload->>'course_raw'
          ) IS DISTINCT FROM p.proposed_slots
      OR re_engine.contextual_course_evidence_category(
            s.normalized_payload->>'course_raw'
          ) IS DISTINCT FROM e.evidence_category
  ) THEN
    RAISE EXCEPTION 'contextual proposal evidence diverges from its source course and slot set';
  END IF;
  IF EXISTS (
    SELECT 1 FROM ops.dish_meal_slot_set_proposals p
    WHERE (p.proposal_status IN ('pending','in_review')
        AND (p.reviewed_by IS NOT NULL OR p.reviewed_at IS NOT NULL))
       OR (p.proposal_status IN ('approved','rejected')
        AND (p.reviewed_by IS NULL OR p.reviewed_at IS NULL))
  ) THEN
    RAISE EXCEPTION 'contextual proposal review provenance is incomplete';
  END IF;
END $$;
