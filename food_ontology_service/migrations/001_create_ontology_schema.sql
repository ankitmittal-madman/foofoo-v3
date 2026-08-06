-- Standalone Food Ontology Service schema. Apply only to the ontology service database.
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE SCHEMA IF NOT EXISTS ontology;
REVOKE ALL ON SCHEMA ontology FROM PUBLIC;

CREATE TYPE ontology.review_status AS ENUM ('provisional','accepted','rejected');
CREATE TYPE ontology.planning_role AS ENUM ('primary','addon','combo_component');
CREATE TYPE ontology.job_status AS ENUM ('queued','running','retry','review','complete','dead');

CREATE TABLE ontology.dishes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  canonical_name text NOT NULL CHECK (length(btrim(canonical_name)) BETWEEN 2 AND 160),
  normalized_name text NOT NULL,
  locale text NOT NULL DEFAULT 'en-IN',
  status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','active','merged','retired','quarantined')),
  merged_into_id uuid REFERENCES ontology.dishes(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (normalized_name, locale),
  CHECK (merged_into_id IS NULL OR merged_into_id <> id)
);

CREATE TABLE ontology.meal_classes (
  class_code text PRIMARY KEY,
  display_name text NOT NULL,
  slot text NOT NULL CHECK (slot IN ('breakfast','lunch','dinner','snack')),
  planning_role ontology.planning_role NOT NULL,
  parent_class_code text REFERENCES ontology.meal_classes(class_code),
  family_code text,
  is_active boolean NOT NULL DEFAULT true
);

CREATE TABLE ontology.data_sources (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_code text NOT NULL UNIQUE,
  source_type text NOT NULL,
  licence_code text,
  terms_url text,
  allowed_uses jsonb NOT NULL DEFAULT '{}',
  enabled boolean NOT NULL DEFAULT true,
  checked_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE ontology.source_records (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_id uuid NOT NULL REFERENCES ontology.data_sources(id),
  provider_record_id text,
  subject_dish_id uuid REFERENCES ontology.dishes(id) ON DELETE CASCADE,
  query_text text,
  source_url text,
  payload jsonb NOT NULL,
  payload_sha256 text NOT NULL CHECK (payload_sha256 ~ '^[a-f0-9]{64}$'),
  fetched_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (source_id, payload_sha256)
);

CREATE TABLE ontology.assertions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  dish_id uuid NOT NULL REFERENCES ontology.dishes(id) ON DELETE CASCADE,
  field_path text NOT NULL,
  value jsonb NOT NULL,
  confidence numeric(4,3) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
  review_status ontology.review_status NOT NULL DEFAULT 'provisional',
  extraction_method text NOT NULL,
  model_name text,
  model_version text,
  last_verified_at timestamptz NOT NULL DEFAULT now(),
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK (model_name IS NULL OR model_version IS NOT NULL)
);
CREATE INDEX assertions_dish_field ON ontology.assertions(dish_id,field_path,confidence DESC);

CREATE TABLE ontology.assertion_evidence (
  assertion_id uuid NOT NULL REFERENCES ontology.assertions(id) ON DELETE CASCADE,
  source_record_id uuid NOT NULL REFERENCES ontology.source_records(id) ON DELETE RESTRICT,
  evidence_role text NOT NULL DEFAULT 'supports' CHECK (evidence_role IN ('supports','contradicts')),
  PRIMARY KEY (assertion_id,source_record_id)
);

CREATE TABLE ontology.current_field_values (
  dish_id uuid NOT NULL REFERENCES ontology.dishes(id) ON DELETE CASCADE,
  field_path text NOT NULL,
  assertion_id uuid NOT NULL UNIQUE REFERENCES ontology.assertions(id) ON DELETE RESTRICT,
  selected_by text NOT NULL,
  selected_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (dish_id,field_path)
);

CREATE TABLE ontology.dish_aliases (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  dish_id uuid NOT NULL REFERENCES ontology.dishes(id) ON DELETE CASCADE,
  alias_text text NOT NULL,
  normalized_alias text NOT NULL,
  language text NOT NULL DEFAULT 'en',
  region_code text,
  alias_type text NOT NULL,
  assertion_id uuid NOT NULL REFERENCES ontology.assertions(id) ON DELETE RESTRICT
);
CREATE INDEX dish_aliases_lookup ON ontology.dish_aliases(normalized_alias,language);
CREATE UNIQUE INDEX dish_aliases_identity ON ontology.dish_aliases
  (dish_id,normalized_alias,language,coalesce(region_code,''));

CREATE TABLE ontology.dish_class_memberships (
  dish_id uuid NOT NULL REFERENCES ontology.dishes(id) ON DELETE CASCADE,
  class_code text NOT NULL REFERENCES ontology.meal_classes(class_code),
  slot text NOT NULL CHECK (slot IN ('breakfast','lunch','dinner','snack')),
  role ontology.planning_role NOT NULL,
  assertion_id uuid NOT NULL REFERENCES ontology.assertions(id) ON DELETE RESTRICT,
  PRIMARY KEY (dish_id,class_code,slot,role)
);

CREATE FUNCTION ontology.enforce_class_role() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE expected ontology.planning_role;
BEGIN
  SELECT planning_role INTO expected FROM ontology.meal_classes WHERE class_code=NEW.class_code;
  IF expected IS DISTINCT FROM NEW.role THEN RAISE EXCEPTION 'dish/class planning role mismatch'; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER dish_class_role_guard BEFORE INSERT OR UPDATE ON ontology.dish_class_memberships
FOR EACH ROW EXECUTE FUNCTION ontology.enforce_class_role();

CREATE TABLE ontology.dish_relationships (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  subject_dish_id uuid NOT NULL REFERENCES ontology.dishes(id) ON DELETE CASCADE,
  predicate text NOT NULL CHECK (predicate IN ('same_as','variant_of','parent_of','sibling_of','similar_to','substitute_for')),
  object_dish_id uuid NOT NULL REFERENCES ontology.dishes(id) ON DELETE CASCADE,
  score numeric(5,4) NOT NULL CHECK (score BETWEEN 0 AND 1),
  explanation_features text[] NOT NULL DEFAULT '{}',
  assertion_id uuid NOT NULL REFERENCES ontology.assertions(id) ON DELETE RESTRICT,
  UNIQUE (subject_dish_id,predicate,object_dish_id),
  CHECK (subject_dish_id <> object_dish_id)
);
CREATE INDEX dish_relationships_reverse ON ontology.dish_relationships(object_dish_id,predicate);

CREATE TABLE ontology.image_assets (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  cloudinary_public_id text NOT NULL UNIQUE,
  cloudinary_asset_id text,
  cloudinary_version bigint,
  secure_url text NOT NULL CHECK (secure_url LIKE 'https://%'),
  checksum_sha256 text NOT NULL UNIQUE CHECK (checksum_sha256 ~ '^[a-f0-9]{64}$'),
  perceptual_hash text,
  source_type text NOT NULL CHECK (source_type IN ('licensed_source','ai_generated','human_upload')),
  licence_code text,
  attribution text,
  prompt_text text,
  model_name text,
  model_version text,
  generation_seed bigint,
  moderation_status text NOT NULL DEFAULT 'pending' CHECK (moderation_status IN ('pending','accepted','rejected')),
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK (source_type <> 'licensed_source' OR licence_code IS NOT NULL)
);

CREATE TABLE ontology.dish_images (
  dish_id uuid NOT NULL REFERENCES ontology.dishes(id) ON DELETE CASCADE,
  image_asset_id uuid NOT NULL REFERENCES ontology.image_assets(id) ON DELETE RESTRICT,
  is_primary boolean NOT NULL DEFAULT false,
  review_status ontology.review_status NOT NULL DEFAULT 'provisional',
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (dish_id,image_asset_id)
);
CREATE UNIQUE INDEX dish_images_primary ON ontology.dish_images(dish_id) WHERE is_primary AND review_status='accepted';

CREATE TABLE ontology.jobs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  dish_id uuid REFERENCES ontology.dishes(id) ON DELETE CASCADE,
  kind text NOT NULL CHECK (kind IN ('enrich','classify','similarity','image','publish')),
  deduplication_key text NOT NULL,
  requested_fields text[] NOT NULL DEFAULT '{}',
  priority smallint NOT NULL DEFAULT 50 CHECK (priority BETWEEN 0 AND 100),
  status ontology.job_status NOT NULL DEFAULT 'queued',
  attempts smallint NOT NULL DEFAULT 0,
  max_attempts smallint NOT NULL DEFAULT 8,
  next_attempt_at timestamptz NOT NULL DEFAULT now(),
  locked_by text,
  lease_expires_at timestamptz,
  last_error_code text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX jobs_due ON ontology.jobs(priority DESC,next_attempt_at,created_at)
  WHERE status IN ('queued','retry');
CREATE UNIQUE INDEX jobs_active_deduplication ON ontology.jobs(deduplication_key)
  WHERE status IN ('queued','running','retry');

CREATE FUNCTION ontology.claim_jobs(p_worker_id text, p_limit integer DEFAULT 20)
RETURNS SETOF ontology.jobs LANGUAGE plpgsql SECURITY DEFINER SET search_path=ontology,pg_temp AS $$
BEGIN
  IF length(btrim(coalesce(p_worker_id,''))) < 3 THEN RAISE EXCEPTION 'worker_id_required'; END IF;
  RETURN QUERY
  WITH due AS (
    SELECT id FROM ontology.jobs
    WHERE status IN ('queued','retry') AND next_attempt_at<=now()
      AND (lease_expires_at IS NULL OR lease_expires_at<now()) AND attempts<max_attempts
    ORDER BY priority DESC,next_attempt_at,created_at
    FOR UPDATE SKIP LOCKED LIMIT greatest(1,least(coalesce(p_limit,20),100))
  )
  UPDATE ontology.jobs j SET status='running',attempts=j.attempts+1,locked_by=p_worker_id,
    lease_expires_at=now()+interval '5 minutes',updated_at=now()
  FROM due WHERE j.id=due.id RETURNING j.*;
END $$;

CREATE FUNCTION ontology.finish_job(
  p_job_id uuid,p_worker_id text,p_outcome text,p_error_code text DEFAULT NULL
) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=ontology,pg_temp AS $$
BEGIN
  IF p_outcome NOT IN ('complete','review','retry','dead') THEN RAISE EXCEPTION 'invalid_outcome'; END IF;
  UPDATE ontology.jobs SET
    status=p_outcome::ontology.job_status,
    next_attempt_at=CASE WHEN p_outcome='retry'
      THEN now()+least(interval '24 hours',interval '1 minute'*power(2,attempts)) ELSE next_attempt_at END,
    last_error_code=left(p_error_code,120),locked_by=NULL,lease_expires_at=NULL,updated_at=now()
  WHERE id=p_job_id AND locked_by=p_worker_id AND status='running';
  IF NOT FOUND THEN RAISE EXCEPTION 'job_lease_not_owned'; END IF;
END $$;

CREATE FUNCTION ontology.reconcile_jobs() RETURNS integer LANGUAGE plpgsql
SECURITY DEFINER SET search_path=ontology,pg_temp AS $$
DECLARE affected integer;
BEGIN
  UPDATE ontology.jobs SET status=(CASE WHEN attempts>=max_attempts THEN 'dead' ELSE 'retry' END)::ontology.job_status,
    next_attempt_at=now(),locked_by=NULL,lease_expires_at=NULL,last_error_code='lease_expired',updated_at=now()
  WHERE status='running' AND lease_expires_at<now();
  GET DIAGNOSTICS affected=ROW_COUNT;
  RETURN affected;
END $$;

CREATE TABLE ontology.review_tasks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workflow_type text NOT NULL CHECK (workflow_type IN ('ingestion','field','relationship','image','safety')),
  subject_type text NOT NULL,
  subject_id uuid NOT NULL,
  field_path text,
  reason_code text NOT NULL,
  risk_tier text NOT NULL CHECK (risk_tier IN ('low','medium','high','safety')),
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','assigned','accepted','rejected','superseded')),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE ontology.review_decisions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  review_task_id uuid NOT NULL REFERENCES ontology.review_tasks(id) ON DELETE RESTRICT,
  decision text NOT NULL CHECK (decision IN ('accepted','rejected','superseded')),
  reason text NOT NULL,
  reviewer_principal text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE FUNCTION ontology.prevent_decision_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'review decisions are immutable'; END $$;
CREATE TRIGGER review_decisions_immutable BEFORE UPDATE OR DELETE ON ontology.review_decisions
FOR EACH ROW EXECUTE FUNCTION ontology.prevent_decision_mutation();

CREATE TABLE ontology.correction_submissions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  dish_id uuid NOT NULL REFERENCES ontology.dishes(id) ON DELETE CASCADE,
  field_path text NOT NULL,
  proposed_value jsonb NOT NULL,
  reason text NOT NULL,
  actor_reference text,
  submitted_by_principal text NOT NULL,
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','accepted','rejected','superseded')),
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX correction_submissions_pending ON ontology.correction_submissions(created_at)
  WHERE status='pending';

CREATE TABLE ontology.idempotency_records (
  principal text NOT NULL,
  operation text NOT NULL,
  idempotency_key text NOT NULL,
  request_sha256 text NOT NULL,
  response_status smallint NOT NULL,
  response_body jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz NOT NULL DEFAULT now()+interval '24 hours',
  PRIMARY KEY (principal,operation,idempotency_key)
);

CREATE TABLE ontology.catalogue_versions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  content_sha256 text NOT NULL UNIQUE,
  schema_version text NOT NULL,
  status text NOT NULL CHECK (status IN ('building','validated','published','retired','failed')),
  manifest jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  published_at timestamptz
);

-- Runtime roles are created by infrastructure, never by this migration. Grant only explicit
-- least-privilege roles there; the Foofoo app receives API credentials, not database access.
