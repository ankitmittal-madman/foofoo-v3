-- Migration: 072_normalize_ontology_policy_and_ai_lineage.sql
-- Replaces array-only AI lineage with normalized inputs/links and makes the founder-approved
-- field policy executable. Safety exclusions and confidence bands are enforced independently of
-- the Edge worker prompt.

CREATE TABLE ops.ai_generation_run_inputs (
  ai_generation_run_id uuid NOT NULL REFERENCES ops.ai_generation_runs(id) ON DELETE CASCADE,
  input_sequence smallint NOT NULL CHECK(input_sequence>0),
  data_source_id uuid REFERENCES ops.data_sources(id) ON DELETE RESTRICT,
  source_record_id uuid REFERENCES public.food_source_records(id) ON DELETE SET NULL,
  input_artifact_uri text,
  input_checksum text,
  purpose_code text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY(ai_generation_run_id,input_sequence),
  CHECK(num_nonnulls(source_record_id,input_artifact_uri)>=1)
);
CREATE INDEX ai_generation_run_inputs_source ON ops.ai_generation_run_inputs(source_record_id);

CREATE TABLE ops.assertion_sources (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  assertion_type_code text NOT NULL,
  assertion_id uuid NOT NULL,
  data_source_id uuid REFERENCES ops.data_sources(id) ON DELETE RESTRICT,
  source_record_id uuid REFERENCES public.food_source_records(id) ON DELETE SET NULL,
  evidence_role_code text NOT NULL DEFAULT 'supports' CHECK(
    evidence_role_code IN ('supports','contradicts','derived_from','supersedes')
  ),
  source_locator text,
  evidence_checksum text,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(assertion_type_code,assertion_id,source_record_id,evidence_role_code)
);
CREATE INDEX assertion_sources_assertion ON ops.assertion_sources(assertion_type_code,assertion_id);

CREATE TABLE ops.assertion_ai_runs (
  assertion_type_code text NOT NULL,
  assertion_id uuid NOT NULL,
  ai_generation_run_id uuid NOT NULL REFERENCES ops.ai_generation_runs(id) ON DELETE CASCADE,
  proposal_role_code text NOT NULL DEFAULT 'generated' CHECK(
    proposal_role_code IN ('generated','validated','selected','rejected')
  ),
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY(assertion_type_code,assertion_id,ai_generation_run_id,proposal_role_code)
);

CREATE TABLE food.ontology_field_policies (
  policy_version text NOT NULL,
  field_key text NOT NULL,
  risk_tier text NOT NULL CHECK(risk_tier IN ('low','medium','high','safety')),
  required_source_types text[] NOT NULL DEFAULT '{}',
  candidate_threshold numeric(4,3) CHECK(candidate_threshold BETWEEN 0 AND 1),
  auto_publish_threshold numeric(4,3) CHECK(auto_publish_threshold BETWEEN 0 AND 1),
  human_review_count smallint NOT NULL DEFAULT 0 CHECK(human_review_count>=0),
  is_safety_field boolean NOT NULL DEFAULT false,
  is_primary_required boolean NOT NULL DEFAULT false,
  effective_from timestamptz NOT NULL DEFAULT now(),
  effective_until timestamptz,
  approved_by text NOT NULL,
  policy_checksum text NOT NULL,
  PRIMARY KEY(policy_version,field_key),
  CHECK(auto_publish_threshold IS NULL OR candidate_threshold IS NOT NULL),
  CHECK(auto_publish_threshold IS NULL OR auto_publish_threshold>=candidate_threshold),
  CHECK(NOT is_safety_field OR auto_publish_threshold IS NULL)
);
CREATE UNIQUE INDEX ontology_field_policies_active_field
  ON food.ontology_field_policies(field_key) WHERE effective_until IS NULL;

CREATE TABLE food.ontology_review_decisions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  assertion_type_code text NOT NULL,
  assertion_id uuid NOT NULL,
  risk_tier text NOT NULL CHECK(risk_tier IN ('low','medium','high','safety')),
  reviewer_profile_id uuid REFERENCES auth.users(id) ON DELETE SET NULL,
  decision_code text NOT NULL CHECK(decision_code IN ('accepted','rejected','needs_evidence','superseded')),
  reason_code text NOT NULL,
  evidence_note text,
  occurred_at timestamptz NOT NULL DEFAULT now(),
  policy_version text NOT NULL,
  supersedes_decision_id uuid REFERENCES food.ontology_review_decisions(id) ON DELETE RESTRICT
);
CREATE INDEX ontology_review_decisions_assertion
  ON food.ontology_review_decisions(assertion_type_code,assertion_id,occurred_at DESC);

INSERT INTO food.ontology_field_policies(policy_version,field_key,risk_tier,
  required_source_types,candidate_threshold,auto_publish_threshold,human_review_count,
  is_safety_field,is_primary_required,approved_by,policy_checksum)
SELECT 'groq-low-risk-v1',field_key,'low',ARRAY['ml_model'],0.65,0.80,0,false,false,
  'founder-decision-2026-08-05','groq-low-risk-v1-065-080-safety-excluded'
FROM unnest(ARRAY['alias_candidate','cooking_method','spice_level','heaviness','texture',
  'richness','weather_affinity','regional_affinity_candidate']) field_key
ON CONFLICT DO NOTHING;

INSERT INTO food.ontology_field_policies(policy_version,field_key,risk_tier,
  required_source_types,candidate_threshold,auto_publish_threshold,human_review_count,
  is_safety_field,is_primary_required,approved_by,policy_checksum)
SELECT 'groq-low-risk-v1',field_key,'safety',ARRAY['external_api','human_review'],NULL,NULL,1,true,
  false,'founder-decision-2026-08-05','groq-low-risk-v1-safety-no-ai'
FROM unnest(ARRAY['ingredient','allergen','nutrition','religious_suitability',
  'clinical_suitability','vegetarian_status','alcohol_status']) field_key
ON CONFLICT DO NOTHING;

CREATE OR REPLACE FUNCTION public.enforce_groq_ontology_field_policy()
RETURNS trigger LANGUAGE plpgsql SET search_path=public,food,pg_temp AS $$
DECLARE v_policy food.ontology_field_policies%ROWTYPE;
BEGIN
  IF NEW.source_name<>'groq' THEN RETURN NEW; END IF;
  SELECT * INTO v_policy FROM food.ontology_field_policies
  WHERE policy_version='groq-low-risk-v1' AND field_key=NEW.field_key
    AND effective_from<=now() AND effective_until IS NULL;
  IF NOT FOUND THEN RAISE EXCEPTION 'groq field is not allowlisted: %',NEW.field_key; END IF;
  IF v_policy.is_safety_field THEN RAISE EXCEPTION 'groq cannot assert safety field: %',NEW.field_key; END IF;
  IF NEW.confidence<v_policy.candidate_threshold THEN
    RAISE EXCEPTION 'groq candidate below field policy threshold';
  END IF;
  IF NEW.review_status='accepted' AND (
    v_policy.auto_publish_threshold IS NULL OR NEW.confidence<v_policy.auto_publish_threshold
  ) THEN RAISE EXCEPTION 'groq accepted assertion below auto-publish threshold'; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER dish_taxonomy_assertions_groq_field_policy
BEFORE INSERT OR UPDATE ON public.dish_taxonomy_assertions
FOR EACH ROW EXECUTE FUNCTION public.enforce_groq_ontology_field_policy();

CREATE OR REPLACE FUNCTION food.prevent_ontology_review_decision_mutation()
RETURNS trigger LANGUAGE plpgsql SET search_path=food,pg_temp AS $$
BEGIN RAISE EXCEPTION 'ontology review decisions are immutable'; END $$;
CREATE TRIGGER ontology_review_decisions_immutable
BEFORE UPDATE OR DELETE ON food.ontology_review_decisions
FOR EACH ROW EXECUTE FUNCTION food.prevent_ontology_review_decision_mutation();

INSERT INTO ops.ai_generation_run_inputs(ai_generation_run_id,input_sequence,data_source_id,
  source_record_id,input_checksum,purpose_code,created_at)
SELECT r.id,u.ordinality::smallint,ds.id,s.id,s.payload_sha256,'canonical_dish_ontology',r.created_at
FROM ops.ai_generation_runs r
CROSS JOIN LATERAL unnest(r.input_source_ids) WITH ORDINALITY u(source_id,ordinality)
JOIN public.food_source_records s ON s.id=u.source_id
LEFT JOIN ops.data_sources ds ON ds.source_code=CASE s.provider WHEN 'groq' THEN 'groq_free' ELSE s.provider END
ON CONFLICT DO NOTHING;

INSERT INTO ops.assertion_sources(assertion_type_code,assertion_id,data_source_id,source_record_id,
  evidence_role_code,source_locator,evidence_checksum,created_at)
SELECT 'dish_taxonomy_assertion',a.id,ds.id,s.id,'supports',s.source_url,s.payload_sha256,a.created_at
FROM public.dish_taxonomy_assertions a JOIN public.food_source_records s ON s.id=a.source_record_id
LEFT JOIN ops.data_sources ds ON ds.source_code=CASE s.provider WHEN 'groq' THEN 'groq_free' ELSE s.provider END
ON CONFLICT DO NOTHING;

INSERT INTO ops.assertion_sources(assertion_type_code,assertion_id,data_source_id,source_record_id,
  evidence_role_code,source_locator,evidence_checksum,created_at)
SELECT 'nutrient_assertion',a.id,ds.id,s.id,'supports',s.source_url,s.payload_sha256,a.created_at
FROM food.nutrient_assertions a JOIN public.food_source_records s ON s.id=a.source_record_id
LEFT JOIN ops.data_sources ds ON ds.source_code=CASE s.provider WHEN 'groq' THEN 'groq_free' ELSE s.provider END
ON CONFLICT DO NOTHING;

INSERT INTO ops.assertion_ai_runs(assertion_type_code,assertion_id,ai_generation_run_id,
  proposal_role_code,created_at)
SELECT DISTINCT src.assertion_type_code,src.assertion_id,input.ai_generation_run_id,
  CASE WHEN a.review_status='accepted' THEN 'selected' ELSE 'generated' END,a.created_at
FROM ops.assertion_sources src
JOIN public.dish_taxonomy_assertions a ON src.assertion_type_code='dish_taxonomy_assertion'
  AND a.id=src.assertion_id
JOIN ops.ai_generation_run_inputs input ON input.source_record_id=src.source_record_id
ON CONFLICT DO NOTHING;

ALTER TABLE ops.ai_generation_run_inputs ENABLE ROW LEVEL SECURITY;
ALTER TABLE ops.assertion_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE ops.assertion_ai_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE food.ontology_field_policies ENABLE ROW LEVEL SECURITY;
ALTER TABLE food.ontology_review_decisions ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON ops.ai_generation_run_inputs,ops.assertion_sources,ops.assertion_ai_runs,
  food.ontology_field_policies,food.ontology_review_decisions FROM PUBLIC,anon,authenticated;
GRANT SELECT,INSERT,UPDATE,DELETE ON ops.ai_generation_run_inputs,ops.assertion_sources,
  ops.assertion_ai_runs TO service_role;
GRANT SELECT ON food.ontology_field_policies TO service_role;
GRANT SELECT,INSERT ON food.ontology_review_decisions TO service_role;
REVOKE ALL ON FUNCTION public.enforce_groq_ontology_field_policy() FROM PUBLIC,anon,authenticated;
REVOKE ALL ON FUNCTION food.prevent_ontology_review_decision_mutation() FROM PUBLIC,anon,authenticated;

COMMENT ON TABLE food.ontology_field_policies IS
  'Executable per-field risk and confidence authority; generative safety publication is structurally disabled.';
COMMENT ON TABLE ops.assertion_ai_runs IS
  'Normalized link from an AI run to each assertion it generated or selected.';
