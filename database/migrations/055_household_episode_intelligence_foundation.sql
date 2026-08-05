-- Foofoo final-product foundation: household tenancy, meal episodes, canonical slates/outcomes,
-- food provenance, and private RE/ML/operations control planes.
--
-- This is an expand-only migration. Existing profile-scoped contracts remain valid while new
-- clients and services move to household_id and episode_id. Backfills deliberately use the
-- existing profile UUID as the initial one-owner household UUID, making the transition stable,
-- deterministic, and reversible without inventing identity mappings.

CREATE SCHEMA IF NOT EXISTS food;
CREATE SCHEMA IF NOT EXISTS re_engine;
CREATE SCHEMA IF NOT EXISTS ml;
CREATE SCHEMA IF NOT EXISTS ops;

ALTER TABLE public.feedback_events DROP CONSTRAINT IF EXISTS feedback_events_event_type_check;
ALTER TABLE public.feedback_events ADD CONSTRAINT feedback_events_event_type_check CHECK (
  event_type IN (
    'accept','edit','swap','like','dislike','shown_not_tapped','never','not_today','lock','unlock',
    'add_to_date','make_this','too_much_work','missing_ingredient','member_objection','cooked',
    'ordered','replaced','completed','regretted'
  )
);

DO $$ BEGIN
  GRANT USAGE ON SCHEMA food, re_engine, ml, ops TO service_role;
EXCEPTION WHEN undefined_object THEN
  RAISE NOTICE 'service_role is absent outside Supabase; schema grants skipped';
END $$;

-- ---------------------------------------------------------------------------
-- Household tenancy and authorization
-- ---------------------------------------------------------------------------
CREATE TABLE public.households (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  household_type_code text,
  owner_user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE RESTRICT,
  default_locale text NOT NULL DEFAULT 'en-IN',
  timezone text NOT NULL DEFAULT 'Asia/Kolkata',
  status text NOT NULL DEFAULT 'active' CHECK (status IN ('active','suspended','deleting')),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz
);

CREATE TABLE public.household_memberships (
  household_id uuid NOT NULL REFERENCES public.households(id) ON DELETE CASCADE,
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  role_code text NOT NULL CHECK (role_code IN ('owner','planner','cook','member','viewer')),
  status text NOT NULL DEFAULT 'active' CHECK (status IN ('invited','active','revoked')),
  joined_at timestamptz NOT NULL DEFAULT now(),
  revoked_at timestamptz,
  PRIMARY KEY (household_id, user_id)
);

CREATE TABLE public.household_invites (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  household_id uuid NOT NULL REFERENCES public.households(id) ON DELETE CASCADE,
  token_hash text NOT NULL UNIQUE,
  invited_role text NOT NULL CHECK (invited_role IN ('planner','cook','member','viewer')),
  invited_by uuid NOT NULL REFERENCES auth.users(id) ON DELETE RESTRICT,
  expires_at timestamptz NOT NULL,
  accepted_at timestamptz,
  revoked_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now()
);

INSERT INTO public.households (id, name, household_type_code, owner_user_id, created_at, updated_at)
SELECT p.id, coalesce(nullif(p.primary_cook_name, ''), 'My household'), NULL, p.id,
       p.created_at, p.updated_at
FROM public.profiles p
ON CONFLICT (id) DO NOTHING;

INSERT INTO public.household_memberships (household_id, user_id, role_code, status, joined_at)
SELECT p.id, p.id, 'owner', 'active', p.created_at
FROM public.profiles p
ON CONFLICT (household_id, user_id) DO NOTHING;

ALTER TABLE public.household_members
  ADD COLUMN IF NOT EXISTS household_id uuid REFERENCES public.households(id) ON DELETE CASCADE,
  ADD COLUMN IF NOT EXISTS user_id uuid REFERENCES auth.users(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS display_name text,
  ADD COLUMN IF NOT EXISTS member_role_code text NOT NULL DEFAULT 'member',
  ADD COLUMN IF NOT EXISTS effective_from timestamptz NOT NULL DEFAULT now(),
  ADD COLUMN IF NOT EXISTS effective_to timestamptz;
UPDATE public.household_members SET household_id = profile_id WHERE household_id IS NULL;
CREATE INDEX IF NOT EXISTS idx_household_members_household_active
  ON public.household_members (household_id) WHERE is_active = true;

-- Add the new tenant key without breaking legacy profile-keyed writes.
ALTER TABLE public.week_plans ADD COLUMN IF NOT EXISTS household_id uuid REFERENCES public.households(id);
ALTER TABLE public.recommendation_events ADD COLUMN IF NOT EXISTS household_id uuid REFERENCES public.households(id);
ALTER TABLE public.feedback_events ADD COLUMN IF NOT EXISTS household_id uuid REFERENCES public.households(id);
ALTER TABLE public.product_events ADD COLUMN IF NOT EXISTS household_id uuid REFERENCES public.households(id);
ALTER TABLE public.household_context ADD COLUMN IF NOT EXISTS household_id uuid REFERENCES public.households(id);
UPDATE public.week_plans SET household_id = profile_id WHERE household_id IS NULL;
UPDATE public.recommendation_events SET household_id = profile_id WHERE household_id IS NULL;
UPDATE public.feedback_events SET household_id = profile_id WHERE household_id IS NULL;
UPDATE public.product_events SET household_id = profile_id WHERE household_id IS NULL;
UPDATE public.household_context SET household_id = profile_id WHERE household_id IS NULL;
CREATE INDEX IF NOT EXISTS idx_week_plans_household_week ON public.week_plans (household_id, week_start_date DESC);
CREATE INDEX IF NOT EXISTS idx_recommendation_events_household_time ON public.recommendation_events (household_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_feedback_events_household_time ON public.feedback_events (household_id, created_at DESC);

-- ---------------------------------------------------------------------------
-- Governed food intelligence and episode ontology
-- ---------------------------------------------------------------------------
CREATE TABLE ops.data_sources (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_code text NOT NULL UNIQUE,
  owner_name text NOT NULL,
  license_code text,
  source_uri text,
  retrieved_at timestamptz,
  checksum text,
  permitted_uses text[] NOT NULL DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE food.plate_grammars (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  grammar_code text NOT NULL UNIQUE,
  display_name text NOT NULL,
  locale_scope text[] NOT NULL DEFAULT ARRAY['IN'],
  meal_slots text[] NOT NULL,
  intent_codes text[] NOT NULL DEFAULT '{}',
  required_roles jsonb NOT NULL DEFAULT '{}',
  optional_roles jsonb NOT NULL DEFAULT '{}',
  burden_prior real NOT NULL DEFAULT 0.5 CHECK (burden_prior BETWEEN 0 AND 1),
  data_origin text NOT NULL CHECK (data_origin IN ('external','ai_generated','app','usage','hybrid')),
  source_id uuid REFERENCES ops.data_sources(id),
  confidence real NOT NULL DEFAULT 0.5 CHECK (confidence BETWEEN 0 AND 1),
  review_status text NOT NULL DEFAULT 'draft' CHECK (review_status IN ('draft','reviewed','published','rejected','retired')),
  version integer NOT NULL DEFAULT 1,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE food.grammar_component_rules (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  grammar_id uuid NOT NULL REFERENCES food.plate_grammars(id) ON DELETE CASCADE,
  component_role text NOT NULL,
  allowed_class_codes text[] NOT NULL DEFAULT '{}',
  min_count smallint NOT NULL DEFAULT 0 CHECK (min_count >= 0),
  max_count smallint NOT NULL DEFAULT 1 CHECK (max_count >= min_count),
  compatibility_expression jsonb NOT NULL DEFAULT '{}',
  sequence smallint NOT NULL DEFAULT 0,
  data_origin text NOT NULL CHECK (data_origin IN ('external','ai_generated','hybrid')),
  source_id uuid REFERENCES ops.data_sources(id),
  confidence real NOT NULL DEFAULT 0.5 CHECK (confidence BETWEEN 0 AND 1),
  review_status text NOT NULL DEFAULT 'draft',
  UNIQUE (grammar_id, component_role, sequence)
);

CREATE TABLE food.recipes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  dish_id uuid NOT NULL REFERENCES public.dishes(id) ON DELETE RESTRICT,
  locale text NOT NULL DEFAULT 'en-IN',
  title text NOT NULL,
  servings numeric(6,2) CHECK (servings > 0),
  total_time_minutes integer CHECK (total_time_minutes >= 0),
  active_time_minutes integer CHECK (active_time_minutes >= 0),
  difficulty_code text,
  equipment_codes text[] NOT NULL DEFAULT '{}',
  instructions_status text NOT NULL DEFAULT 'draft',
  data_origin text NOT NULL CHECK (data_origin IN ('external','ai_generated','hybrid')),
  source_id uuid REFERENCES ops.data_sources(id),
  source_version text,
  confidence real NOT NULL DEFAULT 0.5 CHECK (confidence BETWEEN 0 AND 1),
  review_status text NOT NULL DEFAULT 'draft',
  version integer NOT NULL DEFAULT 1,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (dish_id, locale, version)
);

CREATE TABLE food.recipe_steps (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  recipe_id uuid NOT NULL REFERENCES food.recipes(id) ON DELETE CASCADE,
  step_number smallint NOT NULL CHECK (step_number > 0),
  instruction text NOT NULL,
  duration_seconds integer CHECK (duration_seconds >= 0),
  active_seconds integer CHECK (active_seconds >= 0),
  equipment_code text,
  predecessor_step_ids uuid[] NOT NULL DEFAULT '{}',
  parallel_group text,
  skill_level text,
  UNIQUE (recipe_id, step_number)
);

CREATE TABLE food.recipe_ingredients (
  recipe_id uuid NOT NULL REFERENCES food.recipes(id) ON DELETE CASCADE,
  ingredient_id uuid NOT NULL REFERENCES public.ingredients(id) ON DELETE RESTRICT,
  quantity numeric,
  unit_code text,
  preparation text,
  is_optional boolean NOT NULL DEFAULT false,
  substitution_group_id uuid,
  PRIMARY KEY (recipe_id, ingredient_id, preparation)
);

CREATE TABLE food.meal_episodes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  episode_code text NOT NULL UNIQUE,
  episode_hash text NOT NULL UNIQUE,
  grammar_id uuid NOT NULL REFERENCES food.plate_grammars(id) ON DELETE RESTRICT,
  shared_base_dish_id uuid REFERENCES public.dishes(id) ON DELETE RESTRICT,
  episode_genome_vector real[],
  intent_codes text[] NOT NULL DEFAULT '{}',
  richness_prior real CHECK (richness_prior BETWEEN 0 AND 1),
  effort_prior real CHECK (effort_prior BETWEEN 0 AND 1),
  catalog_status text NOT NULL DEFAULT 'draft' CHECK (catalog_status IN ('draft','published','retired','quarantined')),
  data_origin text NOT NULL CHECK (data_origin IN ('external','ai_generated','app','usage','hybrid')),
  source_id uuid REFERENCES ops.data_sources(id),
  source_version text,
  confidence real NOT NULL DEFAULT 0.5 CHECK (confidence BETWEEN 0 AND 1),
  review_status text NOT NULL DEFAULT 'draft',
  version integer NOT NULL DEFAULT 1,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE food.meal_episode_components (
  episode_id uuid NOT NULL REFERENCES food.meal_episodes(id) ON DELETE CASCADE,
  dish_id uuid NOT NULL REFERENCES public.dishes(id) ON DELETE RESTRICT,
  recipe_id uuid REFERENCES food.recipes(id) ON DELETE RESTRICT,
  component_role text NOT NULL,
  is_required boolean NOT NULL DEFAULT true,
  portion_relation numeric,
  sequence smallint NOT NULL DEFAULT 0,
  adaptation_scope text NOT NULL DEFAULT 'shared',
  data_origin text NOT NULL CHECK (data_origin IN ('external','ai_generated','hybrid')),
  source_id uuid REFERENCES ops.data_sources(id),
  confidence real NOT NULL DEFAULT 0.5 CHECK (confidence BETWEEN 0 AND 1),
  review_status text NOT NULL DEFAULT 'draft',
  PRIMARY KEY (episode_id, dish_id, component_role)
);

CREATE TABLE food.episode_workload_features (
  episode_id uuid NOT NULL REFERENCES food.meal_episodes(id) ON DELETE CASCADE,
  recipe_variant_hash text NOT NULL,
  active_minutes integer CHECK (active_minutes >= 0),
  critical_path_minutes integer CHECK (critical_path_minutes >= 0),
  vessel_count smallint CHECK (vessel_count >= 0),
  burner_peak smallint CHECK (burner_peak >= 0),
  ingredient_count smallint CHECK (ingredient_count >= 0),
  rare_ingredient_count smallint CHECK (rare_ingredient_count >= 0),
  cleanup_score real CHECK (cleanup_score BETWEEN 0 AND 1),
  batchability real CHECK (batchability BETWEEN 0 AND 1),
  leftover_value real CHECK (leftover_value BETWEEN 0 AND 1),
  feature_version text NOT NULL,
  computed_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (episode_id, recipe_variant_hash, feature_version)
);

CREATE TABLE food.episode_cadence (
  episode_id uuid NOT NULL REFERENCES food.meal_episodes(id) ON DELETE CASCADE,
  region_code text NOT NULL DEFAULT 'IN',
  household_type_code text NOT NULL DEFAULT 'all',
  cadence_tier text NOT NULL CHECK (cadence_tier IN ('daily_staple','regular_rotation','weekly_rich','occasional','festive')),
  frequency_prior real CHECK (frequency_prior BETWEEN 0 AND 1),
  richness_dimensions jsonb NOT NULL DEFAULT '{}',
  source_id uuid REFERENCES ops.data_sources(id),
  confidence real NOT NULL DEFAULT 0.5 CHECK (confidence BETWEEN 0 AND 1),
  PRIMARY KEY (episode_id, region_code, household_type_code)
);

CREATE INDEX idx_food_episodes_grammar_status ON food.meal_episodes (grammar_id, catalog_status);
CREATE INDEX idx_food_episode_components_dish ON food.meal_episode_components (dish_id);

-- ---------------------------------------------------------------------------
-- Pantry, leftovers, canonical exposure and outcomes
-- ---------------------------------------------------------------------------
CREATE TABLE public.pantry_beliefs (
  household_id uuid NOT NULL REFERENCES public.households(id) ON DELETE CASCADE,
  ingredient_id uuid NOT NULL REFERENCES public.ingredients(id) ON DELETE CASCADE,
  probability_present real NOT NULL CHECK (probability_present BETWEEN 0 AND 1),
  quantity_range jsonb NOT NULL DEFAULT '{}',
  last_evidence_at timestamptz NOT NULL,
  evidence_type text NOT NULL,
  expires_at timestamptz,
  feature_version text NOT NULL,
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (household_id, ingredient_id)
);

CREATE TABLE public.leftover_lots (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  household_id uuid NOT NULL REFERENCES public.households(id) ON DELETE CASCADE,
  source_plan_slot_id uuid REFERENCES public.plan_slots(id) ON DELETE SET NULL,
  dish_id uuid NOT NULL REFERENCES public.dishes(id) ON DELETE RESTRICT,
  estimated_servings numeric(6,2) CHECK (estimated_servings >= 0),
  created_at timestamptz NOT NULL DEFAULT now(),
  safe_until timestamptz NOT NULL,
  status text NOT NULL DEFAULT 'available' CHECK (status IN ('available','reserved','consumed','discarded','expired')),
  confidence real NOT NULL DEFAULT 0.5 CHECK (confidence BETWEEN 0 AND 1)
);

CREATE TABLE public.slates (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  request_id text NOT NULL,
  household_id uuid NOT NULL REFERENCES public.households(id) ON DELETE CASCADE,
  plan_slot_id uuid REFERENCES public.plan_slots(id) ON DELETE SET NULL,
  surface text NOT NULL,
  policy_code text NOT NULL DEFAULT 'deterministic_v1',
  model_version text NOT NULL,
  config_version text NOT NULL,
  catalog_version text,
  eligible_set_hash text,
  household_snapshot_hash text,
  context_snapshot jsonb NOT NULL DEFAULT '{}',
  intent_posterior jsonb NOT NULL DEFAULT '{}',
  experiment_assignments jsonb NOT NULL DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz,
  UNIQUE (household_id, request_id)
);

CREATE TABLE public.slate_items (
  slate_id uuid NOT NULL REFERENCES public.slates(id) ON DELETE CASCADE,
  episode_id uuid REFERENCES food.meal_episodes(id) ON DELETE RESTRICT,
  episode_hash text NOT NULL,
  rank smallint NOT NULL CHECK (rank > 0),
  point_score real NOT NULL,
  rerank_score real NOT NULL,
  selection_propensity real CHECK (selection_propensity > 0 AND selection_propensity <= 1),
  generator_codes text[] NOT NULL DEFAULT '{}',
  reason_tags text[] NOT NULL DEFAULT '{}',
  predicted_choose real CHECK (predicted_choose BETWEEN 0 AND 1),
  predicted_execute real CHECK (predicted_execute BETWEEN 0 AND 1),
  predicted_regret real CHECK (predicted_regret BETWEEN 0 AND 1),
  decision_trace jsonb NOT NULL DEFAULT '{}',
  PRIMARY KEY (slate_id, rank),
  UNIQUE (slate_id, episode_hash)
);

CREATE TABLE public.outcome_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  idempotency_key uuid NOT NULL UNIQUE,
  household_id uuid NOT NULL REFERENCES public.households(id) ON DELETE CASCADE,
  profile_id uuid REFERENCES public.profiles(id) ON DELETE SET NULL,
  member_id uuid REFERENCES public.household_members(id) ON DELETE SET NULL,
  slate_id uuid REFERENCES public.slates(id) ON DELETE SET NULL,
  plan_slot_id uuid REFERENCES public.plan_slots(id) ON DELETE SET NULL,
  episode_id uuid REFERENCES food.meal_episodes(id) ON DELETE SET NULL,
  episode_hash text,
  outcome_type text NOT NULL CHECK (outcome_type IN ('chosen','locked','cooked','ordered','replaced','completed','enjoyed','regretted','leftover_created','leftover_consumed','discarded')),
  value jsonb NOT NULL DEFAULT '{}',
  source text NOT NULL CHECK (source IN ('explicit','inferred','integration','operator')),
  confidence real NOT NULL DEFAULT 1 CHECK (confidence BETWEEN 0 AND 1),
  occurred_at timestamptz NOT NULL,
  received_at timestamptz NOT NULL DEFAULT now(),
  schema_version text NOT NULL DEFAULT '1'
);

ALTER TABLE public.plan_slots ADD COLUMN IF NOT EXISTS selected_episode_id uuid REFERENCES food.meal_episodes(id);
ALTER TABLE public.plan_slots ADD COLUMN IF NOT EXISTS selected_episode_hash text;
ALTER TABLE public.interaction_events ADD COLUMN IF NOT EXISTS household_id uuid REFERENCES public.households(id);
ALTER TABLE public.interaction_events ADD COLUMN IF NOT EXISTS member_id uuid REFERENCES public.household_members(id);
ALTER TABLE public.interaction_events ADD COLUMN IF NOT EXISTS slate_id uuid REFERENCES public.slates(id);
ALTER TABLE public.interaction_events ADD COLUMN IF NOT EXISTS event_name text;
ALTER TABLE public.interaction_events ADD COLUMN IF NOT EXISTS surface text;
ALTER TABLE public.interaction_events ADD COLUMN IF NOT EXISTS received_at timestamptz NOT NULL DEFAULT now();
ALTER TABLE public.interaction_events ADD COLUMN IF NOT EXISTS schema_version text NOT NULL DEFAULT '1';
ALTER TABLE public.interaction_events ADD COLUMN IF NOT EXISTS properties jsonb NOT NULL DEFAULT '{}';
ALTER TABLE public.interaction_events ADD COLUMN IF NOT EXISTS consent_basis text;

CREATE INDEX idx_slates_household_time ON public.slates (household_id, created_at DESC);
CREATE INDEX idx_outcomes_household_time ON public.outcome_events (household_id, occurred_at DESC);
CREATE INDEX idx_leftovers_household_status ON public.leftover_lots (household_id, status, safe_until);

-- ---------------------------------------------------------------------------
-- Private online intelligence and ML/operations control plane
-- ---------------------------------------------------------------------------
CREATE TABLE re_engine.intent_state (
  household_id uuid NOT NULL REFERENCES public.households(id) ON DELETE CASCADE,
  meal_slot text NOT NULL,
  state_probabilities jsonb NOT NULL,
  inference_time timestamptz NOT NULL,
  context_hash text NOT NULL,
  model_version text NOT NULL,
  PRIMARY KEY (household_id, meal_slot)
);

CREATE TABLE re_engine.household_cadence_state (
  household_id uuid PRIMARY KEY REFERENCES public.households(id) ON DELETE CASCADE,
  rolling_state jsonb NOT NULL DEFAULT '{}',
  richness_debt real NOT NULL DEFAULT 0,
  effort_debt real NOT NULL DEFAULT 0,
  novelty_budget real NOT NULL DEFAULT 0.15 CHECK (novelty_budget BETWEEN 0 AND 1),
  ordinary_meal_ratio real CHECK (ordinary_meal_ratio BETWEEN 0 AND 1),
  updated_at timestamptz NOT NULL DEFAULT now(),
  feature_version text NOT NULL
);

CREATE TABLE re_engine.member_fairness_state (
  household_id uuid NOT NULL REFERENCES public.households(id) ON DELETE CASCADE,
  member_id uuid NOT NULL REFERENCES public.household_members(id) ON DELETE CASCADE,
  satisfaction_debt real NOT NULL DEFAULT 0,
  evidence_count integer NOT NULL DEFAULT 0 CHECK (evidence_count >= 0),
  last_served_at timestamptz,
  updated_at timestamptz NOT NULL DEFAULT now(),
  policy_version text NOT NULL,
  PRIMARY KEY (household_id, member_id)
);

CREATE TABLE ml.feature_definitions (
  feature_name text NOT NULL,
  feature_version text NOT NULL,
  value_type text NOT NULL,
  owner_name text NOT NULL,
  expression text NOT NULL,
  null_policy text NOT NULL,
  online_source text,
  offline_source text,
  status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','active','deprecated','retired')),
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (feature_name, feature_version)
);

CREATE TABLE ml.model_registry (
  model_name text NOT NULL,
  model_version text NOT NULL,
  objective text NOT NULL,
  training_dataset_uri text NOT NULL,
  artifact_uri text NOT NULL,
  artifact_checksum text NOT NULL,
  metrics jsonb NOT NULL,
  slice_metrics jsonb NOT NULL DEFAULT '{}',
  stage text NOT NULL CHECK (stage IN ('candidate','shadow','canary','production','retired','rejected')),
  approved_by text,
  created_at timestamptz NOT NULL DEFAULT now(),
  activated_at timestamptz,
  PRIMARY KEY (model_name, model_version)
);

CREATE TABLE ml.experiment_assignments (
  experiment_key text NOT NULL REFERENCES public.experiments(experiment_key) ON DELETE CASCADE,
  household_id uuid NOT NULL REFERENCES public.households(id) ON DELETE CASCADE,
  variant text NOT NULL,
  assignment_version text NOT NULL,
  assigned_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (experiment_key, household_id)
);

CREATE TABLE ops.ai_generation_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  model_name text NOT NULL,
  model_version text NOT NULL,
  prompt_version text NOT NULL,
  input_source_ids uuid[] NOT NULL DEFAULT '{}',
  parameters jsonb NOT NULL DEFAULT '{}',
  output_artifact_uri text,
  output_checksum text,
  validator_result jsonb NOT NULL DEFAULT '{}',
  reviewer text,
  status text NOT NULL DEFAULT 'generated' CHECK (status IN ('generated','validated','approved','rejected','published')),
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE ops.coverage_gap_log (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  request_id text,
  household_id uuid REFERENCES public.households(id) ON DELETE SET NULL,
  region_code text,
  meal_class_code text,
  constraints_hash text,
  candidate_counts jsonb NOT NULL DEFAULT '{}',
  fallback_code text,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE ops.safety_gate_log (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  request_id text,
  slate_id uuid REFERENCES public.slates(id) ON DELETE SET NULL,
  episode_hash text,
  gate_code text NOT NULL,
  result text NOT NULL CHECK (result IN ('pass','block','quarantine','error')),
  evidence jsonb NOT NULL DEFAULT '{}',
  model_version text,
  catalog_version text,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- Tenant tables are client-readable only through active household membership. Writes remain
-- service-role mediated so event validation and idempotency cannot be bypassed by clients.
ALTER TABLE public.households ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.household_memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.household_invites ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pantry_beliefs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.leftover_lots ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.slates ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.slate_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.outcome_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY households_select_member ON public.households FOR SELECT USING (
  EXISTS (SELECT 1 FROM public.household_memberships hm
          WHERE hm.household_id = id AND hm.user_id = (SELECT auth.uid()) AND hm.status = 'active')
);
CREATE POLICY memberships_select_self ON public.household_memberships FOR SELECT
  USING (user_id = (SELECT auth.uid()));
CREATE POLICY invites_select_member ON public.household_invites FOR SELECT USING (
  EXISTS (SELECT 1 FROM public.household_memberships hm
          WHERE hm.household_id = household_invites.household_id
            AND hm.user_id = (SELECT auth.uid()) AND hm.status = 'active')
);
CREATE POLICY pantry_select_member ON public.pantry_beliefs FOR SELECT USING (
  EXISTS (SELECT 1 FROM public.household_memberships hm
          WHERE hm.household_id = pantry_beliefs.household_id
            AND hm.user_id = (SELECT auth.uid()) AND hm.status = 'active')
);
CREATE POLICY leftovers_select_member ON public.leftover_lots FOR SELECT USING (
  EXISTS (SELECT 1 FROM public.household_memberships hm
          WHERE hm.household_id = leftover_lots.household_id
            AND hm.user_id = (SELECT auth.uid()) AND hm.status = 'active')
);
CREATE POLICY slates_select_member ON public.slates FOR SELECT USING (
  EXISTS (SELECT 1 FROM public.household_memberships hm
          WHERE hm.household_id = slates.household_id
            AND hm.user_id = (SELECT auth.uid()) AND hm.status = 'active')
);
CREATE POLICY slate_items_select_member ON public.slate_items FOR SELECT USING (
  EXISTS (SELECT 1 FROM public.slates s JOIN public.household_memberships hm ON hm.household_id = s.household_id
          WHERE s.id = slate_items.slate_id AND hm.user_id = (SELECT auth.uid()) AND hm.status = 'active')
);
CREATE POLICY outcomes_select_member ON public.outcome_events FOR SELECT USING (
  EXISTS (SELECT 1 FROM public.household_memberships hm
          WHERE hm.household_id = outcome_events.household_id
            AND hm.user_id = (SELECT auth.uid()) AND hm.status = 'active')
);

DO $$
DECLARE qualified text;
BEGIN
  FOREACH qualified IN ARRAY ARRAY[
    'food.plate_grammars','food.grammar_component_rules','food.recipes','food.recipe_steps',
    'food.recipe_ingredients','food.meal_episodes','food.meal_episode_components',
    'food.episode_workload_features','food.episode_cadence','re_engine.intent_state',
    're_engine.household_cadence_state','re_engine.member_fairness_state',
    'ml.feature_definitions','ml.model_registry','ml.experiment_assignments',
    'ops.data_sources','ops.ai_generation_runs','ops.coverage_gap_log','ops.safety_gate_log'
  ] LOOP
    EXECUTE format('ALTER TABLE %s ENABLE ROW LEVEL SECURITY', qualified);
    BEGIN
      EXECUTE format('REVOKE ALL ON %s FROM anon, authenticated', qualified);
    EXCEPTION WHEN undefined_object THEN
      RAISE NOTICE 'Supabase client roles absent; revoke skipped for %', qualified;
    END;
  END LOOP;
END $$;
