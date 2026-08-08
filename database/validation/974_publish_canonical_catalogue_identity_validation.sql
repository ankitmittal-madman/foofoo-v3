DO $$
DECLARE
  v_identity_count bigint;
  v_publication_mismatch bigint;
  v_bad_regional_metadata bigint;
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
  LEFT JOIN public.dishes identity
    ON identity.id = (published.row_data->>'id')::uuid
   AND identity.name = published.row_data->>'name'
  WHERE identity.id IS NULL;
  IF v_publication_mismatch <> 0 THEN
    RAISE EXCEPTION 'safety-closed catalogue rows are missing canonical identity';
  END IF;

  SELECT count(*) INTO v_bad_regional_metadata
  FROM re_engine.catalogue_identity_rows(NULL, 2000) identities
  WHERE jsonb_typeof(identities.regional_affinities) <> 'array'
     OR EXISTS (
       SELECT 1
       FROM jsonb_array_elements(identities.regional_affinities) item
       WHERE nullif(item->>'region_code', '') IS NULL
          OR (item->>'affinity_score')::numeric NOT BETWEEN 0 AND 1
          OR (item->>'confidence')::numeric NOT BETWEEN 0 AND 1
          OR item->>'review_status' = 'rejected'
     );
  IF v_bad_regional_metadata <> 0 THEN
    RAISE EXCEPTION 'canonical catalogue regional metadata is invalid';
  END IF;
END $$;
