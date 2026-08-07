-- Govern workbook ingestion without allowing synthetic identities, plans, or events into the
-- production tenant boundary. Raw evidence remains immutable in research; transformed records
-- reuse the versioned auto-training staging table introduced by migration 087.

CREATE TABLE ml.training_import_batches (
  id uuid PRIMARY KEY,
  import_key text NOT NULL UNIQUE,
  source_bundle_sha256 text NOT NULL CHECK (source_bundle_sha256 ~ '^[0-9a-f]{64}$'),
  source_dataset_version text NOT NULL,
  generation_version text NOT NULL,
  transformation_version text NOT NULL,
  synthetic_only boolean NOT NULL DEFAULT true CHECK (synthetic_only),
  status text NOT NULL DEFAULT 'loading'
    CHECK (status IN ('loading','completed','completed_with_rejections','failed')),
  source_files jsonb NOT NULL CHECK (jsonb_typeof(source_files) = 'array'),
  source_row_count bigint NOT NULL DEFAULT 0 CHECK (source_row_count >= 0),
  accepted_source_row_count bigint NOT NULL DEFAULT 0 CHECK (accepted_source_row_count >= 0),
  rejected_source_row_count bigint NOT NULL DEFAULT 0 CHECK (rejected_source_row_count >= 0),
  normalized_record_count bigint NOT NULL DEFAULT 0 CHECK (normalized_record_count >= 0),
  load_summary jsonb NOT NULL DEFAULT '{}',
  started_at timestamptz NOT NULL DEFAULT now(),
  completed_at timestamptz,
  CHECK (accepted_source_row_count + rejected_source_row_count <= source_row_count)
);

CREATE TABLE research.training_source_rows (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  batch_id uuid NOT NULL REFERENCES ml.training_import_batches(id) ON DELETE CASCADE,
  source_dataset text NOT NULL,
  source_file text NOT NULL,
  source_file_sha256 text NOT NULL CHECK (source_file_sha256 ~ '^[0-9a-f]{64}$'),
  sheet_name text NOT NULL,
  source_row_number integer NOT NULL CHECK (source_row_number >= 2),
  source_record_key text,
  raw_payload jsonb NOT NULL CHECK (jsonb_typeof(raw_payload) = 'object'),
  raw_payload_sha256 text NOT NULL CHECK (raw_payload_sha256 ~ '^[0-9a-f]{64}$'),
  validation_status text NOT NULL CHECK (validation_status IN ('accepted','rejected')),
  validation_errors jsonb NOT NULL DEFAULT '[]'
    CHECK (jsonb_typeof(validation_errors) = 'array'),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (batch_id, source_dataset, sheet_name, source_row_number)
);

CREATE INDEX training_source_rows_batch_status
  ON research.training_source_rows(batch_id, validation_status, sheet_name);
CREATE INDEX training_source_rows_record_key
  ON research.training_source_rows(source_dataset, sheet_name, source_record_key)
  WHERE source_record_key IS NOT NULL;

ALTER TABLE research.auto_training_records
  ADD COLUMN synthetic_only boolean NOT NULL DEFAULT true CHECK (synthetic_only),
  ADD COLUMN source_dataset_version text NOT NULL DEFAULT 'legacy:auto-engine',
  ADD COLUMN generation_version text NOT NULL DEFAULT 'auto-engine-v1',
  ADD COLUMN transformation_version text NOT NULL DEFAULT 'auto-engine-v1',
  ADD COLUMN source_lineage jsonb NOT NULL DEFAULT '[]'
    CHECK (jsonb_typeof(source_lineage) = 'array');

REVOKE ALL ON ml.training_import_batches, research.training_source_rows
  FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT, UPDATE ON ml.training_import_batches TO service_role;
GRANT SELECT, INSERT ON research.training_source_rows TO service_role;
GRANT USAGE, SELECT ON SEQUENCE research.training_source_rows_id_seq TO service_role;

COMMENT ON TABLE ml.training_import_batches IS
  'Private audit header for deterministic synthetic workbook imports; never a production user batch.';
COMMENT ON TABLE research.training_source_rows IS
  'Immutable workbook rows with file, sheet, row, hash and validation lineage. Rejected rows remain evidence only.';
COMMENT ON COLUMN research.auto_training_records.source_lineage IS
  'Source files/artifacts and row references used by the versioned synthetic transformation.';

