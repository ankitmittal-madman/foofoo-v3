-- Migration: 076_dish_ingestion_pipeline.sql
-- CSV-to-canonical dish ingestion pipeline (database/seeds/IndianFoodDatasetCSV.csv, 16,523 rows).
--
-- Scope: this migration adds ONLY the tables genuinely missing for the ingestion pipeline
-- described in docs/architecture/[ACTIVE]_RUNBOOK_Dish_Ingestion_Pipeline_v1.0.md. It reuses,
-- rather than duplicates, every table confirmed to already exist: public.dishes,
-- public.dish_ingredients, public.dish_tags, public.cuisines, public.meal_classes,
-- public.dish_regional_affinities, public.dish_name_synonyms, public.dish_enrichment_jobs,
-- public.dish_taxonomy_assertions, public.food_source_records.
--
-- New tables (genuine gaps):
--   public.import_runs          -- one row per ETL invocation (app-generated, operational)
--   public.dish_source_rows     -- raw CSV row snapshot + fingerprint, keyed to an import_run
--   public.import_row_results   -- per-row outcome (matched/created/skipped/errored) + link to dish
--   public.import_row_errors    -- structured per-row error log, many-per-row
--   public.dish_aliases         -- ETL-sourced free-text aliases distinct from the curated,
--                                  human-researched public.dish_name_synonyms table (see decision
--                                  note below)
--   public.image_assets         -- physical asset record (checksum, storage path, provenance)
--   public.dish_images          -- dish <-> image_assets junction with primary flag + provenance
--
-- Decision: dish_taxonomy_review_queue is a VIEW (migration 056) over dish_enrichment_jobs +
-- dishes.ontology_status, not a physical table. Rather than fork a second, competing review
-- surface, this migration adds public.dish_ingestion_review_queue as its own physical table
-- scoped to import-time triage (missing meal class, low-confidence ontology match, ambiguous
-- dedupe) which is a different lifecycle than post-hoc taxonomy field review. The existing view
-- is left untouched and continues to serve its existing purpose (dish_enrichment_jobs triage).
--
-- Decision: dish_aliases (new) vs dish_name_synonyms (existing, migration 051). The existing
-- table is an intentionally curated, sourced ontology (data_source IN ('real','ai_generated',
-- 'stub'), CHECK requiring source_url for 'real' rows) built by manual research batches (WP-19).
-- ETL-discovered aliases (RecipeName vs TranslatedRecipeName variants, near-duplicate names
-- merged during dedupe) are a different kind of fact — provenance is "this CSV import run", not
-- "researcher citation" — and forcing them through dish_name_synonyms' CHECK constraint would
-- either violate it or require fabricating a source_url. dish_aliases is intentionally narrower
-- and simpler, FK'd to import_runs, and is NOT a replacement for dish_name_synonyms; both may
-- describe the same dish. Downstream consumers should read both tables as a UNION.
--
-- Data classification per column family (docs requirement, see runbook §5 for full table):
--   strictly app-generated : import_runs.*, dish_source_rows.row_fingerprint/status/*_at,
--                            import_row_results.status, import_row_errors.*, image_assets.checksum
--   external seeded master : cuisines, meal_classes (already exist, reused, never written by ETL)
--   AI-generated enrichment : dish_aliases.source='groq_inferred', dish_taxonomy_assertions rows
--                            this ETL inserts with source_type IN ('rules','ml_model')
--   user-usage-generated    : not touched by this migration or the ETL (no ratings/likes here)
--   hybrid                  : dishes row itself (raw CSV fields + AI-inferred fields coexist,
--                            never overwriting each other — see dish_source_rows.raw_payload
--                            which is retained permanently alongside the derived dish)

CREATE TABLE public.import_runs (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_name       text NOT NULL,               -- e.g. 'IndianFoodDatasetCSV.csv'
  source_checksum   text NOT NULL,                -- sha256 of the whole source file, for exact-repeat detection
  run_mode          text NOT NULL CHECK (run_mode IN ('dry_run', 'apply')),
  status            text NOT NULL DEFAULT 'running' CHECK (status IN ('running','completed','failed')),
  total_rows        integer,
  rows_matched_existing integer NOT NULL DEFAULT 0,
  rows_created_dish     integer NOT NULL DEFAULT 0,
  rows_routed_review    integer NOT NULL DEFAULT 0,
  rows_errored          integer NOT NULL DEFAULT 0,
  started_at        timestamptz NOT NULL DEFAULT now(),
  completed_at      timestamptz,
  summary_report    jsonb NOT NULL DEFAULT '{}',   -- full import summary report (see runbook §7)
  triggered_by      text NOT NULL DEFAULT 'etl_script'
);
COMMENT ON TABLE public.import_runs IS
  'One row per dish-ingestion ETL invocation (dry-run or apply). Strictly app-generated/operational.';

CREATE TABLE public.dish_source_rows (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  import_run_id     uuid NOT NULL REFERENCES public.import_runs(id) ON DELETE CASCADE,
  source_srno       integer NOT NULL,             -- original CSV Srno column, not assumed unique across files
  row_fingerprint   text NOT NULL,                 -- sha256 of normalized(name, translated_name, ingredients, url)
  raw_payload       jsonb NOT NULL,                 -- verbatim CSV row, never mutated once written
  normalized_payload jsonb NOT NULL,                -- parsed/normalized fields (strings trimmed, ingredients split)
  created_at        timestamptz NOT NULL DEFAULT now(),
  UNIQUE (import_run_id, source_srno)
);
CREATE INDEX dish_source_rows_fingerprint ON public.dish_source_rows (row_fingerprint);
COMMENT ON TABLE public.dish_source_rows IS
  'Immutable per-row snapshot of the source CSV as loaded by one import run. raw_payload is never overwritten by inference — see dish_ingestion_pipeline runbook Rule 5.';

CREATE TABLE public.import_row_results (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_row_id     uuid NOT NULL REFERENCES public.dish_source_rows(id) ON DELETE CASCADE,
  dish_id           uuid REFERENCES public.dishes(id) ON DELETE SET NULL,
  status            text NOT NULL CHECK (status IN (
                       'matched_existing', 'created_new', 'merged_duplicate',
                       'routed_review', 'skipped', 'errored'
                     )),
  match_method      text,                          -- e.g. 'exact_name', 'fingerprint', 'fuzzy_name', 'ontology_api'
  match_score       numeric(4,3) CHECK (match_score BETWEEN 0 AND 1),
  ontology_confidence numeric(4,3) CHECK (ontology_confidence BETWEEN 0 AND 1),
  meal_class_code   text REFERENCES public.meal_classes(class_code),
  processed_at      timestamptz NOT NULL DEFAULT now(),
  UNIQUE (source_row_id)
);
CREATE INDEX import_row_results_dish ON public.import_row_results (dish_id);
CREATE INDEX import_row_results_status ON public.import_row_results (status);
COMMENT ON TABLE public.import_row_results IS
  'One outcome per source row per run: which canonical dish it resolved to (if any) and how. Strictly app-generated.';

CREATE TABLE public.import_row_errors (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_row_id     uuid NOT NULL REFERENCES public.dish_source_rows(id) ON DELETE CASCADE,
  stage             text NOT NULL CHECK (stage IN (
                       'load','normalize','dedupe','ontology_map','enrich','image','persist'
                     )),
  error_code        text NOT NULL,
  error_detail      text,
  occurred_at       timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX import_row_errors_row ON public.import_row_errors (source_row_id);
COMMENT ON TABLE public.import_row_errors IS
  'Structured, many-per-row error log for the ingestion pipeline. Strictly app-generated.';

CREATE TABLE public.dish_ingestion_review_queue (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_row_id     uuid NOT NULL REFERENCES public.dish_source_rows(id) ON DELETE CASCADE,
  dish_id           uuid REFERENCES public.dishes(id) ON DELETE SET NULL,
  reason_code       text NOT NULL CHECK (reason_code IN (
                       'no_meal_class_match', 'low_confidence_ontology_match',
                       'ambiguous_dedupe_candidate', 'missing_required_field', 'other'
                     )),
  detail            jsonb NOT NULL DEFAULT '{}',
  review_status     text NOT NULL DEFAULT 'pending' CHECK (review_status IN ('pending','resolved','dismissed')),
  created_at        timestamptz NOT NULL DEFAULT now(),
  resolved_at       timestamptz
);
CREATE INDEX dish_ingestion_review_queue_status ON public.dish_ingestion_review_queue (review_status);
COMMENT ON TABLE public.dish_ingestion_review_queue IS
  'Import-time triage queue (unmapped meal class, low-confidence match, ambiguous dedupe). Distinct lifecycle from the existing dish_taxonomy_review_queue VIEW (migration 056), which is post-hoc taxonomy-field review over dish_enrichment_jobs. Deliberate design decision — see migration header.';

CREATE TABLE public.dish_aliases (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  dish_id           uuid NOT NULL REFERENCES public.dishes(id) ON DELETE CASCADE,
  alias_text        text NOT NULL,
  alias_source      text NOT NULL CHECK (alias_source IN (
                       'csv_translated_name', 'csv_original_name', 'dedupe_merge', 'groq_inferred'
                     )),
  import_run_id     uuid REFERENCES public.import_runs(id) ON DELETE SET NULL,
  confidence        numeric(4,3) CHECK (confidence BETWEEN 0 AND 1),
  created_at        timestamptz NOT NULL DEFAULT now(),
  UNIQUE (dish_id, alias_text)
);
COMMENT ON TABLE public.dish_aliases IS
  'ETL-discovered aliases (name variants, dedupe merges). Complements, does not replace, the curated public.dish_name_synonyms (migration 051) — see migration header decision note.';

CREATE TABLE public.image_assets (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_url        text,
  storage_path       text,                          -- local/object-storage path once downloaded; NULL until fetched
  checksum_sha256    text,
  content_type       text,
  width_px           integer,
  height_px          integer,
  fetch_status       text NOT NULL DEFAULT 'pending' CHECK (fetch_status IN ('pending','fetched','failed','not_applicable')),
  fetched_at         timestamptz,
  created_at         timestamptz NOT NULL DEFAULT now(),
  UNIQUE (checksum_sha256)
);
COMMENT ON TABLE public.image_assets IS
  'Physical image asset record with provenance. For the current CSV (no image column) rows are created with fetch_status=not_applicable and are plumbing for future enrichment.';

CREATE TABLE public.dish_images (
  dish_id           uuid NOT NULL REFERENCES public.dishes(id) ON DELETE CASCADE,
  image_asset_id    uuid NOT NULL REFERENCES public.image_assets(id) ON DELETE CASCADE,
  alt_text          text,
  is_primary        boolean NOT NULL DEFAULT false,
  source_type       text NOT NULL CHECK (source_type IN ('csv_source','external_api','ai_generated','human_upload')),
  confidence        numeric(4,3) CHECK (confidence BETWEEN 0 AND 1),
  created_at        timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (dish_id, image_asset_id)
);
CREATE UNIQUE INDEX dish_images_one_primary ON public.dish_images (dish_id) WHERE is_primary;
COMMENT ON TABLE public.dish_images IS
  'Dish-to-image junction with primary flag and provenance. Hybrid: image selection may be human-reviewed or AI-suggested.';

-- RLS: same posture as public.dish_name_synonyms (public reference-style read, service-role-only write).
ALTER TABLE public.import_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dish_source_rows ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.import_row_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.import_row_errors ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dish_ingestion_review_queue ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dish_aliases ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.image_assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dish_images ENABLE ROW LEVEL SECURITY;

-- Operational tables (import_runs, dish_source_rows, import_row_results, import_row_errors,
-- dish_ingestion_review_queue) are service-role/back-office only — no public read policy at all,
-- matching the posture of public.dish_enrichment_jobs (migration 056) which is not publicly listable.
-- Content-facing tables (dish_aliases, image_assets, dish_images) get public read, matching
-- public.dish_name_synonyms.
CREATE POLICY dish_aliases_public_read ON public.dish_aliases FOR SELECT USING (true);
CREATE POLICY image_assets_public_read ON public.image_assets FOR SELECT USING (true);
CREATE POLICY dish_images_public_read ON public.dish_images FOR SELECT USING (true);

REVOKE INSERT, UPDATE, DELETE ON public.dish_aliases, public.image_assets, public.dish_images
  FROM anon, authenticated;
REVOKE ALL ON public.import_runs, public.dish_source_rows, public.import_row_results,
  public.import_row_errors, public.dish_ingestion_review_queue
  FROM anon, authenticated;

DO $$
BEGIN
  GRANT SELECT, INSERT, UPDATE, DELETE ON
    public.import_runs, public.dish_source_rows, public.import_row_results,
    public.import_row_errors, public.dish_ingestion_review_queue,
    public.dish_aliases, public.image_assets, public.dish_images
    TO service_role;
EXCEPTION WHEN undefined_object THEN
  RAISE NOTICE 'service_role absent outside Supabase; grants skipped';
END $$;
