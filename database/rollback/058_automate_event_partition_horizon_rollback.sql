-- Stop automation but deliberately retain already-created partitions and their possible data.

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
  END IF;
END
$schedule$;

DROP FUNCTION IF EXISTS ops.ensure_event_partition_horizon(integer);
DROP TABLE IF EXISTS ops.partition_maintenance_runs;
