# Repository Recovery Roadmap v1.0

**Status:** ACTIVE — Roadmap, report only (no work package executed)
**Version:** v1.0
**Date:** 2026-07-13
**Placement:** docs/roadmaps/[ACTIVE]_Repository_Recovery_Roadmap_v1.0.md
**Supersedes:** None — first Repository Recovery Roadmap
**Dependencies:** Repository_Completeness_Audit_v1_0, Repository_Recovery_Backlog_v1_0, Repository_Recovery_Risk_Register_v1_0, Repository_Recovery_Decision_Log_v1_0, Repository_Recovery_Work_Package_Plan_v1_0.

---

## Executive Summary

This roadmap sequences the recovery of the FooFoo repository to a GREEN, freeze-ready state. The order is **derived** from artifact dependencies found in the audit, not assumed. The single Critical risk (RR-01: the repo cannot rebuild its own database) drives migration recovery to the front. Nothing here is executed; each stage maps to a work package in the Recovery Work Package Plan and requires Founder approval before it begins.

## 1. Current Position

- Repository health: **YELLOW** (Repository_Completeness_Audit_v1_0).
- Engineering roadmap position (`FooFoo_Project_Roadmap_v1.1`): Phase 6, **Repository Gate PENDING**. The Repository Gate ("a trivial migration applies AND rolls back — proven") cannot be honestly passed until rollback files exist for the structural baseline. Recovery is therefore the prerequisite to the next roadmap gate.

## 2. Derived Dependency Graph (Step 7)

Derived from: a rollback reverses a specific forward migration (so a rollback cannot be trusted until its forward file is present); a seed loads into a migrated schema; validation checks a seeded schema; a certificate attests to a completed run.

```
WP-5A Audit (this deliverable set — DONE)
        │
        ▼
WP-5B Migration Recovery ── recover 021–026 forward files (+ re_dish_regional_affinity)
        │        (source: live-DB introspection + WP-02 §7.6 + Freeze Packs; RD-01/RD-02)
        ├───────────────► WP-5C Rollback Recovery
        │                    ├─ 020–026 rollbacks  (needs WP-5B forwards)
        │                    └─ 001–019 rollbacks  (needs only present 001–019 forwards — can start in parallel)
        │
        ▼
WP-5D Execution Recovery ── re-run/certify WP-4B, WP-4C, WP-4DB seed+validation; emit missing certificates
        │        (needs complete migration set in-repo [5B] + rollback safety [5C] + RD-01/RD-04)
        ▼
WP-5E Repository Freeze ── templates, runbooks, RACR, naming normalization, README/BOOT-03 errata, freeze certificate
        │        (needs 5B/5C/5D closed; RD-05/RD-06/RD-07)
        ▼
WP-5F Repository Green Certification ── independent re-audit confirms GREEN; sign-off
```

**Parallelism note:** the 001–019 rollback authoring (WP-5C, sub-track b) depends only on the already-present forward files and may run in parallel with WP-5B. Everything else is strictly sequential.

## 3. Sequenced Milestones

| Stage | WP | Exit gate | Blocked by |
|---|---|---|---|
| 1 | WP-5A | This audit accepted by Founder | — |
| 2 | WP-5B | 021–026 present in-repo; clean-room rebuild matches live schema | RD-01, RD-02, RD-08 |
| 3 | WP-5C | 001–026 have paired, tested rollbacks | WP-5B (for 020–026); RD-03 |
| 4 | WP-5D | WP-4B/4C/4DB certified with real output | WP-5B, WP-5C, RD-04 |
| 5 | WP-5E | Templates/runbooks/RACR/naming/errata committed; Freeze Certificate DRAFT | WP-5B/5C/5D; RD-05/06/07 |
| 6 | WP-5F | Independent re-audit = GREEN; Founder signs | WP-5E |

## 4. Out of Recovery Scope (carried, not scheduled here)

Three PIR decisions, DPDP age-gate, IDR-001 master data — product/architecture items owned outside recovery (see Decision Log §2).

## Critical Self-Review

- **Considered** front-loading governance (templates/naming) because it is Low-complexity and quick. **Rejected** — sequencing by ease rather than by risk would leave the only Critical risk (RR-01) open longest; the graph is risk-ordered, with the one genuinely independent low-risk track (001–019 rollback authoring) allowed to run in parallel rather than reordered ahead.
- **Considered** collapsing WP-5E and WP-5F. **Rejected** — a freeze and its independent certification must be separate acts, mirroring how REPO-BOOT-03 certifies a state it did not itself create.

## Versioning & Placement

`[ACTIVE]_Repository_Recovery_Roadmap_v1.0.md` → `docs/roadmaps/`. New file; supersedes nothing.

## Founder Sign-off

Founder acceptance of the Repository Recovery Roadmap: _______________________ Date: ___________
