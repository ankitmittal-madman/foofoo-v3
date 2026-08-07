-- Removes only the isolated ingestion lineage introduced by migration 088. Production catalogue,
-- tenant, planning and event data are never touched by this rollback.

DROP TABLE IF EXISTS research.training_source_rows;
DROP TABLE IF EXISTS ml.training_import_batches;

ALTER TABLE research.auto_training_records
  DROP COLUMN IF EXISTS source_lineage,
  DROP COLUMN IF EXISTS transformation_version,
  DROP COLUMN IF EXISTS generation_version,
  DROP COLUMN IF EXISTS source_dataset_version,
  DROP COLUMN IF EXISTS synthetic_only;

