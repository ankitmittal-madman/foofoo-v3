-- Migration 058 acceptance contract.

SELECT parent_name, month_start
FROM (VALUES ('interaction_events'), ('suggestion_logs')) AS parents(parent_name)
CROSS JOIN LATERAL generate_series(
  date_trunc('month', CURRENT_DATE)::date,
  (date_trunc('month', CURRENT_DATE) + interval '6 months')::date,
  interval '1 month'
) AS months(month_start)
WHERE to_regclass(format(
  'public.%I',
  parent_name || '_' || to_char(month_start, 'YYYY_MM')
)) IS NULL;

SELECT count(*) AS missing_successful_maintenance_run
FROM (SELECT 1) required
WHERE NOT EXISTS (
  SELECT 1
  FROM ops.partition_maintenance_runs
  WHERE status = 'completed'
    AND horizon_end >= (date_trunc('month', CURRENT_DATE) + interval '7 months')::date
);

SELECT count(*) AS public_execute_grants
FROM (VALUES ('anon'), ('authenticated')) AS roles(role_name)
WHERE has_function_privilege(
  role_name,
  'ops.ensure_event_partition_horizon(integer)'::regprocedure,
  'EXECUTE'
);
