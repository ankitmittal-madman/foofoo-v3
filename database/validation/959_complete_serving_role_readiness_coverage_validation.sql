DO $$
DECLARE
  v_report jsonb;
  v_active_dishes bigint;
  v_active_dish_slots bigint;
BEGIN
  IF to_regprocedure(
       're_engine.catalogue_serving_role_readiness_report_v2()'
     ) IS NULL THEN
    RAISE EXCEPTION 'complete catalogue serving-role readiness report is missing';
  END IF;

  IF has_function_privilege(
       'anon', 're_engine.catalogue_serving_role_readiness_report_v2()', 'EXECUTE'
     ) OR has_function_privilege(
       'authenticated',
       're_engine.catalogue_serving_role_readiness_report_v2()', 'EXECUTE'
     ) THEN
    RAISE EXCEPTION 'complete catalogue serving-role readiness report must remain service-only';
  END IF;

  SELECT re_engine.catalogue_serving_role_readiness_report_v2() INTO v_report;
  v_active_dishes := (v_report->>'active_dishes')::bigint;
  v_active_dish_slots := (v_report->>'active_dish_slots')::bigint;

  IF v_report->>'schema_version'
       <> 'recommendation-catalogue-serving-role-readiness-v2' THEN
    RAISE EXCEPTION 'complete catalogue serving-role readiness schema is invalid';
  END IF;

  IF NOT (v_report->'policy'->>'all_active_dishes_reconciled')::boolean
     OR (v_report->'policy'->>'identity_exposed')::boolean
     OR (v_report->'policy'->>'automatic_proposal_acceptance_allowed')::boolean
     OR (v_report->'policy'->>'publication_gate_changed')::boolean THEN
    RAISE EXCEPTION 'complete catalogue serving-role readiness policy is unsafe';
  END IF;

  IF (v_report->>'active_dishes_with_canonical_slot')::bigint
       + (v_report->>'active_dishes_without_canonical_slot')::bigint
       <> v_active_dishes THEN
    RAISE EXCEPTION 'canonical-slot dish coverage does not reconcile';
  END IF;

  IF (
    SELECT coalesce(sum(value::bigint), 0)
    FROM jsonb_each_text(v_report->'dish_routes')
  ) <> v_active_dishes THEN
    RAISE EXCEPTION 'complete catalogue dish routes do not reconcile';
  END IF;

  IF (
    SELECT coalesce(sum(value::bigint), 0)
    FROM jsonb_each_text(v_report->'hero_roles')
  ) <> v_active_dishes THEN
    RAISE EXCEPTION 'complete catalogue hero roles do not reconcile';
  END IF;

  IF (
    SELECT coalesce(sum(value::bigint), 0)
    FROM jsonb_each_text(v_report->'slot_routes')
  ) <> v_active_dish_slots THEN
    RAISE EXCEPTION 'complete catalogue slot routes do not reconcile';
  END IF;
END $$;
