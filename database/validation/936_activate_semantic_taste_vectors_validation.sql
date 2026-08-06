DO $$
DECLARE
  v_dimension_count integer;
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'user_taste_vectors'
      AND column_name = 'tag_affinity' AND data_type = 'jsonb'
  ) THEN
    RAISE EXCEPTION 'public.user_taste_vectors.tag_affinity is missing';
  END IF;

  SELECT max(vector_position) + 1 INTO v_dimension_count FROM public.tags;

  IF EXISTS (
    SELECT 1
    FROM public.dishes d
    WHERE EXISTS (
      SELECT 1 FROM public.dish_tags dt JOIN public.tags t ON t.id = dt.tag_id
      WHERE dt.dish_id = d.id AND t.tier IN (1, 2)
    ) AND cardinality(d.genome_vector) IS DISTINCT FROM v_dimension_count
  ) THEN
    RAISE EXCEPTION 'a tagged dish does not have a dense, vocabulary-aligned genome vector';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM public.dishes d
    CROSS JOIN LATERAL generate_subscripts(d.genome_vector, 1) position
    LEFT JOIN public.tags t ON t.vector_position = position - 1 AND t.tier IN (1, 2)
    LEFT JOIN public.dish_tags dt ON dt.dish_id = d.id AND dt.tag_id = t.id
    WHERE abs(d.genome_vector[position] - coalesce(dt.confidence, 0.0)) > 0.00001
  ) THEN
    RAISE EXCEPTION 'a dish genome value is not aligned to tags.vector_position';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM public.user_taste_vectors u
    CROSS JOIN LATERAL jsonb_each_text(u.tag_affinity) value
    LEFT JOIN public.tags t ON t.dimension || ':' || t.tag_name = value.key
    WHERE t.id IS NULL
      OR value.value::real NOT BETWEEN -1.0 AND 1.0
      OR cardinality(u.genome_tag_affinity) IS DISTINCT FROM v_dimension_count
      OR abs(u.genome_tag_affinity[t.vector_position + 1] - value.value::real) > 0.00001
  ) THEN
    RAISE EXCEPTION 'a semantic tag affinity is invalid or misaligned with its genome vector';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM public.feedback_events f
    JOIN public.dish_tags dt ON dt.dish_id = f.dish_id
    JOIN public.tags tag ON tag.id = dt.tag_id AND tag.tier IN (1, 2)
    LEFT JOIN public.user_taste_vectors taste ON taste.profile_id = f.profile_id
    WHERE f.data_source = 'real'
      AND f.event_type IN ('like', 'accept', 'make_this', 'cooked', 'completed', 'dislike', 'never')
      AND NOT EXISTS (SELECT 1 FROM jsonb_object_keys(coalesce(taste.tag_affinity, '{}'::jsonb)))
  ) THEN
    RAISE EXCEPTION 'tagged explicit feedback is missing semantic tag affinity';
  END IF;
END $$;

SELECT
  count(*) FILTER (WHERE EXISTS (SELECT 1 FROM jsonb_object_keys(class_affinity)))
    AS class_profiles,
  count(*) FILTER (WHERE EXISTS (SELECT 1 FROM jsonb_object_keys(tag_affinity)))
    AS tag_profiles,
  max(cardinality(genome_tag_affinity)) AS genome_dimensions
FROM public.user_taste_vectors;
