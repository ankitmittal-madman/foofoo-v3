BEGIN;

DO $$
DECLARE
  expected_count integer;
  actual_count integer;
BEGIN
  IF to_regclass('food.festivals') IS NULL
    OR to_regclass('food.festival_calendar_occurrences') IS NULL
  THEN
    RAISE EXCEPTION 'normalized festival calendar tables are missing';
  END IF;

  IF has_table_privilege('anon', 'food.festivals', 'SELECT')
    OR has_table_privilege('authenticated', 'food.festivals', 'SELECT')
    OR has_table_privilege('anon', 'food.festival_calendar_occurrences', 'SELECT')
    OR has_table_privilege('authenticated', 'food.festival_calendar_occurrences', 'SELECT')
  THEN
    RAISE EXCEPTION 'normalized festival calendar tables must remain private';
  END IF;

  IF has_function_privilege('anon', 'public.active_festivals_on(date)', 'EXECUTE')
    OR has_function_privilege('authenticated', 'public.active_festivals_on(date)', 'EXECUTE')
    OR NOT has_function_privilege('service_role', 'public.active_festivals_on(date)', 'EXECUTE')
  THEN
    RAISE EXCEPTION 'active_festivals_on must be executable only by service_role';
  END IF;

  SELECT count(*) INTO expected_count
  FROM food.festival_calendar_occurrences AS occurrence
  JOIN food.festivals AS festival ON festival.id = occurrence.festival_id
  WHERE DATE '2026-09-21' BETWEEN occurrence.start_date AND occurrence.end_date
    AND festival.status = 'active';

  SELECT count(*) INTO actual_count
  FROM public.active_festivals_on(DATE '2026-09-21');

  IF expected_count = 0 OR actual_count <> expected_count THEN
    RAISE EXCEPTION 'active_festivals_on returned %, expected non-zero %', actual_count, expected_count;
  END IF;
END $$;

ROLLBACK;
