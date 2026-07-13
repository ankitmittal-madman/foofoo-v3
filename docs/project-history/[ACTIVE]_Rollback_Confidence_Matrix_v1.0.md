# [ACTIVE]_Rollback_Confidence_Matrix_v1.0

**Status:** ACTIVE — confidence matrix
**Version:** v1.0
**Date:** 2026-07-13
**Placement:** docs/project-history/[ACTIVE]_Rollback_Confidence_Matrix_v1.0.md
**Supersedes:** None
**Dependencies:** [ACTIVE]_WP-5C_Rollback_Recovery_Report_v1.0; [ACTIVE]_Rollback_Evidence_Register_v1.0.

---

## Executive Summary

Per-rollback recovery classification and confidence. Classes (WP-5C Step 4): **A** original recoverable · **B** recoverable from evidence · **C** requires reconstruction · **D** impossible. No rollback is Class A (no originals survive) or Class D (all are reconstructable). 001–020 are Class C (no original ever existed → reconstructed from the forward file); 021–026 are Class B (forward file recovered in WP-5B → rollback derived from it). Confidence reflects how mechanical the reversal is.

## 1. Matrix

| # | Class | Confidence | Reason |
|---|---|---|---|
| 001 | C | MEDIUM | schema/grants drop is exact; `DROP EXTENSION pgcrypto` is runtime-conditional (core function in PG13+) |
| 002–007 | C | HIGH | pure `DROP TABLE` inverse of `CREATE TABLE` |
| 008 | C | HIGH | drop 2 tables; REVOKE moot after drop |
| 009 | C | HIGH | pure table drops |
| 010 | C | HIGH | trigger/function/table drops; bindings verified against forward file |
| 011–016 | C | HIGH | pure table drops |
| 017 | C | MEDIUM | partition names runtime-generated → dynamic `DO` drop (correct but not a static list) |
| 018 | C | HIGH | no-op; migration is an empty placeholder |
| 019 | C | HIGH | drop 23 policies + disable RLS on 19 tables; full list from forward file |
| 020 | C | HIGH | drop 36 named indexes; full list from forward file |
| 021 | B | HIGH | drop policy/columns/table; recovered forward file is exact |
| 022 | B | HIGH | drop 3 columns |
| 023 | B | MEDIUM | function/constraint drop exact; **restoring global UNIQUE is data-conditional** (fails on conflicting rows) |
| 024 | B | HIGH | drop 1 table |
| 025 | B | MEDIUM | column drop exact; **slot text[]→text is lossy** for multi-slot rows (reconstructed USING expr) |
| 026 | B | MEDIUM | **slot text[]→text is lossy** for multi-slot rows |

## 2. Aggregate

- Class C (reconstructed, no original): 20 (001–020)
- Class B (from recovered forward file): 6 (021–026)
- Class A / D: 0
- HIGH confidence: 21 · MEDIUM confidence: 5 (001, 017, 023, 025, 026) · LOW: 0

## 3. The 5 MEDIUM-confidence files — why, and mitigation

1. **001** — `DROP EXTENSION pgcrypto` may be unnecessary on PG13+ (core `gen_random_uuid`); guarded with `IF EXISTS`; harmless if absent.
2. **017** — partition names are deploy-time values; dynamic drop is faithful but drops *all* current partitions (incl. any created by the ongoing job), which is the correct full reversal.
3. **023** — restoring `UNIQUE(tag_name)` re-introduces the Batch-3 conflict by design; fails loudly on conflicting seeded data (intended).
4. **025 / 026** — array→scalar `slot` conversion cannot represent multi-slot rows; lossy on populated data, clean on the currently-unseeded tables. Loud warnings present.

All five are safe on the current (unseeded/illustrative) database state and carry explicit in-file warnings; none is a blocker to repository reconstructability.

## Critical Self-Review

- **Considered** rating 002–016 table drops as MEDIUM because no original existed. **Rejected** — a `DROP TABLE` is the unambiguous, complete inverse of a `CREATE TABLE`; the absence of an original does not reduce confidence when the inverse is mechanical. Class (reconstruction) and confidence (mechanical certainty) are tracked separately for exactly this reason.

## Versioning & Placement

`[ACTIVE]_Rollback_Confidence_Matrix_v1.0.md` → docs/project-history/. New file.

## Founder Sign-off

Founder acceptance: _______________________ Date: ___________
