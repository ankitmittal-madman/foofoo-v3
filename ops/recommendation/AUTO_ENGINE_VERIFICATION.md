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

The original production-image execution used a deterministic weak-DB fixture because that shell
had no database credential. Subsequent protected, credential-isolated workflows supplied the live
database evidence described below.

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

## Historical production writer attribution

The 461-row set found in production matched the checked-in execute report exactly:

| Evidence | Value |
|---|---|
| Writing application path | `.github/workflows/recommendation-auto-engine.yml` → `ops/recommendation/auto_engine.py` → PostgreSQL training store |
| Batch ID | `sha256:e0a3bacfef4406057177ca4a` |
| Generation method | `expert-household-research-v1` |
| Rows | 461 |

This identifies the automated writer path and payload. The historical rows did not preserve a
reliable initiating human/AI actor, so they cannot support stronger personal attribution.

## Live two-project relocation verification

Read-only run [31177968315](https://github.com/ankitmittal-madman/foofoo-v3/actions/runs/31177968315)
bounded the transfer to that immutable batch. Protected execute run
[31178058011](https://github.com/ankitmittal-madman/foofoo-v3/actions/runs/31178058011)
completed successfully.

| Check | Result |
|---|---:|
| Exported from production | 461 |
| Inserted into training | 461 |
| Verified in training | 461 |
| Deleted from production after verification | 461 |
| Remaining matching production rows | 0 |
| Manifest content SHA-256 | `5ef9eee5ffbf7f91de5da281a3816fd8d78e993f54e9b763b1bb37c3c4b706d3` |

Production database size fell from 378,825,875 to 172,182,675 bytes during the exact cleanup and
compaction. The training database grew from 224,095,379 to 224,537,747 bytes. The data-bearing
transfer artifacts were deleted after the move; non-sensitive count reports remain as audit
evidence.

The current workflow gives the production job read-only access for aggregate snapshot creation.
Only the protected training job can create synthetic research rows, and it uses
`TRAINING_DATABASE_URL` with explicit project-reference inequality and a typed confirmation.

## Regression evidence

- New auto-engine plus auxiliary tests: 53 passed.
- Existing recommendation core: 151 passed, 1 skipped.
- Existing recommendation service: 93 passed.
- Food ontology service: 16 passed, 6 integration skips.
- Ruff format/lint: passed.
- Mypy: passed for all seven new operational modules.
