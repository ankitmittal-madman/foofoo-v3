-- Make generalized taste state semantically correct and consumable by online ranking.
--
-- The original genome trigger packed only the tags present on a dish into a short array. Two
-- arrays therefore used different meanings at the same index (for example, position 1 could be
-- `bread` for one dish and `curry` for another). Build a dense vector indexed by the governed
-- tags.vector_position vocabulary, and persist a readable dimension:name map beside it so the
-- serving service never has to infer vector semantics.

ALTER TABLE public.user_taste_vectors
  ADD COLUMN IF NOT EXISTS tag_affinity jsonb NOT NULL DEFAULT '{}'::jsonb;

CREATE OR REPLACE FUNCTION public.fn_update_dish_genome_vector()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $function$
DECLARE
  v_dish uuid := coalesce(NEW.dish_id, OLD.dish_id);
  v_dim integer;
  v_vec real[];
BEGIN
  SELECT max(vector_position) + 1 INTO v_dim FROM public.tags;

  IF v_dim IS NULL OR NOT EXISTS (
    SELECT 1
    FROM public.dish_tags dt
    JOIN public.tags t ON t.id = dt.tag_id
    WHERE dt.dish_id = v_dish AND t.tier IN (1, 2)
  ) THEN
    v_vec := NULL;
  ELSE
    SELECT array_agg(coalesce(dt.confidence, 0.0)::real ORDER BY positions.position)
      INTO v_vec
    FROM generate_series(0, v_dim - 1) AS positions(position)
    LEFT JOIN public.tags t
      ON t.vector_position = positions.position AND t.tier IN (1, 2)
    LEFT JOIN public.dish_tags dt
      ON dt.tag_id = t.id AND dt.dish_id = v_dish;
  END IF;

  UPDATE public.dishes
  SET genome_vector = v_vec, updated_at = now()
  WHERE id = v_dish;
  RETURN NULL;
END
$function$;

-- Repair every existing vector in one set-based pass. Untagged ingestion rows deliberately keep
-- NULL rather than masquerading as fully-known zero vectors.
WITH dimensions AS (
  SELECT max(vector_position) + 1 AS dimension_count FROM public.tags
), tagged_dishes AS (
  SELECT DISTINCT dt.dish_id
  FROM public.dish_tags dt
  JOIN public.tags t ON t.id = dt.tag_id
  WHERE t.tier IN (1, 2)
), rebuilt AS (
  SELECT
    td.dish_id,
    array_agg(coalesce(dt.confidence, 0.0)::real ORDER BY positions.position) AS genome_vector
  FROM tagged_dishes td
  CROSS JOIN dimensions dims
  CROSS JOIN LATERAL generate_series(0, dims.dimension_count - 1) AS positions(position)
  LEFT JOIN public.tags t
    ON t.vector_position = positions.position AND t.tier IN (1, 2)
  LEFT JOIN public.dish_tags dt
    ON dt.tag_id = t.id AND dt.dish_id = td.dish_id
  GROUP BY td.dish_id
)
UPDATE public.dishes d
SET genome_vector = rebuilt.genome_vector, updated_at = now()
FROM rebuilt
WHERE d.id = rebuilt.dish_id;

UPDATE public.dishes d
SET genome_vector = NULL, updated_at = now()
WHERE genome_vector IS NOT NULL
  AND NOT EXISTS (
    SELECT 1
    FROM public.dish_tags dt
    JOIN public.tags t ON t.id = dt.tag_id
    WHERE dt.dish_id = d.id AND t.tier IN (1, 2)
  );

CREATE OR REPLACE FUNCTION public.refresh_user_taste_vector(p_profile_id uuid)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $function$
DECLARE
  v_dish_affinity jsonb := '{}'::jsonb;
  v_class_affinity jsonb := '{}'::jsonb;
  v_tag_affinity jsonb := '{}'::jsonb;
  v_genome real[] := ARRAY[]::real[];
  v_genome_length integer := 0;
  v_signal record;
BEGIN
  IF NOT EXISTS (SELECT 1 FROM public.profiles WHERE id = p_profile_id) THEN
    RAISE EXCEPTION 'profile does not exist';
  END IF;

  WITH signals AS (
    SELECT
      coalesce(d.name, nullif(f.detail->>'canonical_dish_name', ''),
               nullif(f.detail->>'dish_name', '')) AS dish_name,
      CASE
        WHEN f.event_type IN ('like', 'accept', 'make_this', 'cooked', 'completed') THEN 0.20
        WHEN f.event_type IN ('dislike', 'never') THEN -0.30
        ELSE 0.0
      END::real AS delta
    FROM public.feedback_events f
    LEFT JOIN public.dishes d ON d.id = f.dish_id
    WHERE f.profile_id = p_profile_id AND f.data_source = 'real'
  ), dish_scores AS (
    SELECT dish_name, greatest(-1.0, least(1.0, sum(delta)))::real AS affinity
    FROM signals
    WHERE dish_name IS NOT NULL AND delta <> 0
    GROUP BY dish_name
  )
  SELECT coalesce(jsonb_object_agg(dish_name, affinity ORDER BY dish_name), '{}'::jsonb)
  INTO v_dish_affinity
  FROM dish_scores;

  WITH signals AS (
    SELECT
      f.dish_id,
      CASE
        WHEN f.event_type IN ('like', 'accept', 'make_this', 'cooked', 'completed') THEN 0.20
        WHEN f.event_type IN ('dislike', 'never') THEN -0.30
        ELSE 0.0
      END::real AS delta
    FROM public.feedback_events f
    WHERE f.profile_id = p_profile_id AND f.data_source = 'real' AND f.dish_id IS NOT NULL
  ), mapping_confidence AS (
    SELECT dish_id, class_code, max(coalesce(confidence, 1.0))::real AS confidence
    FROM public.dish_meal_class_mappings
    WHERE review_status <> 'rejected'
    GROUP BY dish_id, class_code
  ), class_scores AS (
    SELECT
      m.class_code,
      greatest(-1.0, least(1.0, sum(s.delta * m.confidence)))::real AS affinity
    FROM signals s
    JOIN mapping_confidence m ON m.dish_id = s.dish_id
    WHERE s.delta <> 0
    GROUP BY m.class_code
  )
  SELECT coalesce(jsonb_object_agg(class_code, affinity ORDER BY class_code), '{}'::jsonb)
  INTO v_class_affinity
  FROM class_scores;

  WITH signals AS (
    SELECT
      f.dish_id,
      CASE
        WHEN f.event_type IN ('like', 'accept', 'make_this', 'cooked', 'completed') THEN 0.20
        WHEN f.event_type IN ('dislike', 'never') THEN -0.30
        ELSE 0.0
      END::real AS delta
    FROM public.feedback_events f
    WHERE f.profile_id = p_profile_id AND f.data_source = 'real' AND f.dish_id IS NOT NULL
  ), tag_scores AS (
    SELECT
      t.dimension || ':' || t.tag_name AS tag_key,
      greatest(-1.0, least(1.0, sum(s.delta * coalesce(dt.confidence, 1.0))))::real AS affinity
    FROM signals s
    JOIN public.dish_tags dt ON dt.dish_id = s.dish_id
    JOIN public.tags t ON t.id = dt.tag_id AND t.tier IN (1, 2)
    WHERE s.delta <> 0
    GROUP BY t.dimension, t.tag_name
  )
  SELECT coalesce(jsonb_object_agg(tag_key, affinity ORDER BY tag_key), '{}'::jsonb)
  INTO v_tag_affinity
  FROM tag_scores;

  IF v_tag_affinity <> '{}'::jsonb THEN
    SELECT max(vector_position) + 1 INTO v_genome_length FROM public.tags;
    v_genome := array_fill(0.0::real, ARRAY[v_genome_length]);
    FOR v_signal IN
      SELECT t.vector_position, (value.value)::real AS affinity
      FROM jsonb_each_text(v_tag_affinity) value
      JOIN public.tags t ON t.dimension || ':' || t.tag_name = value.key
    LOOP
      v_genome[v_signal.vector_position + 1] := v_signal.affinity;
    END LOOP;
  END IF;

  INSERT INTO public.user_taste_vectors (
    profile_id, dish_affinity, class_affinity, tag_affinity, genome_tag_affinity, updated_at
  ) VALUES (
    p_profile_id, v_dish_affinity, v_class_affinity, v_tag_affinity, v_genome, now()
  )
  ON CONFLICT (profile_id) DO UPDATE SET
    dish_affinity = EXCLUDED.dish_affinity,
    class_affinity = EXCLUDED.class_affinity,
    tag_affinity = EXCLUDED.tag_affinity,
    genome_tag_affinity = EXCLUDED.genome_tag_affinity,
    updated_at = EXCLUDED.updated_at;

  RETURN jsonb_build_object(
    'profile_id', p_profile_id,
    'dish_dimensions', (SELECT count(*) FROM jsonb_object_keys(v_dish_affinity)),
    'class_dimensions', (SELECT count(*) FROM jsonb_object_keys(v_class_affinity)),
    'tag_dimensions', (SELECT count(*) FROM jsonb_object_keys(v_tag_affinity)),
    'genome_dimensions', cardinality(v_genome),
    'updated_at', now()
  );
END
$function$;

REVOKE ALL ON FUNCTION public.refresh_user_taste_vector(uuid) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.refresh_user_taste_vector(uuid) TO service_role;

COMMENT ON COLUMN public.user_taste_vectors.tag_affinity IS
  'Human-readable dimension:tag affinity projection consumed by online recommendation ranking.';
COMMENT ON FUNCTION public.refresh_user_taste_vector(uuid) IS
  'Idempotently derives exact-dish, meal-class, semantic-tag and aligned genome affinities from canonical explicit feedback.';

DO $backfill$
DECLARE
  v_profile_id uuid;
BEGIN
  FOR v_profile_id IN
    SELECT DISTINCT f.profile_id
    FROM public.feedback_events f
    WHERE f.data_source = 'real'
      AND f.event_type IN ('like', 'accept', 'make_this', 'cooked', 'completed', 'dislike', 'never')
  LOOP
    PERFORM public.refresh_user_taste_vector(v_profile_id);
  END LOOP;
END
$backfill$;
