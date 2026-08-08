DO $$
DECLARE
  v_report jsonb;
  v_slot_count bigint;
BEGIN
  IF to_regclass('food.dish_component_compatibility') IS NULL
     OR to_regclass('ops.dish_component_compatibility_proposals') IS NULL THEN
    RAISE EXCEPTION 'dish component compatibility tables are missing';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'food' AND c.relname = 'dish_component_compatibility'
      AND c.relrowsecurity
  ) OR NOT EXISTS (
    SELECT 1 FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'ops' AND c.relname = 'dish_component_compatibility_proposals'
      AND c.relrowsecurity
  ) THEN
    RAISE EXCEPTION 'dish component compatibility tables must enforce RLS';
  END IF;

  IF has_table_privilege('anon', 'food.dish_component_compatibility', 'SELECT')
     OR has_table_privilege('authenticated', 'food.dish_component_compatibility', 'SELECT')
     OR has_table_privilege('anon', 'ops.dish_component_compatibility_proposals', 'SELECT')
     OR has_table_privilege(
       'authenticated', 'ops.dish_component_compatibility_proposals', 'SELECT'
     ) THEN
    RAISE EXCEPTION 'dish component compatibility data must remain service-only';
  END IF;

  IF to_regprocedure('re_engine.canonical_meal_slot(text)') IS NULL
     OR to_regprocedure(
       're_engine.catalogue_serving_role_readiness_report()'
     ) IS NULL THEN
    RAISE EXCEPTION 'dish component compatibility functions are missing';
  END IF;

  IF re_engine.canonical_meal_slot('snack') <> 'snacks'
     OR re_engine.canonical_meal_slot(' snacks ') <> 'snacks'
     OR re_engine.canonical_meal_slot('lunch') <> 'lunch'
     OR re_engine.canonical_meal_slot('invalid') IS NOT NULL THEN
    RAISE EXCEPTION 'canonical meal slot normalization is invalid';
  END IF;

  IF has_function_privilege(
       'anon', 're_engine.catalogue_serving_role_readiness_report()', 'EXECUTE'
     ) OR has_function_privilege(
       'authenticated', 're_engine.catalogue_serving_role_readiness_report()', 'EXECUTE'
     ) THEN
    RAISE EXCEPTION 'catalogue serving-role readiness report must remain service-only';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM food.dish_component_compatibility c
    JOIN food.plate_grammars g ON g.id = c.grammar_id
    WHERE NOT c.meal_slot = ANY(g.meal_slots)
       OR NOT (g.required_roles ? c.grammar_role OR g.optional_roles ? c.grammar_role)
       OR c.reviewed_by IS NULL
       OR c.reviewed_at IS NULL
  ) THEN
    RAISE EXCEPTION 'accepted component compatibility violates grammar or review provenance';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM ops.dish_component_compatibility_proposals p
    WHERE (p.proposal_status IN ('approved','rejected','applied')
           AND (p.reviewed_by IS NULL OR p.reviewed_at IS NULL))
       OR (p.proposal_status = 'applied' AND p.applied_compatibility_id IS NULL)
  ) THEN
    RAISE EXCEPTION 'component proposal lifecycle provenance is invalid';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM ops.dish_component_compatibility_proposals p
    LEFT JOIN food.dish_component_compatibility c
      ON c.id = p.applied_compatibility_id
      AND c.dish_id = p.dish_id
      AND c.grammar_id = p.grammar_id
      AND c.meal_slot = p.meal_slot
      AND c.grammar_role = p.grammar_role
      AND c.component_role = p.component_role
      AND c.review_status = 'accepted'
    WHERE p.proposal_status = 'applied' AND c.id IS NULL
  ) THEN
    RAISE EXCEPTION 'applied component proposal does not match its accepted fact';
  END IF;

  SELECT re_engine.catalogue_serving_role_readiness_report() INTO v_report;
  v_slot_count := (v_report->>'active_dish_slots')::bigint;

  IF v_report->>'schema_version'
       <> 'recommendation-catalogue-serving-role-readiness-v1' THEN
    RAISE EXCEPTION 'catalogue serving-role readiness report schema is invalid';
  END IF;

  IF (v_report->'policy'->>'identity_exposed')::boolean
     OR (v_report->'policy'->>'automatic_proposal_acceptance_allowed')::boolean
     OR (v_report->'policy'->>'publication_gate_changed')::boolean THEN
    RAISE EXCEPTION 'catalogue serving-role readiness policy is unsafe';
  END IF;

  IF (
    SELECT coalesce(sum(value::bigint), 0)
    FROM jsonb_each_text(v_report->'serving_routes')
  ) <> v_slot_count THEN
    RAISE EXCEPTION 'catalogue serving routes do not reconcile';
  END IF;

  IF (
    SELECT coalesce(sum(value::bigint), 0)
    FROM jsonb_each_text(v_report->'hero_roles')
  ) <> v_slot_count THEN
    RAISE EXCEPTION 'catalogue serving hero roles do not reconcile';
  END IF;
END $$;
