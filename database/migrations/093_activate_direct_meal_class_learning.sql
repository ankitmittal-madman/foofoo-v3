-- Make direct meal-class actions first-class recommendation evidence.
--
-- Migration 084 projected dish feedback into class affinity, but could not distinguish that
-- inference from a user's explicit class selection/lock/replacement. Keep both sources so Ghar
-- RE can weight and explain them separately, while class_affinity remains the bounded combined
-- map consumed by older serving code and Aux features.

ALTER TABLE public.user_taste_vectors
  ADD COLUMN IF NOT EXISTS direct_class_affinity jsonb NOT NULL DEFAULT '{}'::jsonb,
  ADD COLUMN IF NOT EXISTS projected_class_affinity jsonb NOT NULL DEFAULT '{}'::jsonb;

ALTER FUNCTION public.refresh_user_taste_vector(uuid)
  RENAME TO refresh_user_taste_vector_without_direct_class;

CREATE FUNCTION public.refresh_user_taste_vector(p_profile_id uuid)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $function$
DECLARE
  v_base_result jsonb;
  v_direct jsonb := '{}'::jsonb;
  v_projected jsonb := '{}'::jsonb;
  v_combined jsonb := '{}'::jsonb;
BEGIN
  -- Preserve exact-dish, tag/genome and legacy class projection behavior from migration 084.
  v_base_result := public.refresh_user_taste_vector_without_direct_class(p_profile_id);

  WITH dish_signals AS (
    SELECT
      f.dish_id,
      CASE
        WHEN f.event_type IN ('like', 'accept', 'make_this', 'cooked', 'completed') THEN 0.20
        WHEN f.event_type IN ('dislike', 'never') THEN -0.30
        ELSE 0.0
      END::real AS delta
    FROM public.feedback_events f
    WHERE f.profile_id = p_profile_id
      AND f.data_source = 'real'
      AND f.evidence_kind = 'explicit'
      AND f.dish_id IS NOT NULL
  ), mapping_confidence AS (
    SELECT dish_id, class_code, max(coalesce(confidence, 1.0))::real AS confidence
    FROM public.dish_meal_class_mappings
    WHERE review_status <> 'rejected'
    GROUP BY dish_id, class_code
  ), projected_scores AS (
    SELECT
      m.class_code,
      greatest(-1.0, least(1.0, sum(s.delta * m.confidence)))::real AS affinity
    FROM dish_signals s
    JOIN mapping_confidence m ON m.dish_id = s.dish_id
    WHERE s.delta <> 0
    GROUP BY m.class_code
  )
  SELECT coalesce(jsonb_object_agg(class_code, affinity ORDER BY class_code), '{}'::jsonb)
    INTO v_projected
  FROM projected_scores;

  WITH direct_signals AS (
    -- The current/new class receives the user's explicit action.
    SELECT
      f.target_id AS class_code,
      CASE
        WHEN f.event_type = 'lock' THEN 0.40
        WHEN f.event_type IN ('selected', 'accept', 'make_this', 'replaced') THEN 0.30
        WHEN f.event_type IN ('dislike', 'never') THEN -0.40
        ELSE 0.0
      END::real AS delta
    FROM public.feedback_events f
    WHERE f.profile_id = p_profile_id
      AND f.data_source = 'real'
      AND f.evidence_kind = 'explicit'
      AND f.target_type = 'meal_class'
      AND f.target_identity_status = 'resolved'

    UNION ALL

    -- A replacement is weak negative evidence for the explicitly displaced class. Unlock is
    -- neutral: it removes commitment but does not mean the household dislikes that class.
    SELECT
      f.detail #>> '{replacement,from,target_id}' AS class_code,
      -0.15::real AS delta
    FROM public.feedback_events f
    WHERE f.profile_id = p_profile_id
      AND f.data_source = 'real'
      AND f.evidence_kind = 'explicit'
      AND f.event_type = 'replaced'
      AND f.detail #>> '{replacement,from,target_type}' = 'meal_class'
      AND f.detail #>> '{replacement,from,target_identity_status}' = 'resolved'
  ), direct_scores AS (
    SELECT
      s.class_code,
      greatest(-1.0, least(1.0, sum(s.delta)))::real AS affinity
    FROM direct_signals s
    JOIN public.meal_classes c ON c.class_code = s.class_code AND c.is_active
    WHERE s.class_code IS NOT NULL AND s.delta <> 0
    GROUP BY s.class_code
  )
  SELECT coalesce(jsonb_object_agg(class_code, affinity ORDER BY class_code), '{}'::jsonb)
    INTO v_direct
  FROM direct_scores;

  WITH dimensions AS (
    SELECT key AS class_code FROM jsonb_object_keys(v_projected) AS keys(key)
    UNION
    SELECT key AS class_code FROM jsonb_object_keys(v_direct) AS keys(key)
  ), combined AS (
    SELECT
      class_code,
      greatest(
        -1.0,
        least(
          1.0,
          coalesce((v_projected ->> class_code)::real, 0.0) +
          coalesce((v_direct ->> class_code)::real, 0.0)
        )
      )::real AS affinity
    FROM dimensions
  )
  SELECT coalesce(jsonb_object_agg(class_code, affinity ORDER BY class_code), '{}'::jsonb)
    INTO v_combined
  FROM combined;

  UPDATE public.user_taste_vectors
  SET direct_class_affinity = v_direct,
      projected_class_affinity = v_projected,
      class_affinity = v_combined,
      updated_at = now()
  WHERE profile_id = p_profile_id;

  RETURN v_base_result || jsonb_build_object(
    'direct_class_dimensions', (SELECT count(*) FROM jsonb_object_keys(v_direct)),
    'projected_class_dimensions', (SELECT count(*) FROM jsonb_object_keys(v_projected)),
    'class_dimensions', (SELECT count(*) FROM jsonb_object_keys(v_combined))
  );
END
$function$;

REVOKE ALL ON FUNCTION public.refresh_user_taste_vector(uuid) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.refresh_user_taste_vector(uuid) TO service_role;

COMMENT ON COLUMN public.user_taste_vectors.direct_class_affinity IS
  'Bounded class preference learned only from explicit events targeting a meal class.';
COMMENT ON COLUMN public.user_taste_vectors.projected_class_affinity IS
  'Bounded class preference projected from explicit dish events through reviewed mappings.';
COMMENT ON FUNCTION public.refresh_user_taste_vector(uuid) IS
  'Idempotently refreshes dish/tag vectors plus separately auditable direct, projected and combined meal-class affinity.';

DO $backfill$
DECLARE
  v_profile_id uuid;
BEGIN
  FOR v_profile_id IN
    SELECT DISTINCT f.profile_id
    FROM public.feedback_events f
    WHERE f.data_source = 'real'
  LOOP
    PERFORM public.refresh_user_taste_vector(v_profile_id);
  END LOOP;
END
$backfill$;
