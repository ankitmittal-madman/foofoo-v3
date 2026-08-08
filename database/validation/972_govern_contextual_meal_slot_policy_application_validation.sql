DO $$
DECLARE
  v_status_constraint text;
BEGIN
  IF to_regclass('ops.dish_meal_slot_set_applications') IS NULL THEN
    RAISE EXCEPTION 'contextual meal-slot application ledger is missing';
  END IF;
  IF NOT EXISTS (
    SELECT 1
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'ops'
      AND c.relname = 'dish_meal_slot_set_applications'
      AND c.relrowsecurity
  ) THEN
    RAISE EXCEPTION 'contextual meal-slot application ledger must enforce RLS';
  END IF;
  IF has_table_privilege('anon', 'ops.dish_meal_slot_set_applications', 'SELECT')
     OR has_table_privilege('authenticated', 'ops.dish_meal_slot_set_applications', 'SELECT')
     OR has_table_privilege('service_role', 'ops.dish_meal_slot_set_applications', 'INSERT')
     OR has_table_privilege('service_role', 'ops.dish_meal_slot_set_applications', 'UPDATE')
     OR NOT has_table_privilege('service_role', 'ops.dish_meal_slot_set_applications', 'SELECT') THEN
    RAISE EXCEPTION 'contextual application ledger access is not service/function gated';
  END IF;
  IF to_regprocedure(
       'ops.apply_contextual_meal_slot_set_policy(text,integer,integer,integer,text,text,text,text,text,text,text)'
     ) IS NULL
     OR to_regprocedure(
       'ops.rollback_contextual_meal_slot_set_policy(text,integer,text,text,text,text)'
     ) IS NULL THEN
    RAISE EXCEPTION 'contextual application or rollback function is missing';
  END IF;
  IF has_function_privilege(
       'anon',
       'ops.apply_contextual_meal_slot_set_policy(text,integer,integer,integer,text,text,text,text,text,text,text)',
       'EXECUTE'
     ) OR has_function_privilege(
       'authenticated',
       'ops.apply_contextual_meal_slot_set_policy(text,integer,integer,integer,text,text,text,text,text,text,text)',
       'EXECUTE'
     ) OR has_function_privilege(
       'anon',
       'ops.rollback_contextual_meal_slot_set_policy(text,integer,text,text,text,text)',
       'EXECUTE'
     ) OR has_function_privilege(
       'authenticated',
       'ops.rollback_contextual_meal_slot_set_policy(text,integer,text,text,text,text)',
       'EXECUTE'
     ) THEN
    RAISE EXCEPTION 'contextual application functions must remain service-only';
  END IF;

  SELECT pg_get_constraintdef(c.oid) INTO v_status_constraint
  FROM pg_constraint c
  JOIN pg_class t ON t.oid = c.conrelid
  JOIN pg_namespace n ON n.oid = t.relnamespace
  WHERE n.nspname = 'ops'
    AND t.relname = 'dish_meal_slot_set_proposals'
    AND c.conname = 'dish_meal_slot_set_proposals_proposal_status_check';
  IF v_status_constraint IS NULL
     OR v_status_constraint NOT LIKE '%applied%'
     OR v_status_constraint NOT LIKE '%rolled_back%' THEN
    RAISE EXCEPTION 'contextual proposal lifecycle does not include applied and rolled_back';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM ops.dish_meal_slot_set_applications a
    JOIN ops.dish_meal_slot_set_proposals p ON p.id = a.proposal_id
    JOIN public.dishes d ON d.id = a.dish_id
    WHERE a.dish_id <> p.dish_id
      OR a.applied_meal_occasion IS DISTINCT FROM p.proposed_slots
      OR a.candidate_policy_version <> p.candidate_policy_version
      OR a.candidate_policy_sha256 <> p.candidate_policy_sha256
      OR (
        a.application_status = 'applied'
        AND (
          p.proposal_status <> 'applied'
          OR d.meal_occasion IS DISTINCT FROM a.applied_meal_occasion
        )
      )
      OR (
        a.application_status = 'rolled_back'
        AND (
          p.proposal_status <> 'rolled_back'
          OR d.meal_occasion IS DISTINCT FROM a.previous_meal_occasion
        )
      )
  ) THEN
    RAISE EXCEPTION 'contextual application ledger, proposal and dish state diverged';
  END IF;
  IF EXISTS (
    SELECT 1
    FROM ops.dish_meal_slot_set_proposals p
    WHERE p.proposal_status IN ('applied','rolled_back')
      AND NOT EXISTS (
        SELECT 1
        FROM ops.dish_meal_slot_set_applications a
        WHERE a.proposal_id = p.id
      )
  ) THEN
    RAISE EXCEPTION 'contextual applied lifecycle state is missing its ledger row';
  END IF;
END $$;
