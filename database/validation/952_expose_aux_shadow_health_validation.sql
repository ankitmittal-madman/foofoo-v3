DO $$
BEGIN
  IF to_regprocedure(
    're_engine.aux_shadow_health(timestamp with time zone,timestamp with time zone)'
  ) IS NULL THEN
    RAISE EXCEPTION 're_engine.aux_shadow_health is missing';
  END IF;
  IF has_function_privilege(
    'anon',
    're_engine.aux_shadow_health(timestamp with time zone,timestamp with time zone)',
    'EXECUTE'
  ) OR has_function_privilege(
    'authenticated',
    're_engine.aux_shadow_health(timestamp with time zone,timestamp with time zone)',
    'EXECUTE'
  ) THEN
    RAISE EXCEPTION 'Aux shadow health must remain service-only';
  END IF;
END $$;

SELECT *
FROM re_engine.aux_shadow_health(now() - interval '1 day', now());
