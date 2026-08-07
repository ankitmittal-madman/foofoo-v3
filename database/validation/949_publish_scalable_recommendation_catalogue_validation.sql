DO $$
DECLARE
  v_coverage record;
  v_exported bigint;
  v_bad_rows bigint;
BEGIN
  SELECT * INTO v_coverage FROM re_engine.catalogue_publication_coverage();

  SELECT count(*) INTO v_exported
  FROM re_engine.catalogue_publication_rows(NULL, 2000);

  IF v_exported > least(v_coverage.publishable_dishes, 2000) THEN
    RAISE EXCEPTION 'bounded catalogue export exceeded coverage: % > %',
      v_exported, v_coverage.publishable_dishes;
  END IF;

  SELECT count(*) INTO v_bad_rows
  FROM re_engine.catalogue_publication_rows(NULL, 2000) AS rows(row_data)
  WHERE row_data->>'schema_version' <> 'recommendation-catalogue-row-v1'
     OR nullif(row_data->>'id', '') IS NULL
     OR nullif(row_data->>'name', '') IS NULL
     OR jsonb_array_length(row_data->'ingredients') = 0
     OR jsonb_array_length(row_data->'meal_classes') = 0;

  IF v_bad_rows <> 0 THEN
    RAISE EXCEPTION 'catalogue publication returned % structurally unsafe rows', v_bad_rows;
  END IF;

  IF has_function_privilege('anon', 're_engine.catalogue_publication_rows(uuid,integer)', 'EXECUTE')
     OR has_function_privilege('authenticated', 're_engine.catalogue_publication_rows(uuid,integer)', 'EXECUTE') THEN
    RAISE EXCEPTION 'catalogue publication rows must remain service-only';
  END IF;
END $$;
