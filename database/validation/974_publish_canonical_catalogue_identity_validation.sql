DO $$
DECLARE
  v_identity_count bigint;
  v_publication_mismatch bigint;
BEGIN
  IF to_regprocedure('re_engine.catalogue_identity_coverage()') IS NULL
     OR to_regprocedure('re_engine.catalogue_identity_rows(uuid,integer)') IS NULL THEN
    RAISE EXCEPTION 'canonical catalogue identity publication boundary is missing';
  END IF;
  IF has_function_privilege('anon', 're_engine.catalogue_identity_coverage()', 'EXECUTE')
     OR has_function_privilege('authenticated', 're_engine.catalogue_identity_coverage()', 'EXECUTE')
     OR has_function_privilege(
       'anon', 're_engine.catalogue_identity_rows(uuid,integer)', 'EXECUTE'
     )
     OR has_function_privilege(
       'authenticated', 're_engine.catalogue_identity_rows(uuid,integer)', 'EXECUTE'
     )
     OR NOT has_function_privilege(
       'service_role', 're_engine.catalogue_identity_coverage()', 'EXECUTE'
     )
     OR NOT has_function_privilege(
       'service_role', 're_engine.catalogue_identity_rows(uuid,integer)', 'EXECUTE'
     ) THEN
    RAISE EXCEPTION 'canonical catalogue identity publication must remain service-only';
  END IF;

  SELECT re_engine.catalogue_identity_coverage() INTO v_identity_count;
  IF v_identity_count <= 0 OR v_identity_count <> (SELECT count(*) FROM public.dishes) THEN
    RAISE EXCEPTION 'canonical catalogue identity coverage drifted';
  END IF;

  SELECT count(*) INTO v_publication_mismatch
  FROM re_engine.catalogue_publication_rows(NULL, 2000) AS published(row_data)
  LEFT JOIN re_engine.catalogue_identity_rows(NULL, 2000) identities
    ON identities.dish_id = (published.row_data->>'id')::uuid
   AND identities.name = published.row_data->>'name'
  WHERE identities.dish_id IS NULL;
  IF v_publication_mismatch <> 0 THEN
    RAISE EXCEPTION 'safety-closed catalogue rows are missing canonical identity';
  END IF;
END $$;
