-- Safe, repeatable control plane for DB-first recommendation training.
-- Synthetic research remains isolated from real user/feedback tables and can never masquerade
-- as consented behavioural evidence.

CREATE TABLE ml.auto_training_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  batch_id text NOT NULL,
  engine_version text NOT NULL,
  run_mode text NOT NULL CHECK (run_mode IN ('audit','dry_run','execute')),
  batch_confidence numeric(5,4) CHECK (batch_confidence BETWEEN 0 AND 1),
  batch_confidence_band text CHECK (batch_confidence_band IN ('high','medium','low')),
  status text NOT NULL DEFAULT 'running'
    CHECK (status IN ('running','completed','completed_with_gates','failed')),
  config jsonb NOT NULL DEFAULT '{}',
  inspection_summary jsonb NOT NULL DEFAULT '{}',
  research_summary jsonb NOT NULL DEFAULT '{}',
  seed_summary jsonb NOT NULL DEFAULT '{}',
  ontology_summary jsonb NOT NULL DEFAULT '{}',
  training_summary jsonb NOT NULL DEFAULT '{}',
  evaluation_summary jsonb NOT NULL DEFAULT '{}',
  readiness_summary jsonb NOT NULL DEFAULT '{}',
  next_actions jsonb NOT NULL DEFAULT '[]',
  started_at timestamptz NOT NULL DEFAULT now(),
  completed_at timestamptz,
  error_code text,
  error_detail text
);
CREATE INDEX auto_training_runs_batch ON ml.auto_training_runs(batch_id, started_at DESC);

CREATE TABLE ml.auto_training_table_audits (
  run_id uuid NOT NULL REFERENCES ml.auto_training_runs(id) ON DELETE CASCADE,
  entity_type text NOT NULL,
  source_table text NOT NULL,
  total_records bigint NOT NULL DEFAULT 0 CHECK (total_records >= 0),
  usable_records bigint NOT NULL DEFAULT 0 CHECK (usable_records >= 0),
  missing_fields bigint NOT NULL DEFAULT 0 CHECK (missing_fields >= 0),
  duplicate_records bigint NOT NULL DEFAULT 0 CHECK (duplicate_records >= 0),
  orphan_records bigint NOT NULL DEFAULT 0 CHECK (orphan_records >= 0),
  low_confidence_records bigint NOT NULL DEFAULT 0 CHECK (low_confidence_records >= 0),
  coverage_score numeric(5,4) NOT NULL CHECK (coverage_score BETWEEN 0 AND 1),
  details jsonb NOT NULL DEFAULT '{}',
  PRIMARY KEY (run_id, entity_type)
);

CREATE TABLE research.auto_training_records (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  target_table text NOT NULL,
  record_key text NOT NULL,
  payload jsonb NOT NULL,
  payload_sha256 text NOT NULL,
  source_type text NOT NULL DEFAULT 'expert_research_synthetic'
    CHECK (source_type IN ('expert_research_synthetic','curated_external','derived_ontology')),
  generation_method text NOT NULL,
  confidence numeric(5,4) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
  confidence_band text NOT NULL CHECK (confidence_band IN ('high','medium','low')),
  ontology_mapping_status text NOT NULL
    CHECK (ontology_mapping_status IN ('mapped','not_applicable','rejected')),
  ontology_version text NOT NULL,
  provenance_tags text[] NOT NULL DEFAULT '{}',
  explanation text,
  first_batch_id text NOT NULL,
  last_batch_id text NOT NULL,
  version integer NOT NULL DEFAULT 1 CHECK (version > 0),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (target_table, record_key)
);
CREATE INDEX auto_training_records_batch
  ON research.auto_training_records(last_batch_id, target_table);
CREATE INDEX auto_training_records_confidence
  ON research.auto_training_records(target_table, confidence_band, confidence DESC);

CREATE TABLE ml.auto_training_seed_counts (
  run_id uuid NOT NULL REFERENCES ml.auto_training_runs(id) ON DELETE CASCADE,
  target_table text NOT NULL,
  inserted_count bigint NOT NULL DEFAULT 0 CHECK (inserted_count >= 0),
  updated_count bigint NOT NULL DEFAULT 0 CHECK (updated_count >= 0),
  skipped_count bigint NOT NULL DEFAULT 0 CHECK (skipped_count >= 0),
  rejected_count bigint NOT NULL DEFAULT 0 CHECK (rejected_count >= 0),
  average_confidence numeric(5,4) CHECK (average_confidence BETWEEN 0 AND 1),
  high_confidence_count bigint NOT NULL DEFAULT 0 CHECK (high_confidence_count >= 0),
  medium_confidence_count bigint NOT NULL DEFAULT 0 CHECK (medium_confidence_count >= 0),
  low_confidence_count bigint NOT NULL DEFAULT 0 CHECK (low_confidence_count >= 0),
  PRIMARY KEY (run_id, target_table)
);

CREATE TABLE ml.auto_training_model_runs (
  run_id uuid NOT NULL REFERENCES ml.auto_training_runs(id) ON DELETE CASCADE,
  model_name text NOT NULL,
  status text NOT NULL CHECK (status IN ('trained','refreshed','skipped','failed','gated')),
  input_source_split jsonb NOT NULL DEFAULT '{}',
  input_record_count bigint NOT NULL DEFAULT 0 CHECK (input_record_count >= 0),
  artifact_uri text,
  artifact_checksum text,
  metrics jsonb NOT NULL DEFAULT '{}',
  gate_checks jsonb NOT NULL DEFAULT '{}',
  reason text,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (run_id, model_name)
);

REVOKE ALL ON ml.auto_training_runs, ml.auto_training_table_audits,
  ml.auto_training_seed_counts, ml.auto_training_model_runs,
  research.auto_training_records FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT, UPDATE ON ml.auto_training_runs, ml.auto_training_table_audits,
  ml.auto_training_seed_counts, ml.auto_training_model_runs,
  research.auto_training_records TO service_role;

COMMENT ON TABLE research.auto_training_records IS
  'Governed synthetic/curated training staging. Never treated as real user feedback or written to tenant tables.';
COMMENT ON COLUMN research.auto_training_records.confidence IS
  'Composite source, ontology, realism, plausibility and dedupe confidence in [0,1].';
