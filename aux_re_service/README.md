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

## Local model and retrieval hooks

Candidates may be passed in the request, loaded from a local JSON pool, or retrieved from Qdrant.
Qdrant URLs are restricted to loopback or the `qdrant` service hostname. Query embeddings use a
stable local feature hash. The registry exposes hooks for LightFM, RecBole LightGCN, KGAT,
FairRec, Debias, CDR, and DA; a hook is only enabled when its local package is installed. This
service never downloads a model or calls an AI API at runtime.

The current production-safe baseline is weighted local reranking with safety filtering,
popularity debiasing, repetition penalties, diversity selection, and template reason codes. Set
`AUX_REC_USE_LOCAL_RERANKER=false` to force an existing-engine fallback until another governed
local model produces a result.

Every optional registry entry also has an independent ablation flag of the form
`AUX_REC_MODEL_<NAME>_ENABLED`; the complete list is in `.env.example`. Safety and hard dietary
rules are intentionally not disable-able.

## Contract notes

The existing engine payload is intentionally opaque so its schema cannot be changed or narrowed
here. Its optional `metrics` object can expose `quality_score`, `confidence`, `diversity_score`,
`safety_score`, and `alignment_score`; conservative defaults apply when absent. Candidate fields
are documented by `Candidate` in `schemas.py`, and FastAPI publishes the complete JSON Schema at
`/openapi.json`.
