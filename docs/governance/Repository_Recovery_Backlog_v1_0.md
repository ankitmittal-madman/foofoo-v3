# Repository Recovery Backlog v1.0

**Status:** ACTIVE — Backlog, report only
**Version:** v1.0
**Date:** 2026-07-13
**Placement:** docs/governance/Repository_Recovery_Backlog_v1_0.md
**Supersedes:** None — first Repository Recovery Backlog
**Dependencies:** Repository_Completeness_Audit_v1_0 (source of every item). Parallels the existing Governance Improvement Backlog (DOC-P3-12) in form: nothing is removed; every item carries a recovery-feasibility class.

---

## Executive Summary

This backlog enumerates every missing or incomplete artifact found by the Repository Completeness Audit, and — per Step 6 — classifies each by recovery feasibility. It performs no recovery. Feasibility classes:

- **R1** Recoverable entirely from repository
- **R2** Recoverable partially from repository
- **R3** Recoverable from repository + database (live-DB introspection permitted as a recovery input)
- **R4** Recoverable only from ChatGPT (design/authorship that lived in Claude.ai)
- **R5** Recoverable only from Founder (a decision or external asset)
- **R6** Not recoverable

## 1. Backlog Items

| ID | Missing artifact | Feasibility | Reasoning (evidence) |
|---|---|---|---|
| RB-01 | Forward migrations `021`–`026` (files) | **R3** | DDL was applied to the live DB (`REPO-WP-02:113`, commit `4ed5e91`); exact text is not in-repo. Best source: introspect the live applied schema and reconcile against the WP-02 §7.6 descriptions + Architecture Freeze Packs A/B/C. R4 is a faster path if the original files survive in ChatGPT/Project Files. |
| RB-02 | Table DDL `re_engine.re_dish_regional_affinity` (migration 024) | **R3** | Subset of RB-01; named in `028...sql:33`; 0 CREATE in repo. Spec exists (Batch6 / Freeze Pack B "new dedicated table, dish_id FK, state_code FK, affinity_score numeric"), so DDL is reconstructable from spec + live introspection. |
| RB-03 | Rollbacks `020`–`026` (files) | **R2/R3** | Were authored (`REPO-WP-02:112-113`; `REPO-WP-03 v1.1:47` "020–026 already paired") then lost. Once RB-01 forward files are recovered, their inverses are derivable in-repo (R2); live-DB confirms current object shapes (R3). |
| RB-04 | Rollbacks `001`–`019` (files) | **R1** | Never existed (`REPO-WP-02:109`). The forward files `001`–`020` ARE present, so inverse down-scripts can be authored entirely from the repository. This is engineering authorship, not loss-recovery. |
| RB-05 | WP-4A design document | **R4** | Referenced (`REPO-WP-04B:7` "WP-4A ✅ complete") but never in repo; design authorship occurred in Claude.ai. Re-author if not retrievable. |
| RB-06 | WP-4C design document | **R4** | Referenced (`AGR-006:5` "WP-4C execution"); same as RB-05. |
| RB-07 | WP-4B execution output / Execution Report | **R4 → else R3** | Run happened (`AGR-005:5`); output never committed. Recover from ChatGPT session logs if retained; otherwise re-run WP-4B v1.1 and certify (repository + database). |
| RB-08 | WP-4C execution output | **R4 → else R3** | Run happened (`AGR-006:5`, produced migration 028); same as RB-07. |
| RB-09 | WP-4DB validation output (to 901 Test 5 halt) + Validation Certificate | **R4 → else R3** | Ran and halted (`REPO-WP-04DC:7,13`); no output committed. Recover logs or re-run 900–904 and certify. |
| RB-10 | WP-3D Seed Readiness Certificate | **R3** | WP-03D is DESIGNED only; the promised certificate deliverable was never produced. Produced by executing WP-03D against repo + DB. |
| RB-11 | Engineering templates (WP, Certificate, AGR) | **R1** | Derivable from `REPO-BOOT-02` Task 8, `REPO-BOOT-03`, `AGR-005/006` — all in-repo. |
| RB-12 | Runbooks (session-bootstrap, repository-recovery, git-workflow, migration-authoring) | **R1** | Each backed by an in-repo standard (CLAUDE.md; REPO-BOOT-03; DOC-P3-05 Part A). |
| RB-13 | RACR process definition | **R1** | Named in `CLAUDE.md`; derivable from the existing AGR/SER raise→approve→act shape. |
| RB-14 | Naming normalization (`Copy of _ACTIVE__` / `_ACTIVE__` → `[ACTIVE]_`) | **R5** | Canonical form exists (DOC-P3-09 §06E) but §06E reserves file renaming to the Founder; requires explicit approval before any `git mv`. |
| RB-15 | REPO-BOOT-03 §6 errata (corrects "001–020…paired…100%") | **R1** | Additive errata derivable from this audit; the original assertion is never edited in place. |
| RB-16 | Three PIR architecture decisions (cuisine, tag-vector, combo-role) | **R5** | Founder decisions; Architecture Freeze Packs present the options but leave them unselected. Out of recovery scope; tracked here for completeness. |
| RB-17 | AGR-P3-07-001 (DPDP age-verification) | **R5** | Launch-blocker; Founder/legal owned. Out of recovery scope. |
| RB-18 | IDR-001 master seed data (`Indian_Meal_Cohort_Persona_DB_v3.xlsx`, ~30k rows) | **R5** | External asset; PIR reports it functionally present but it is not in `data/source/` at full volume. Out of recovery scope. |

## 2. Not-Recoverable (R6)

None identified. The original Git commit *history* of the lost `apverse-labs` repo is permanently gone (REPO-BOOT-03 §7), but that is history, not an artifact this backlog can or should reconstruct.

## Critical Self-Review

- **Considered** marking RB-01 as R4 (ChatGPT-only). **Rejected** — the live database is the authoritative record of what DDL was actually applied, making R3 the more reliable primary path; ChatGPT is a convenience accelerator, not the source of truth.
- **Considered** merging RB-03 and RB-04. **Rejected** for the same reason as the audit: different origin, different feasibility (R2/R3 vs R1).
- **Limitation:** R4 items assume ChatGPT/Project-File retention that this session cannot verify; each R4 therefore carries an explicit "else re-author/re-run" fallback so no item depends solely on an unverifiable source.

## Versioning & Placement

`Repository_Recovery_Backlog_v1_0.md` → `docs/governance/`. New file; supersedes nothing.

## Founder Sign-off

Founder acceptance of the Repository Recovery Backlog: _______________________ Date: ___________
