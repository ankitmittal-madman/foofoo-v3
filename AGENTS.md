# FooFoo AI Agent Instructions

Read `CLAUDE.md` before modifying this repository; its operating, documentation, testing, Git,
and session-knowledge rules apply to every AI coding tool.

## Database placement boundary

- Production Supabase owns real accounts, households, catalogue facts, recommendation exposures,
  outcomes, feedback, and user-visible plans.
- Training Supabase owns synthetic/generated personas, interactions, weekly signals, research
  examples, model-training staging, and synthetic import lineage.
- Write `research.auto_training_records`, `research.training_source_rows`, and
  `ml.auto_training_*` only through `TRAINING_DATABASE_URL` after verifying
  `TRAINING_PROJECT_REF != PRODUCTION_PROJECT_REF` and that the connection URL identifies the
  training project.
- `FOOFOO_SUPABASE_URI` is never a fallback training write target. Production access for an
  Auto Engine run is read-only and may emit only aggregate, non-identifying audit snapshots.
- Fail closed on missing or ambiguous credentials. Never print credentials or store them in code,
  reports, artifacts, or documentation.
- Research relocation must be exact and recoverable: export, hash/count, import, verify, then
  delete only unchanged source rows. Never truncate a table containing mixed batches.
- Record the workflow run, application name, batch ID, and counts so future audits can identify
  which automated path wrote the data even when the initiating human/AI identity is unavailable.
