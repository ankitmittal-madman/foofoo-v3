-- Govern explicit and inferred recommendation context without converting hypotheses into facts.
-- Safety remains owned by explicit diet/allergen/Jain rules. These rows are ranking context only.

CREATE TABLE re_engine.governed_context_signals (
  household_id uuid NOT NULL REFERENCES public.households(id) ON DELETE CASCADE,
  feature_code text NOT NULL CHECK (
    feature_code IN ('health_objective','working_professionals','weekday_time_pressure')
  ),
  feature_value jsonb NOT NULL,
  authority text NOT NULL CHECK (authority IN ('explicit','inferred')),
  confidence real NOT NULL CHECK (confidence BETWEEN 0 AND 1),
  sources text[] NOT NULL CHECK (
    cardinality(sources) BETWEEN 1 AND 8
    AND sources <@ ARRAY[
      'q1_household_type','q2_working_professionals','q12_member_ages',
      'q13_who_cooks','q15_objective','observed_quick_meal_ratio'
    ]::text[]
  ),
  allowed_use text NOT NULL CHECK (allowed_use IN ('strong_rank','soft_rank','context_input')),
  created_at timestamptz NOT NULL DEFAULT now(),
  observed_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz,
  correction_state text NOT NULL DEFAULT 'active'
    CHECK (correction_state IN ('active','confirmed','rejected')),
  corrected_value jsonb,
  corrected_at timestamptz,
  corrected_by uuid REFERENCES auth.users(id) ON DELETE SET NULL,
  feature_version text NOT NULL DEFAULT 'governed-context-v1',
  PRIMARY KEY (household_id, feature_code),
  CHECK (
    (authority = 'explicit' AND confidence = 1 AND expires_at IS NULL)
    OR (authority = 'inferred' AND confidence <= 0.70 AND expires_at IS NOT NULL)
  ),
  CHECK (
    (feature_code = 'health_objective' AND authority = 'explicit'
      AND allowed_use = 'strong_rank')
    OR (feature_code = 'working_professionals' AND authority = 'explicit'
      AND allowed_use = 'context_input')
    OR (feature_code = 'weekday_time_pressure' AND authority = 'inferred'
      AND allowed_use = 'soft_rank')
  )
);

CREATE INDEX governed_context_signals_expiry
  ON re_engine.governed_context_signals (expires_at)
  WHERE authority = 'inferred' AND correction_state <> 'rejected';

REVOKE ALL ON re_engine.governed_context_signals FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON re_engine.governed_context_signals TO service_role;

CREATE FUNCTION public.materialize_governed_context_signals(
  p_household_id uuid,
  p_signals jsonb
) RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public, re_engine
AS $function$
DECLARE
  item jsonb;
  v_code text;
  v_authority text;
  v_allowed_use text;
  v_confidence real;
  v_sources text[];
  v_expected_authority text;
  v_expected_use text;
BEGIN
  IF NOT EXISTS (SELECT 1 FROM public.households WHERE id = p_household_id) THEN
    RAISE EXCEPTION 'household does not exist';
  END IF;
  IF jsonb_typeof(p_signals) <> 'array' OR jsonb_array_length(p_signals) > 20 THEN
    RAISE EXCEPTION 'signals must be an array with at most 20 items';
  END IF;

  FOR item IN SELECT value FROM jsonb_array_elements(p_signals)
  LOOP
    v_code := item->>'feature_code';
    v_authority := item->>'authority';
    v_allowed_use := item->>'allowed_use';
    v_confidence := (item->>'confidence')::real;
    SELECT array_agg(DISTINCT value ORDER BY value) INTO v_sources
    FROM jsonb_array_elements_text(coalesce(item->'sources', '[]'::jsonb));

    SELECT expected_authority, expected_use
      INTO v_expected_authority, v_expected_use
    FROM (VALUES
      ('health_objective','explicit','strong_rank'),
      ('working_professionals','explicit','context_input'),
      ('weekday_time_pressure','inferred','soft_rank')
    ) policy(feature_code, expected_authority, expected_use)
    WHERE policy.feature_code = v_code;

    IF v_expected_authority IS NULL OR v_authority <> v_expected_authority
      OR v_allowed_use <> v_expected_use OR v_sources IS NULL
      OR NOT (v_sources <@ ARRAY[
        'q1_household_type','q2_working_professionals','q12_member_ages',
        'q13_who_cooks','q15_objective','observed_quick_meal_ratio'
      ]::text[])
    THEN
      RAISE EXCEPTION 'unsupported governed context signal';
    END IF;
    IF (v_authority = 'explicit' AND v_confidence <> 1)
      OR (v_authority = 'inferred' AND (v_confidence < 0 OR v_confidence > 0.70))
    THEN
      RAISE EXCEPTION 'invalid signal confidence';
    END IF;
    IF v_code = 'health_objective' AND NOT (
      item->'value' IN (
        '"awesome_taste"'::jsonb, '"healthy_living"'::jsonb,
        '"into_fitness"'::jsonb, '"protein_calculator"'::jsonb
      )
    ) THEN
      RAISE EXCEPTION 'invalid health objective';
    END IF;
    IF v_code = 'working_professionals' AND (
      jsonb_typeof(item->'value') <> 'number'
      OR (item->>'value')::integer NOT BETWEEN 0 AND 20
    ) THEN
      RAISE EXCEPTION 'invalid working professional count';
    END IF;
    IF v_code = 'weekday_time_pressure' AND (
      jsonb_typeof(item->'value') <> 'number'
      OR (item->>'value')::real NOT BETWEEN 0 AND 1
    ) THEN
      RAISE EXCEPTION 'invalid weekday time pressure';
    END IF;

    INSERT INTO re_engine.governed_context_signals (
      household_id, feature_code, feature_value, authority, confidence, sources,
      allowed_use, observed_at, expires_at
    ) VALUES (
      p_household_id, v_code, item->'value', v_authority, v_confidence, v_sources,
      v_allowed_use, now(),
      CASE WHEN v_authority = 'inferred' THEN now() + interval '30 days' END
    )
    ON CONFLICT (household_id, feature_code) DO UPDATE SET
      feature_value = EXCLUDED.feature_value,
      authority = EXCLUDED.authority,
      confidence = EXCLUDED.confidence,
      sources = EXCLUDED.sources,
      allowed_use = EXCLUDED.allowed_use,
      observed_at = EXCLUDED.observed_at,
      expires_at = EXCLUDED.expires_at,
      feature_version = 'governed-context-v1';
  END LOOP;

  RETURN (
    SELECT coalesce(jsonb_agg(jsonb_build_object(
      'feature_code', feature_code,
      'value', CASE WHEN correction_state = 'confirmed' AND corrected_value IS NOT NULL
        THEN corrected_value ELSE feature_value END,
      'authority', authority,
      'confidence', CASE WHEN correction_state = 'confirmed' THEN 1 ELSE confidence END,
      'sources', to_jsonb(sources),
      'allowed_use', allowed_use,
      'created_at', created_at,
      'expires_at', expires_at,
      'correction_state', correction_state,
      'feature_version', feature_version
    ) ORDER BY feature_code), '[]'::jsonb)
    FROM re_engine.governed_context_signals
    WHERE household_id = p_household_id
      AND correction_state <> 'rejected'
      AND (correction_state = 'confirmed' OR expires_at IS NULL OR expires_at > now())
  );
END
$function$;

CREATE FUNCTION public.get_governed_context_signals(p_household_id uuid)
RETURNS jsonb
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, public, re_engine
AS $function$
  SELECT coalesce(jsonb_agg(jsonb_build_object(
    'feature_code', feature_code,
    'value', CASE WHEN correction_state = 'confirmed' AND corrected_value IS NOT NULL
      THEN corrected_value ELSE feature_value END,
    'authority', authority,
    'confidence', CASE WHEN correction_state = 'confirmed' THEN 1 ELSE confidence END,
    'sources', to_jsonb(sources),
    'allowed_use', allowed_use,
    'created_at', created_at,
    'expires_at', expires_at,
    'correction_state', correction_state,
    'feature_version', feature_version
  ) ORDER BY feature_code), '[]'::jsonb)
  FROM re_engine.governed_context_signals
  WHERE household_id = p_household_id
    AND correction_state <> 'rejected'
    AND (correction_state = 'confirmed' OR expires_at IS NULL OR expires_at > now());
$function$;

CREATE FUNCTION public.correct_governed_context_signal(
  p_household_id uuid,
  p_feature_code text,
  p_correction_state text,
  p_corrected_value jsonb DEFAULT NULL
) RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public, re_engine
AS $function$
BEGIN
  IF auth.uid() IS NULL OR NOT EXISTS (
    SELECT 1 FROM public.household_memberships
    WHERE household_id = p_household_id AND user_id = auth.uid() AND status = 'active'
  ) THEN
    RAISE EXCEPTION 'active household membership required';
  END IF;
  IF p_feature_code <> 'weekday_time_pressure'
    OR p_correction_state NOT IN ('confirmed','rejected')
    OR (p_correction_state = 'confirmed' AND (
      p_corrected_value IS NULL
      OR jsonb_typeof(p_corrected_value) <> 'number'
      OR (p_corrected_value #>> '{}')::real NOT BETWEEN 0 AND 1
    ))
  THEN
    RAISE EXCEPTION 'invalid inferred-feature correction';
  END IF;

  UPDATE re_engine.governed_context_signals SET
    correction_state = p_correction_state,
    corrected_value = CASE WHEN p_correction_state = 'confirmed' THEN p_corrected_value END,
    corrected_at = now(),
    corrected_by = auth.uid()
  WHERE household_id = p_household_id AND feature_code = p_feature_code
    AND authority = 'inferred';
  RETURN FOUND;
END
$function$;

REVOKE ALL ON FUNCTION public.materialize_governed_context_signals(uuid, jsonb),
  public.get_governed_context_signals(uuid),
  public.correct_governed_context_signal(uuid, text, text, jsonb)
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.materialize_governed_context_signals(uuid, jsonb)
  TO service_role;
GRANT EXECUTE ON FUNCTION public.get_governed_context_signals(uuid) TO service_role;
GRANT EXECUTE ON FUNCTION public.correct_governed_context_signal(uuid, text, text, jsonb)
  TO authenticated, service_role;

COMMENT ON TABLE re_engine.governed_context_signals IS
  'Recommendation-only context with authority, provenance, expiry, and user correction. Inference never controls safety.';
