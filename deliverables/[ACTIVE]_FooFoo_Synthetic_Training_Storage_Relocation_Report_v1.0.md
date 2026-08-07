# FooFoo Synthetic Training Storage Relocation Report

**Status:** ACTIVE  
**Version:** 1.0  
**Date:** 2026-08-07  
**Placement:** `deliverables/`  
**Supersedes:** None  
**Dependencies:** FooFoo Synthetic Training Ingestion Audit and Load Report v1.0; migrations 087–088; batch `06a38fd3-ec53-54ab-ab0f-ef04bdf92c44`

## Executive Summary

FooFoo's generated training data has been relocated from the production Supabase database to a
separate, private training Supabase project. The training project retains all 113,868 normalized
records and the 45 rejected source rows needed for actionable audit evidence. The 132,541 accepted
raw workbook rows remain reproducible from checked-in, checksummed source files instead of being
duplicated in PostgreSQL.

Production cleanup first removed exactly 132,586 raw source rows and 113,868 normalized records
created by the verified workbook batch. A second, batch-bounded relocation then copied and verified
the remaining 461 Auto Engine records in the training project before deleting their unchanged
production copies. Production database size ultimately fell to 172,182,675 bytes. Production now
contains zero synthetic training records covered by either relocation.

## 1. Final Storage Placement

| Data class | Final location | Count | Production impact |
|---|---|---:|---|
| Normalized synthetic training records | Dedicated training Supabase | 113,868 | Removed from production |
| Rejected raw lineage rows | Dedicated training Supabase | 45 | Removed from production |
| Accepted raw workbook rows | Checked-in source workbooks/artifacts | 132,541 | Not duplicated in either database |
| Import batch counts, hashes and policy | Both database audit header and repository report | 1 batch | Small metadata retained |
| Auto Engine synthetic research records | Dedicated training Supabase | 461 | Copied, verified, then removed from production |
| Production users, plans and events | Production Supabase | Unchanged | Never targeted by this operation |
| Trained LightFM artifact and report | Repository/container artifact | 1 model artifact | Unchanged |

## 2. Dedicated Training Project Load

Protected workflow run [31174719969](https://github.com/ankitmittal-madman/foofoo-v3/actions/runs/31174719969)
completed successfully in 1m56s from commit `bd5b5498521ff12a7feed5950ad71fb06e012085`.
It verified that the database URL belonged to the configured training project and differed from
production before running any SQL.

| Verified training result | Count/status |
|---|---:|
| Import status | `completed_with_rejections` |
| Source rows represented by batch metadata | 132,586 |
| Accepted source rows represented | 132,541 |
| Rejected source rows represented and retained | 45 |
| Normalized private records | 113,868 |
| Training dishes | 86 |
| Household personas | 10,000 |
| Interactions | 64,842 |
| Weekly signals | 10,000 |
| Household preference edges | 28,940 |
| Training database size after load | 224,054,419 bytes |
| Production targets requested | 0 |

Evidence artifact `governed-training-ingestion-31174719969-1` has artifact ID `8992399917`
and expires on 2026-09-06. Canonical evidence remains in this report and the checked-in source
manifest rather than depending on the temporary artifact.

## 3. Production Audit and Cleanup

Read-only audits [31175143225](https://github.com/ankitmittal-madman/foofoo-v3/actions/runs/31175143225)
and [31175480571](https://github.com/ankitmittal-madman/foofoo-v3/actions/runs/31175480571)
ran before deletion. They found 114,329 normalized research records: 113,868 created by the
workbook seed and 461 created later. Zero seed-created record had been updated by a later batch.
The cleanup was therefore changed from whole-table normalized truncation to batch-scoped deletion.

Protected execute run [31175558623](https://github.com/ankitmittal-madman/foofoo-v3/actions/runs/31175558623)
completed successfully in 1m05s from commit `c986d8c6126c34cfc3983d2c1837ef80966e7e8e`.

| Production result | Before | After |
|---|---:|---:|
| Database size | 563,186,835 bytes | 376,728,723 bytes |
| Raw training source rows | 132,586 | 0 |
| Workbook-seed normalized records | 113,868 | 0 |
| Later research records | 461 | 461 |
| Production dish/user/plan/event writes | 0 | 0 |

The operation reclaimed 186,458,112 bytes immediately. Supabase dashboard usage metrics may take
until their next refresh to reflect the lower PostgreSQL database size.

## 4. Auto Engine Research Relocation

The 461 records were written through the Auto Engine execute path: the recommendation workflow
invoked `ops/recommendation/auto_engine.py`, selected its PostgreSQL training store, and wrote batch
`sha256:e0a3bacfef4406057177ca4a` with generation method
`expert-household-research-v1`. The matching checked-in execute report proves the application path
and batch. The historical database rows do not contain enough actor metadata to reliably name the
human or AI tool that initiated that run, so no individual attribution is claimed.

Read-only audit run [31177968315](https://github.com/ankitmittal-madman/foofoo-v3/actions/runs/31177968315)
proved the exact batch, count and content hash. Protected execute run
[31178058011](https://github.com/ankitmittal-madman/foofoo-v3/actions/runs/31178058011)
then completed export, training import verification and production cleanup successfully.

| Target | Relocated records |
|---|---:|
| `research.constraint_examples` | 4 |
| `research.household_personas` | 24 |
| `research.interactions` | 240 |
| `research.meal_examples` | 72 |
| `research.substitution_examples` | 37 |
| `research.user_personas` | 60 |
| `research.weekly_plans` | 24 |
| **Total** | **461** |

| Execute verification | Before | After |
|---|---:|---:|
| Training database size | 224,095,379 bytes | 224,537,747 bytes |
| Auto Engine records in training | 0 | 461 |
| Production database size | 378,825,875 bytes | 172,182,675 bytes |
| Auto Engine records in production | 461 | 0 |
| Production research relation size | 207,708,160 bytes | 901,120 bytes |

Every destination row was checked before cleanup. The manifest contained 461 records with content
SHA-256 `5ef9eee5ffbf7f91de5da281a3816fd8d78e993f54e9b763b1bb37c3c4b706d3`;
the import reported 461 inserted and 461 verified, and cleanup reported 461 deleted. The execute
workflow deleted its private transfer artifact automatically. The earlier audit transfer artifact
was also deleted after success; only non-sensitive aggregate reports remain.

## 5. Permanent Writer Controls

| Control | What it prevents |
|---|---|
| Root `AGENTS.md` | Tells Codex and other instruction-aware AI agents that all synthetic training writes belong in the training project |
| Root `CLAUDE.md` | Applies the same mandatory boundary to Claude-based repository sessions |
| `recommendation-auto-engine.yml` | Gives production only a read-only aggregate audit role and routes the writable training phase through `TRAINING_DATABASE_URL` |
| Project-reference guards | Fail closed unless the training and production project references are present, different and consistent with their URLs |
| Typed execution confirmation | Prevents an accidental manual training write |
| Batch/run evidence | Preserves application path, workflow run, batch ID and counts for future attribution |

`FOOFOO_SUPABASE_URI` is no longer a fallback Auto Engine training destination. Pull-request and
push jobs only validate; scheduled/manual database work uses protected GitHub environments.

## 6. Secrets and Access Boundary

| GitHub environment | Credential/identifier | Scope |
|---|---|---|
| `training` | `TRAINING_DATABASE_URL` | Training ingestion only |
| `training` | `TRAINING_PROJECT_REF` | Training identity guard |
| `training` | `PRODUCTION_PROJECT_REF` | Cross-project inequality guard |
| `production` | `FOOFOO_SUPABASE_URI` | Existing protected production operations |
| `production` | `PRODUCTION_PROJECT_REF` variable | Production URL identity guard |

No credential value is stored in the repository, reports or workflow logs. Both workflows use
read-only GitHub token permissions, explicit confirmation phrases, environment protection and
project-reference checks. The training workflow has no fallback to a production secret.

## 7. Recommendation and Model Impact

The relocation does not alter current user-facing recommendations. Real-time recommendation code
does not query the workbook source-row or normalized staging tables. The trained
`lightfm_v2.joblib` artifact, its checksum, recommendation rules and production catalogue remain
unchanged. Future synthetic retraining can read the dedicated training project or recreate the
snapshot from checked-in sources.

## 8. Recovery and Rollback

The schema and loaders remain available in both code and the dedicated training project. Deleted
production training payloads can be recreated deterministically from the checksummed source
artifacts or copied through the governed loader. This would consume production storage again and
therefore requires a new explicit approval. Production identities, dishes, plans and events were
never deleted and need no restoration.

## 9. Verification

- Eight focused importer/cleanup policy tests passed.
- Ruff, mypy with third-party import stubs ignored, Python compilation and workflow YAML parsing
  passed.
- Training schema privacy validations 901, 939 and 940 passed.
- Production cleanup validation 941 passed.
- Secret-name and hardcoded-token-pattern checks found no credential value in touched code.
- Both production audit runs completed without mutation before the execute run was approved.
- The Auto Engine transfer verified 461 destination records before deleting 461 unchanged source
  records; the private transfer artifacts were deleted after use.

## 10. Critical Self-Review

- The production database is below 500 MB but not empty; future ingestion must retain explicit
  storage budgets and size checks.
- The large production footprint was predominantly relation/index bloat rather than the compressed
  461-row payload itself. The completed compaction reclaimed it, but future writers should still
  monitor relation size as well as row count.
- The training database stores normalized data and rejected raw evidence, not every accepted raw
  row. Full lineage remains reproducible only while the checked-in workbooks and manifest are
  preserved.
- GitHub Actions currently reports a Node.js 20 deprecation annotation for pinned official actions;
  the runner forced Node.js 24 and all steps passed.

## 11. Versioning and Placement

This report is the canonical evidence for the first production-to-training storage relocation.
Any later retention-policy, database-location or credential-boundary change requires a new version.

## Founder Sign-off

Founder acceptance: _______________________ Date: ___________
