-- Derive every online taste projection from canonical explicit feedback history.
-- Recomputing from source events makes retries and concurrent feedback writes converge instead
-- of applying an in-memory read/modify/write delta that can be lost or doubled.

CREATE OR REPLACE FUNCTION public.refresh_user_taste_vector(p_profile_id uuid)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $function$
DECLARE
  v_dish_affinity jsonb := '{}'::jsonb;
  v_class_affinity jsonb := '{}'::jsonb;
  v_genome real[] := ARRAY[]::real[];
  v_genome_length integer := 0;
  v_index integer;
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

  WITH scored_dishes AS (
    SELECT
      f.dish_id,
      sum(CASE
        WHEN f.event_type IN ('like', 'accept', 'make_this', 'cooked', 'completed') THEN 0.20
        WHEN f.event_type IN ('dislike', 'never') THEN -0.30
        ELSE 0.0
      END)::real AS delta
    FROM public.feedback_events f
    WHERE f.profile_id = p_profile_id AND f.data_source = 'real' AND f.dish_id IS NOT NULL
    GROUP BY f.dish_id
  )
  SELECT coalesce(max(cardinality(d.genome_vector)), 0)
  INTO v_genome_length
  FROM scored_dishes s
  JOIN public.dishes d ON d.id = s.dish_id
  WHERE s.delta <> 0;

  IF v_genome_length > 0 THEN
    v_genome := array_fill(0.0::real, ARRAY[v_genome_length]);
    FOR v_signal IN
      WITH scored_dishes AS (
        SELECT
          f.dish_id,
          sum(CASE
            WHEN f.event_type IN ('like', 'accept', 'make_this', 'cooked', 'completed') THEN 0.20
            WHEN f.event_type IN ('dislike', 'never') THEN -0.30
            ELSE 0.0
          END)::real AS delta
        FROM public.feedback_events f
        WHERE f.profile_id = p_profile_id AND f.data_source = 'real'
          AND f.dish_id IS NOT NULL
        GROUP BY f.dish_id
      )
      SELECT d.genome_vector, s.delta
      FROM scored_dishes s
      JOIN public.dishes d ON d.id = s.dish_id
      WHERE s.delta <> 0 AND cardinality(d.genome_vector) > 0
    LOOP
      FOR v_index IN 1..v_genome_length LOOP
        v_genome[v_index] := greatest(
          -1.0,
          least(
            1.0,
            v_genome[v_index] + v_signal.delta *
              coalesce(v_signal.genome_vector[v_index], 0.0)
          )
        )::real;
      END LOOP;
    END LOOP;
  END IF;

  INSERT INTO public.user_taste_vectors (
    profile_id, dish_affinity, class_affinity, genome_tag_affinity, updated_at
  ) VALUES (
    p_profile_id, v_dish_affinity, v_class_affinity, v_genome, now()
  )
  ON CONFLICT (profile_id) DO UPDATE SET
    dish_affinity = EXCLUDED.dish_affinity,
    class_affinity = EXCLUDED.class_affinity,
    genome_tag_affinity = EXCLUDED.genome_tag_affinity,
    updated_at = EXCLUDED.updated_at;

  RETURN jsonb_build_object(
    'profile_id', p_profile_id,
    'dish_dimensions', (SELECT count(*) FROM jsonb_object_keys(v_dish_affinity)),
    'class_dimensions', (SELECT count(*) FROM jsonb_object_keys(v_class_affinity)),
    'genome_dimensions', cardinality(v_genome),
    'updated_at', now()
  );
END
$function$;

REVOKE ALL ON FUNCTION public.refresh_user_taste_vector(uuid) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.refresh_user_taste_vector(uuid) TO service_role;

COMMENT ON FUNCTION public.refresh_user_taste_vector(uuid) IS
  'Idempotently derives exact-dish, meal-class and genome affinities from canonical real explicit feedback.';

-- Backfill profiles with relevant feedback without emitting profile identifiers in migration logs.
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
