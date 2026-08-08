DO $$
BEGIN
  IF to_regclass('ops.dish_meal_slot_proposals') IS NULL
     OR to_regclass('ops.dish_meal_slot_proposal_evidence') IS NULL THEN
    RAISE EXCEPTION 'governed meal-slot proposal tables are missing';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'ops' AND c.relname = 'dish_meal_slot_proposals'
      AND c.relrowsecurity
  ) OR NOT EXISTS (
    SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'ops' AND c.relname = 'dish_meal_slot_proposal_evidence'
      AND c.relrowsecurity
  ) THEN
    RAISE EXCEPTION 'governed meal-slot proposal tables must enforce RLS';
  END IF;

  IF has_table_privilege('anon', 'ops.dish_meal_slot_proposals', 'SELECT')
     OR has_table_privilege('authenticated', 'ops.dish_meal_slot_proposals', 'SELECT')
     OR has_table_privilege('anon', 'ops.dish_meal_slot_proposal_evidence', 'SELECT')
     OR has_table_privilege(
       'authenticated', 'ops.dish_meal_slot_proposal_evidence', 'SELECT'
     ) THEN
    RAISE EXCEPTION 'governed meal-slot proposals must remain service-only';
  END IF;

  IF has_table_privilege(
       'service_role', 'ops.dish_meal_slot_proposals', 'INSERT'
     ) OR has_table_privilege(
       'service_role', 'ops.dish_meal_slot_proposals', 'UPDATE'
     ) OR has_table_privilege(
       'service_role', 'ops.dish_meal_slot_proposal_evidence', 'INSERT'
     ) THEN
    RAISE EXCEPTION 'direct proposal table writes must remain function-gated';
  END IF;

  IF to_regprocedure('re_engine.direct_meal_slot_proposal_candidates()') IS NULL
     OR to_regprocedure(
       'ops.generate_direct_meal_slot_proposals(text,integer)'
     ) IS NULL THEN
    RAISE EXCEPTION 'governed meal-slot proposal functions are missing';
  END IF;

  IF has_function_privilege(
       'anon', 'ops.generate_direct_meal_slot_proposals(text,integer)', 'EXECUTE'
     ) OR has_function_privilege(
       'authenticated',
       'ops.generate_direct_meal_slot_proposals(text,integer)', 'EXECUTE'
     ) THEN
    RAISE EXCEPTION 'meal-slot proposal generator must remain service-only';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM ops.dish_meal_slot_proposals p
    WHERE NOT EXISTS (
      SELECT 1 FROM ops.dish_meal_slot_proposal_evidence e
      WHERE e.proposal_id = p.id
    )
  ) THEN
    RAISE EXCEPTION 'governed meal-slot proposal is missing evidence';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM ops.dish_meal_slot_proposal_evidence e
    JOIN ops.dish_meal_slot_proposals p ON p.id = e.proposal_id
    LEFT JOIN public.import_row_results r ON r.source_row_id = e.source_row_id
      AND r.dish_id = p.dish_id
      AND r.status IN ('matched_existing','created_new','merged_duplicate','routed_review')
    LEFT JOIN public.dish_source_rows s ON s.id = e.source_row_id
    WHERE r.id IS NULL OR re_engine.direct_slot_from_import_course(
      s.normalized_payload->>'course_raw'
    ) IS DISTINCT FROM p.proposed_slot
  ) THEN
    RAISE EXCEPTION 'governed meal-slot proposal evidence does not match dish and slot';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM ops.dish_meal_slot_proposals p
    WHERE p.proposal_status IN ('approved','rejected','applied')
      AND (p.reviewed_by IS NULL OR p.reviewed_at IS NULL)
  ) THEN
    RAISE EXCEPTION 'governed meal-slot proposal review provenance is incomplete';
  END IF;
END $$;
