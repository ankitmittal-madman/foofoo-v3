-- Aggregate-only migration 096 validation. Returns no household values or identities.
SELECT
  to_regclass('re_engine.governed_context_signals') IS NOT NULL AS table_exists,
  to_regprocedure('public.materialize_governed_context_signals(uuid,jsonb)') IS NOT NULL
    AS materialize_rpc_exists,
  to_regprocedure('public.get_governed_context_signals(uuid)') IS NOT NULL
    AS read_rpc_exists,
  to_regprocedure('public.correct_governed_context_signal(uuid,text,text,jsonb)') IS NOT NULL
    AS correction_rpc_exists;

SELECT authority, allowed_use, count(*) AS row_count
FROM re_engine.governed_context_signals
GROUP BY authority, allowed_use
ORDER BY authority, allowed_use;

SELECT
  count(*) FILTER (WHERE confidence NOT BETWEEN 0 AND 1) AS invalid_confidence,
  count(*) FILTER (WHERE authority = 'inferred' AND confidence > 0.70) AS overpowered_inference,
  count(*) FILTER (WHERE authority = 'inferred' AND expires_at IS NULL) AS unexpiring_inference,
  count(*) FILTER (WHERE feature_code NOT IN (
    'health_objective','working_professionals','weekday_time_pressure'
  )) AS unsupported_features
FROM re_engine.governed_context_signals;

SELECT grantee, privilege_type
FROM information_schema.role_table_grants
WHERE table_schema = 're_engine' AND table_name = 'governed_context_signals'
ORDER BY grantee, privilege_type;
