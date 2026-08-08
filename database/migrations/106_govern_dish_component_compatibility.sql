-- Govern slot-aware component compatibility separately from primary meal-class identity.
--
-- Ghar RE ranks dry/liquid/single/standalone dishes as meal heroes and attaches support dishes
-- only while composing a complete episode. The catalogue publication gate currently requires a
-- meal-class mapping from every dish, which incorrectly pressures staples and accompaniments into
-- primary classes. These tables create an explicit, reviewable component path. This migration is
-- additive: it does not alter catalogue eligibility, publish dishes, or route traffic to Aux.

CREATE OR REPLACE FUNCTION re_engine.canonical_meal_slot(p_slot text)
RETURNS text
LANGUAGE sql
IMMUTABLE
STRICT
PARALLEL SAFE
SET search_path = pg_catalog, pg_temp
AS $$
  SELECT CASE lower(btrim(p_slot))
    WHEN 'breakfast' THEN 'breakfast'
    WHEN 'lunch' THEN 'lunch'
    WHEN 'dinner' THEN 'dinner'
    WHEN 'snack' THEN 'snacks'
    WHEN 'snacks' THEN 'snacks'
    ELSE NULL
  END;
$$;

CREATE TABLE food.dish_component_compatibility (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  dish_id uuid NOT NULL REFERENCES public.dishes(id) ON DELETE RESTRICT,
  grammar_id uuid NOT NULL REFERENCES food.plate_grammars(id) ON DELETE RESTRICT,
  meal_slot text NOT NULL CHECK (meal_slot IN ('breakfast','lunch','dinner','snacks')),
  grammar_role text NOT NULL DEFAULT 'side' CHECK (grammar_role = 'side'),
  component_role text NOT NULL CHECK (
    component_role IN ('staple','side','accompaniment')
  ),
  compatibility_expression jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (
    jsonb_typeof(compatibility_expression) = 'object'
  ),
  confidence numeric(4,3) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
  source_name text NOT NULL,
  source_type text NOT NULL CHECK (source_type IN (
    'internal_research','external_api','rules','ml_model','human_review'
  )),
  source_id uuid REFERENCES ops.data_sources(id) ON DELETE SET NULL,
  source_url text,
  evidence_method text NOT NULL,
  model_name text,
  model_version text,
  review_status text NOT NULL CHECK (review_status IN ('accepted','superseded')),
  reviewed_by text NOT NULL CHECK (btrim(reviewed_by) <> ''),
  reviewed_at timestamptz NOT NULL,
  version integer NOT NULL DEFAULT 1 CHECK (version > 0),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CHECK (source_type <> 'ml_model' OR model_name IS NOT NULL),
  UNIQUE (dish_id, grammar_id, meal_slot, component_role, version)
);

CREATE UNIQUE INDEX dish_component_compatibility_current
  ON food.dish_component_compatibility (
    dish_id, grammar_id, meal_slot, component_role
  )
  WHERE review_status = 'accepted';
CREATE INDEX dish_component_compatibility_serving_lookup
  ON food.dish_component_compatibility (meal_slot, component_role, confidence DESC)
  WHERE review_status = 'accepted';

CREATE TABLE ops.dish_component_compatibility_proposals (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  dish_id uuid NOT NULL REFERENCES public.dishes(id) ON DELETE RESTRICT,
  grammar_id uuid NOT NULL REFERENCES food.plate_grammars(id) ON DELETE RESTRICT,
  meal_slot text NOT NULL CHECK (meal_slot IN ('breakfast','lunch','dinner','snacks')),
  grammar_role text NOT NULL DEFAULT 'side' CHECK (grammar_role = 'side'),
  component_role text NOT NULL CHECK (
    component_role IN ('staple','side','accompaniment')
  ),
  compatibility_expression jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (
    jsonb_typeof(compatibility_expression) = 'object'
  ),
  evidence_payload jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (
    jsonb_typeof(evidence_payload) = 'object'
  ),
  confidence numeric(4,3) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
  source_name text NOT NULL,
  source_type text NOT NULL CHECK (source_type IN (
    'internal_research','external_api','rules','ml_model','human_review'
  )),
  source_id uuid REFERENCES ops.data_sources(id) ON DELETE SET NULL,
  source_url text,
  proposal_method text NOT NULL,
  proposer_version text NOT NULL,
  model_name text,
  model_version text,
  proposal_status text NOT NULL DEFAULT 'pending' CHECK (
    proposal_status IN ('pending','in_review','approved','rejected','applied')
  ),
  reviewed_by text,
  reviewed_at timestamptz,
  review_notes text,
  applied_compatibility_id uuid REFERENCES food.dish_component_compatibility(id)
    ON DELETE RESTRICT,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CHECK (source_type <> 'ml_model' OR model_name IS NOT NULL),
  CHECK (
    (proposal_status IN ('pending','in_review') AND reviewed_by IS NULL
      AND reviewed_at IS NULL AND applied_compatibility_id IS NULL)
    OR
    (proposal_status IN ('approved','rejected') AND reviewed_by IS NOT NULL
      AND btrim(reviewed_by) <> '' AND reviewed_at IS NOT NULL
      AND applied_compatibility_id IS NULL)
    OR
    (proposal_status = 'applied' AND reviewed_by IS NOT NULL
      AND btrim(reviewed_by) <> '' AND reviewed_at IS NOT NULL
      AND applied_compatibility_id IS NOT NULL)
  ),
  UNIQUE (
    dish_id, grammar_id, meal_slot, component_role, proposal_method, proposer_version
  )
);

CREATE INDEX dish_component_proposals_review_queue
  ON ops.dish_component_compatibility_proposals (
    proposal_status, confidence DESC, created_at, id
  );

CREATE OR REPLACE FUNCTION food.validate_dish_component_grammar()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = food, pg_catalog, pg_temp
AS $$
DECLARE
  v_meal_slots text[];
  v_required_roles jsonb;
  v_optional_roles jsonb;
  v_grammar_review_status text;
BEGIN
  SELECT g.meal_slots, g.required_roles, g.optional_roles, g.review_status
  INTO v_meal_slots, v_required_roles, v_optional_roles, v_grammar_review_status
  FROM food.plate_grammars g
  WHERE g.id = NEW.grammar_id;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'component compatibility grammar does not exist';
  END IF;
  IF NOT NEW.meal_slot = ANY(v_meal_slots) THEN
    RAISE EXCEPTION 'grammar does not support canonical meal slot %', NEW.meal_slot;
  END IF;
  IF NOT (v_required_roles ? NEW.grammar_role OR v_optional_roles ? NEW.grammar_role) THEN
    RAISE EXCEPTION 'grammar does not define component role %', NEW.grammar_role;
  END IF;
  IF v_grammar_review_status <> 'published' THEN
    RAISE EXCEPTION 'component compatibility requires a published grammar';
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER dish_component_compatibility_grammar_guard
BEFORE INSERT OR UPDATE ON food.dish_component_compatibility
FOR EACH ROW EXECUTE FUNCTION food.validate_dish_component_grammar();

CREATE TRIGGER dish_component_proposal_grammar_guard
BEFORE INSERT OR UPDATE ON ops.dish_component_compatibility_proposals
FOR EACH ROW EXECUTE FUNCTION food.validate_dish_component_grammar();

CREATE OR REPLACE FUNCTION food.protect_dish_component_compatibility()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = food, pg_catalog, pg_temp
AS $$
BEGIN
  IF OLD.review_status = 'superseded' THEN
    RAISE EXCEPTION 'superseded component compatibility is immutable';
  END IF;
  IF ROW(
       NEW.dish_id, NEW.grammar_id, NEW.meal_slot, NEW.grammar_role,
       NEW.component_role, NEW.compatibility_expression, NEW.confidence,
       NEW.source_name, NEW.source_type, NEW.source_id, NEW.source_url,
       NEW.evidence_method, NEW.model_name, NEW.model_version,
       NEW.reviewed_by, NEW.reviewed_at, NEW.version, NEW.created_at
     ) IS DISTINCT FROM ROW(
       OLD.dish_id, OLD.grammar_id, OLD.meal_slot, OLD.grammar_role,
       OLD.component_role, OLD.compatibility_expression, OLD.confidence,
       OLD.source_name, OLD.source_type, OLD.source_id, OLD.source_url,
       OLD.evidence_method, OLD.model_name, OLD.model_version,
       OLD.reviewed_by, OLD.reviewed_at, OLD.version, OLD.created_at
     ) OR NEW.review_status <> 'superseded' THEN
    RAISE EXCEPTION 'accepted component compatibility may only be superseded';
  END IF;
  NEW.updated_at := now();
  RETURN NEW;
END;
$$;

CREATE TRIGGER dish_component_compatibility_immutability_guard
BEFORE UPDATE ON food.dish_component_compatibility
FOR EACH ROW EXECUTE FUNCTION food.protect_dish_component_compatibility();

CREATE OR REPLACE FUNCTION ops.protect_component_proposal_lifecycle()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ops, pg_catalog, pg_temp
AS $$
BEGIN
  IF ROW(
       NEW.dish_id, NEW.grammar_id, NEW.meal_slot, NEW.grammar_role,
       NEW.component_role, NEW.compatibility_expression, NEW.evidence_payload,
       NEW.confidence, NEW.source_name, NEW.source_type, NEW.source_id,
       NEW.source_url, NEW.proposal_method, NEW.proposer_version,
       NEW.model_name, NEW.model_version, NEW.created_at
     ) IS DISTINCT FROM ROW(
       OLD.dish_id, OLD.grammar_id, OLD.meal_slot, OLD.grammar_role,
       OLD.component_role, OLD.compatibility_expression, OLD.evidence_payload,
       OLD.confidence, OLD.source_name, OLD.source_type, OLD.source_id,
       OLD.source_url, OLD.proposal_method, OLD.proposer_version,
       OLD.model_name, OLD.model_version, OLD.created_at
     ) THEN
    RAISE EXCEPTION 'component proposal evidence is immutable';
  END IF;
  IF OLD.proposal_status IN ('rejected','applied')
     OR NOT (
       (OLD.proposal_status = 'pending'
         AND NEW.proposal_status IN ('in_review','approved','rejected'))
       OR (OLD.proposal_status = 'in_review'
         AND NEW.proposal_status IN ('approved','rejected'))
       OR (OLD.proposal_status = 'approved' AND NEW.proposal_status = 'applied')
     ) THEN
    RAISE EXCEPTION 'invalid component proposal lifecycle transition';
  END IF;
  NEW.updated_at := now();
  RETURN NEW;
END;
$$;

CREATE TRIGGER dish_component_proposal_lifecycle_guard
BEFORE UPDATE ON ops.dish_component_compatibility_proposals
FOR EACH ROW EXECUTE FUNCTION ops.protect_component_proposal_lifecycle();

CREATE OR REPLACE FUNCTION ops.validate_component_proposal_application()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ops, food, pg_catalog, pg_temp
AS $$
BEGIN
  IF NEW.proposal_status = 'applied' AND NOT EXISTS (
    SELECT 1
    FROM food.dish_component_compatibility c
    WHERE c.id = NEW.applied_compatibility_id
      AND c.dish_id = NEW.dish_id
      AND c.grammar_id = NEW.grammar_id
      AND c.meal_slot = NEW.meal_slot
      AND c.grammar_role = NEW.grammar_role
      AND c.component_role = NEW.component_role
      AND c.review_status = 'accepted'
  ) THEN
    RAISE EXCEPTION 'applied proposal must reference its matching accepted compatibility fact';
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER dish_component_proposal_application_guard
BEFORE INSERT OR UPDATE ON ops.dish_component_compatibility_proposals
FOR EACH ROW EXECUTE FUNCTION ops.validate_component_proposal_application();

ALTER TABLE food.dish_component_compatibility ENABLE ROW LEVEL SECURITY;
ALTER TABLE ops.dish_component_compatibility_proposals ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON food.dish_component_compatibility FROM PUBLIC, anon, authenticated;
REVOKE ALL ON ops.dish_component_compatibility_proposals FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT, UPDATE ON food.dish_component_compatibility TO service_role;
GRANT SELECT, INSERT, UPDATE ON ops.dish_component_compatibility_proposals TO service_role;

CREATE OR REPLACE FUNCTION re_engine.catalogue_serving_role_readiness_report()
RETURNS jsonb
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public, food, ops, re_engine, pg_temp
AS $$
  WITH hero_role AS (
    SELECT
      d.id AS dish_id,
      max(coalesce(t.code, a.value_text, a.value_json #>> '{}')) FILTER (
        WHERE cur.field_key = 'hero_role' AND a.review_status <> 'rejected'
      ) AS hero_role
    FROM public.dishes d
    LEFT JOIN public.dish_taxonomy_current cur ON cur.dish_id = d.id
      AND cur.field_key = 'hero_role'
    LEFT JOIN public.dish_taxonomy_assertions a ON a.id = cur.assertion_id
    LEFT JOIN public.taxonomy_terms t ON t.id = a.term_id
    WHERE d.is_active
    GROUP BY d.id
  ),
  dish_slots AS (
    SELECT DISTINCT
      d.id AS dish_id,
      re_engine.canonical_meal_slot(raw_slot) AS meal_slot,
      h.hero_role
    FROM public.dishes d
    JOIN hero_role h ON h.dish_id = d.id
    CROSS JOIN LATERAL unnest(d.meal_occasion) AS raw(raw_slot)
    WHERE d.is_active
      AND re_engine.canonical_meal_slot(raw_slot) IS NOT NULL
  ),
  classified AS (
    SELECT
      s.dish_id,
      s.meal_slot,
      s.hero_role,
      EXISTS (
        SELECT 1
        FROM public.dish_meal_class_mappings m
        WHERE m.dish_id = s.dish_id
          AND re_engine.canonical_meal_slot(m.slot) = s.meal_slot
          AND m.review_status <> 'rejected'
          AND m.confidence >= 0.700
      ) AS primary_mapping_ready,
      EXISTS (
        SELECT 1
        FROM food.dish_component_compatibility c
        JOIN food.plate_grammars g ON g.id = c.grammar_id
        WHERE c.dish_id = s.dish_id
          AND c.meal_slot = s.meal_slot
          AND c.review_status = 'accepted'
          AND c.confidence >= 0.800
          AND g.review_status = 'published'
      ) AS component_compatibility_ready
    FROM dish_slots s
  ),
  routed AS (
    SELECT
      *,
      CASE
        WHEN hero_role IS NULL THEN 'missing_hero_role'
        WHEN hero_role = 'support' AND component_compatibility_ready
          THEN 'component_ready'
        WHEN hero_role = 'support' THEN 'component_review_required'
        WHEN hero_role IN ('dry','liquid','single','standalone') AND primary_mapping_ready
          THEN 'primary_ready'
        WHEN hero_role IN ('dry','liquid','single','standalone')
          THEN 'primary_class_review_required'
        ELSE 'invalid_hero_role'
      END AS serving_route
    FROM classified
  )
  SELECT jsonb_build_object(
    'schema_version', 'recommendation-catalogue-serving-role-readiness-v1',
    'source', 'catalogue_serving_role_readiness_report',
    'active_dishes', (SELECT count(*) FROM public.dishes WHERE is_active),
    'active_dish_slots', count(*),
    'policy', jsonb_build_object(
      'canonical_meal_slots', jsonb_build_array('breakfast','lunch','dinner','snacks'),
      'snack_alias_normalized_to', 'snacks',
      'primary_class_confidence_minimum', 0.700,
      'component_confidence_minimum', 0.800,
      'identity_exposed', false,
      'automatic_proposal_acceptance_allowed', false,
      'publication_gate_changed', false
    ),
    'serving_routes', coalesce((
      SELECT jsonb_object_agg(route_counts.serving_route, route_counts.slot_count)
      FROM (
        SELECT serving_route, count(*) AS slot_count
        FROM routed
        GROUP BY serving_route
        ORDER BY serving_route
      ) route_counts
    ), '{}'::jsonb),
    'hero_roles', coalesce((
      SELECT jsonb_object_agg(role_counts.role_key, role_counts.slot_count)
      FROM (
        SELECT coalesce(hero_role, 'missing') AS role_key, count(*) AS slot_count
        FROM routed
        GROUP BY coalesce(hero_role, 'missing')
        ORDER BY coalesce(hero_role, 'missing')
      ) role_counts
    ), '{}'::jsonb),
    'component_governance', jsonb_build_object(
      'accepted_assertions', (
        SELECT count(*) FROM food.dish_component_compatibility
        WHERE review_status = 'accepted'
      ),
      'pending_proposals', (
        SELECT count(*) FROM ops.dish_component_compatibility_proposals
        WHERE proposal_status IN ('pending','in_review')
      ),
      'approved_not_applied', (
        SELECT count(*) FROM ops.dish_component_compatibility_proposals
        WHERE proposal_status = 'approved'
      ),
      'applied_proposals', (
        SELECT count(*) FROM ops.dish_component_compatibility_proposals
        WHERE proposal_status = 'applied'
      )
    )
  )
  FROM routed;
$$;

REVOKE ALL ON FUNCTION re_engine.canonical_meal_slot(text)
  FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION re_engine.catalogue_serving_role_readiness_report()
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION re_engine.canonical_meal_slot(text) TO service_role;
GRANT EXECUTE ON FUNCTION re_engine.catalogue_serving_role_readiness_report() TO service_role;

COMMENT ON TABLE food.dish_component_compatibility IS
  'Human-reviewed slot-aware facts for using a dish as a meal component; separate from primary meal-class identity.';
COMMENT ON TABLE ops.dish_component_compatibility_proposals IS
  'Service-only proposal queue; no proposal changes serving until independently reviewed and copied into an accepted compatibility fact.';
COMMENT ON FUNCTION re_engine.catalogue_serving_role_readiness_report() IS
  'Returns aggregate primary-versus-component readiness without dish/user identity and without changing publication eligibility.';
