DO $$
DECLARE
  v_case_count integer;
  v_evidence_count integer;
BEGIN
  IF to_regclass('ops.deferred_meal_slot_cases') IS NULL
     OR to_regclass('ops.deferred_meal_slot_case_evidence') IS NULL THEN
    RAISE EXCEPTION 'deferred meal-slot case tables are missing';
  END IF;
  IF to_regprocedure(
       'ops.generate_deferred_meal_slot_cases(text,text,text,text,text,integer,integer,integer)'
     ) IS NULL THEN
    RAISE EXCEPTION 'deferred meal-slot case generator is missing';
  END IF;
  IF NOT EXISTS (
       SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
       WHERE n.nspname = 'ops' AND c.relname = 'deferred_meal_slot_cases'
         AND c.relrowsecurity
     ) OR NOT EXISTS (
       SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
       WHERE n.nspname = 'ops' AND c.relname = 'deferred_meal_slot_case_evidence'
         AND c.relrowsecurity
     ) THEN
    RAISE EXCEPTION 'deferred meal-slot case RLS is not enabled';
  END IF;
  IF EXISTS (
       SELECT 1 FROM pg_policies
       WHERE schemaname = 'ops'
         AND tablename IN ('deferred_meal_slot_cases','deferred_meal_slot_case_evidence')
     ) THEN
    RAISE EXCEPTION 'deferred meal-slot case tables must have no client policies';
  END IF;
  IF has_table_privilege('anon', 'ops.deferred_meal_slot_cases', 'SELECT')
     OR has_table_privilege('authenticated', 'ops.deferred_meal_slot_cases', 'SELECT')
     OR has_table_privilege('anon', 'ops.deferred_meal_slot_case_evidence', 'SELECT')
     OR has_table_privilege('authenticated', 'ops.deferred_meal_slot_case_evidence', 'SELECT')
     OR NOT has_table_privilege('service_role', 'ops.deferred_meal_slot_cases', 'SELECT')
     OR NOT has_table_privilege(
       'service_role', 'ops.deferred_meal_slot_case_evidence', 'SELECT'
     ) THEN
    RAISE EXCEPTION 'deferred meal-slot case table privileges are invalid';
  END IF;
  IF has_function_privilege(
       'anon',
       'ops.generate_deferred_meal_slot_cases(text,text,text,text,text,integer,integer,integer)',
       'EXECUTE'
     ) OR has_function_privilege(
       'authenticated',
       'ops.generate_deferred_meal_slot_cases(text,text,text,text,text,integer,integer,integer)',
       'EXECUTE'
     ) OR NOT has_function_privilege(
       'service_role',
       'ops.generate_deferred_meal_slot_cases(text,text,text,text,text,integer,integer,integer)',
       'EXECUTE'
     ) THEN
    RAISE EXCEPTION 'deferred meal-slot case generator must remain service-only';
  END IF;
  IF NOT EXISTS (
       SELECT 1 FROM pg_trigger
       WHERE tgrelid = 'ops.deferred_meal_slot_cases'::regclass
         AND tgname = 'deferred_meal_slot_case_lifecycle_guard' AND NOT tgisinternal
     ) OR NOT EXISTS (
       SELECT 1 FROM pg_trigger
       WHERE tgrelid = 'ops.deferred_meal_slot_case_evidence'::regclass
         AND tgname = 'deferred_meal_slot_case_evidence_immutable' AND NOT tgisinternal
     ) THEN
    RAISE EXCEPTION 'deferred meal-slot case immutability guards are missing';
  END IF;

  SELECT count(*) INTO v_case_count
  FROM ops.deferred_meal_slot_cases
  WHERE case_policy_version = 'deferred-meal-slot-case-generation-v1';
  SELECT count(*) INTO v_evidence_count
  FROM ops.deferred_meal_slot_case_evidence e
  JOIN ops.deferred_meal_slot_cases c ON c.id = e.case_id
  WHERE c.case_policy_version = 'deferred-meal-slot-case-generation-v1';
  IF v_case_count NOT IN (0, 23)
     OR (v_case_count = 0 AND v_evidence_count <> 0)
     OR (v_case_count = 23 AND v_evidence_count < 90) THEN
    RAISE EXCEPTION 'deferred meal-slot stored cohort is partial';
  END IF;
  IF EXISTS (
       SELECT 1
       FROM ops.deferred_meal_slot_case_evidence e
       LEFT JOIN ops.deferred_meal_slot_cases c ON c.id = e.case_id
       WHERE c.id IS NULL
     ) THEN
    RAISE EXCEPTION 'deferred meal-slot case evidence is orphaned';
  END IF;
END $$;
