# Verification results — 2026-08-06

## Executed paths

| Path | Result | Evidence |
|---|---|---|
| Disabled/shadow/compare/active policy | Pass | Service and HTTP integration tests |
| Existing-result immutability | Pass | Deep-copy regression test |
| Local weighted reranker | Pass | Scores structured candidates and changes order by context |
| Safety rules | Pass | Peanut/groundnut alias, restriction, unavailable item, and slot rejection |
| Diversity and repetition | Pass | MMR ingredient penalty and recent-meal novelty test |
| Feature-hash embedder | Pass | Determinism, normalization, and context-sensitivity test |
| Local food graph | Pass | Seed expansion and regional/slot cold-start lookup test |
| Qdrant adapter | Contract pass | Query/filter/timeout/response tested with a local HTTP double; no live server was available |
| JSON candidate pool | Pass | Load and source-isolated failure behavior |
| Offline replay | Pass | Example scenario achieved expected deterministic decision |
| Observability | Pass | Trace, model states, stage timings, counters, rates, and score aggregates emitted |
| Existing Ghar RE regression | Pass | 238 passed, 1 skipped |
| Independent container | Pass | Pinned image built; non-root `/healthz` returned 200 |

## Model readiness

| Model family | Runtime state | Selection capable? |
|---|---|---|
| Existing engine | Opaque input dependency | Baseline only |
| Local weighted/MMR reranker v1 | Ready and exercised | Yes |
| Rule/safety/diversity engines v1 | Ready and exercised | Yes |
| Feature-hash embedder v1 | Ready and exercised | Retrieval only |
| Local food graph v1 | Ready when a graph path is configured | Candidate generation |
| Qdrant | Ready when a local endpoint is configured | Candidate generation |
| LightFM | Package absent; no artifact/loader | No |
| RecBole LightGCN | Package absent; no artifact/loader | No |
| KGAT/FairRec/Debias/CDR/DA | Package absent; no artifact/loader | No |
| Exploration | Not implemented | No |

Framework names are not treated as working models merely because registry rows exist. They remain
disabled until training data, an artifact manifest, an actual loader/scorer, and promotion metrics
are added.

## Commands and results

```text
PYTHONPATH=aux_re_service pytest -q aux_re_service/tests
26 passed

pytest -q ghar_re_core/tests ghar_re_service/tests
238 passed, 1 skipped

ruff check aux_re_service
All checks passed

mypy aux_re_service/aux_re_service --ignore-missing-imports
Success: no issues found in 13 source files

AUX_REC_ENABLED=true AUX_REC_MODE=active AUX_REC_ALLOW_OVERRIDE=true \
  python -m aux_re_service.evaluation aux_re_service/examples/evaluation.json
expected decision accuracy=1.0, selection rate=1.0, quality=0.795, diversity=1.0
```

The example replay proves wiring and metric calculation, not real-world lift. Production claims
require the household-disjoint, time-split dataset and promotion gates in `PRODUCTION_READINESS.md`.
