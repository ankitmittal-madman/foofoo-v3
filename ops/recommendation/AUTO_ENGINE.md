# Recommendation auto-training engine

The auto-engine is a DB-first operational pipeline. It inventories real production data before it
does anything else, generates bounded expert-style research only for measured coverage gaps, maps
every food reference through the canonical ontology, and writes generated evidence only to the
private `research.auto_training_records` staging table. It never creates fake production users,
never labels synthetic interactions as real, never changes the active recommender, and never
activates a model.

## Workflow

```text
DB inspection
  -> coverage/readiness decision
  -> deterministic research role (only for gaps)
  -> ontology + confidence gate
  -> idempotent research staging with exact counts
  -> retrieval/baseline refresh
  -> real preference trainer only when real-event gate passes
  -> LightGCN/KGAT gates
  -> evaluation/readiness report
```

The research role uses checked-in canonical food knowledge, the supplied FooFoo training datasets,
and the curated FAO/ICMR grounding recorded in
`aux_re_service/INDIAN_HOME_FOOD_BEHAVIOR.md`. It does not call an external model or paid API.
Generated records include provenance tags, generation method, ontology status, numeric confidence,
confidence band, explanation, version, batch ID, and timestamps.

## Database objects

Migration `087_auto_training_control_plane.sql` adds:

- `ml.auto_training_runs`: one complete A-H run report per execution.
- `ml.auto_training_table_audits`: usable/missing/duplicate/orphan/low-confidence counts.
- `research.auto_training_records`: private, ontology-gated synthetic/curated evidence.
- `ml.auto_training_seed_counts`: exact inserted/updated/skipped/rejected counts per target table.
- `ml.auto_training_model_runs`: input provenance, artifacts, metrics, gates and reasons.

Research records are unique by `(target_table, record_key)`. A repeat run therefore reports the
same unchanged records as skipped; it does not duplicate them. Changed records update only when the
new confidence is at least as strong as the stored confidence.

## Run modes

The CLI requires a service-role PostgreSQL connection through `DATABASE_URL`, `SUPABASE_DB_URL`, or
`FOOFOO_SUPABASE_URI`.

```bash
# Read-only inventory. No research generation, seeding, or training.
PYTHONPATH=.:aux_re_service python -m ops.recommendation.auto_engine \
  --mode audit --report /tmp/foofoo-auto-engine-audit.json

# Read the real DB, simulate enrichment in memory, and show exact would-write counts.
PYTHONPATH=.:aux_re_service python -m ops.recommendation.auto_engine \
  --mode dry_run --report /tmp/foofoo-auto-engine-dry-run.json

# Seed governed research staging and refresh eligible local candidates.
PYTHONPATH=.:aux_re_service python -m ops.recommendation.auto_engine \
  --mode execute --report /secure/foofoo-auto-engine-run.json \
  --output-dir /secure/foofoo-auto-engine-artifacts
```

`execute` trains a research-only LightFM challenger only when its minimum staging threshold passes.
Its provenance forces it to remain non-production. The existing real preference trainer receives
only `data_source='real'`, exactly attributed events and runs only when its existing volume,
household and holdout gates pass. LightGCN and KGAT remain gated until their real interaction and
ontology thresholds pass.

## Scheduling and promotion

The `recommendation-auto-engine` workflow validates the pipeline on changes and weekly. If the
protected DB secret is configured, scheduled runs use `dry_run`; a write/training `execute` run is
manual so production DB mutation remains an explicit operator decision. Every run artifact is
retained for review. Model promotion is still a separate governed action.

Before manual execution:

1. Apply migration 087 and validation 939 in the intended environment.
2. Run `audit`, review missing/orphan/duplicate counts, then run `dry_run`.
3. Confirm generated table counts and confidence bands are plausible.
4. Run `execute` with a private artifact directory.
5. Review offline metrics, gates, and next actions. Do not enable an artifact merely because it
   trained successfully.

The output report always contains DB audit, research generation, seeding, ontology, training,
evaluation, readiness, and exact next-action sections.
