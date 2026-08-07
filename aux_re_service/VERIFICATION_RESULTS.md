# Verification results — 2026-08-07

## Executed paths

| Path | Result |
|---|---|
| Disabled/shadow/compare/active and immutable fallback | Pass |
| Stable household A/B assignment and control-arm protection | Pass |
| Local feedback validation, idempotency, persistence, and normalization | Pass |
| Dataset PK/FK/schema/label/temporal/dedupe checks | Pass; Dataset 2 gaps remain reported |
| Canonical ontology v2 and typed graph | Pass: 86 dishes and 1,908 ontology relations |
| Household/member preference graph | Pass: 29,020 edges |
| Weekly feature and plan-context pipeline | Pass: 10,000 households |
| Qdrant vectors, metadata filters, local upload and live query | Pass: 86 points |
| LightFM v2 training, loading, scoring and active-mode synthetic block | Pass |
| Safety, diversity, repetition, pantry, leftovers, schedule and occasion ranking | Pass |
| Offline scorecards and before/after promotion comparison | Pass |
| Prometheus-compatible metrics, structured logs and model trace | Pass |
| Independent Python 3.11 production image | Pass |

## Model evidence

| Model family | State | Evidence |
|---|---|---|
| LightFM WARP hybrid v2 | Shadow-ready only | Recall@10 0.1093 vs 0.0351 popularity; NDCG@10 0.0393 vs 0.0149; coverage 0.6047 vs 0.1395 |
| Local weighted/MMR reranker | Ready | Deterministic household/context score and hard-filter tests |
| Qdrant + local feature hash | Ready for local/shadow | Live 64-dimensional point upload/query and payload filtering |
| Local food/household graph | Ready for retrieval/export | Ontology, similarity, substitution and member relations |
| LightGCN | Deferred | Input exported; no real interaction volume and density gate fails |
| KGAT | Deferred | Input exported; same interaction gate plus ingredient coverage 43.0% |
| FairRec/Debias/CDR/DA | Scaffold-only | Current deterministic fairness/diversity/debias policies remain safer until real slice benchmarks exist |

The machine-readable source of truth is `data/reports/quality_gate_v2.json`. Synthetic artifacts are
allowed only in shadow mode, even when the local synthetic-artifact switch is enabled. Production
activation remains false.
