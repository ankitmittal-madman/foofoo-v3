DO $$
BEGIN
  IF to_regprocedure('public.refresh_user_taste_vector(uuid)') IS NULL THEN
    RAISE EXCEPTION 'public.refresh_user_taste_vector(uuid) is missing';
  END IF;
  IF has_function_privilege('anon', 'public.refresh_user_taste_vector(uuid)', 'EXECUTE')
     OR has_function_privilege(
       'authenticated', 'public.refresh_user_taste_vector(uuid)', 'EXECUTE'
     ) THEN
    RAISE EXCEPTION 'taste-vector refresh must be service-role only';
  END IF;
  IF EXISTS (
    SELECT 1
    FROM public.user_taste_vectors t
    CROSS JOIN LATERAL jsonb_each_text(t.dish_affinity) value
    WHERE value.value::real NOT BETWEEN -1.0 AND 1.0
  ) OR EXISTS (
    SELECT 1
    FROM public.user_taste_vectors t
    CROSS JOIN LATERAL jsonb_each_text(t.class_affinity) value
    WHERE value.value::real NOT BETWEEN -1.0 AND 1.0
  ) OR EXISTS (
    SELECT 1
    FROM public.user_taste_vectors t
    CROSS JOIN LATERAL unnest(coalesce(t.genome_tag_affinity, ARRAY[]::real[])) value
    WHERE value NOT BETWEEN -1.0 AND 1.0
  ) THEN
    RAISE EXCEPTION 'a persisted taste affinity is outside [-1,1]';
  END IF;
  IF EXISTS (
    SELECT 1
    FROM public.feedback_events f
    JOIN public.dishes d ON d.id = f.dish_id
    JOIN public.dish_meal_class_mappings m ON m.dish_id = f.dish_id
    LEFT JOIN public.user_taste_vectors t ON t.profile_id = f.profile_id
    WHERE f.data_source = 'real'
      AND f.event_type IN ('like', 'accept', 'make_this', 'cooked', 'completed', 'dislike', 'never')
      AND (
        NOT EXISTS (SELECT 1 FROM jsonb_object_keys(coalesce(t.class_affinity, '{}'::jsonb)))
        OR (cardinality(d.genome_vector) > 0
            AND coalesce(cardinality(t.genome_tag_affinity), 0) = 0)
      )
  ) THEN
    RAISE EXCEPTION 'resolved explicit feedback is missing generalized taste dimensions';
  END IF;
END $$;

SELECT
  count(*) FILTER (
    WHERE EXISTS (SELECT 1 FROM jsonb_object_keys(class_affinity))
  ) AS class_profiles,
  count(*) FILTER (WHERE cardinality(genome_tag_affinity) > 0) AS genome_profiles
FROM public.user_taste_vectors;
