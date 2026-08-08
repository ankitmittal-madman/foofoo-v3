DO $$
DECLARE
  v_report jsonb;
  v_distribution_total bigint;
BEGIN
  IF to_regprocedure('re_engine.catalogue_publication_gap_report()') IS NULL THEN
    RAISE EXCEPTION 'catalogue publication gap report function is missing';
  END IF;

  IF has_function_privilege('anon', 're_engine.catalogue_publication_gap_report()', 'EXECUTE')
     OR has_function_privilege(
       'authenticated', 're_engine.catalogue_publication_gap_report()', 'EXECUTE'
     ) THEN
    RAISE EXCEPTION 'catalogue publication gap report must remain service-only';
  END IF;

  SELECT re_engine.catalogue_publication_gap_report() INTO v_report;

  IF v_report->>'schema_version' <> 'recommendation-catalogue-gap-report-v1' THEN
    RAISE EXCEPTION 'catalogue publication gap report schema is invalid';
  END IF;

  IF (v_report->'inventory'->>'stored_dishes')::bigint
       <> (v_report->'inventory'->>'active_dishes')::bigint
          + (v_report->'inventory'->>'inactive_dishes')::bigint THEN
    RAISE EXCEPTION 'stored catalogue inventory does not reconcile';
  END IF;

  IF (v_report->'inventory'->>'active_dishes')::bigint
       <> (v_report->'serving_readiness'->>'publishable_dishes')::bigint
          + (v_report->'serving_readiness'->>'active_not_publishable')::bigint THEN
    RAISE EXCEPTION 'active catalogue inventory does not reconcile';
  END IF;

  IF (v_report->'ordered_funnel'->>'active')::bigint
       <> (v_report->'inventory'->>'active_dishes')::bigint
     OR (v_report->'ordered_funnel'->>'taxonomy_complete_publishable')::bigint
       <> (v_report->'serving_readiness'->>'publishable_dishes')::bigint THEN
    RAISE EXCEPTION 'catalogue readiness funnel endpoints do not reconcile';
  END IF;

  IF NOT (
    (v_report->'ordered_funnel'->>'active')::bigint
      >= (v_report->'ordered_funnel'->>'enriched')::bigint
    AND (v_report->'ordered_funnel'->>'enriched')::bigint
      >= (v_report->'ordered_funnel'->>'safety_closed')::bigint
    AND (v_report->'ordered_funnel'->>'safety_closed')::bigint
      >= (v_report->'ordered_funnel'->>'cuisine_complete')::bigint
    AND (v_report->'ordered_funnel'->>'cuisine_complete')::bigint
      >= (v_report->'ordered_funnel'->>'ingredients_complete')::bigint
    AND (v_report->'ordered_funnel'->>'ingredients_complete')::bigint
      >= (v_report->'ordered_funnel'->>'class_mapped')::bigint
    AND (v_report->'ordered_funnel'->>'class_mapped')::bigint
      >= (v_report->'ordered_funnel'->>'taxonomy_complete_publishable')::bigint
  ) THEN
    RAISE EXCEPTION 'catalogue readiness funnel is not monotonic';
  END IF;

  SELECT coalesce(sum(value::bigint), 0)
  INTO v_distribution_total
  FROM jsonb_each_text(v_report->'missing_gate_distribution');

  IF v_distribution_total <> (v_report->'inventory'->>'active_dishes')::bigint THEN
    RAISE EXCEPTION 'missing-gate distribution does not cover every active dish';
  END IF;

  IF coalesce((v_report->'missing_gate_distribution'->>'0')::bigint, 0)
       <> (v_report->'serving_readiness'->>'publishable_dishes')::bigint THEN
    RAISE EXCEPTION 'zero-gap dishes do not match publishable dishes';
  END IF;
END $$;
