-- Normalize the governed festival calendar into the target `food` schema and expose only the
-- narrow date lookup needed by Edge Functions. The retired re_engine calendar is deliberately
-- not recreated.

CREATE TABLE IF NOT EXISTS food.festivals (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  festival_code text NOT NULL UNIQUE,
  name text NOT NULL,
  region_scope_code text NOT NULL DEFAULT 'IN',
  calendar_system_code text NOT NULL DEFAULT 'gregorian_occurrence',
  source_id uuid NOT NULL REFERENCES ops.data_sources(id) ON DELETE RESTRICT,
  confidence numeric(4,3) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
  status text NOT NULL DEFAULT 'active' CHECK (status IN ('draft', 'active', 'retired')),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS food.festival_calendar_occurrences (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  festival_id uuid NOT NULL REFERENCES food.festivals(id) ON DELETE RESTRICT,
  region_scope_code text NOT NULL DEFAULT 'IN',
  start_date date NOT NULL,
  end_date date NOT NULL,
  source_id uuid NOT NULL REFERENCES ops.data_sources(id) ON DELETE RESTRICT,
  confidence numeric(4,3) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK (end_date >= start_date),
  UNIQUE (festival_id, region_scope_code, start_date, source_id)
);

CREATE INDEX IF NOT EXISTS festival_occurrences_active_dates
  ON food.festival_calendar_occurrences (start_date, end_date, region_scope_code);

REVOKE ALL ON food.festivals, food.festival_calendar_occurrences
  FROM PUBLIC, anon, authenticated;

INSERT INTO ops.data_sources (
  source_code, owner_name, license_code, source_uri, retrieved_at, checksum, permitted_uses
)
VALUES (
  'foofoo_legacy_festival_calendar_2026',
  'Foofoo',
  'internal',
  'database/archive/re_engine_backup_20260803/re_festival_calendar.json',
  TIMESTAMPTZ '2026-08-03 00:00:00+00',
  'legacy-calendar-2026-v1',
  ARRAY['recommendation_context', 'internal_research']::text[]
)
ON CONFLICT (source_code) DO NOTHING;

INSERT INTO food.festivals (
  festival_code, name, region_scope_code, calendar_system_code, source_id, confidence
)
SELECT seed.festival_code, seed.name, 'IN', 'gregorian_occurrence', source.id, 0.700
FROM (
  VALUES
    ('diwali', 'Diwali'),
    ('navratri', 'Navratri')
) AS seed(festival_code, name)
CROSS JOIN ops.data_sources AS source
WHERE source.source_code = 'foofoo_legacy_festival_calendar_2026'
ON CONFLICT (festival_code) DO NOTHING;

INSERT INTO food.festival_calendar_occurrences (
  festival_id, region_scope_code, start_date, end_date, source_id, confidence
)
SELECT festival.id, 'IN', seed.start_date, seed.end_date, source.id, 0.700
FROM (
  VALUES
    ('diwali', DATE '2026-11-08', DATE '2026-11-09'),
    ('navratri', DATE '2026-09-21', DATE '2026-09-29')
) AS seed(festival_code, start_date, end_date)
JOIN food.festivals AS festival ON festival.festival_code = seed.festival_code
CROSS JOIN ops.data_sources AS source
WHERE source.source_code = 'foofoo_legacy_festival_calendar_2026'
ON CONFLICT (festival_id, region_scope_code, start_date, source_id) DO NOTHING;

CREATE OR REPLACE FUNCTION public.active_festivals_on(p_date date)
RETURNS TABLE (
  festival_name text,
  start_date date,
  end_date date
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, food
AS $function$
  SELECT f.festival_code || '_' || extract(year FROM o.start_date)::integer::text,
         o.start_date,
         o.end_date
  FROM food.festival_calendar_occurrences AS o
  JOIN food.festivals AS f ON f.id = o.festival_id
  WHERE p_date BETWEEN o.start_date AND o.end_date
    AND f.status = 'active'
  ORDER BY f.festival_code
$function$;

REVOKE ALL ON FUNCTION public.active_festivals_on(date) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.active_festivals_on(date) TO service_role;
