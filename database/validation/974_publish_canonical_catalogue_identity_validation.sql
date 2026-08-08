DO $$
DECLARE
  v_identity_count bigint;
  v_identity_seen bigint := 0;
  v_identity_after uuid := NULL;
  v_identity_page_count integer;
  v_identity_page_max uuid;
  v_identity_page_invalid integer;
  v_identity_page_bad_regional integer;
  v_publication_after uuid := NULL;
  v_publication_page_count integer;
  v_publication_page_max uuid;
  v_publication_page_mismatch integer;
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

  LOOP
    SELECT
      count(*),
      (array_agg(dish_id ORDER BY dish_id DESC))[1],
      count(*) FILTER (
        WHERE name IS NULL OR btrim(name) = ''
          OR (v_identity_after IS NOT NULL AND dish_id <= v_identity_after)
      ),
      count(*) FILTER (
        WHERE jsonb_typeof(regional_affinities) <> 'array'
          OR EXISTS (
            SELECT 1
            FROM jsonb_array_elements(
              CASE WHEN jsonb_typeof(regional_affinities) = 'array'
                THEN regional_affinities ELSE '[]'::jsonb END
            ) item
            WHERE nullif(item->>'region_code', '') IS NULL
               OR (item->>'affinity_score')::numeric NOT BETWEEN 0 AND 1
               OR (item->>'confidence')::numeric NOT BETWEEN 0 AND 1
               OR item->>'review_status' = 'rejected'
          )
      )
    INTO
      v_identity_page_count,
      v_identity_page_max,
      v_identity_page_invalid,
      v_identity_page_bad_regional
    FROM re_engine.catalogue_identity_rows(v_identity_after, 2000);
    EXIT WHEN v_identity_page_count = 0;
    IF v_identity_page_count > 2000 OR v_identity_page_max IS NULL
       OR v_identity_page_invalid <> 0 THEN
      RAISE EXCEPTION 'canonical catalogue identity page is invalid';
    END IF;
    IF v_identity_page_bad_regional <> 0 THEN
      RAISE EXCEPTION 'canonical catalogue regional metadata is invalid';
    END IF;
    v_identity_seen := v_identity_seen + v_identity_page_count;
    v_identity_after := v_identity_page_max;
  END LOOP;
  IF v_identity_seen <> v_identity_count THEN
    RAISE EXCEPTION 'canonical catalogue identity pagination is incomplete';
  END IF;

  LOOP
    WITH publication_page AS (
      SELECT row_data
      FROM re_engine.catalogue_publication_rows(v_publication_after, 2000)
        AS published(row_data)
    )
    SELECT
      count(*),
      (array_agg(
        (row_data->>'id')::uuid ORDER BY (row_data->>'id')::uuid DESC
      ))[1],
      count(*) FILTER (
        WHERE NOT EXISTS (
          SELECT 1 FROM public.dishes d
          WHERE d.id = (publication_page.row_data->>'id')::uuid
            AND d.name = publication_page.row_data->>'name'
        )
      )
    INTO v_publication_page_count, v_publication_page_max, v_publication_page_mismatch
    FROM publication_page;
    EXIT WHEN v_publication_page_count = 0;
    IF v_publication_page_count > 2000 OR v_publication_page_max IS NULL
       OR v_publication_page_mismatch <> 0
       OR (v_publication_after IS NOT NULL
         AND v_publication_page_max <= v_publication_after) THEN
      RAISE EXCEPTION 'safety-closed catalogue rows are missing canonical identity';
    END IF;
    v_publication_after := v_publication_page_max;
  END LOOP;
END $$;
