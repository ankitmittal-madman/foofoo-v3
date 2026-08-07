DO $$
BEGIN
  IF to_regprocedure('public.refresh_user_taste_vector(uuid)') IS NULL THEN
    RAISE EXCEPTION 'direct-class-aware taste refresh function is missing';
  END IF;
  IF to_regprocedure('public.refresh_user_taste_vector_without_direct_class(uuid)') IS NULL THEN
    RAISE EXCEPTION 'base taste refresh function is missing';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'user_taste_vectors'
      AND column_name = 'direct_class_affinity'
  ) OR NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'user_taste_vectors'
      AND column_name = 'projected_class_affinity'
  ) THEN
    RAISE EXCEPTION 'separate meal-class affinity columns are missing';
  END IF;
  IF has_function_privilege('anon', 'public.refresh_user_taste_vector(uuid)', 'EXECUTE') OR
     has_function_privilege('authenticated', 'public.refresh_user_taste_vector(uuid)', 'EXECUTE') THEN
    RAISE EXCEPTION 'taste refresh must remain service-only';
  END IF;
END $$;

SELECT
  count(*) AS vector_rows,
  count(*) FILTER (WHERE direct_class_affinity <> '{}'::jsonb) AS direct_class_rows,
  count(*) FILTER (WHERE projected_class_affinity <> '{}'::jsonb) AS projected_class_rows,
  count(*) FILTER (WHERE class_affinity <> '{}'::jsonb) AS combined_class_rows
FROM public.user_taste_vectors;
