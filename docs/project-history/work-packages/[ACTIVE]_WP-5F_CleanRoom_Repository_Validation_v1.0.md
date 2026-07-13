# WP-5F — Clean-Room Repository Validation v1.0

**Status:** ACTIVE — executed (validation-only; no schema/DB/app change)
**Version:** v1.0
**Date:** 2026-07-13
**Placement:** docs/project-history/work-packages/[ACTIVE]_WP-5F_CleanRoom_Repository_Validation_v1.0.md
**Supersedes:** None
**Dependencies:** WP-5B (Migration Recovery), WP-5C (Rollback Recovery), Repository Completeness Audit, Repository Recovery Work Package Plan. Produces: [ACTIVE]_CleanRoom_Validation_Report_v1.0 (findings) and its execution certificate.

---

## 1. Objective

Prove — without building new functionality and without executing against any database — that the recovered FooFoo repository is internally consistent, reproducible and implementation-ready. This is the final engineering validation before Repository Green Certification.

## 2. Scope

**In scope:** full independent read and validation of migrations 001–028, rollbacks 001–028, seeds 100–102, validation scripts 900–904; a clean-room build+teardown *simulation* grounded in repository files; production of eight engineering matrices; a RED/YELLOW/GREEN readiness verdict; a factual remaining-gaps list.

**Out of scope:** any schema change; any migration/rollback/seed/validation edit; any execution against production (`foofoo-mvp`) or any database; any application/API/frontend code; any remediation of the gaps found (deferred to WP-5D/5E/5G).

## 3. Inputs

Repository @ `ab516c6` (HEAD == origin/main, clean tree). CLAUDE.md; the 28 migration + 28 rollback + 3 seed + 6 validation SQL files; recovery reports (Migration Recovery, WP-5C Rollback Recovery, Completeness Audit, Recovery Backlog/Roadmap/WP-Plan, Rollback Dependency Graph / Confidence Matrix); governance (Naming Standard, AGR-005/006, WP-04DC RLS Diagnostic).

## 4. Repository state before execution

HEAD `ab516c6`; migrations 001–028 present; rollbacks 001–028 present (28/28 after WP-5C); seeds 100–102; validation 900–904; readiness prior to this pass recorded as YELLOW by the Completeness Audit. No certificates with real seed/validation output present.

## 5. Execution plan

Steps 1–12 of the WP-5F brief: sync → reconstruct → migration validation → rollback validation → clean-room simulation → integrity → matrices → readiness → gaps → knowledge → git → report. Read every SQL file in full; treat prior reports as claims to verify.

## 6. Validation plan

Numbering contiguity; per-file dependency resolution; FK/index/trigger/policy correctness; seed-vs-schema compatibility; validation-script-vs-schema compatibility; 1:1 rollback pairing; reverse-order teardown to empty; loud-fail/lossy classification; integrity (orphans/duplicates/cycles/broken refs/undocumented objects/numbering).

## 7. Risks

Low for the act itself (read-only + documentation). Principal risk is *analytical*: inheriting a prior report's conclusion instead of re-deriving it — mitigated by full re-reads and file:line citations.

## 8. Acceptance criteria

Every one of the brief's Step-7 matrices produced from evidence; readiness rated with evidence; every gap factual and cited; nothing fabricated, nothing executed, no schema touched.

## 9. Exit criteria

Clean-Room Validation Report + this WP + execution certificate committed; KNOWLEDGE.html Session 5 appended; STOP for Founder approval before any recommended follow-on WP.

## 10. Outcome (executed 2026-07-13)

**Readiness = YELLOW.** Migration+rollback layer sound and self-reconstructable (28/28, contiguous, clean simulated build+teardown). Two new evidence-backed defects (SEED-01 seed/slot incompatibility; VALIDATION-01 stale table-count) plus carried gaps (PROD-PARITY, EXEC-EVIDENCE, SEC-901T5) block GREEN. Full detail, matrices and gap list in the Clean-Room Validation Report.

## 11. Critical Self-Review

- **Considered** treating WP-5F as a rubber-stamp of WP-5B/5C since both reported HIGH confidence. **Rejected** — independent validation that cannot fail is not validation; re-reading surfaced SEED-01/VALIDATION-01 that the recovery reports missed.
- **Considered** running a live apply given Supabase MCP availability. **Rejected** — no disposable DB approval; brief mandates simulation absent explicit approval. Live replay assigned to WP-5G.
- **Governance discovery:** the brief re-sequences the committed Recovery WP Plan (5F Green→now 5F Validation; new 5D Production-Migration-Recovery; 5E Execution-Evidence; 5G Green). Recorded in the companion IDR for Founder ratification rather than silently adopted.

## 12. Founder Sign-off

Founder acceptance of WP-5F execution: _______________________ Date: ___________
