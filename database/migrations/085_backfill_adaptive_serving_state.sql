-- Materialize truthful recent serving history that predates migration 081, and keep the duplicated
-- lifecycle projection synchronized with its authoritative profile value. No recommendation,
-- preference, score or point-in-time household feature is reconstructed.

CREATE OR REPLACE FUNCTION public.refresh_user_re_state(p_profile_id uuid)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $function$
DECLARE
  v_interaction_count integer;
  v_weight_tier text;
  v_engine_version text;
  v_city_overlay_weight real;
  v_result public.user_re_state;
BEGIN
  SELECT city_overlay_weight INTO v_city_overlay_weight
  FROM public.profiles WHERE id = p_profile_id;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'profile does not exist';
  END IF;

  SELECT count(*)::integer INTO v_interaction_count
  FROM public.feedback_events
  WHERE household_id = p_profile_id
    AND data_source = 'real'
    AND event_type <> 'shown_not_tapped';

  v_weight_tier := CASE
    WHEN v_interaction_count <= 10 THEN 'cold_start'
    WHEN v_interaction_count <= 50 THEN 'early'
    WHEN v_interaction_count <= 150 THEN 'emerging'
    WHEN v_interaction_count <= 500 THEN 'established'
    ELSE 'mature'
  END;

  SELECT engine_version INTO v_engine_version
  FROM public.recommendation_events
  WHERE household_id = p_profile_id AND engine_version IS NOT NULL
  ORDER BY created_at DESC LIMIT 1;

  INSERT INTO public.user_re_state (
    profile_id, interaction_count, cold_start_mode, re_engine_version, weight_tier,
    city_overlay_weight, updated_at
  ) VALUES (
    p_profile_id, v_interaction_count, v_interaction_count < 14, v_engine_version, v_weight_tier,
    v_city_overlay_weight, now()
  )
  ON CONFLICT (profile_id) DO UPDATE SET
    interaction_count = EXCLUDED.interaction_count,
    cold_start_mode = EXCLUDED.cold_start_mode,
    re_engine_version = coalesce(EXCLUDED.re_engine_version,
                                 public.user_re_state.re_engine_version),
    weight_tier = EXCLUDED.weight_tier,
    city_overlay_weight = EXCLUDED.city_overlay_weight,
    updated_at = EXCLUDED.updated_at
  RETURNING * INTO v_result;

  RETURN to_jsonb(v_result);
END
$function$;

REVOKE ALL ON FUNCTION public.refresh_user_re_state(uuid) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.refresh_user_re_state(uuid) TO service_role;

COMMENT ON FUNCTION public.refresh_user_re_state(uuid) IS
  'Idempotently derives lifecycle state from real feedback and synchronizes profile-owned regional overlay weight.';

-- Refresh every existing lifecycle row. This changes only values derivable from current durable
-- facts; confidence/persona fields are deliberately left untouched.
SELECT public.refresh_user_re_state(p.id)
FROM public.profiles p
WHERE EXISTS (SELECT 1 FROM public.user_re_state s WHERE s.profile_id = p.id)
   OR EXISTS (
     SELECT 1 FROM public.feedback_events f
     WHERE f.household_id = p.id AND f.data_source = 'real'
       AND f.event_type <> 'shown_not_tapped'
   );

-- Backfill the exact recent display facts already retained in recommendation_events. The runtime
-- RPC remains the single writer for deduplication and cadence math, so replay is retry-safe and
-- produces the same state as an online write. Events older than the live 30-day window are skipped.
DO $backfill$
DECLARE
  v_event record;
  v_items jsonb;
BEGIN
  FOR v_event IN
    SELECT r.id, r.plates
    FROM public.recommendation_events r
    WHERE r.re_served = true
      AND r.outcome IN ('success', 'partial')
      AND r.created_at >= now() - interval '30 days'
      AND jsonb_typeof(r.plates) = 'array'
      AND jsonb_array_length(r.plates) > 0
      AND NOT EXISTS (
        SELECT 1 FROM re_engine.recommendation_item_exposures e
        WHERE e.recommendation_event_id = r.id
      )
    ORDER BY r.created_at, r.id
  LOOP
    WITH plates AS (
      SELECT value AS plate
      FROM jsonb_array_elements(v_event.plates)
      WHERE jsonb_typeof(value) = 'object'
    ), flattened AS (
      SELECT jsonb_strip_nulls(jsonb_build_object(
        'dish_name', nullif(btrim(plate->>'name'), ''),
        'meal_class_code', nullif(btrim(plate->>'meal_class_code'), ''),
        'cuisine_family', nullif(btrim(coalesce(plate->>'cuisine_family', plate->>'cuisine')), ''),
        'heaviness', CASE WHEN jsonb_typeof(plate->'heaviness') = 'number'
          THEN plate->'heaviness' END,
        'total_mins', CASE WHEN jsonb_typeof(plate->'total_mins') = 'number'
          THEN plate->'total_mins' END,
        'richness_score', CASE WHEN jsonb_typeof(plate->'richness_score') = 'number'
          THEN plate->'richness_score' END
      )) AS item
      FROM plates WHERE nullif(btrim(plate->>'name'), '') IS NOT NULL

      UNION ALL

      SELECT jsonb_build_object('dish_name', hero.value)
      FROM plates
      CROSS JOIN LATERAL jsonb_array_elements_text(
        CASE WHEN jsonb_typeof(plate->'hero_dish_names') = 'array'
          THEN plate->'hero_dish_names' ELSE '[]'::jsonb END
      ) AS hero(value)
      WHERE nullif(btrim(hero.value), '') IS NOT NULL

      UNION ALL

      SELECT jsonb_strip_nulls(jsonb_build_object(
        'dish_name', nullif(btrim(component.value->>'dish_name'), ''),
        'meal_class_code', nullif(btrim(component.value->>'meal_class_code'), ''),
        'cuisine_family', nullif(btrim(coalesce(
          component.value->>'cuisine_family', component.value->>'cuisine'
        )), ''),
        'total_mins', CASE WHEN jsonb_typeof(plate#>'{practicality,active_minutes}') = 'number'
          THEN plate#>'{practicality,active_minutes}' END,
        'richness_score', CASE WHEN jsonb_typeof(plate->'richness_score') = 'number'
          THEN plate->'richness_score' END
      ))
      FROM plates
      CROSS JOIN LATERAL jsonb_array_elements(
        CASE WHEN jsonb_typeof(plate->'components') = 'array'
          THEN plate->'components' ELSE '[]'::jsonb END
      ) AS component(value)
      WHERE jsonb_typeof(component.value) = 'object'
        AND nullif(btrim(component.value->>'dish_name'), '') IS NOT NULL
    )
    SELECT coalesce(jsonb_agg(item), '[]'::jsonb) INTO v_items FROM flattened;

    IF jsonb_array_length(v_items) > 0 THEN
      PERFORM public.record_recommendation_exposure_state(v_event.id, v_items);
    END IF;
  END LOOP;
END
$backfill$;
