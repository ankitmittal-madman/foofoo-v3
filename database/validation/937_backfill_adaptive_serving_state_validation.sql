DO $$
BEGIN
  IF position(
    'city_overlay_weight = EXCLUDED.city_overlay_weight' IN
    pg_get_functiondef('public.refresh_user_re_state(uuid)'::regprocedure)
  ) = 0 THEN
    RAISE EXCEPTION 'lifecycle refresh does not synchronize regional overlay state';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM public.user_re_state s
    JOIN public.profiles p ON p.id = s.profile_id
    WHERE s.city_overlay_weight IS DISTINCT FROM p.city_overlay_weight
  ) THEN
    RAISE EXCEPTION 'user recommendation state has stale city overlay weights';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM public.recommendation_events r
    WHERE r.re_served = true
      AND r.outcome IN ('success', 'partial')
      AND r.created_at >= now() - interval '30 days'
      AND jsonb_typeof(r.plates) = 'array'
      AND jsonb_array_length(r.plates) > 0
      AND (
        EXISTS (
          SELECT 1 FROM jsonb_array_elements(r.plates) p
          WHERE nullif(btrim(p->>'name'), '') IS NOT NULL
             OR jsonb_array_length(CASE WHEN jsonb_typeof(p->'hero_dish_names') = 'array'
                  THEN p->'hero_dish_names' ELSE '[]'::jsonb END) > 0
             OR jsonb_array_length(CASE WHEN jsonb_typeof(p->'components') = 'array'
                  THEN p->'components' ELSE '[]'::jsonb END) > 0
        )
      )
      AND NOT EXISTS (
        SELECT 1 FROM re_engine.recommendation_item_exposures e
        WHERE e.recommendation_event_id = r.id
      )
  ) THEN
    RAISE EXCEPTION 'recent dish-bearing recommendation events are missing exposure state';
  END IF;

  IF EXISTS (
    SELECT DISTINCT e.household_id
    FROM re_engine.recommendation_item_exposures e
    WHERE e.exposed_at >= now() - interval '30 days'
    EXCEPT
    SELECT v.household_id FROM re_engine.variety_window_state v
  ) THEN
    RAISE EXCEPTION 'exposure households are missing variety state';
  END IF;

  IF EXISTS (
    SELECT DISTINCT e.household_id
    FROM re_engine.recommendation_item_exposures e
    WHERE e.exposed_at >= now() - interval '30 days'
    EXCEPT
    SELECT c.household_id FROM re_engine.household_cadence_state c
  ) THEN
    RAISE EXCEPTION 'exposure households are missing cadence state';
  END IF;
END $$;

SELECT count(*) AS exposure_rows FROM re_engine.recommendation_item_exposures;
SELECT count(*) AS variety_rows FROM re_engine.variety_window_state;
SELECT count(*) AS cadence_households FROM re_engine.household_cadence_state;
