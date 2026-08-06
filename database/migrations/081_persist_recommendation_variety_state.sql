-- Persist exact, retry-safe serving exposure for freshness, variety and cadence features.
-- Runtime state remains private in re_engine; Edge Functions use service-role-only RPCs.

CREATE TABLE re_engine.recommendation_item_exposures (
  recommendation_event_id uuid NOT NULL
    REFERENCES public.recommendation_events(id) ON DELETE CASCADE,
  household_id uuid NOT NULL REFERENCES public.households(id) ON DELETE CASCADE,
  dish_name text NOT NULL CHECK (btrim(dish_name) <> ''),
  dish_id uuid REFERENCES public.dishes(id) ON DELETE SET NULL,
  meal_class_code text,
  cuisine_family text,
  heaviness real CHECK (heaviness IS NULL OR heaviness BETWEEN 0 AND 3),
  total_mins real CHECK (total_mins IS NULL OR total_mins >= 0),
  richness_score real CHECK (richness_score IS NULL OR richness_score BETWEEN 0 AND 1),
  exposed_at timestamptz NOT NULL,
  feature_version text NOT NULL DEFAULT 'recommendation-exposure-v1',
  PRIMARY KEY (recommendation_event_id, dish_name)
);

CREATE INDEX recommendation_item_exposures_household_time
  ON re_engine.recommendation_item_exposures (household_id, exposed_at DESC);

CREATE TABLE re_engine.variety_window_state (
  household_id uuid NOT NULL REFERENCES public.households(id) ON DELETE CASCADE,
  dimension_code text NOT NULL CHECK (dimension_code IN ('dish_name','meal_class','cuisine')),
  entity_key text NOT NULL CHECK (btrim(entity_key) <> ''),
  window_code text NOT NULL CHECK (window_code IN ('7d','30d')),
  last_seen_at timestamptz NOT NULL,
  count_in_window integer NOT NULL CHECK (count_in_window > 0),
  feature_version text NOT NULL DEFAULT 'recommendation-variety-v1',
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (household_id, dimension_code, entity_key, window_code)
);

CREATE INDEX variety_window_state_household_recent
  ON re_engine.variety_window_state (household_id, window_code, last_seen_at DESC);

REVOKE ALL ON TABLE re_engine.recommendation_item_exposures,
  re_engine.variety_window_state FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE re_engine.recommendation_item_exposures,
  re_engine.variety_window_state TO service_role;

CREATE OR REPLACE FUNCTION public.record_recommendation_exposure_state(
  p_recommendation_event_id uuid,
  p_items jsonb
)
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public, re_engine
AS $function$
DECLARE
  v_household_id uuid;
  v_exposed_at timestamptz;
  v_inserted integer := 0;
BEGIN
  IF jsonb_typeof(p_items) <> 'array' THEN
    RAISE EXCEPTION 'p_items must be a JSON array';
  END IF;

  SELECT household_id, created_at
    INTO v_household_id, v_exposed_at
  FROM public.recommendation_events
  WHERE id = p_recommendation_event_id;

  IF v_household_id IS NULL THEN
    RAISE EXCEPTION 'recommendation event does not exist';
  END IF;

  WITH parsed AS (
    SELECT
      nullif(btrim(item->>'dish_name'), '') AS supplied_name,
      nullif(btrim(item->>'meal_class_code'), '') AS supplied_class,
      nullif(btrim(item->>'cuisine_family'), '') AS supplied_cuisine,
      CASE WHEN jsonb_typeof(item->'heaviness') = 'number'
        THEN (item->>'heaviness')::real END AS heaviness,
      CASE WHEN jsonb_typeof(item->'total_mins') = 'number'
        THEN (item->>'total_mins')::real END AS total_mins,
      CASE WHEN jsonb_typeof(item->'richness_score') = 'number'
        THEN (item->>'richness_score')::real END AS richness_score
    FROM jsonb_array_elements(p_items) AS item
  ), resolved AS (
    SELECT DISTINCT ON (lower(coalesce(d.name, p.supplied_name)))
      coalesce(d.name, p.supplied_name) AS dish_name,
      d.id AS dish_id,
      coalesce(p.supplied_class, classes.class_code) AS meal_class_code,
      coalesce(p.supplied_cuisine, c.cuisine_group, c.name) AS cuisine_family,
      p.heaviness,
      p.total_mins,
      p.richness_score
    FROM parsed p
    LEFT JOIN public.dishes d ON lower(d.name) = lower(p.supplied_name)
    LEFT JOIN public.cuisines c ON c.id = d.cuisine_id
    LEFT JOIN LATERAL (
      SELECT m.class_code
      FROM public.dish_meal_class_mappings m
      WHERE m.dish_id = d.id AND m.review_status <> 'rejected'
      ORDER BY m.confidence DESC, m.class_code
      LIMIT 1
    ) classes ON true
    WHERE p.supplied_name IS NOT NULL
    ORDER BY lower(coalesce(d.name, p.supplied_name))
  )
  INSERT INTO re_engine.recommendation_item_exposures (
    recommendation_event_id, household_id, dish_name, dish_id, meal_class_code,
    cuisine_family, heaviness, total_mins, richness_score, exposed_at
  )
  SELECT p_recommendation_event_id, v_household_id, dish_name, dish_id, meal_class_code,
         cuisine_family, heaviness, total_mins, richness_score, v_exposed_at
  FROM resolved
  ON CONFLICT (recommendation_event_id, dish_name) DO NOTHING;
  GET DIAGNOSTICS v_inserted = ROW_COUNT;

  -- A retry of the same recommendation event is a no-op, including cadence calculations.
  IF v_inserted = 0 THEN
    RETURN false;
  END IF;

  DELETE FROM re_engine.recommendation_item_exposures
  WHERE household_id = v_household_id AND exposed_at < now() - interval '30 days';

  DELETE FROM re_engine.variety_window_state WHERE household_id = v_household_id;
  INSERT INTO re_engine.variety_window_state (
    household_id, dimension_code, entity_key, window_code, last_seen_at, count_in_window
  )
  SELECT v_household_id, dimension_code, entity_key, window_code,
         max(exposed_at), count(*)::integer
  FROM (
    SELECT 'dish_name'::text AS dimension_code, lower(dish_name) AS entity_key,
           '30d'::text AS window_code, exposed_at
    FROM re_engine.recommendation_item_exposures
    WHERE household_id = v_household_id AND exposed_at >= now() - interval '30 days'
    UNION ALL
    SELECT 'meal_class', meal_class_code, '7d', exposed_at
    FROM re_engine.recommendation_item_exposures
    WHERE household_id = v_household_id AND exposed_at >= now() - interval '7 days'
      AND meal_class_code IS NOT NULL
    UNION ALL
    SELECT 'cuisine', lower(cuisine_family), '7d', exposed_at
    FROM re_engine.recommendation_item_exposures
    WHERE household_id = v_household_id AND exposed_at >= now() - interval '7 days'
      AND cuisine_family IS NOT NULL
  ) dimensions
  GROUP BY dimension_code, entity_key, window_code;

  -- Materialize transparent recent cadence observations. "Debt" is excess over the neutral
  -- midpoint, not a prediction; missing metadata stays absent from the corresponding average.
  WITH recent AS (
    SELECT * FROM re_engine.recommendation_item_exposures
    WHERE household_id = v_household_id AND exposed_at >= now() - interval '7 days'
  ), stats AS (
    SELECT
      count(*)::integer AS exposure_count,
      count(DISTINCT lower(dish_name))::integer AS distinct_dishes,
      avg(coalesce(richness_score, CASE WHEN heaviness IS NOT NULL
        THEN greatest(0, least(1, (heaviness - 1) / 2)) END)) AS mean_richness,
      avg(total_mins) AS mean_effort_minutes,
      avg(CASE WHEN coalesce(richness_score, (heaviness - 1) / 2) <= 0.5
                    AND total_mins <= 45 THEN 1.0 ELSE 0.0 END)
        FILTER (WHERE coalesce(richness_score, heaviness) IS NOT NULL
                  AND total_mins IS NOT NULL) AS ordinary_ratio
    FROM recent
  )
  INSERT INTO re_engine.household_cadence_state (
    household_id, rolling_state, richness_debt, effort_debt, novelty_budget,
    ordinary_meal_ratio, updated_at, feature_version
  )
  SELECT
    v_household_id,
    jsonb_build_object(
      'window', '7d', 'exposure_count', exposure_count,
      'distinct_dishes', distinct_dishes, 'mean_richness', mean_richness,
      'mean_effort_minutes', mean_effort_minutes
    ),
    greatest(0, coalesce(mean_richness, 0) - 0.5),
    greatest(0, coalesce(mean_effort_minutes, 30) / 60.0 - 0.5),
    greatest(0.15, least(0.60, 0.15 + 0.45 *
      (1 - distinct_dishes::real / greatest(exposure_count, 1)))),
    ordinary_ratio,
    now(),
    'recommendation-exposure-v1'
  FROM stats
  ON CONFLICT (household_id) DO UPDATE SET
    rolling_state = EXCLUDED.rolling_state,
    richness_debt = EXCLUDED.richness_debt,
    effort_debt = EXCLUDED.effort_debt,
    novelty_budget = EXCLUDED.novelty_budget,
    ordinary_meal_ratio = EXCLUDED.ordinary_meal_ratio,
    updated_at = EXCLUDED.updated_at,
    feature_version = EXCLUDED.feature_version;

  RETURN true;
END
$function$;

CREATE OR REPLACE FUNCTION public.get_recommendation_variety_state(p_household_id uuid)
RETURNS jsonb
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, public, re_engine
AS $function$
  SELECT jsonb_build_object(
    'recent_dish_names', coalesce((
      SELECT jsonb_agg(dish_name ORDER BY last_seen_at DESC)
      FROM (
        SELECT dish_name, max(exposed_at) AS last_seen_at
        FROM re_engine.recommendation_item_exposures
        WHERE household_id = p_household_id AND exposed_at >= now() - interval '30 days'
        GROUP BY dish_name ORDER BY last_seen_at DESC LIMIT 50
      ) recent
    ), '[]'::jsonb),
    'dimensions', coalesce((
      SELECT jsonb_agg(jsonb_build_object(
        'dimension_code', dimension_code, 'entity_key', entity_key,
        'window_code', window_code, 'last_seen_at', last_seen_at,
        'count_in_window', count_in_window
      ) ORDER BY window_code, dimension_code, count_in_window DESC, entity_key)
      FROM re_engine.variety_window_state WHERE household_id = p_household_id
    ), '[]'::jsonb),
    'cadence', (
      SELECT to_jsonb(c) - 'household_id'
      FROM re_engine.household_cadence_state c WHERE household_id = p_household_id
    )
  );
$function$;

REVOKE ALL ON FUNCTION public.record_recommendation_exposure_state(uuid, jsonb),
  public.get_recommendation_variety_state(uuid) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.record_recommendation_exposure_state(uuid, jsonb),
  public.get_recommendation_variety_state(uuid) TO service_role;

COMMENT ON FUNCTION public.record_recommendation_exposure_state(uuid, jsonb) IS
  'Idempotently persists displayed dishes and rebuilds exact rolling variety/cadence state.';
COMMENT ON FUNCTION public.get_recommendation_variety_state(uuid) IS
  'Private online read model for recent dish exposure and auditable variety/cadence dimensions.';
