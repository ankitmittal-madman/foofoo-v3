BEGIN;

DO $$
DECLARE
  expected_count integer;
  actual_count integer;
BEGIN
  IF has_function_privilege('anon', 'public.active_festivals_on(date)', 'EXECUTE')
    OR has_function_privilege('authenticated', 'public.active_festivals_on(date)', 'EXECUTE')
    OR NOT has_function_privilege('service_role', 'public.active_festivals_on(date)', 'EXECUTE')
  THEN
    RAISE EXCEPTION 'active_festivals_on must be executable only by service_role';
  END IF;

  SELECT count(*) INTO expected_count
  FROM re_engine.re_festival_calendar
  WHERE DATE '2026-10-20' BETWEEN start_date AND end_date;

  SELECT count(*) INTO actual_count
  FROM public.active_festivals_on(DATE '2026-10-20');

  IF actual_count <> expected_count THEN
    RAISE EXCEPTION 'active_festivals_on returned %, expected %', actual_count, expected_count;
  END IF;
END $$;

ROLLBACK;
