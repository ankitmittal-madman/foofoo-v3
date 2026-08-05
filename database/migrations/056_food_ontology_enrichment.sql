-- Migration: 056_food_ontology_enrichment.sql
-- Food ontology and meal-taxonomy ingestion gate.
--
-- Every canonical dish is queued by a database trigger, including rows written outside the API.
-- Source payloads stay in staging tables; reviewed current values and class mappings are normalized;
-- runtime candidate reads use the final view and cannot mix add-on-only items into primary pools.

ALTER TABLE public.meal_classes
  ADD COLUMN parent_class_code text REFERENCES public.meal_classes(class_code),
  ADD COLUMN class_family_code text,
  ADD COLUMN planning_role text NOT NULL DEFAULT 'MAIN_PRIMARY'
    CHECK (planning_role IN ('MAIN_PRIMARY','ADDON_ONLY_NOT_PRIMARY','COMBO_TEMPLATE_NOT_PRIMARY')),
  ADD COLUMN weekday_fit_1_5 smallint CHECK (weekday_fit_1_5 BETWEEN 1 AND 5),
  ADD COLUMN weekend_fit_1_5 smallint CHECK (weekend_fit_1_5 BETWEEN 1 AND 5);

UPDATE public.meal_classes
SET planning_role = CASE WHEN is_addon THEN 'ADDON_ONLY_NOT_PRIMARY' ELSE 'MAIN_PRIMARY' END;

CREATE TABLE public.meal_class_families (
  family_code text PRIMARY KEY,
  display_name text NOT NULL,
  parent_family_code text REFERENCES public.meal_class_families(family_code),
  is_active boolean NOT NULL DEFAULT true
);

ALTER TABLE public.meal_classes
  ADD CONSTRAINT meal_classes_family_fkey
  FOREIGN KEY (class_family_code) REFERENCES public.meal_class_families(family_code);

CREATE TABLE public.taxonomy_terms (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  dimension text NOT NULL CHECK (dimension IN (
    'cuisine','diet_type','cooking_method','spice_level','heaviness','texture','richness',
    'weather_affinity','constraint','slot','regional_affinity','item_role','external_food_term'
  )),
  code text NOT NULL,
  display_name text NOT NULL,
  parent_id uuid REFERENCES public.taxonomy_terms(id),
  external_uri text,
  is_active boolean NOT NULL DEFAULT true,
  UNIQUE (dimension, code)
);

CREATE TABLE public.taxonomy_term_aliases (
  term_id uuid NOT NULL REFERENCES public.taxonomy_terms(id) ON DELETE CASCADE,
  alias text NOT NULL,
  language text NOT NULL DEFAULT 'en',
  region text,
  source_name text NOT NULL,
  source_url text,
  confidence numeric(4,3) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
  PRIMARY KEY (term_id, alias, language)
);

-- User input lands here first. It is not recommendation-eligible until it has been normalized and
-- promoted to public.dishes by a service-role workflow.
CREATE TABLE public.dish_submissions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  submitted_by uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  entered_name text NOT NULL CHECK (length(btrim(entered_name)) BETWEEN 2 AND 160),
  submitted_metadata jsonb NOT NULL DEFAULT '{}',
  canonical_dish_id uuid REFERENCES public.dishes(id) ON DELETE SET NULL,
  status text NOT NULL DEFAULT 'pending' CHECK (
    status IN ('pending','researching','pending_ai','review','resolved','rejected','failed')
  ),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- Raw external responses are staged, hashed and retained separately from normalized product truth.
CREATE TABLE public.food_source_records (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  provider text NOT NULL,
  provider_record_id text,
  dish_id uuid REFERENCES public.dishes(id) ON DELETE CASCADE,
  submission_id uuid REFERENCES public.dish_submissions(id) ON DELETE CASCADE,
  query_text text NOT NULL,
  source_url text,
  source_payload jsonb NOT NULL,
  payload_sha256 text NOT NULL,
  fetched_at timestamptz NOT NULL DEFAULT now(),
  CHECK ((dish_id IS NOT NULL)::integer + (submission_id IS NOT NULL)::integer = 1)
);

CREATE TABLE public.dish_enrichment_jobs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  dish_id uuid REFERENCES public.dishes(id) ON DELETE CASCADE,
  submission_id uuid REFERENCES public.dish_submissions(id) ON DELETE CASCADE,
  status text NOT NULL DEFAULT 'pending_external' CHECK (status IN (
    'pending_external','external_complete','pending_ai','review','complete','failed'
  )),
  missing_fields text[] NOT NULL DEFAULT '{}',
  attempts smallint NOT NULL DEFAULT 0 CHECK (attempts >= 0),
  last_error_code text,
  locked_at timestamptz,
  locked_by text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CHECK ((dish_id IS NOT NULL)::integer + (submission_id IS NOT NULL)::integer = 1)
);
CREATE UNIQUE INDEX dish_enrichment_jobs_active_dish
  ON public.dish_enrichment_jobs (dish_id)
  WHERE dish_id IS NOT NULL AND status NOT IN ('complete','failed');
CREATE UNIQUE INDEX dish_enrichment_jobs_active_submission
  ON public.dish_enrichment_jobs (submission_id)
  WHERE submission_id IS NOT NULL AND status NOT IN ('complete','failed');

-- Candidate assertions are append-only evidence. A separate pointer chooses current truth, so an
-- inference never destroys earlier research or a human-reviewed value.
CREATE TABLE public.dish_taxonomy_assertions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  dish_id uuid REFERENCES public.dishes(id) ON DELETE CASCADE,
  submission_id uuid REFERENCES public.dish_submissions(id) ON DELETE CASCADE,
  field_key text NOT NULL,
  term_id uuid REFERENCES public.taxonomy_terms(id),
  value_text text,
  value_json jsonb,
  confidence numeric(4,3) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
  source_name text NOT NULL,
  source_type text NOT NULL CHECK (source_type IN (
    'user','internal_research','external_api','rules','ml_model','human_review'
  )),
  source_record_id uuid REFERENCES public.food_source_records(id) ON DELETE SET NULL,
  source_url text,
  model_name text,
  model_version text,
  review_status text NOT NULL DEFAULT 'provisional' CHECK (
    review_status IN ('provisional','accepted','rejected')
  ),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CHECK ((dish_id IS NOT NULL)::integer + (submission_id IS NOT NULL)::integer = 1),
  CHECK (num_nonnulls(term_id, value_text, value_json) = 1),
  CHECK (source_type <> 'ml_model' OR model_name IS NOT NULL)
);
CREATE INDEX dish_taxonomy_assertions_dish_field
  ON public.dish_taxonomy_assertions (dish_id, field_key, confidence DESC);

CREATE TABLE public.dish_taxonomy_current (
  dish_id uuid NOT NULL REFERENCES public.dishes(id) ON DELETE CASCADE,
  field_key text NOT NULL,
  assertion_id uuid NOT NULL UNIQUE REFERENCES public.dish_taxonomy_assertions(id),
  selected_at timestamptz NOT NULL DEFAULT now(),
  selected_by text NOT NULL,
  PRIMARY KEY (dish_id, field_key)
);

CREATE TABLE public.dish_meal_class_mappings (
  dish_id uuid NOT NULL REFERENCES public.dishes(id) ON DELETE CASCADE,
  class_code text NOT NULL REFERENCES public.meal_classes(class_code),
  slot text NOT NULL CHECK (slot IN ('breakfast','lunch','dinner','snack')),
  item_role text NOT NULL CHECK (item_role IN ('primary','addon','combo_component')),
  confidence numeric(4,3) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
  source_name text NOT NULL,
  classification_method text NOT NULL,
  source_type text NOT NULL CHECK (source_type IN (
    'internal_research','external_api','rules','ml_model','human_review'
  )),
  source_url text,
  model_name text,
  model_version text,
  review_status text NOT NULL DEFAULT 'provisional' CHECK (
    review_status IN ('provisional','accepted','rejected')
  ),
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (dish_id, class_code, slot),
  CHECK (source_type <> 'ml_model' OR model_name IS NOT NULL)
);
CREATE INDEX dish_meal_class_candidates
  ON public.dish_meal_class_mappings (class_code, slot, confidence DESC)
  WHERE review_status <> 'rejected';

CREATE TABLE public.dish_constraints (
  dish_id uuid NOT NULL REFERENCES public.dishes(id) ON DELETE CASCADE,
  constraint_code text NOT NULL,
  suitability text NOT NULL CHECK (suitability IN ('allowed','excluded','conditional')),
  confidence numeric(4,3) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
  source_name text NOT NULL,
  source_type text NOT NULL CHECK (source_type IN (
    'internal_research','external_api','rules','ml_model','human_review'
  )),
  review_status text NOT NULL DEFAULT 'provisional' CHECK (
    review_status IN ('provisional','accepted','rejected')
  ),
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (dish_id, constraint_code)
);

CREATE TABLE public.dish_regional_affinities (
  dish_id uuid NOT NULL REFERENCES public.dishes(id) ON DELETE CASCADE,
  region_code text NOT NULL,
  affinity_score numeric(4,3) NOT NULL CHECK (affinity_score BETWEEN 0 AND 1),
  confidence numeric(4,3) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
  source_name text NOT NULL,
  source_type text NOT NULL CHECK (source_type IN (
    'internal_research','external_api','rules','ml_model','human_review'
  )),
  review_status text NOT NULL DEFAULT 'provisional' CHECK (
    review_status IN ('provisional','accepted','rejected')
  ),
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (dish_id, region_code)
);

ALTER TABLE public.dishes
  ADD COLUMN ontology_status text NOT NULL DEFAULT 'pending' CHECK (
    ontology_status IN ('pending','researching','pending_ai','review','enriched','rejected','failed')
  ),
  ADD COLUMN ontology_confidence numeric(4,3) CHECK (ontology_confidence BETWEEN 0 AND 1),
  ADD COLUMN ontology_last_reviewed_at timestamptz;

CREATE OR REPLACE FUNCTION public.enqueue_dish_enrichment()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
BEGIN
  IF TG_OP = 'INSERT' OR
     ROW(NEW.name, NEW.description, NEW.meal_occasion, NEW.cuisine_id) IS DISTINCT FROM
     ROW(OLD.name, OLD.description, OLD.meal_occasion, OLD.cuisine_id) THEN
    NEW.ontology_status := 'pending';
    NEW.ontology_confidence := NULL;
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER dishes_mark_ontology_pending
BEFORE INSERT OR UPDATE OF name, description, meal_occasion, cuisine_id ON public.dishes
FOR EACH ROW EXECUTE FUNCTION public.enqueue_dish_enrichment();

CREATE OR REPLACE FUNCTION public.create_dish_enrichment_job()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
BEGIN
  INSERT INTO public.dish_enrichment_jobs (dish_id, missing_fields)
  VALUES (NEW.id, ARRAY[
    'meal_class','cuisine','diet_type','cooking_method','spice_level','heaviness',
    'texture','richness','weather_affinity','constraints','slot_eligibility','regional_affinity'
  ])
  ON CONFLICT DO NOTHING;
  RETURN NEW;
END;
$$;

CREATE TRIGGER dishes_queue_ontology_enrichment
AFTER INSERT OR UPDATE OF name, description, meal_occasion, cuisine_id ON public.dishes
FOR EACH ROW EXECUTE FUNCTION public.create_dish_enrichment_job();

CREATE OR REPLACE FUNCTION public.create_submission_enrichment_job()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
BEGIN
  INSERT INTO public.dish_enrichment_jobs (submission_id, missing_fields)
  VALUES (NEW.id, ARRAY[
    'canonical_dish','meal_class','cuisine','diet_type','cooking_method','spice_level',
    'heaviness','texture','richness','weather_affinity','constraints','slot_eligibility',
    'regional_affinity'
  ])
  ON CONFLICT DO NOTHING;
  RETURN NEW;
END;
$$;

CREATE TRIGGER dish_submissions_queue_enrichment
AFTER INSERT OR UPDATE OF entered_name, submitted_metadata ON public.dish_submissions
FOR EACH ROW EXECUTE FUNCTION public.create_submission_enrichment_job();

-- Enforce the add-on invariant against the canonical meal-class row.
CREATE OR REPLACE FUNCTION public.validate_dish_class_role()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE class_is_addon boolean;
DECLARE class_role text;
BEGIN
  SELECT is_addon, planning_role INTO class_is_addon, class_role
  FROM public.meal_classes WHERE class_code = NEW.class_code;
  IF NEW.item_role = 'primary' AND
     (class_is_addon OR class_role <> 'MAIN_PRIMARY') THEN
    RAISE EXCEPTION 'add-on/combo class % cannot enter a primary dish pool', NEW.class_code;
  END IF;
  IF NEW.item_role = 'addon' AND NOT class_is_addon THEN
    RAISE EXCEPTION 'primary class % cannot be stored as an add-on mapping', NEW.class_code;
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER dish_meal_class_role_guard
BEFORE INSERT OR UPDATE ON public.dish_meal_class_mappings
FOR EACH ROW EXECUTE FUNCTION public.validate_dish_class_role();

-- Prevent automatic selection from replacing accepted human/canonical truth with weaker evidence.
CREATE OR REPLACE FUNCTION public.protect_reviewed_taxonomy_value()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE old_confidence numeric;
DECLARE old_review text;
DECLARE new_confidence numeric;
DECLARE new_source_type text;
BEGIN
  IF TG_OP = 'UPDATE' AND OLD.assertion_id <> NEW.assertion_id THEN
    SELECT confidence, review_status INTO old_confidence, old_review
    FROM public.dish_taxonomy_assertions WHERE id = OLD.assertion_id;
    SELECT confidence, source_type INTO new_confidence, new_source_type
    FROM public.dish_taxonomy_assertions WHERE id = NEW.assertion_id;
    IF old_review = 'accepted' AND new_source_type <> 'human_review' THEN
      RAISE EXCEPTION 'accepted taxonomy value requires human review to replace';
    END IF;
    IF new_confidence < old_confidence THEN
      RAISE EXCEPTION 'lower-confidence taxonomy value cannot replace current value';
    END IF;
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER dish_taxonomy_current_guard
BEFORE UPDATE ON public.dish_taxonomy_current
FOR EACH ROW EXECUTE FUNCTION public.protect_reviewed_taxonomy_value();

CREATE OR REPLACE FUNCTION public.validate_current_taxonomy_assertion()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM public.dish_taxonomy_assertions a
    WHERE a.id = NEW.assertion_id
      AND a.dish_id = NEW.dish_id
      AND a.field_key = NEW.field_key
      AND a.review_status <> 'rejected'
  ) THEN
    RAISE EXCEPTION 'current taxonomy selection must match dish and field and not be rejected';
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER dish_taxonomy_current_integrity_guard
BEFORE INSERT OR UPDATE ON public.dish_taxonomy_current
FOR EACH ROW EXECUTE FUNCTION public.validate_current_taxonomy_assertion();

CREATE VIEW public.dish_candidates_by_class WITH (security_invoker = true) AS
SELECT
  m.class_code,
  m.slot,
  m.item_role,
  m.confidence AS classification_confidence,
  m.classification_method,
  m.review_status,
  d.id AS dish_id,
  d.name,
  d.description,
  d.diet_type,
  d.is_jain,
  d.allergen_flags,
  d.meal_occasion,
  d.cook_time_minutes,
  d.popularity_score,
  d.ontology_status,
  d.ontology_confidence,
  c.name AS cuisine
FROM public.dish_meal_class_mappings m
JOIN public.dishes d ON d.id = m.dish_id
LEFT JOIN public.cuisines c ON c.id = d.cuisine_id
WHERE d.is_active
  AND d.ontology_status IN ('enriched','review')
  AND m.review_status <> 'rejected';

CREATE VIEW public.dish_ontology_coverage WITH (security_invoker = true) AS
SELECT
  d.id AS dish_id,
  d.name,
  d.ontology_status,
  d.ontology_confidence,
  count(DISTINCT cur.field_key) AS selected_field_count,
  count(DISTINCT m.class_code) FILTER (WHERE m.review_status <> 'rejected') AS meal_class_count,
  max(coalesce(cur.selected_at, m.updated_at)) AS last_taxonomy_update
FROM public.dishes d
LEFT JOIN public.dish_taxonomy_current cur ON cur.dish_id = d.id
LEFT JOIN public.dish_meal_class_mappings m ON m.dish_id = d.id
GROUP BY d.id, d.name, d.ontology_status, d.ontology_confidence;

CREATE VIEW public.dish_taxonomy_review_queue WITH (security_invoker = true) AS
SELECT d.id AS dish_id, d.name, d.ontology_status, d.ontology_confidence,
       j.id AS job_id, j.status AS job_status, j.missing_fields, j.updated_at
FROM public.dishes d
JOIN public.dish_enrichment_jobs j ON j.dish_id = d.id
WHERE d.ontology_status IN ('pending','pending_ai','review','failed')
   OR j.status IN ('pending_external','pending_ai','review','failed');

-- Existing catalogue rows also enter the same pipeline; the idempotent research seed may resolve
-- them immediately after this migration, while future inserts are caught by the trigger above.
INSERT INTO public.dish_enrichment_jobs (dish_id, missing_fields)
SELECT id, ARRAY[
  'meal_class','cuisine','diet_type','cooking_method','spice_level','heaviness',
  'texture','richness','weather_affinity','constraints','slot_eligibility','regional_affinity'
]
FROM public.dishes
ON CONFLICT DO NOTHING;

ALTER TABLE public.meal_class_families ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.taxonomy_terms ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.taxonomy_term_aliases ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dish_submissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.food_source_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dish_enrichment_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dish_taxonomy_assertions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dish_taxonomy_current ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dish_meal_class_mappings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dish_constraints ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dish_regional_affinities ENABLE ROW LEVEL SECURITY;

CREATE POLICY meal_class_families_public_read ON public.meal_class_families FOR SELECT USING (true);
CREATE POLICY taxonomy_terms_public_read ON public.taxonomy_terms FOR SELECT USING (true);
CREATE POLICY taxonomy_term_aliases_public_read ON public.taxonomy_term_aliases FOR SELECT USING (true);
CREATE POLICY dish_meal_class_mappings_public_read ON public.dish_meal_class_mappings FOR SELECT USING (true);
CREATE POLICY dish_constraints_public_read ON public.dish_constraints FOR SELECT USING (true);
CREATE POLICY dish_regional_affinities_public_read ON public.dish_regional_affinities FOR SELECT USING (true);
CREATE POLICY dish_taxonomy_current_public_read ON public.dish_taxonomy_current FOR SELECT USING (true);
CREATE POLICY dish_taxonomy_assertions_public_read ON public.dish_taxonomy_assertions FOR SELECT USING (dish_id IS NOT NULL);
CREATE POLICY dish_submissions_select_own ON public.dish_submissions FOR SELECT
  USING ((select auth.uid()) = submitted_by);
CREATE POLICY dish_submissions_insert_own ON public.dish_submissions FOR INSERT
  WITH CHECK ((select auth.uid()) = submitted_by);
CREATE POLICY food_source_records_select_own_submission ON public.food_source_records FOR SELECT
  USING (EXISTS (
    SELECT 1 FROM public.dish_submissions s
    WHERE s.id = submission_id AND s.submitted_by = (select auth.uid())
  ));
CREATE POLICY dish_enrichment_jobs_select_own_submission ON public.dish_enrichment_jobs FOR SELECT
  USING (EXISTS (
    SELECT 1 FROM public.dish_submissions s
    WHERE s.id = submission_id AND s.submitted_by = (select auth.uid())
  ));

REVOKE INSERT, UPDATE, DELETE ON public.meal_class_families, public.taxonomy_terms,
  public.taxonomy_term_aliases, public.food_source_records, public.dish_enrichment_jobs,
  public.dish_taxonomy_assertions, public.dish_taxonomy_current,
  public.dish_meal_class_mappings, public.dish_constraints, public.dish_regional_affinities
FROM anon, authenticated;
REVOKE UPDATE, DELETE ON public.dish_submissions FROM anon, authenticated;

COMMENT ON VIEW public.dish_candidates_by_class IS
  'Recommendation read model: class-bound active dishes with provenance-backed classifications; item_role keeps add-ons out of primary pools.';
COMMENT ON TABLE public.food_source_records IS
  'Staging-only, immutable external research responses. Normalized recommendation truth lives in assertion/current/mapping tables.';
