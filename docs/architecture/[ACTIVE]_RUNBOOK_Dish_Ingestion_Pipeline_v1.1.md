Status: ACTIVE
Version: 1.0
Date: 2026-08-06
Placement: docs/architecture (operational runbook for how the dish catalogue is built/loaded)
Supersedes: none
Dependencies: database/migrations/076_dish_ingestion_pipeline.sql, database/etl/dish_ingestion/*,
  database/etl/ingest_dish_dataset.py, database/seeds/IndianFoodDatasetCSV.csv

# Dish Ingestion Pipeline Runbook

## Executive Summary

This runbook documents the ETL that loads `database/seeds/IndianFoodDatasetCSV.csv` into
`public.dishes` and enriches each dish with canonical ontology mappings, tags, meal-class
mappings, regional affinity, aliases, and image plumbing. It is idempotent, batched,
transactional, dry-run capable, and reuses the repo's existing food-ontology/enrichment schema
(migrations 056, 060, 061, 063-072) rather than duplicating it. It adds one new migration,
`076_dish_ingestion_pipeline.sql`, for the genuine schema gaps only.

**IMPORTANT — corrected row count.** The task that produced this runbook stated the source CSV
has 16,523 data rows, based on `wc -l` (16,524 physical lines). That count is not the actual
number of CSV records: many rows contain literal newlines inside quoted fields (chiefly
`Instructions`/`TranslatedInstructions`, which are long free-text paragraphs), so a single
logical CSV record spans multiple physical lines. Parsing the file with Python's quote-aware
`csv` module (verified twice, once via `csv.DictReader` and once via raw `csv.reader` checking
every row has exactly 15 fields with zero malformed rows) yields **6,871 logical data rows**,
not 16,523. This matches the publicly known size of the "Archana's Kitchen" Indian food dataset
this file is sourced from. Every number in this runbook and in the ETL's own summary report is
against the real, parsed row count (6,871) — the ETL never fabricates or pads towards 16,523.

## 1. What already existed vs what this delivery adds

**Reused, unchanged:** `public.dishes`, `public.dish_ingredients`, `public.dish_tags`,
`public.cuisines`, `public.meal_classes`, `public.dish_regional_affinities`,
`public.dish_name_synonyms`, `public.dish_enrichment_jobs`, `public.dish_taxonomy_assertions`,
`public.food_source_records`, `public.dish_meal_class_mappings`, `public.taxonomy_terms`.

**New (migration 076), and why each was needed:**

| Table | Purpose | Why not reuse something else |
|---|---|---|
| `import_runs` | One row per ETL invocation, with a full JSON summary report | Nothing tracked "a run" as a first-class object before |
| `dish_source_rows` | Immutable raw+normalized CSV row snapshot, keyed by import run | Raw CSV content was never persisted; needed for provenance and resumability |
| `import_row_results` | Per-row outcome (matched/created/merged/review/error) + link to the resulting dish | No per-row audit trail existed |
| `import_row_errors` | Structured, many-per-row error log | No structured ETL error log existed |
| `dish_ingestion_review_queue` | Import-time triage (no meal class match, low-confidence match, ambiguous dedupe) | `dish_taxonomy_review_queue` (migration 056) is a VIEW over `dish_enrichment_jobs`/`ontology_status` — a different lifecycle (post-hoc taxonomy field review, not import-time triage). Extending that view's backing tables would conflate two different queues; kept separate and documented in the migration header. |
| `dish_aliases` | ETL-discovered name variants and dedupe-merge aliases | `dish_name_synonyms` (migration 051) is a curated, human-researched ontology whose CHECK constraint requires a citation `source_url` for real aliases — ETL-discovered variants are a different provenance kind and would either violate that constraint or require fabricating a citation. `dish_aliases` is additive, not a replacement; both tables should be read together by consumers. |
| `image_assets` | Physical image asset record: URL, storage path, checksum, fetch status | Did not exist anywhere in the schema |
| `dish_images` | Dish ↔ image_assets junction, primary flag, provenance | Did not exist anywhere in the schema |

Full detail and the exact SQL is in `database/migrations/076_dish_ingestion_pipeline.sql`
(header comment repeats this table with rationale). Rollback:
`database/migrations/076_dish_ingestion_pipeline_rollback.sql`.

## 2. Pipeline stages

1. **Load & normalize** (`dish_ingestion/normalize.py`) — quote-aware CSV parse, whitespace
   normalization, ingredient list split, a stable SHA-256 row fingerprint over
   (name, translated name, ingredients, URL) — deliberately excludes `Srno` (not stable across
   re-exports) and instruction text (reformatted without changing dish identity).
2. **Canonical lookup & dedupe** (`dish_ingestion/dedupe.py`) — exact fingerprint match, exact
   name match, then a *blocked* fuzzy match (see §4 "Validated vs unexecuted" for why blocking
   is required) that either matches an existing dish, merges as an alias of a near-duplicate, or
   routes to review as ambiguous. Never silently auto-merges below a 0.93 similarity ratio.
3. **Ontology mapping** (`dish_ingestion/ontology_adapter.py`) — pluggable adapter interface.
   The ACTIVE implementation, `NullExternalOntologyAdapter`, is a **local fallback**: no real
   Dish Ontology API is configured or available in this environment, so per the task's explicit
   instruction, no call to a nonexistent external API is fabricated. It matches
   cuisine/course/diet strings against this repo's own `public.cuisines` and
   `public.meal_classes` tables using exact + local fuzzy matching, and always returns
   `match_method` prefixed `local_` so a future real adapter's results are visibly distinguishable
   in reporting. `get_adapter()` raises `NotImplementedError` (rather than silently no-op) if
   `DISH_ONTOLOGY_API_URL` is set but no real client exists yet — this is the documented extension
   point, not a working integration.
4. **Missing-data enrichment** (`dish_ingestion/groq_adapter.py`) — regional affinity and tag
   inference. Reads `GROQ_API_KEY`; if unset, runs in **mock mode**: cheap keyword/cuisine
   heuristics only, every result tagged `source='heuristic'` or `source='mock'`, never
   `source='groq_api'` unless a real call actually happened. `GROQ_API_KEY` was **not** set in
   this delivery environment, so every enrichment in the validated dry run below is heuristic,
   not a real Groq call.
5. **Image handling** (`dish_ingestion/images.py`) — this CSV has no image column, so every row
   resolves to an `image_assets` row with `fetch_status='not_applicable'` and no fabricated URL.
   The download/checksum code path is real and exercised by the plumbing, ready for a future
   source that does carry image URLs.
6. **Persistence** (`dish_ingestion/db.py`, `dish_ingestion/pipeline.py`) — batched (default 200
   rows/batch) transactions; every write is `INSERT ... ON CONFLICT` against a stable natural key
   (dish name, `(dish_id, region_code)`, `(dish_id, class_code, slot)`, `(import_run_id,
   source_srno)`, etc.) so re-running the same batch is a safe no-op. A batch failure rolls back
   only that batch; already-committed batches stay applied.

## 3. Data classification (as required by the task brief)

| Kind | Where |
|---|---|
| Strictly app-generated | `import_runs.*`, `dish_source_rows.row_fingerprint/status/*_at`, `import_row_results.status`, `import_row_errors.*`, `image_assets.checksum_sha256`, `dish_ingestion_review_queue.*` |
| External seeded master data | `public.cuisines`, `public.meal_classes` — read-only to this ETL, never written |
| AI-generated enrichment | `dish_aliases` rows with `alias_source='groq_inferred'`, `dish_taxonomy_assertions`/`dish_regional_affinities`/`dish_meal_class_mappings` rows this ETL inserts with `source_type IN ('rules','ml_model')` and `review_status='provisional'` |
| User-usage-generated | Not touched — no ratings/likes/cooks/favorites/saves tables are written by this ETL |
| Hybrid | The `dishes` row itself: raw CSV-derived columns (name, cook time) sit alongside AI-inferred columns (meal_occasion, cuisine_id) in the same row, but the untouched raw snapshot always survives separately in `dish_source_rows.raw_payload` — inference never overwrites raw source data (task brief rule 5) |

## 4. Validated vs unexecuted (read this before trusting any number above)

**No live database is reachable from this delivery environment.** `mcp__Supabase__*` tools were
not available/connected, and no `DATABASE_URL`/`SUPABASE_DB_URL` was set. As a result:

- **Executed and verified:** `python database/etl/ingest_dish_dataset.py --dry-run` was run
  against the real `database/seeds/IndianFoodDatasetCSV.csv`. This exercises stages 1–5 fully in
  memory (parse, normalize, fingerprint, dedupe, local-fallback ontology matching, heuristic
  enrichment, image plumbing) with **zero database writes**. Output (verbatim):
  ```
  total_rows_processed: 6871
  outcome_counts: {created_new: 6333, ambiguous_review: 518, matched_existing: 1, merged_duplicate: 19}
  match_method_counts: {no_match: 6333, fuzzy_name: 537, exact_name: 1}
  ```
  The `matched_existing`/`exact_name` count of 1 and `no_match` cuisine/class counts are dry-run
  artifacts of running against an **empty in-memory reference set** (no DB connection means
  `public.cuisines`/`public.meal_classes` cannot be loaded) — this is expected in dry-run and is
  why the CLI prints an explicit warning and the JSON report sets
  `"verified_against_live_db": false`. It confirms the parse/normalize/dedupe code path runs
  correctly end-to-end over the real file without crashing or hanging, and completes in ~6
  seconds.
- **Also caught and fixed during validation:** an initial naive fuzzy-dedupe implementation
  (unblocked O(n²) `difflib` comparison across all rows) did not complete in a reasonable time
  against 6,871 rows and was killed. It was replaced with a blocked comparison (candidates grouped
  by the first 4 characters of the first name token before the expensive pairwise check runs) —
  see `dedupe.py`'s `_block_key` docstring for the accepted trade-off this creates (two dish names
  with different first words cannot fuzzy-merge; exact-name/fingerprint matching, both O(1), are
  unaffected).
- **Written but NOT executed:** every SQL statement in `076_dish_ingestion_pipeline.sql`, and the
  `--apply` code path in `db.py`/`pipeline.py` (actual `INSERT`/`UPDATE` statements against
  Postgres). These were validated by careful reading against the exact style, extension usage,
  RLS pattern, and upsert idioms of the existing migrations (008, 009, 021, 051, 056, 061) but
  have never run against a real Postgres instance. **Do not treat "6,871 dishes ingested" as a
  claim this session made** — it did not run `--apply` against any database.
- **Not validated:** the real Groq API path (`_call_groq*` in `groq_adapter.py`) — no
  `GROQ_API_KEY` was available, so only the mock/heuristic path was exercised.

## 5. Idempotency keys (what makes a rerun safe)

| Table | Natural key used for `ON CONFLICT` |
|---|---|
| `dishes` | `name` (pre-existing UNIQUE constraint, migration 008) |
| `dish_source_rows` | `(import_run_id, source_srno)` |
| `import_row_results` | `source_row_id` |
| `dish_aliases` | `(dish_id, alias_text)` |
| `dish_regional_affinities` | `(dish_id, region_code)` — update skipped once `review_status='accepted'` |
| `dish_meal_class_mappings` | `(dish_id, class_code, slot)` — update skipped once `review_status='accepted'` |
| `image_assets` | `checksum_sha256` (when known; otherwise a fresh row per fetch attempt) |
| `dish_images` | `(dish_id, image_asset_id)`, `ON CONFLICT DO NOTHING` |

Rerunning the same CSV twice therefore produces the same canonical DB state, not duplicate rows —
by construction of these keys, not by a special "already ran" check.

## 6. How to run it

```bash
# 1. Dry run (no DB needed) — always do this first
python3 database/etl/ingest_dish_dataset.py --dry-run

# 2. Real run (requires a reachable Postgres with this repo's migrations 001-076 applied)
export DATABASE_URL=postgres://...              # or SUPABASE_DB_URL
pip install psycopg2-binary                      # new dependency for this ETL only
python3 database/etl/ingest_dish_dataset.py --apply

# Optional: different CSV, smaller/larger batches, write the report to a file, verbose logging
python3 database/etl/ingest_dish_dataset.py --apply \
  --csv path/to/other.csv --batch-size 500 --report-out /tmp/import_report.json -v
```

Apply the migration first (via your normal Supabase migration flow —
`supabase db push` or `mcp__Supabase__apply_migration`, not run manually here):
`database/migrations/076_dish_ingestion_pipeline.sql`.

## 7. Import summary report

Both `--dry-run` and `--apply` print a JSON report to stdout (and optionally `--report-out`) with:
`total_rows_processed`, `outcome_counts` (created/matched/merged/review/errored),
`match_method_counts`, `ontology_confidence_distribution` (bucketed), `review_reason_counts`,
`elapsed_seconds`, `source_checksum_sha256`, and `verified_against_live_db`. In `--apply` mode the
same JSON is also persisted to `import_runs.summary_report` for that run.

## 8. Known open risks / TODOs

- Real Dish Ontology API adapter is unimplemented (deliberately — none is configured in this
  repo/environment); `ontology_adapter.get_adapter()` is the single place to wire one in later.
- Real Groq calls are unvalidated end-to-end (no API key in this environment); only the
  mock/heuristic path has been exercised.
- Migration 076 has never been applied to a real database in this delivery — needs a review pass
  plus `supabase db push` (or equivalent) before `--apply` can be run for real.
- Fuzzy dedupe blocking (first 4 chars of the first name token) will miss near-duplicates that
  start with different words (e.g. reordered names) — acceptable, documented trade-off, not a bug.
- `dish_ingestion_review_queue` needs an operational consumer/dashboard; this migration only
  creates the table, it does not build UI or a reviewer workflow.
- Ingredient names are stored as-is from the CSV's free-text ingredient phrases (e.g. "6 Karela
  (Bitter Gourd) - deseeded"), not further parsed into quantity/unit/canonical-ingredient triples
  — `dish_ingredients` link exists, but ingredient normalization is future work, not this delivery.

## Critical Self-Review

The biggest risk in this delivery is that it was built and validated entirely without a live
database — every SQL statement is unexecuted. The mitigation taken was maximal fidelity to
existing migration style (read six prior migrations in full before writing) and a real dry run
against the actual CSV to prove the non-DB code path is correct and fast. The corrected row count
(6,871, not 16,523) is disclosed prominently rather than silently substituted, per this repo's
"never fabricate" rule — the original task brief's row-count framing was based on a physical
line count that does not account for embedded newlines in quoted CSV fields.

## Versioning & Placement

v1.0, initial version. Placed in `docs/architecture` (operational runbook for how the dish
catalogue is built), naming standard `[ACTIVE]_RUNBOOK_Name_vMAJOR.MINOR.md` per
`docs/governance/[ACTIVE]_Repository_Naming_Standard_v1.1.md` §3.

Founder Sign-off:
