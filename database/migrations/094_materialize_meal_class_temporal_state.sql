-- Materialize meal-class rhythm by meal moment and weekday/weekend type.
-- Explicit selections and outcomes remain distinct from impressions: exposure can add repetition
-- pressure, but only explicit class events teach acceptance/rejection or learned spacing.

CREATE FUNCTION public.validate_recommendation_meal_moment()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog, public
AS $function$
DECLARE
  v_weekday text;
  v_day_type text;
BEGIN
  IF NEW.schema_version <> '2' OR NEW.target_type <> 'meal_class' THEN RETURN NEW; END IF;
  IF NEW.intended_meal_date IS NULL OR NEW.weekday IS NULL OR NEW.day_type IS NULL THEN
    RAISE EXCEPTION 'meal_class interaction requires intended date, weekday and day type';
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

CREATE TRIGGER feedback_events_validate_meal_moment
  BEFORE INSERT OR UPDATE OF schema_version,target_type,intended_meal_date,weekday,day_type,local_timezone
  ON public.feedback_events
  FOR EACH ROW EXECUTE FUNCTION public.validate_recommendation_meal_moment();

CREATE TABLE re_engine.meal_class_exposures (
  recommendation_event_id uuid NOT NULL
    REFERENCES public.recommendation_events(id) ON DELETE CASCADE,
  household_id uuid NOT NULL REFERENCES public.households(id) ON DELETE CASCADE,
  class_code text NOT NULL REFERENCES public.meal_classes(class_code),
  meal_slot text NOT NULL CHECK (meal_slot IN ('breakfast','lunch','dinner')),
  intended_meal_date date NOT NULL,
  day_type text NOT NULL CHECK (day_type IN ('weekday','weekend')),
  shown_rank smallint NOT NULL CHECK (shown_rank > 0),
  exposed_at timestamptz NOT NULL,
  feature_version text NOT NULL DEFAULT 'meal-class-temporal-v1',
  PRIMARY KEY (recommendation_event_id, class_code, meal_slot, intended_meal_date)
);

CREATE INDEX meal_class_exposures_household_moment
  ON re_engine.meal_class_exposures
    (household_id, meal_slot, day_type, intended_meal_date DESC, class_code);

CREATE TABLE re_engine.meal_class_temporal_state (
  household_id uuid NOT NULL REFERENCES public.households(id) ON DELETE CASCADE,
  meal_slot text NOT NULL CHECK (meal_slot IN ('breakfast','lunch','dinner')),
  day_type text NOT NULL CHECK (day_type IN ('weekday','weekend')),
  class_code text NOT NULL REFERENCES public.meal_classes(class_code),
  explicit_positive_count_28d integer NOT NULL DEFAULT 0 CHECK (explicit_positive_count_28d >= 0),
  explicit_negative_count_28d integer NOT NULL DEFAULT 0 CHECK (explicit_negative_count_28d >= 0),
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
  feature_version text NOT NULL DEFAULT 'meal-class-temporal-v1',
  PRIMARY KEY (household_id, meal_slot, day_type, class_code)
);

REVOKE ALL ON TABLE re_engine.meal_class_exposures,
  re_engine.meal_class_temporal_state FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE re_engine.meal_class_exposures,
  re_engine.meal_class_temporal_state TO service_role;

CREATE FUNCTION public.refresh_meal_class_temporal_state(p_household_id uuid)
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

  DELETE FROM re_engine.meal_class_temporal_state WHERE household_id = p_household_id;

  WITH explicit_signals AS (
    SELECT
      f.slot AS meal_slot,
      f.day_type,
      f.target_id AS class_code,
      f.intended_meal_date,
      f.occurred_at,
      CASE
        WHEN f.event_type IN ('selected','lock','accept','make_this','replaced','completed') THEN 1
        WHEN f.event_type IN ('dislike','never') THEN -1
        ELSE 0
      END AS direction
    FROM public.feedback_events f
    WHERE f.household_id = p_household_id
      AND f.data_source = 'real'
      AND f.evidence_kind = 'explicit'
      AND f.target_type = 'meal_class'
      AND f.target_identity_status = 'resolved'
      AND f.slot IN ('breakfast','lunch','dinner')
      AND f.day_type IN ('weekday','weekend')
      AND f.intended_meal_date IS NOT NULL

    UNION ALL

    SELECT
      f.slot,
      f.day_type,
      f.detail #>> '{replacement,from,target_id}',
      f.intended_meal_date,
      f.occurred_at,
      -1
    FROM public.feedback_events f
    WHERE f.household_id = p_household_id
      AND f.data_source = 'real'
      AND f.evidence_kind = 'explicit'
      AND f.event_type = 'replaced'
      AND f.detail #>> '{replacement,from,target_type}' = 'meal_class'
      AND f.detail #>> '{replacement,from,target_identity_status}' = 'resolved'
      AND f.slot IN ('breakfast','lunch','dinner')
      AND f.day_type IN ('weekday','weekend')
      AND f.intended_meal_date IS NOT NULL
  ), dated_positive AS (
    SELECT DISTINCT meal_slot, day_type, class_code, intended_meal_date
    FROM explicit_signals
    WHERE direction > 0 AND occurred_at >= now() - interval '90 days'
  ), spacing AS (
    SELECT meal_slot, day_type, class_code,
      avg(intended_meal_date - prior_date)::real AS mean_spacing
    FROM (
      SELECT *, lag(intended_meal_date) OVER (
        PARTITION BY meal_slot, day_type, class_code ORDER BY intended_meal_date
      ) AS prior_date
      FROM dated_positive
    ) intervals
    WHERE prior_date IS NOT NULL
    GROUP BY meal_slot, day_type, class_code
  ), explicit_stats AS (
    SELECT meal_slot, day_type, class_code,
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
    WHERE class_code IS NOT NULL AND direction <> 0
    GROUP BY meal_slot, day_type, class_code
  ), exposure_stats AS (
    SELECT meal_slot, day_type, class_code,
      count(*) FILTER (WHERE exposed_at >= now() - interval '14 days')::integer AS exposure_count,
      max(intended_meal_date) AS last_exposed_date,
      array_agg(DISTINCT intended_meal_date ORDER BY intended_meal_date) FILTER (
        WHERE exposed_at >= now() - interval '14 days'
      ) AS exposure_dates
    FROM re_engine.meal_class_exposures
    WHERE household_id = p_household_id
    GROUP BY meal_slot, day_type, class_code
  ), keys AS (
    SELECT meal_slot, day_type, class_code FROM explicit_stats
    UNION
    SELECT meal_slot, day_type, class_code FROM exposure_stats
  )
  INSERT INTO re_engine.meal_class_temporal_state (
    household_id, meal_slot, day_type, class_code,
    explicit_positive_count_28d, explicit_negative_count_28d, exposure_count_14d,
    last_positive_meal_date, last_negative_meal_date,
    positive_meal_dates_28d, negative_meal_dates_28d, last_action_at,
    last_exposed_meal_date, exposure_meal_dates_14d, mean_positive_spacing_days
  )
  SELECT p_household_id, k.meal_slot, k.day_type, k.class_code,
    coalesce(es.positive_count, 0), coalesce(es.negative_count, 0),
    coalesce(xs.exposure_count, 0), es.last_positive_date, es.last_negative_date,
    coalesce(es.positive_dates, '{}'), coalesce(es.negative_dates, '{}'),
    es.last_action_at, xs.last_exposed_date, coalesce(xs.exposure_dates, '{}'), sp.mean_spacing
  FROM keys k
  JOIN public.meal_classes c ON c.class_code = k.class_code AND c.is_active
  LEFT JOIN explicit_stats es USING (meal_slot, day_type, class_code)
  LEFT JOIN exposure_stats xs USING (meal_slot, day_type, class_code)
  LEFT JOIN spacing sp USING (meal_slot, day_type, class_code);
  GET DIAGNOSTICS v_rows = ROW_COUNT;

  RETURN jsonb_build_object(
    'household_id', p_household_id,
    'state_rows', v_rows,
    'feature_version', 'meal-class-temporal-v1',
    'updated_at', now()
  );
END
$function$;

CREATE FUNCTION public.record_meal_class_exposure_state(
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

  INSERT INTO re_engine.meal_class_exposures (
    recommendation_event_id, household_id, class_code, meal_slot,
    intended_meal_date, day_type, shown_rank, exposed_at
  )
  SELECT p_recommendation_event_id, v_household_id,
    item->>'class_code', item->>'meal_slot', (item->>'intended_meal_date')::date,
    item->>'day_type', (item->>'shown_rank')::smallint, v_exposed_at
  FROM jsonb_array_elements(p_items) item
  JOIN public.meal_classes c ON c.class_code = item->>'class_code' AND c.is_active
  WHERE item->>'meal_slot' IN ('breakfast','lunch','dinner')
    AND item->>'day_type' IN ('weekday','weekend')
    AND item->>'intended_meal_date' ~ '^\d{4}-\d{2}-\d{2}$'
    AND (item->>'shown_rank') ~ '^\d+$'
    AND (item->>'shown_rank')::integer > 0
  ON CONFLICT DO NOTHING;
  GET DIAGNOSTICS v_inserted = ROW_COUNT;

  IF v_inserted > 0 THEN
    PERFORM public.refresh_meal_class_temporal_state(v_household_id);
  END IF;
  RETURN v_inserted > 0;
END
$function$;

CREATE FUNCTION public.get_meal_class_temporal_state(p_household_id uuid)
RETURNS jsonb
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, public, re_engine
AS $function$
  SELECT coalesce(jsonb_agg(
    to_jsonb(s) - 'household_id' - 'updated_at'
    ORDER BY meal_slot, day_type, class_code
  ), '[]'::jsonb)
  FROM re_engine.meal_class_temporal_state s
  WHERE household_id = p_household_id;
$function$;

REVOKE ALL ON FUNCTION public.refresh_meal_class_temporal_state(uuid),
  public.record_meal_class_exposure_state(uuid, jsonb),
  public.get_meal_class_temporal_state(uuid) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.refresh_meal_class_temporal_state(uuid),
  public.record_meal_class_exposure_state(uuid, jsonb),
  public.get_meal_class_temporal_state(uuid) TO service_role;

COMMENT ON TABLE re_engine.meal_class_temporal_state IS
  'Private, replayable class rhythm by household, meal slot and weekday/weekend; exposure is not acceptance.';
COMMENT ON FUNCTION public.get_meal_class_temporal_state(uuid) IS
  'Returns bounded class spacing state for private online recommendation composition.';

DO $backfill$
DECLARE
  v_household_id uuid;
BEGIN
  FOR v_household_id IN
    SELECT DISTINCT household_id FROM public.feedback_events
    WHERE data_source = 'real' AND target_type = 'meal_class'
  LOOP
    PERFORM public.refresh_meal_class_temporal_state(v_household_id);
  END LOOP;
END
$backfill$;
