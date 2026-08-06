Status: ACTIVE
Version: 1.1
Date: 2026-08-06
Placement: docs/architecture (operational runbook for how the dish catalogue is built/loaded)
Supersedes: [ACTIVE]_RUNBOOK_Dish_Ingestion_Pipeline_v1.0.md (this file, in place — v1.1 adds Stage 5
  real image generation; nothing in v1.0's scope was removed)
Dependencies: database/migrations/076_dish_ingestion_pipeline.sql,
  database/migrations/077_dish_image_generation_provenance.sql, database/etl/dish_ingestion/*,
  database/etl/ingest_dish_dataset.py, database/seeds/IndianFoodDatasetCSV.csv,
  ghar_re_service/ghar_re_service/media.py, ghar_re_service/ghar_re_service/scripts/build_image_map.py

# Dish Ingestion Pipeline Runbook

## Executive Summary

This runbook documents the ETL that loads `database/seeds/IndianFoodDatasetCSV.csv` into
`public.dishes` and enriches each dish with canonical ontology mappings, tags, meal-class
mappings, regional affinity, aliases, and (as of v1.1) real AI-generated dish images. It is
idempotent, batched, transactional, dry-run capable, and reuses the repo's existing
food-ontology/enrichment schema (migrations 056, 060, 061, 063-072) rather than duplicating it. It
adds two migrations for genuine schema gaps only: `076_dish_ingestion_pipeline.sql` (v1.0, the
core import scaffolding) and `077_dish_image_generation_provenance.sql` (v1.1, image-generation
provenance columns).

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
5. **Image handling** (`dish_ingestion/image_prompt.py`, `dish_ingestion/images.py`) — **v1.1: this
   is now a real generation + upload stage, not a placeholder.** See §2A below for full detail.
   In short: for a dish that does not already have an image, a prompt-fill LLM call (Groq, then
   Hugging Face, then a deterministic heuristic) supplies four fields that are assembled into a
   fixed, standardized prompt template; that prompt is sent to Pollinations.ai (`flux-pro`,
   1024x1024) to generate PNG bytes in memory; those bytes are uploaded directly to Cloudinary
   (no local disk write anywhere in the path) under a `<dish_slug>_hero_01_<random>` public_id
   matching the house convention already used by `ghar_re_service`. `--skip-images` reverts to the
   v1.0 `not_applicable` placeholder behavior for every row.
6. **Persistence** (`dish_ingestion/db.py`, `dish_ingestion/pipeline.py`) — batched (default 200
   rows/batch) transactions; every write is `INSERT ... ON CONFLICT` against a stable natural key
   (dish name, `(dish_id, region_code)`, `(dish_id, class_code, slot)`, `(import_run_id,
   source_srno)`, etc.) so re-running the same batch is a safe no-op. A batch failure rolls back
   only that batch; already-committed batches stay applied.

## 2A. Stage 5 detail (v1.1): real image generation, prompt template, provenance

### Required environment variables

| Variable | Purpose | Required? |
|---|---|---|
| `GROQ_API_KEY` | Primary backend for the four prompt fill-in fields | No — falls back to HF, then heuristic |
| `HF_API_KEY` or `HUGGINGFACE_API_KEY` | Alternate/fallback prompt-field backend (Hugging Face Inference API) | No — falls back to heuristic |
| `HF_MODEL` | HF model id (default `mistralai/Mistral-7B-Instruct-v0.3`) | No |
| `GROQ_MODEL` | Groq model id (default `llama-3.1-8b-instant`, same var `groq_adapter.py` already uses) | No |
| `CLOUDINARY_CLOUD_NAME` | Upload target cloud (default `dzlqsobol`, same default as `ghar_re_service.media`) | No (has default) |
| `CLOUDINARY_API_KEY` | Signed upload auth | **Yes, for real uploads** — without it `--apply --generate-images` fails fast on the first dish needing an image, rather than fabricating an upload |
| `CLOUDINARY_API_SECRET` | Signed upload auth (signature computation) | **Yes, for real uploads** |

Pollinations.ai needs **no** API key or env var — it is a free, unauthenticated public endpoint,
same as the Founder-supplied reference script.

### Standardized prompt template (fixed, code-owned — never generated by the LLM)

Ported literally from `FooFoo_Dish_Image_Prompts_v2.xlsx`'s `prompt` column, verified against 5
sample rows (Butter Chicken, Dal Makhani, Sarson Ka Saag, Makki Ki Roti, Tandoori Chicken) — the
template text held identically across all five; only `dish_name`, `vessel_type`, the 2-3 sentence
visual description, and the 2-3 word color/visual focal point varied. `PROMPT_TEMPLATE` in
`dish_ingestion/image_prompt.py`:

```
Generate a high-quality professional food photograph of {dish_name}: {visual_description}. Served
in a traditional {vessel_type}. The table surface is a clean warm-toned rustic wooden board with
nothing else on it — no scattered spices, no loose herbs, no cloth, no glass, no items that are
not part of the dish. Only the dish and its actual accompaniments. Photography style: 45-degree
angle, soft natural window light from the left side, warm color temperature, shallow depth of
field with a softly blurred background, appetizing steam rising gently. The colors should draw
attention to {color_focal_point}. The image should look like premium editorial food photography —
ultra sharp, high resolution, clean composition. Aspect ratio 16:9.
```

`category` is also returned by the prompt-field backend (cuisine/course-style label) but is not
part of the template text itself — it is stored alongside the other provenance fields for future
filtering/reporting use, matching the xlsx's own `category` column.

An LLM (Groq primary, Hugging Face alternate, deterministic heuristic last resort) fills in only
`visual_description`, `vessel_type`, and `color_focal_point` (plus `category`) — the template text
around them is assembled server-side in `image_prompt.assemble_prompt()`, so output format cannot
drift dish to dish regardless of which backend answered. Every result is tagged with its real
source: `'groq_api' | 'hf_api' | 'heuristic'`, mirroring `groq_adapter.py`'s existing honesty
discipline — a heuristic fallback is never mislabeled as a real model call.

### Cloudinary naming convention (must match `ghar_re_service` exactly)

`public_id = "<dish_slug>_hero_01_<random-6-char-suffix>"`, where `dish_slug` is computed by
`images.slugify()` — lowercase, every run of non-alphanumerics collapsed to one underscore —
**identical logic** to `build_image_map.py`'s `_slug()`. This was verified directly:
`slugify("Thai Spring Roll (Fried)") == "thai_spring_roll_fried"`, matching that script's own
worked example. `dish_images.storage_path` stores the Cloudinary **public_id**, not the full
delivery URL — the delivery URL is always derivable from the public_id via
`ghar_re_service.media.image_url()`'s existing formula
(`https://res.cloudinary.com/<CLOUD>/image/upload/<TRANSFORM>/<public_id>`), so storing the
public_id keeps this ETL decoupled from whichever cloud name/transform is configured at read time.
This is a deliberate choice, not an oversight — documented here per the task brief's requirement to
pick one and document it.

### Idempotency guarantee

Before generating anything, the pipeline loads `db.load_dish_ids_with_image()` — every `dish_id`
that already has a `dish_images` row — into `ImageContext.existing_dish_ids_with_image` at the
start of an `--apply` run, and adds to that same in-memory set immediately after each successful
generation within the run (so two rows that dedupe-merge onto the same dish in one run cannot
double-generate either). A dish already in that set is **skipped entirely**: no Pollinations call,
no Cloudinary call, no new `image_assets` row. This is checked at persist time in `pipeline.py`'s
`_persist_row`, not at parse time, because the check needs a resolved `dish_id`.

### Trigger condition and CLI flags

`--generate-images` (default) / `--skip-images` (mutually exclusive) on
`ingest_dish_dataset.py`. `--skip-images` reverts every row to the v1.0
`fetch_status='not_applicable'` placeholder — no network path is even constructed.
`--dry-run` **never** calls Pollinations or Cloudinary regardless of `--generate-images` — Stage 5
in dry-run mode only plans and reports (heuristic prompt fields only, to keep dry-run free of any
network call at all, including to Groq/HF) via `images.planned_dry_run()`.

### Rate limiting / cost discipline

`--image-delay` (default 3 seconds, ported from the reference script's
`DELAY_BETWEEN_REQUESTS`) sleeps between each real Pollinations call in `_persist_row`. Pollinations
retries use the reference script's own backoff (`time.sleep(15 * attempt)`, up to 3 attempts) —
`PollinationsClient(max_retries=..., timeout=...)` and `--batch-size` (existing flag, reused —
controls DB transaction batch size, which also gates how many images are attempted before a
commit) are the tunable knobs for batch size / cost control.

### Validated vs NOT validated (Stage 5 specifically — read before trusting anything below)

This sandboxed delivery environment has **no live credentials for any of the three external
services this stage needs**, confirmed by direct inspection, not assumed:

```
$ env | grep -iE 'GROQ|HF_API|HUGGINGFACE|CLOUDINARY'
(no output — none of GROQ_API_KEY, HF_API_KEY, HUGGINGFACE_API_KEY, CLOUDINARY_CLOUD_NAME,
 CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET are set)
```

Network reachability was tested directly (not assumed) via the sandbox's own outbound proxy status
endpoint and a real call through `PollinationsClient.generate_png()`:

- `curl` to `image.pollinations.ai`, `api.cloudinary.com`, and `api.groq.com` — all three return a
  proxy-level **403 (Tunnel connection failed / gateway policy denial)**, confirmed via
  `$HTTPS_PROXY/__agentproxy/status`'s `recentRelayFailures` log, which recorded a
  `connect_rejected` / `"gateway answered 403 to CONNECT (policy denial or upstream failure)"` for
  all three hosts.
- A real call through this delivery's own `PollinationsClient.generate_png()` (not curl — the
  actual code path this ETL runs) was executed and reproduced the same failure:
  `RuntimeError: pollinations generation failed after 1 attempts: <urlopen error Tunnel connection
  failed: 403 Forbidden>`.

**Conclusion: no live Pollinations, Cloudinary, or Groq/HF call succeeded in this delivery
environment — the outbound network policy blocks all three, independent of whether credentials are
configured.** Do not treat "an image was generated and uploaded" as a claim this session makes; none
was.

**Executed and verified for real in this session:**
- `--dry-run` end-to-end over the real (truncated, for speed) `IndianFoodDatasetCSV.csv`, with Stage
  5 wired in and reporting `planned_dry_run` outcomes — zero network calls, confirmed by
  sub-100ms elapsed time for 57 rows.
- `--dry-run --skip-images` — confirms the disable flag correctly reverts to the placeholder path.
- `image_prompt.ImagePromptGenerator().resolve_fields(..., force_heuristic=True)` and
  `image_prompt.assemble_prompt()` — the heuristic fallback path and template assembly produce a
  well-formed prompt string matching the fixed template exactly (byte-for-byte diffed against the
  xlsx template's fixed segments).
- `images.slugify()` — produces the exact expected slug for the worked `build_image_map.py`
  example.
- `images.PollinationsClient.generate_png()` — executed for real against the live host; failed with
  the proxy 403 documented above (this **is** the real-call attempt the task brief asked for; the
  result is a network-policy denial, not a code bug).

**Written but NOT executed (no reachable path in this environment):**
- Any successful Pollinations generation (all attempts blocked at the proxy).
- `CloudinaryUploader.upload_png()` — the signed-upload/multipart-body code was written and
  reviewed against Cloudinary's documented signing algorithm (sorted `key=value&...` + secret,
  sha1) but has never received a real HTTP response from Cloudinary.
- `ImagePromptGenerator._call_groq()` / `_call_hf()` — the real API call code paths (payload shape,
  auth headers, response parsing) were written and reviewed against `groq_adapter.py`'s existing
  pattern and the HF Inference API's documented request/response shape, but neither has ever run
  against a live key+endpoint in this environment.
- Migration `077_dish_image_generation_provenance.sql` and the `--apply` persistence path for
  Stage 5 (`db.insert_image_asset()` with the new provenance columns, `_persist_image_result()`) —
  same "written, reviewed against existing style, never run against Postgres" status as
  migration 076's tables (see §4 below).

### Migration 077

`database/migrations/077_dish_image_generation_provenance.sql` adds 5 columns to the existing
`public.image_assets` table (from migration 076): `prompt_text`, `prompt_backend`,
`prompt_model_name`, `image_gen_backend`, `image_gen_seed`. This was a genuine gap — 076's
`image_assets` recorded *what* was fetched (URL, checksum, fetch_status) but had no column for
*how* an `ai_generated` image was produced, which the task brief explicitly requires ("full
provenance: which model/prompt/adapter generated it"). Everything else Stage 5 needs
(`source_url`, `storage_path`, `checksum_sha256`, `fetch_status`, and `dish_images.source_type` /
`confidence` / `alt_text` / `is_primary`) already existed in 076 and is reused unchanged — no
duplicate tables were created. Rollback:
`database/migrations/077_dish_image_generation_provenance_rollback.sql`.

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
- **Stage 5 (v1.1) validated vs unexecuted:** see §2A's dedicated subsection above — short
  version, `--dry-run` was run for real, `PollinationsClient.generate_png()` was called for real
  and hit a proxy 403, and no Groq/HF/Cloudinary call succeeded because no credentials are
  configured in this environment and the sandbox's outbound network policy blocks all three hosts
  regardless.

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

**Stage 5 (v1.1) idempotency is an additional, explicit guard on top of the table-level keys
above:** before generating anything, `ImageContext.existing_dish_ids_with_image` is loaded from
`db.load_dish_ids_with_image()` (every `dish_id` with at least one `dish_images` row). A dish
already in that set causes Stage 5 to skip entirely for that row — no Pollinations call, no
Cloudinary call, no new `image_assets`/`dish_images` write attempt at all (not merely a
conflict-tolerant write). This is a belt-and-suspenders design: even if `checksum_sha256`
happened to collide or differ across reruns (each generation uses a fresh random seed, so bytes
are never identical), the dish-level guard still prevents a second real network call and a second
image being attached to the same dish.

## 6. How to run it

```bash
# 1. Dry run (no DB needed) — always do this first
python3 database/etl/ingest_dish_dataset.py --dry-run

# 2. Real run (requires a reachable Postgres with this repo's migrations 001-077 applied)
export DATABASE_URL=postgres://...              # or SUPABASE_DB_URL
pip install psycopg2-binary                      # new dependency for this ETL only
export CLOUDINARY_API_KEY=...  CLOUDINARY_API_SECRET=...   # required for real image uploads
export GROQ_API_KEY=...                                     # optional — else HF, else heuristic
python3 database/etl/ingest_dish_dataset.py --apply

# Optional: different CSV, smaller/larger batches, write the report to a file, verbose logging,
# disable Stage 5 image generation entirely, or change the delay between Pollinations calls
python3 database/etl/ingest_dish_dataset.py --apply \
  --csv path/to/other.csv --batch-size 500 --report-out /tmp/import_report.json -v \
  --skip-images                 # or: --image-delay 5
```

Apply the migrations first (via your normal Supabase migration flow —
`supabase db push` or `mcp__Supabase__apply_migration`, not run manually here), in order:
`database/migrations/076_dish_ingestion_pipeline.sql`, then
`database/migrations/077_dish_image_generation_provenance.sql`.

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
- **(v1.1)** No live Pollinations, Cloudinary, or Groq/HF call has ever succeeded from this
  delivery environment — the sandbox's outbound proxy blocks all three hosts (403), independent of
  credentials. The full generate+upload code path (`images.generate_and_upload`,
  `CloudinaryUploader.upload_png`, `ImagePromptGenerator._call_groq`/`_call_hf`) is written and
  reviewed but genuinely unexecuted end-to-end; first real `--apply --generate-images` run against
  a reachable network + real credentials needs to be treated as the actual validation, not this
  delivery.
- **(v1.1)** Cloudinary's Admin API-side `build_image_map.py` has not been re-run against any
  images this ETL might eventually upload — once real generation happens, that script needs a
  fresh run to fold the new `dish_slug_hero_01_*` assets into `dish_images_v1.json` for
  `ghar_re_service.media` to actually serve them.
- **(v1.1)** The heuristic prompt-field fallback (`ImagePromptGenerator._heuristic`) produces a
  generic description ("prepared with X, Y, Z, presented with its typical color, texture and
  garnish") rather than a genuinely dish-specific one — acceptable as a last-resort, cost-free
  fallback, but real Groq/HF calls will produce materially better prompts and should be preferred
  whenever credentials are available.
- **(v1.1)** `--image-delay` (default 3s) and Pollinations' own retry backoff are the only
  rate-limiting in place; there is no batch-level circuit breaker if Pollinations starts failing
  systematically mid-run (e.g. rate-limited) — each row's failure is caught and logged to
  `import_row_errors`, but the run does not pause or slow down in response to a string of
  failures. Acceptable for a free/best-effort API, flagged as a possible future improvement.

## Critical Self-Review

The biggest risk in this delivery is that it was built and validated entirely without a live
database — every SQL statement is unexecuted. The mitigation taken was maximal fidelity to
existing migration style (read six prior migrations in full before writing) and a real dry run
against the actual CSV to prove the non-DB code path is correct and fast. The corrected row count
(6,871, not 16,523) is disclosed prominently rather than silently substituted, per this repo's
"never fabricate" rule — the original task brief's row-count framing was based on a physical
line count that does not account for embedded newlines in quoted CSV fields.

**(v1.1 addition)** The second biggest risk is the same pattern repeating for Stage 5: this
delivery environment has neither a live database nor live network access to any of Pollinations,
Cloudinary, or Groq/HF (confirmed via `$HTTPS_PROXY/__agentproxy/status`'s own failure log, not
assumed), so the entire real generate-and-upload path is unexecuted. The mitigation taken was the
same as for migration 076: maximal fidelity to an existing, working reference (the Founder's
Pollinations script, ported field-for-field for the generation call; `build_image_map.py`'s naming
convention, matched exactly and unit-verified with `slugify()`) plus disclosing precisely which
single real network attempt was made and what it returned (a 403 from the sandbox's own proxy,
not a code failure) rather than silently downgrading to "written but unexecuted" without saying so.

## Versioning & Placement

v1.1 (2026-08-06) — adds Stage 5 real image generation (Groq/HF prompt-field generation,
Pollinations.ai flux-pro image generation, signed Cloudinary upload), migration 077, and
`--generate-images`/`--skip-images`/`--image-delay` CLI flags. Renamed from
`[ACTIVE]_RUNBOOK_Dish_Ingestion_Pipeline_v1.0.md` in place per the Naming Standard's single-dot
version convention — v1.0's content is fully preserved above (nothing was removed, only extended
and annotated with v1.1-labeled additions).

v1.0, initial version. Placed in `docs/architecture` (operational runbook for how the dish
catalogue is built), naming standard `[ACTIVE]_RUNBOOK_Name_vMAJOR.MINOR.md` per
`docs/governance/[ACTIVE]_Repository_Naming_Standard_v1.1.md` §3.

Founder Sign-off:
