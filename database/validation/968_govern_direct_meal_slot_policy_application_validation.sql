DO $$
BEGIN
  IF to_regclass('ops.dish_meal_slot_applications') IS NULL THEN
    RAISE EXCEPTION 'direct meal-slot application ledger is missing';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'ops' AND c.relname = 'dish_meal_slot_applications'
      AND c.relrowsecurity
  ) THEN
    RAISE EXCEPTION 'direct meal-slot application ledger must enforce RLS';
  END IF;
  IF has_table_privilege('anon', 'ops.dish_meal_slot_applications', 'SELECT')
     OR has_table_privilege('authenticated', 'ops.dish_meal_slot_applications', 'SELECT')
     OR has_table_privilege('service_role', 'ops.dish_meal_slot_applications', 'INSERT')
     OR has_table_privilege('service_role', 'ops.dish_meal_slot_applications', 'UPDATE') THEN
    RAISE EXCEPTION 'direct meal-slot application ledger access is not function-gated';
  END IF;
  IF to_regprocedure(
       'ops.apply_direct_meal_slot_mapping_policy(text,integer,integer,integer,text,text,text,text,text,text,text)'
     ) IS NULL
     OR to_regprocedure(
       'ops.rollback_direct_meal_slot_mapping_policy(text,integer,text,text,text,text)'
     ) IS NULL THEN
    RAISE EXCEPTION 'direct meal-slot application or rollback function is missing';
  END IF;
  IF has_function_privilege(
       'anon',
       'ops.apply_direct_meal_slot_mapping_policy(text,integer,integer,integer,text,text,text,text,text,text,text)',
       'EXECUTE'
     ) OR has_function_privilege(
       'authenticated',
       'ops.apply_direct_meal_slot_mapping_policy(text,integer,integer,integer,text,text,text,text,text,text,text)',
       'EXECUTE'
     ) OR has_function_privilege(
       'anon',
       'ops.rollback_direct_meal_slot_mapping_policy(text,integer,text,text,text,text)',
       'EXECUTE'
     ) OR has_function_privilege(
       'authenticated',
       'ops.rollback_direct_meal_slot_mapping_policy(text,integer,text,text,text,text)',
       'EXECUTE'
     ) THEN
    RAISE EXCEPTION 'direct meal-slot application functions must remain service-only';
  END IF;
  IF EXISTS (
    SELECT 1
    FROM ops.dish_meal_slot_applications a
    JOIN ops.dish_meal_slot_proposals p ON p.id = a.proposal_id
    WHERE a.dish_id IS DISTINCT FROM p.dish_id
      OR a.applied_slot IS DISTINCT FROM p.proposed_slot
      OR a.mapping_policy_version <> 'direct-import-course-slot-v1'
      OR a.mapping_policy_sha256 <>
        '2dda4d35c8ab9314c89b6e56ab2d637eb9e7ba1fce9d3f113242813bdb01d3db'
  ) THEN
    RAISE EXCEPTION 'direct meal-slot application ledger diverges from its proposal or policy';
  END IF;
  IF EXISTS (
    SELECT 1
    FROM ops.dish_meal_slot_applications a
    JOIN public.dishes d ON d.id = a.dish_id
    WHERE a.application_status = 'applied'
      AND d.meal_occasion IS DISTINCT FROM a.applied_meal_occasion
  ) THEN
    RAISE EXCEPTION 'active direct meal-slot application no longer matches dish state';
  END IF;
END $$;
