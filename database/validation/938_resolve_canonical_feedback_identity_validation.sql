DO $$
DECLARE v_dish record;
BEGIN
  IF to_regprocedure('public.resolve_canonical_dish_identity(text)') IS NULL THEN
    RAISE EXCEPTION 'canonical dish identity resolver is missing';
  END IF;
  IF has_function_privilege('anon', 'public.resolve_canonical_dish_identity(text)', 'EXECUTE')
     OR has_function_privilege(
       'authenticated', 'public.resolve_canonical_dish_identity(text)', 'EXECUTE'
     ) THEN
    RAISE EXCEPTION 'canonical dish identity resolver must remain service-role only';
  END IF;
  IF position(
    'LIMIT 1' IN upper(pg_get_functiondef(
      'public.resolve_canonical_dish_identity(text)'::regprocedure
    ))
  ) > 0 THEN
    RAISE EXCEPTION 'canonical identity resolver may not choose an arbitrary first alias';
  END IF;

  SELECT * INTO v_dish
  FROM public.resolve_canonical_dish_identity('  Poha   Jalebi (Indori)  ');
  IF v_dish.dish_id IS NULL OR v_dish.canonical_name <> 'Poha Jalebi (Indori)' THEN
    RAISE EXCEPTION 'canonical identity normalization failed for serving-catalogue identity';
  END IF;

  IF EXISTS (
    SELECT 1 FROM public.feedback_events f
    WHERE f.data_source = 'real' AND f.dish_id IS NULL
      AND EXISTS (
        SELECT 1 FROM public.resolve_canonical_dish_identity(
          coalesce(nullif(f.detail->>'canonical_dish_name', ''), nullif(f.detail->>'dish_name', ''))
        )
      )
  ) THEN
    RAISE EXCEPTION 'resolvable real feedback remains identity-less';
  END IF;
END $$;

SELECT count(*) FILTER (WHERE dish_id IS NOT NULL) AS resolved_real_feedback,
       count(*) FILTER (WHERE dish_id IS NULL) AS unresolved_real_feedback
FROM public.feedback_events WHERE data_source = 'real';
