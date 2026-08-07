DO $$
DECLARE
  v_definition text;
BEGIN
  IF to_regclass('public.recommendation_interactions_v2') IS NULL THEN
    RAISE EXCEPTION 'canonical recommendation interaction view is missing';
  END IF;
  IF has_table_privilege('anon', 'public.recommendation_interactions_v2', 'SELECT') OR
     has_table_privilege('authenticated', 'public.recommendation_interactions_v2', 'SELECT') THEN
    RAISE EXCEPTION 'canonical interaction view must remain service-only';
  END IF;
  IF has_table_privilege('anon', 'public.feedback_events', 'INSERT') OR
     has_table_privilege('authenticated', 'public.feedback_events', 'INSERT') OR
     has_table_privilege('authenticated', 'public.feedback_events', 'UPDATE') OR
     has_table_privilege('authenticated', 'public.feedback_events', 'DELETE') THEN
    RAISE EXCEPTION 'feedback events must be written only through the authenticated Edge boundary';
  END IF;
  IF NOT has_table_privilege('service_role', 'public.recommendation_interactions_v2', 'SELECT') THEN
    RAISE EXCEPTION 'service_role cannot read canonical interactions';
  END IF;
  SELECT pg_get_viewdef('public.recommendation_interactions_v2'::regclass, true)
    INTO v_definition;
  IF position('target_identity_status' IN v_definition) = 0 OR
     position('intended_meal_date' IN v_definition) = 0 OR
     position('evidence_kind' IN v_definition) = 0 THEN
    RAISE EXCEPTION 'canonical view is missing identity, moment, or evidence semantics';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger
    WHERE tgrelid = 'public.feedback_events'::regclass
      AND tgname = 'feedback_events_validate_v2_target' AND NOT tgisinternal
  ) THEN
    RAISE EXCEPTION 'v2 target validation trigger is missing';
  END IF;
END $$;

SELECT schema_version, target_type, target_identity_status, event_type, count(*)
FROM public.recommendation_interactions_v2
GROUP BY schema_version, target_type, target_identity_status, event_type
ORDER BY schema_version, target_type, event_type;
