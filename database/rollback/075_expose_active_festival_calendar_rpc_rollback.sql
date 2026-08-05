DROP FUNCTION IF EXISTS public.active_festivals_on(date);
DROP TABLE IF EXISTS food.festival_calendar_occurrences;
DROP TABLE IF EXISTS food.festivals;
DELETE FROM ops.data_sources WHERE source_code = 'foofoo_legacy_festival_calendar_2026';
