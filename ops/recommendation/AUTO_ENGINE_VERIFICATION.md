# Auto-engine verification — 2026-08-07

## What was verified

| Check | Result |
|---|---|
| DB-first inventory over production and research entities | Pass with deterministic DB fixtures |
| Weak-data research trigger and strong-data no-generation path | Pass |
| Ontology mapping and per-record composite confidence | Pass |
| Diet/allergy-safe positive scenarios and explicit block examples | Pass |
| First seed and repeat-run idempotency counts | Pass |
| Dry-run reads DB staging without writing | Pass |
| Retrieval refresh and LightFM challenger orchestration | Pass in the Python 3.11 production image |
| Real-only preference gate and LightGCN/KGAT gates | Pass; remain disabled without real volume |
| Existing recommender mutation | None |

The production-image execution used a deterministic weak-DB fixture because this shell has no
`DATABASE_URL`, `SUPABASE_DB_URL`, or `FOOFOO_SUPABASE_URI`. It is integration evidence, not a
claim about current production table counts. The protected workflow will produce the real audit
once its DB secret is configured.

## Production-image result

- Generated and simulated-inserted: 461 records across household, member, meal, weekly-plan,
  interaction, hard-constraint, and substitution research targets.
- Batch confidence: 0.9092 (high).
- Positive safety violations: 0; explicit hard-constraint examples: 4.
- Weekly repetition rate: 0.0000; per-plan diversity: 1.0000; catalogue coverage: 0.8023.
- Regional match rate: 0.7917; household interaction coverage: 1.0000.
- Research LightFM holdout: Recall@10 0.5455, NDCG@10 0.2862, coverage 0.5116 over only 11
  evaluated synthetic households.

The small research challenger trained successfully but remains shadow-only by provenance and
sample size. Retrieval refreshed. The real preference model, LightGCN, and KGAT remained gated.
No artifact was activated and the existing recommender/fallback path was not changed.

## Regression evidence

- New auto-engine plus auxiliary tests: 53 passed.
- Existing recommendation core: 151 passed, 1 skipped.
- Existing recommendation service: 93 passed.
- Food ontology service: 16 passed, 6 integration skips.
- Ruff format/lint: passed.
- Mypy: passed for all seven new operational modules.
