-- Migration: 061_complete_food_intelligence_schema.sql
-- PRD food-intelligence completion: graph, nutrition, publish/review and research evidence.

CREATE SCHEMA IF NOT EXISTS research;
REVOKE ALL ON SCHEMA research FROM PUBLIC, anon, authenticated;
GRANT USAGE ON SCHEMA research TO service_role;

CREATE TABLE food.ontology_nodes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  node_code text NOT NULL UNIQUE,
  node_type text NOT NULL CHECK (node_type IN (
    'dish','dish_variant','ingredient','ingredient_form','meal_class','meal_role','cuisine','region',
    'technique','genome_tag','nutrient','season','festival','equipment','recipe','source',
    'external_food_term'
  )),
  canonical_entity_id uuid,
  label text NOT NULL,
  locale text NOT NULL DEFAULT 'en-IN',
  status text NOT NULL DEFAULT 'active' CHECK (status IN ('draft','active','retired','quarantined')),
  source_name text NOT NULL,
  source_version text,
  confidence numeric(4,3) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
  review_status text NOT NULL DEFAULT 'provisional' CHECK (review_status IN ('provisional','accepted','rejected')),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE food.ontology_edges (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  subject_node_id uuid NOT NULL REFERENCES food.ontology_nodes(id) ON DELETE CASCADE,
  predicate_code text NOT NULL CHECK (predicate_code IN (
    'contains','main_ingredient','variant_of','alias_of','belongs_to_class','originates_in',
    'popular_in','uses_technique','has_tag','pairs_with','substitutes_for','suitable_in',
    'seasonal_in','associated_with','supported_by_source'
  )),
  object_node_id uuid NOT NULL REFERENCES food.ontology_nodes(id) ON DELETE CASCADE,
  scope_region_code text,
  weight numeric(6,5) NOT NULL DEFAULT 1 CHECK (weight BETWEEN 0 AND 1),
  confidence numeric(4,3) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
  source_name text NOT NULL,
  source_version text,
  effective_from timestamptz NOT NULL DEFAULT now(),
  effective_to timestamptz,
  review_status text NOT NULL DEFAULT 'provisional' CHECK (review_status IN ('provisional','accepted','rejected')),
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK (subject_node_id <> object_node_id),
  CHECK (effective_to IS NULL OR effective_to > effective_from)
);
CREATE INDEX ontology_edges_subject ON food.ontology_edges(subject_node_id, predicate_code);
CREATE INDEX ontology_edges_object ON food.ontology_edges(object_node_id, predicate_code);
CREATE UNIQUE INDEX ontology_edges_identity ON food.ontology_edges(
  subject_node_id, predicate_code, object_node_id, coalesce(scope_region_code, '')
);

CREATE TABLE food.nutrients (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  nutrient_code text NOT NULL UNIQUE,
  display_name text NOT NULL,
  unit_code text NOT NULL,
  source_name text NOT NULL,
  source_version text,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE food.nutrient_assertions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  dish_id uuid REFERENCES public.dishes(id) ON DELETE CASCADE,
  ingredient_id uuid REFERENCES public.ingredients(id) ON DELETE CASCADE,
  recipe_id uuid REFERENCES food.recipes(id) ON DELETE CASCADE,
  nutrient_id uuid NOT NULL REFERENCES food.nutrients(id),
  min_value numeric,
  expected_value numeric NOT NULL CHECK (expected_value >= 0),
  max_value numeric,
  serving_basis text NOT NULL,
  method_code text NOT NULL,
  source_name text NOT NULL,
  source_record_id uuid REFERENCES public.food_source_records(id) ON DELETE SET NULL,
  confidence numeric(4,3) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
  review_status text NOT NULL DEFAULT 'provisional' CHECK (review_status IN ('provisional','accepted','rejected')),
  version integer NOT NULL DEFAULT 1,
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK (num_nonnulls(dish_id, ingredient_id, recipe_id) = 1),
  CHECK (min_value IS NULL OR min_value <= expected_value),
  CHECK (max_value IS NULL OR max_value >= expected_value)
);
CREATE INDEX nutrient_assertions_dish ON food.nutrient_assertions(dish_id, nutrient_id, review_status);

CREATE TABLE ops.content_review_tasks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  subject_type text NOT NULL,
  subject_id uuid NOT NULL,
  assertion_path text NOT NULL,
  proposed_origin text NOT NULL CHECK (proposed_origin IN ('external','rules','ai','user')),
  risk_tier text NOT NULL CHECK (risk_tier IN ('low','medium','high','safety')),
  review_status text NOT NULL DEFAULT 'pending' CHECK (review_status IN ('pending','assigned','accepted','rejected','superseded')),
  assigned_reviewer_id uuid REFERENCES auth.users(id) ON DELETE SET NULL,
  decision_code text,
  decision_reason text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX content_review_tasks_active
  ON ops.content_review_tasks(subject_type, subject_id, assertion_path)
  WHERE review_status IN ('pending','assigned');

CREATE TABLE ops.catalog_versions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  version_code text NOT NULL UNIQUE,
  manifest_checksum text NOT NULL UNIQUE,
  source_versions jsonb NOT NULL,
  row_counts jsonb NOT NULL,
  status text NOT NULL CHECK (status IN ('building','validated','published','retired','failed')),
  created_at timestamptz NOT NULL DEFAULT now(),
  published_at timestamptz
);

CREATE TABLE ops.catalog_publish_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  catalog_version_id uuid NOT NULL REFERENCES ops.catalog_versions(id),
  validation_report jsonb NOT NULL DEFAULT '{}',
  safety_results jsonb NOT NULL DEFAULT '{}',
  publish_status text NOT NULL CHECK (publish_status IN ('running','passed','failed','rolled_back')),
  code_commit text,
  approved_by uuid REFERENCES auth.users(id) ON DELETE SET NULL,
  started_at timestamptz NOT NULL DEFAULT now(),
  completed_at timestamptz,
  rollback_of_id uuid REFERENCES ops.catalog_publish_runs(id)
);

CREATE TABLE research.studies (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  study_code text NOT NULL UNIQUE,
  protocol_version text NOT NULL,
  purpose_text text NOT NULL,
  sampling_frame jsonb NOT NULL,
  consent_policy_version text NOT NULL,
  study_status text NOT NULL CHECK (study_status IN ('draft','approved','active','paused','complete','cancelled')),
  ethics_review_uri text,
  privacy_review_uri text,
  starts_at timestamptz,
  ends_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE research.participants (
  study_id uuid NOT NULL REFERENCES research.studies(id) ON DELETE CASCADE,
  participant_id uuid NOT NULL DEFAULT gen_random_uuid(),
  household_token text NOT NULL,
  consent_record_id uuid REFERENCES public.consent_records(id) ON DELETE RESTRICT,
  sampling_dimensions jsonb NOT NULL DEFAULT '{}',
  enrolled_at timestamptz NOT NULL DEFAULT now(),
  withdrawn_at timestamptz,
  PRIMARY KEY (study_id, participant_id),
  UNIQUE (study_id, household_token)
);

CREATE TABLE research.meal_diaries (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  study_id uuid NOT NULL,
  participant_id uuid NOT NULL,
  occurred_at timestamptz NOT NULL,
  meal_slot_code text NOT NULL,
  planned_episode_hash text,
  actual_components jsonb NOT NULL,
  portions jsonb NOT NULL DEFAULT '{}',
  cook_effort jsonb NOT NULL DEFAULT '{}',
  pantry_evidence jsonb NOT NULL DEFAULT '{}',
  leftover_result jsonb NOT NULL DEFAULT '{}',
  satisfaction jsonb NOT NULL DEFAULT '{}',
  media_uri text,
  created_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (study_id, participant_id) REFERENCES research.participants(study_id, participant_id)
);

CREATE TABLE research.annotation_batches (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  corpus_version text NOT NULL,
  handbook_version text NOT NULL,
  task_type_code text NOT NULL,
  sampling_method_code text NOT NULL,
  required_reviewers smallint NOT NULL CHECK (required_reviewers > 0),
  agreement_threshold numeric(4,3) NOT NULL CHECK (agreement_threshold BETWEEN 0 AND 1),
  batch_status text NOT NULL CHECK (batch_status IN ('draft','active','adjudicating','complete','cancelled')),
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE research.annotations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  batch_id uuid NOT NULL REFERENCES research.annotation_batches(id) ON DELETE CASCADE,
  item_id text NOT NULL,
  annotator_token text NOT NULL,
  labels jsonb NOT NULL,
  confidence numeric(4,3) CHECK (confidence BETWEEN 0 AND 1),
  submitted_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (batch_id, item_id, annotator_token)
);

DO $$
BEGIN
  GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA food, ops, research TO service_role;
  ALTER DEFAULT PRIVILEGES IN SCHEMA research GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO service_role;
EXCEPTION WHEN undefined_object THEN
  RAISE NOTICE 'service_role absent outside Supabase; grants skipped';
END $$;
