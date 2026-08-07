-- Materialize dated dish/cuisine/richness/cooking-method rhythm for online serving.
-- Taste affinity remains in user_taste_vectors. This state contains only meal-moment outcomes and
-- impressions, so a cold-start Like does not pretend that the dish was eaten on that date.

CREATE VIEW re_engine.current_dish_temporal_attributes AS
SELECT d.id AS dish_id, 'dish'::text AS dimension_code, lower(btrim(d.name)) AS entity_key
FROM public.dishes d
UNION
SELECT d.id, 'cuisine', lower(btrim(c.name))
FROM public.dishes d JOIN public.cuisines c ON c.id = d.cuisine_id
WHERE nullif(btrim(c.name), '') IS NOT NULL
UNION
SELECT DISTINCT cur.dish_id, cur.field_key,
  lower(btrim(value.entity_key))
FROM public.dish_taxonomy_current cur
JOIN public.dish_taxonomy_assertions a ON a.id = cur.assertion_id
LEFT JOIN public.taxonomy_terms t ON t.id = a.term_id
CROSS JOIN LATERAL (
  SELECT t.code AS entity_key WHERE t.code IS NOT NULL
  UNION ALL
  SELECT a.value_text WHERE a.value_text IS NOT NULL
  UNION ALL
  SELECT jsonb_array_elements_text(a.value_json)
    WHERE jsonb_typeof(a.value_json) = 'array'
  UNION ALL
  SELECT a.value_json #>> '{}'
    WHERE jsonb_typeof(a.value_json) IN ('string','number','boolean')
) value
WHERE cur.field_key IN ('richness','cooking_method')
  AND nullif(btrim(value.entity_key), '') IS NOT NULL;

CREATE TABLE re_engine.meal_attribute_exposures (
  recommendation_event_id uuid NOT NULL
    REFERENCES public.recommendation_events(id) ON DELETE CASCADE,
  household_id uuid NOT NULL REFERENCES public.households(id) ON DELETE CASCADE,
  dish_name text NOT NULL CHECK (btrim(dish_name) <> ''),
  dish_id uuid REFERENCES public.dishes(id) ON DELETE SET NULL,
  meal_slot text NOT NULL CHECK (meal_slot IN ('breakfast','lunch','dinner')),
  intended_meal_date date NOT NULL,
  day_type text NOT NULL CHECK (day_type IN ('weekday','weekend')),
  dimension_code text NOT NULL CHECK (
    dimension_code IN ('dish','cuisine','richness','cooking_method')
  ),
  entity_key text NOT NULL CHECK (btrim(entity_key) <> ''),
  shown_rank smallint NOT NULL CHECK (shown_rank > 0),
  exposed_at timestamptz NOT NULL,
  feature_version text NOT NULL DEFAULT 'meal-attribute-temporal-v1',
  PRIMARY KEY (
    recommendation_event_id, dish_name, meal_slot, intended_meal_date,
    dimension_code, entity_key
  )
);

CREATE INDEX meal_attribute_exposures_household_moment
  ON re_engine.meal_attribute_exposures (
    household_id, meal_slot, day_type, intended_meal_date DESC, dimension_code, entity_key
  );

CREATE TABLE re_engine.meal_attribute_temporal_state (
  household_id uuid NOT NULL REFERENCES public.households(id) ON DELETE CASCADE,
  meal_slot text NOT NULL CHECK (meal_slot IN ('breakfast','lunch','dinner')),
  day_type text NOT NULL CHECK (day_type IN ('weekday','weekend')),
  dimension_code text NOT NULL CHECK (
    dimension_code IN ('dish','cuisine','richness','cooking_method')
  ),
  entity_key text NOT NULL CHECK (btrim(entity_key) <> ''),
  explicit_positive_count_28d integer NOT NULL DEFAULT 0
    CHECK (explicit_positive_count_28d >= 0),
  explicit_negative_count_28d integer NOT NULL DEFAULT 0
    CHECK (explicit_negative_count_28d >= 0),
  exposure_count_14d integer NOT NULL DEFAULT 0 CHECK (exposure_count_14d >= 0),
  last_positive_meal_date date,
  last_negative_meal_date date,
  positive_meal_dates_28d date[] NOT NULL DEFAULT '{}',
  negative_meal_dates_28d date[] NOT NULL DEFAULT '{}',
  last_action_at timestamptz,
  last_exposed_meal_date date,
  exposure_meal_dates_14d date[] NOT NULL DEFAULT '{}',
  mean_positive_spacing_days real CHECK (
    mean_positive_spacing_days IS NULL OR mean_positive_spacing_days BETWEEN 0 AND 365
  ),
  updated_at timestamptz NOT NULL DEFAULT now(),
  feature_version text NOT NULL DEFAULT 'meal-attribute-temporal-v1',
  PRIMARY KEY (household_id, meal_slot, day_type, dimension_code, entity_key)
);

REVOKE ALL ON re_engine.current_dish_temporal_attributes,
  re_engine.meal_attribute_exposures,
  re_engine.meal_attribute_temporal_state FROM PUBLIC, anon, authenticated;
GRANT SELECT ON re_engine.current_dish_temporal_attributes TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON re_engine.meal_attribute_exposures,
  re_engine.meal_attribute_temporal_state TO service_role;

CREATE FUNCTION public.refresh_meal_attribute_temporal_state(p_household_id uuid)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public, re_engine
AS $function$
DECLARE
  v_rows integer := 0;
BEGIN
  IF NOT EXISTS (SELECT 1 FROM public.households WHERE id = p_household_id) THEN
    RAISE EXCEPTION 'household does not exist';
  END IF;

  DELETE FROM re_engine.meal_attribute_temporal_state WHERE household_id = p_household_id;

  WITH event_dishes AS (
    -- A dish target, or the primary dish retained alongside an episode target.
    SELECT DISTINCT f.id AS event_id, f.event_type, f.slot AS meal_slot, f.day_type,
      f.intended_meal_date, f.occurred_at, f.dish_id
    FROM public.feedback_events f
    WHERE f.household_id = p_household_id
      AND f.data_source = 'real' AND f.evidence_kind = 'explicit'
      AND f.target_type IN ('dish','meal_episode') AND f.dish_id IS NOT NULL
      AND f.slot IN ('breakfast','lunch','dinner')
      AND f.day_type IN ('weekday','weekend') AND f.intended_meal_date IS NOT NULL

    UNION

    -- Episode snapshots preserve every component that the household acted on, not only its hero.
    SELECT DISTINCT f.id, f.event_type, f.slot, f.day_type, f.intended_meal_date, f.occurred_at, d.id
    FROM public.feedback_events f
    CROSS JOIN LATERAL jsonb_array_elements(
      CASE WHEN jsonb_typeof(f.target_snapshot->'components') = 'array'
        THEN f.target_snapshot->'components' ELSE '[]'::jsonb END
    ) component
    JOIN public.dishes d ON lower(d.name) = lower(component->>'dish_name')
    WHERE f.household_id = p_household_id
      AND f.data_source = 'real' AND f.evidence_kind = 'explicit'
      AND f.target_type = 'meal_episode'
      AND f.slot IN ('breakfast','lunch','dinner')
      AND f.day_type IN ('weekday','weekend') AND f.intended_meal_date IS NOT NULL
  ), snapshot_components AS (
    SELECT DISTINCT f.id AS event_id, d.id AS dish_id, component
    FROM public.feedback_events f
    CROSS JOIN LATERAL jsonb_array_elements(
      CASE WHEN jsonb_typeof(f.target_snapshot->'components') = 'array'
        THEN f.target_snapshot->'components' ELSE '[]'::jsonb END
    ) component
    JOIN public.dishes d ON lower(d.name) = lower(component->>'dish_name')
    WHERE f.household_id = p_household_id AND f.target_type = 'meal_episode'
  ), snapshot_attributes AS (
    -- Preserve the attributes that were actually served. Current ontology is only a fallback for
    -- legacy events whose point-in-time episode snapshot did not carry a dimension.
    SELECT event_id, dish_id, 'dish'::text AS dimension_code,
      lower(btrim(component->>'dish_name')) AS entity_key
    FROM snapshot_components
    UNION
    SELECT event_id, dish_id, 'cuisine', lower(btrim(component->>'cuisine'))
    FROM snapshot_components WHERE nullif(btrim(component->>'cuisine'), '') IS NOT NULL
    UNION
    SELECT event_id, dish_id, 'richness', lower(btrim(value))
    FROM snapshot_components CROSS JOIN LATERAL jsonb_array_elements_text(
      CASE WHEN jsonb_typeof(component->'richness') = 'array'
        THEN component->'richness' ELSE '[]'::jsonb END
    ) value
    UNION
    SELECT event_id, dish_id, 'cooking_method', lower(btrim(value))
    FROM snapshot_components CROSS JOIN LATERAL jsonb_array_elements_text(
      CASE WHEN jsonb_typeof(component->'cooking_method') = 'array'
        THEN component->'cooking_method' ELSE '[]'::jsonb END
    ) value
  ), explicit_signals AS (
    SELECT e.meal_slot, e.day_type, a.dimension_code, a.entity_key,
      e.intended_meal_date, e.occurred_at,
      CASE
        WHEN e.event_type IN ('accept','make_this','cooked','ordered','replaced','completed','selected')
          THEN 1
        WHEN e.event_type IN ('dislike','never','regretted') THEN -1
        ELSE 0
      END AS direction
    FROM event_dishes e
    JOIN re_engine.current_dish_temporal_attributes a ON a.dish_id = e.dish_id
    WHERE NOT EXISTS (
      SELECT 1 FROM snapshot_attributes s
      WHERE s.event_id = e.event_id AND s.dish_id = e.dish_id
        AND s.dimension_code = a.dimension_code
    )

    UNION ALL

    SELECT e.meal_slot, e.day_type, a.dimension_code, a.entity_key,
      e.intended_meal_date, e.occurred_at,
      CASE
        WHEN e.event_type IN ('accept','make_this','cooked','ordered','replaced','completed','selected')
          THEN 1
        WHEN e.event_type IN ('dislike','never','regretted') THEN -1
        ELSE 0
      END AS direction
    FROM event_dishes e
    JOIN snapshot_attributes a ON a.event_id = e.event_id AND a.dish_id = e.dish_id
  ), dated_positive AS (
    SELECT DISTINCT meal_slot, day_type, dimension_code, entity_key, intended_meal_date
    FROM explicit_signals
    WHERE direction > 0 AND occurred_at >= now() - interval '90 days'
  ), spacing AS (
    SELECT meal_slot, day_type, dimension_code, entity_key,
      avg(intended_meal_date - prior_date)::real AS mean_spacing
    FROM (
      SELECT *, lag(intended_meal_date) OVER (
        PARTITION BY meal_slot, day_type, dimension_code, entity_key
        ORDER BY intended_meal_date
      ) AS prior_date
      FROM dated_positive
    ) intervals
    WHERE prior_date IS NOT NULL
    GROUP BY meal_slot, day_type, dimension_code, entity_key
  ), explicit_stats AS (
    SELECT meal_slot, day_type, dimension_code, entity_key,
      count(*) FILTER (
        WHERE direction > 0 AND occurred_at >= now() - interval '28 days'
      )::integer AS positive_count,
      count(*) FILTER (
        WHERE direction < 0 AND occurred_at >= now() - interval '28 days'
      )::integer AS negative_count,
      max(intended_meal_date) FILTER (WHERE direction > 0) AS last_positive_date,
      max(intended_meal_date) FILTER (WHERE direction < 0) AS last_negative_date,
      array_agg(DISTINCT intended_meal_date ORDER BY intended_meal_date) FILTER (
        WHERE direction > 0 AND occurred_at >= now() - interval '28 days'
      ) AS positive_dates,
      array_agg(DISTINCT intended_meal_date ORDER BY intended_meal_date) FILTER (
        WHERE direction < 0 AND occurred_at >= now() - interval '28 days'
      ) AS negative_dates,
      max(occurred_at) AS last_action_at
    FROM explicit_signals
    WHERE direction <> 0
    GROUP BY meal_slot, day_type, dimension_code, entity_key
  ), exposure_stats AS (
    SELECT meal_slot, day_type, dimension_code, entity_key,
      count(*) FILTER (WHERE exposed_at >= now() - interval '14 days')::integer AS exposure_count,
      max(intended_meal_date) AS last_exposed_date,
      array_agg(DISTINCT intended_meal_date ORDER BY intended_meal_date) FILTER (
        WHERE exposed_at >= now() - interval '14 days'
      ) AS exposure_dates
    FROM re_engine.meal_attribute_exposures
    WHERE household_id = p_household_id
    GROUP BY meal_slot, day_type, dimension_code, entity_key
  ), keys AS (
    SELECT meal_slot, day_type, dimension_code, entity_key FROM explicit_stats
    UNION
    SELECT meal_slot, day_type, dimension_code, entity_key FROM exposure_stats
  )
  INSERT INTO re_engine.meal_attribute_temporal_state (
    household_id, meal_slot, day_type, dimension_code, entity_key,
    explicit_positive_count_28d, explicit_negative_count_28d, exposure_count_14d,
    last_positive_meal_date, last_negative_meal_date,
    positive_meal_dates_28d, negative_meal_dates_28d, last_action_at,
    last_exposed_meal_date, exposure_meal_dates_14d, mean_positive_spacing_days
  )
  SELECT p_household_id, k.meal_slot, k.day_type, k.dimension_code, k.entity_key,
    coalesce(es.positive_count, 0), coalesce(es.negative_count, 0),
    coalesce(xs.exposure_count, 0), es.last_positive_date, es.last_negative_date,
    coalesce(es.positive_dates, '{}'), coalesce(es.negative_dates, '{}'), es.last_action_at,
    xs.last_exposed_date, coalesce(xs.exposure_dates, '{}'), sp.mean_spacing
  FROM keys k
  LEFT JOIN explicit_stats es USING (meal_slot, day_type, dimension_code, entity_key)
  LEFT JOIN exposure_stats xs USING (meal_slot, day_type, dimension_code, entity_key)
  LEFT JOIN spacing sp USING (meal_slot, day_type, dimension_code, entity_key);
  GET DIAGNOSTICS v_rows = ROW_COUNT;

  RETURN jsonb_build_object(
    'household_id', p_household_id, 'state_rows', v_rows,
    'feature_version', 'meal-attribute-temporal-v1', 'updated_at', now()
  );
END
$function$;

CREATE FUNCTION public.record_meal_attribute_exposure_state(
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
  IF jsonb_typeof(p_items) <> 'array' THEN RAISE EXCEPTION 'p_items must be a JSON array'; END IF;
  SELECT household_id, created_at INTO v_household_id, v_exposed_at
  FROM public.recommendation_events WHERE id = p_recommendation_event_id;
  IF v_household_id IS NULL THEN RAISE EXCEPTION 'recommendation event does not exist'; END IF;

  WITH parsed AS (
    SELECT ordinality::integer AS shown_rank, item,
      nullif(btrim(item->>'dish_name'), '') AS supplied_name,
      nullif(btrim(item->>'cuisine'), '') AS supplied_cuisine,
      item->>'meal_slot' AS meal_slot,
      item->>'day_type' AS day_type,
      CASE WHEN item->>'intended_meal_date' ~ '^\d{4}-\d{2}-\d{2}$'
        THEN (item->>'intended_meal_date')::date END AS intended_meal_date
    FROM jsonb_array_elements(p_items) WITH ORDINALITY source(item, ordinality)
  ), resolved AS (
    SELECT p.*, d.id AS dish_id, coalesce(d.name, p.supplied_name) AS dish_name,
      c.name AS database_cuisine
    FROM parsed p
    LEFT JOIN public.dishes d ON lower(d.name) = lower(p.supplied_name)
    LEFT JOIN public.cuisines c ON c.id = d.cuisine_id
    WHERE p.supplied_name IS NOT NULL
      AND p.meal_slot IN ('breakfast','lunch','dinner')
      AND p.day_type IN ('weekday','weekend')
      AND p.intended_meal_date IS NOT NULL
      AND p.day_type = CASE WHEN extract(isodow FROM p.intended_meal_date) >= 6
        THEN 'weekend' ELSE 'weekday' END
  ), supplied_attributes AS (
    SELECT r.*, 'dish'::text AS dimension_code, lower(btrim(r.dish_name)) AS entity_key
    FROM resolved r
    UNION ALL
    SELECT r.*, 'cuisine', lower(btrim(coalesce(r.supplied_cuisine, r.database_cuisine)))
    FROM resolved r WHERE coalesce(r.supplied_cuisine, r.database_cuisine) IS NOT NULL
    UNION ALL
    SELECT r.*, 'richness', lower(btrim(value))
    FROM resolved r CROSS JOIN LATERAL jsonb_array_elements_text(
      CASE WHEN jsonb_typeof(r.item->'richness') = 'array'
        THEN r.item->'richness' ELSE '[]'::jsonb END
    ) value
    UNION ALL
    SELECT r.*, 'cooking_method', lower(btrim(value))
    FROM resolved r CROSS JOIN LATERAL jsonb_array_elements_text(
      CASE WHEN jsonb_typeof(r.item->'cooking_method') = 'array'
        THEN r.item->'cooking_method' ELSE '[]'::jsonb END
    ) value
  ), attributes AS (
    SELECT * FROM supplied_attributes WHERE nullif(entity_key, '') IS NOT NULL
    UNION
    SELECT r.*, a.dimension_code, a.entity_key
    FROM resolved r
    JOIN re_engine.current_dish_temporal_attributes a ON a.dish_id = r.dish_id
    WHERE a.dimension_code IN ('richness','cooking_method')
      AND NOT EXISTS (
        SELECT 1 FROM supplied_attributes supplied
        WHERE supplied.shown_rank = r.shown_rank
          AND supplied.dimension_code = a.dimension_code
      )
  )
  INSERT INTO re_engine.meal_attribute_exposures (
    recommendation_event_id, household_id, dish_name, dish_id, meal_slot,
    intended_meal_date, day_type, dimension_code, entity_key, shown_rank, exposed_at
  )
  SELECT p_recommendation_event_id, v_household_id, dish_name, dish_id, meal_slot,
    intended_meal_date, day_type, dimension_code, entity_key, shown_rank, v_exposed_at
  FROM attributes
  ON CONFLICT DO NOTHING;
  GET DIAGNOSTICS v_inserted = ROW_COUNT;

  IF v_inserted > 0 THEN
    DELETE FROM re_engine.meal_attribute_exposures
    WHERE household_id = v_household_id AND exposed_at < now() - interval '30 days';
    PERFORM public.refresh_meal_attribute_temporal_state(v_household_id);
  END IF;
  RETURN v_inserted > 0;
END
$function$;

CREATE FUNCTION public.get_meal_attribute_temporal_state(p_household_id uuid)
RETURNS jsonb
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, public, re_engine
AS $function$
  SELECT coalesce(jsonb_agg(to_jsonb(s) - 'household_id' - 'updated_at'
    ORDER BY meal_slot, day_type, dimension_code, entity_key), '[]'::jsonb)
  FROM (
    SELECT * FROM re_engine.meal_attribute_temporal_state
    WHERE household_id = p_household_id
    ORDER BY greatest(last_action_at, last_exposed_meal_date::timestamptz) DESC NULLS LAST,
      meal_slot, day_type, dimension_code, entity_key
    LIMIT 1000
  ) s;
$function$;

REVOKE ALL ON FUNCTION public.refresh_meal_attribute_temporal_state(uuid),
  public.record_meal_attribute_exposure_state(uuid, jsonb),
  public.get_meal_attribute_temporal_state(uuid) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.refresh_meal_attribute_temporal_state(uuid),
  public.record_meal_attribute_exposure_state(uuid, jsonb),
  public.get_meal_attribute_temporal_state(uuid) TO service_role;

-- Dated planning actions require a complete and internally consistent meal moment. Preference-only
-- calibration/search events may remain intentionally undated.
CREATE OR REPLACE FUNCTION public.validate_recommendation_meal_moment()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog, public
AS $function$
DECLARE
  v_weekday text;
  v_day_type text;
  v_requires_moment boolean;
BEGIN
  IF NEW.schema_version <> '2' THEN RETURN NEW; END IF;
  v_requires_moment := NEW.target_type = 'meal_class' OR (
    NEW.target_type IN ('dish','meal_episode') AND NEW.source_surface IN (
      'today','today_meal_episode','meal_plan','class_dishes','weekly_plan'
    )
  );
  IF NOT v_requires_moment THEN RETURN NEW; END IF;
  IF NEW.intended_meal_date IS NULL OR NEW.weekday IS NULL OR NEW.day_type IS NULL THEN
    RAISE EXCEPTION 'planned meal interaction requires intended date, weekday and day type';
  END IF;
  v_weekday := to_char(NEW.intended_meal_date, 'FMDay');
  v_day_type := CASE WHEN extract(isodow FROM NEW.intended_meal_date) >= 6
    THEN 'weekend' ELSE 'weekday' END;
  IF NEW.weekday <> v_weekday OR NEW.day_type <> v_day_type THEN
    RAISE EXCEPTION 'meal moment date, weekday and day type disagree';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_catalog.pg_timezone_names WHERE name = NEW.local_timezone) THEN
    RAISE EXCEPTION 'meal moment timezone is not recognized';
  END IF;
  RETURN NEW;
END
$function$;

COMMENT ON VIEW re_engine.current_dish_temporal_attributes IS
  'Canonical private projection used to replay dish feedback into cuisine/richness/method rhythm.';
COMMENT ON TABLE re_engine.meal_attribute_temporal_state IS
  'Private dated rhythm by household, meal slot, weekday/weekend, and food dimension; exposure is not acceptance.';
COMMENT ON FUNCTION public.get_meal_attribute_temporal_state(uuid) IS
  'Returns at most 1000 recent, replayable food-rhythm rows for private online composition.';

DO $backfill$
DECLARE
  v_household_id uuid;
BEGIN
  FOR v_household_id IN
    SELECT DISTINCT household_id FROM public.feedback_events
    WHERE data_source = 'real' AND target_type IN ('dish','meal_episode')
      AND intended_meal_date IS NOT NULL
  LOOP
    PERFORM public.refresh_meal_attribute_temporal_state(v_household_id);
  END LOOP;
END
$backfill$;
