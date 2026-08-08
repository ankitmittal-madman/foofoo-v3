# FooFoo auxiliary recommender

This is a separate, fully local recommendation service. It does not import or modify
`ghar_re_core` or `ghar_re_service`. The caller supplies the existing engine result as an opaque
object; the service deep-copies it, builds an auxiliary result, and applies a deterministic policy
gate. Every error and rejection path returns the original object unchanged.

## Run locally

```bash
python -m pip install -e './aux_re_service[test]'
AUX_REC_ENABLED=true AUX_REC_MODE=shadow \
  uvicorn aux_re_service.main:app --host 127.0.0.1 --port 8081
curl -X POST http://127.0.0.1:8081/v1/recommendations \
  -H 'content-type: application/json' --data @aux_re_service/examples/request.json
```

Run tests with `pytest -q aux_re_service/tests`. Build the independent image from the repository
root with `docker build -f aux_re_service/Dockerfile -t foofoo-aux-re .`.

## Deploy shadow service

The protected `Deploy Aux RE in shadow mode` GitHub workflow deploys `aux_re_service/fly.toml`.
It does not deploy or own Qdrant data. Before approval, the exact immutable collection must already
exist in a separately governed Qdrant service and its point count must equal the publication
manifest. Configure the production environment with:

- variables `FLY_AUX_APP`, `AUX_RE_QDRANT_URL`, and `AUX_RE_QDRANT_ALLOWED_HOST`;
- secrets `FLY_API_TOKEN`, `AUX_RE_SERVICE_SECRET`, and `AUX_RE_QDRANT_API_KEY`.

The workflow checks the collection through HTTPS without placing the API key in the command line,
stages both runtime secrets through Fly's secret input, deploys a no-scale-to-zero service, and
requires `/v1/meta` to report `enabled=true`, `mode=shadow`, and the exact publication. It cannot
enable Aux overrides and does not change Edge's `AUX_RE_MODE`; user-visible serving remains Ghar-only
until the separate evidence and rollout gates approve a later canary.

## Modes and rollout

- Disabled: bypasses candidate retrieval and returns the existing result.
- Shadow: runs and logs both outputs but always selects the existing result.
- Compare: applies the policy; an override additionally requires `AUX_REC_ALLOW_OVERRIDE=true`.
- Active: uses the same safety policy as compare and permits a winning auxiliary result only when
  overrides are enabled.

Start with the defaults in `.env.example`: disabled, shadow, and overrides off. Enable shadow,
inspect the `foofoo.aux_re` structured logs and `/v1/meta` counters, then progress to compare and
active separately. Environment is re-read per request, so the kill switches apply without process
restart. Invalid configuration makes `/readyz` return 503.

## Dataset, model, and retrieval pipeline

Candidates may be passed in the request, loaded from a local JSON pool, or retrieved from Qdrant.
Qdrant URLs are restricted to loopback, the Docker `qdrant` service hostname, or one Fly.io
private `.internal` application hostname on the Qdrant port, or one exact configured HTTPS host.
The governed HTTPS path requires `AUX_REC_QDRANT_ALLOWED_HOST` and `AUX_REC_QDRANT_API_KEY`;
unapproved public hosts, URL credentials, paths, queries and alternate ports are rejected. Query
embeddings use a stable local feature hash. The
supplied workbooks are audited and converted into a checksummed
canonical ontology, household features, weighted interactions, retrieval points, and graph edges.
The committed LightFM hybrid model is real and beats the popularity baseline offline. Because its
source interactions are synthetic, the loader permits it in shadow mode only; active mode rejects
it even when the synthetic-artifact switch is set. RecBole LightGCN and KGAT remain deferred until
the readiness report proves enough real interaction density and ontology coverage. This service
never downloads a model or calls an AI API at runtime.

For a database-backed catalogue publication, upload directly into a new versioned collection. The
importer verifies the JSONL checksum and row count before upload, streams bounded batches, and
verifies the exact Qdrant count afterward:

```bash
python -m aux_re_service.training.retrieval_pipeline \
  --upload-publication /absolute/path/to/publication \
  --qdrant-url http://127.0.0.1:6333 \
  --collection foofoo_recipes__PUBLICATION_HASH_PREFIX
```

Then set `AUX_REC_QDRANT_COLLECTION` to that immutable collection and
`AUX_REC_CATALOGUE_PUBLICATION_VERSION` to the full `sha256:...` value in its manifest. Runtime
queries filter on that version and reject a mismatched or non-UUID result. Switching both values
back to the prior collection is the rollback; activation remains an operator action.

The governed production sequence uses GitHub Actions rather than a workstation:

1. `Recommendation catalogue publication` opens a project-verified read-only production
   transaction and uploads exactly `manifest.json`, `catalogue.jsonl`, and `catalogue.sqlite3`.
2. `Publish recommendation catalogue to Qdrant` accepts that artifact only from the named
   successful producer, creates the hash-named collection over approved HTTPS with the API key
   resolved from an environment variable, and uploads only its aggregate count/version report.
3. `Deploy Aux RE in shadow mode` accepts that exact Qdrant report, rechecks the live collection,
   and then deploys the stateless service. Artifact names alone are insufficient at every handoff.

Run the complete local stack with `docker compose -f aux_re_service/compose.local.yml up --build`.
It starts pinned Qdrant, uploads all canonical dish vectors, and starts the service in shadow mode.
The current evidence and exact schemas are in `DATASET_AND_MODEL_REPORT.md`; the machine-readable
gate is `data/reports/quality_gate_v2.json`, and the ask-by-ask status is in
`REQUIREMENTS_COMPLETION_MATRIX.md`.

Consented product feedback can be posted to `/v1/feedback` after configuring an absolute local
`AUX_REC_FEEDBACK_PATH`. Event IDs are idempotent; ratings, household votes, and substitutions have
event-specific validation. Normalize a captured snapshot before a governed refresh with:

```bash
python -m aux_re_service.training.feedback_pipeline \
  --source /absolute/path/feedback.jsonl \
  --output /absolute/path/normalized.jsonl \
  --report /absolute/path/feedback-report.json
```

`AUX_REC_EXPERIMENT_ENABLED` and `AUX_REC_EXPERIMENT_PERCENT` provide stable household-level
control/treatment assignment. The control arm can never override the existing result. Keep both
switches off until authenticated product integration and experiment approval exist.

The current production-safe baseline is weighted local reranking with safety filtering,
popularity debiasing, repetition penalties, diversity selection, and template reason codes. Set
`AUX_REC_USE_LOCAL_RERANKER=false` to force an existing-engine fallback until another governed
local model produces a result.

Implemented optional paths have independent switches in `.env.example`. Scaffold-only framework
entries cannot be enabled accidentally. Safety and hard dietary rules are intentionally not
disable-able.

## Offline verification

Labeled replay datasets can be evaluated without network access:

```bash
AUX_REC_ENABLED=true AUX_REC_MODE=active AUX_REC_ALLOW_OVERRIDE=true \
  python -m aux_re_service.evaluation path/to/scenarios.json
```

Each scenario contains `request` and `expected_decision_reason`. The report includes deterministic
decision accuracy, constraint pass rate, selection/fallback rates, mean quality/diversity, and
candidate recall size. This harness is operational; a representative production dataset and
promotion thresholds are still required before active rollout. See `PRODUCTION_READINESS.md`.

## Contract notes

The existing engine payload is intentionally opaque so its schema cannot be changed or narrowed
here. Its optional `metrics` object can expose `quality_score`, `confidence`, `diversity_score`,
`safety_score`, and `alignment_score`; conservative defaults apply when absent. Candidate fields
are documented by `Candidate` in `schemas.py`, and FastAPI publishes the complete JSON Schema at
`/openapi.json`.
