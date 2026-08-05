-- Keep append-only event parents writable without relying on a human to create monthly children.

CREATE TABLE IF NOT EXISTS ops.partition_maintenance_runs (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  run_at timestamptz NOT NULL DEFAULT now(),
  months_ahead smallint NOT NULL,
  partitions_created integer NOT NULL,
  horizon_end date NOT NULL,
  status text NOT NULL CHECK (status IN ('completed', 'failed')),
  error_message text
);

ALTER TABLE ops.partition_maintenance_runs ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON ops.partition_maintenance_runs FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT ON ops.partition_maintenance_runs TO service_role;

CREATE OR REPLACE FUNCTION ops.ensure_event_partition_horizon(p_months_ahead integer DEFAULT 6)
RETURNS integer
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog
AS $function$
DECLARE
  month_start date := date_trunc('month', CURRENT_DATE)::date;
  month_offset integer;
  parent_name text;
  partition_name text;
  created_count integer := 0;
BEGIN
  IF p_months_ahead < 2 OR p_months_ahead > 24 THEN
    RAISE EXCEPTION 'p_months_ahead must be between 2 and 24';
  END IF;

  FOREACH parent_name IN ARRAY ARRAY['interaction_events', 'suggestion_logs'] LOOP
    FOR month_offset IN 0..p_months_ahead LOOP
      partition_name := format(
        '%s_%s',
        parent_name,
        to_char(month_start + make_interval(months => month_offset), 'YYYY_MM')
      );
      IF to_regclass(format('public.%I', partition_name)) IS NULL THEN
        EXECUTE format(
          'CREATE TABLE public.%I PARTITION OF public.%I FOR VALUES FROM (%L) TO (%L)',
          partition_name,
          parent_name,
          month_start + make_interval(months => month_offset),
          month_start + make_interval(months => month_offset + 1)
        );
        created_count := created_count + 1;
      END IF;
    END LOOP;
  END LOOP;

  INSERT INTO ops.partition_maintenance_runs (
    months_ahead, partitions_created, horizon_end, status
  ) VALUES (
    p_months_ahead,
    created_count,
    month_start + make_interval(months => p_months_ahead + 1),
    'completed'
  );
  RETURN created_count;
EXCEPTION WHEN OTHERS THEN
  INSERT INTO ops.partition_maintenance_runs (
    months_ahead, partitions_created, horizon_end, status, error_message
  ) VALUES (
    p_months_ahead,
    created_count,
    month_start + make_interval(months => p_months_ahead + 1),
    'failed',
    left(SQLERRM, 1000)
  );
  RAISE;
END
$function$;

REVOKE EXECUTE ON FUNCTION ops.ensure_event_partition_horizon(integer)
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION ops.ensure_event_partition_horizon(integer) TO service_role;

-- Establish a seven-month inclusive horizon immediately.
SELECT ops.ensure_event_partition_horizon(6);

-- Hosted Supabase has pg_cron. Keep clean-room PostgreSQL validation portable by scheduling only
-- when the extension is present. The named schedule is replaced idempotently.
DO $schedule$
DECLARE
  existing_job bigint;
BEGIN
  IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_cron') THEN
    FOR existing_job IN
      SELECT jobid FROM cron.job WHERE jobname = 'foofoo-event-partition-horizon'
    LOOP
      PERFORM cron.unschedule(existing_job);
    END LOOP;
    PERFORM cron.schedule(
      'foofoo-event-partition-horizon',
      '15 0 25 * *',
      'SELECT ops.ensure_event_partition_horizon(6)'
    );
  END IF;
END
$schedule$;
