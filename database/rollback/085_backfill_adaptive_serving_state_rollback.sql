-- Restore migration 082's lifecycle refresh behavior. Factual exposure rows materialized from
-- durable recommendation_events are intentionally retained: deleting them would make freshness
-- state less truthful and cannot be justified as a schema rollback.

CREATE OR REPLACE FUNCTION public.refresh_user_re_state(p_profile_id uuid)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $function$
DECLARE
  v_interaction_count integer;
  v_weight_tier text;
  v_engine_version text;
  v_result public.user_re_state;
BEGIN
  IF NOT EXISTS (SELECT 1 FROM public.profiles WHERE id = p_profile_id) THEN
    RAISE EXCEPTION 'profile does not exist';
  END IF;

  SELECT count(*)::integer INTO v_interaction_count
  FROM public.feedback_events
  WHERE household_id = p_profile_id
    AND data_source = 'real'
    AND event_type <> 'shown_not_tapped';

  v_weight_tier := CASE
    WHEN v_interaction_count <= 10 THEN 'cold_start'
    WHEN v_interaction_count <= 50 THEN 'early'
    WHEN v_interaction_count <= 150 THEN 'emerging'
    WHEN v_interaction_count <= 500 THEN 'established'
    ELSE 'mature'
  END;

  SELECT engine_version INTO v_engine_version
  FROM public.recommendation_events
  WHERE household_id = p_profile_id AND engine_version IS NOT NULL
  ORDER BY created_at DESC LIMIT 1;

  INSERT INTO public.user_re_state (
    profile_id, interaction_count, cold_start_mode, re_engine_version, weight_tier, updated_at
  ) VALUES (
    p_profile_id, v_interaction_count, v_interaction_count < 14, v_engine_version, v_weight_tier,
    now()
  )
  ON CONFLICT (profile_id) DO UPDATE SET
    interaction_count = EXCLUDED.interaction_count,
    cold_start_mode = EXCLUDED.cold_start_mode,
    re_engine_version = coalesce(EXCLUDED.re_engine_version,
                                 public.user_re_state.re_engine_version),
    weight_tier = EXCLUDED.weight_tier,
    updated_at = EXCLUDED.updated_at
  RETURNING * INTO v_result;

  RETURN to_jsonb(v_result);
END
$function$;

REVOKE ALL ON FUNCTION public.refresh_user_re_state(uuid) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.refresh_user_re_state(uuid) TO service_role;
