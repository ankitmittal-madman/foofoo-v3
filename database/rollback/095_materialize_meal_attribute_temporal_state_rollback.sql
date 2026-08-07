DROP FUNCTION IF EXISTS public.get_meal_attribute_temporal_state(uuid);
DROP FUNCTION IF EXISTS public.record_meal_attribute_exposure_state(uuid, jsonb);
DROP FUNCTION IF EXISTS public.refresh_meal_attribute_temporal_state(uuid);
DROP TABLE IF EXISTS re_engine.meal_attribute_temporal_state;
DROP TABLE IF EXISTS re_engine.meal_attribute_exposures;
DROP VIEW IF EXISTS re_engine.current_dish_temporal_attributes;

-- Restore migration 094's class-only meal-moment validator.
CREATE OR REPLACE FUNCTION public.validate_recommendation_meal_moment()
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
