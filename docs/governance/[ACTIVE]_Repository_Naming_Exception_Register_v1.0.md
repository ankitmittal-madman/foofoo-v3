# [ACTIVE]_Repository_Naming_Exception_Register_v1.0

**Status:** ACTIVE — exception register
**Version:** v1.0
**Date:** 2026-07-13 (updated same day — see Revision Note)
**Placement:** docs/governance/[ACTIVE]_Repository_Naming_Exception_Register_v1.0.md
**Supersedes:** In-place revision of this document's own v1.0 (not a new version — see note below; content, not identity, changed)
**Dependencies:** [ACTIVE]_Repository_Naming_Standard_v1.0; [ACTIVE]_Repository_Normalization_Report_v1.0.

---

## Revision Note

This document originally listed 19 exceptions after the first WP-5AA pass. The Founder then issued four corrective directives: (1) DRAFT documents that are the latest/only version are final — no explicit review gate; (2) FROZEN and ACTIVE must not be treated as conflicting statuses — collapse to ACTIVE; (3) both APDF documents (Base v1.0 and vNext Addendum v2.0) are current and complementary, not superseded; (4) check naming in Product/Governance/other files not yet touched. A second pass applied these directives, resolving 10 of the original 19 exceptions (the REPO-WP/AGR lifecycle-word set, now `[ACTIVE]`) and completing 14 further renames in Product/Architecture/Governance/Roadmaps/Visuals that were previously held back as "binary, out of scope" once evidence showed they were plain text with real DRAFT headers. **9 exceptions remain**, listed below.

## Executive Summary

Every file still left unchanged after both WP-5AA passes, with the reason and recommended action. Per the Naming Standard §4, genuine ambiguity means "do not rename; record here; never guess."

## 1. Remaining exceptions — genuine ambiguity or missing evidence

| File | Reason | Recommended action |
|---|---|---|
| `Copy of _ACTIVE__SESSION_HANDOFF-4.md` | No version; body literally says "Status: Founder to assign exact phases" — status genuinely unset by its own text | Founder to assign status/version directly |
| `Copy of _ACTIVE__SESSION_HANDOFF_v1_0-1.docx` | Same June-2026 date as SESSION_HANDOFF-4.md; relationship between the two (which supersedes which) is undetermined — a real identity conflict (Baseline Register gap G-6), not a status question | Founder to state which is canonical/current before either is renamed |
| `Copy of _ACTIVE__Project_Checkpoint_v1_0.md` | No explicit Status header line anywhere in the document | Founder to classify |
| `Copy of _ACTIVE__DOC-P3-05_Part_B_Completion_Summary_1_0.md` | Status is a completion phrase ("Files 001–009 complete"), not a token; a pre-REPO-era certificate, not a draft under review | Founder to classify (likely [FROZEN] or a certificate-class exception) |
| `Copy of _ACTIVE__DOC-P3-05_Part_C_Completion_Summary.md` | Same as above; no version | same |
| `Copy of _ACTIVE__DOC-P3-05_Part_D_Completion_Summary.md` | Same as above; no version | same |
| `Copy of _ACTIVE__DOC-P3-05_Regression_Validation_AGR002_003.md` | No status token; no version | same |
| `Copy of _ACTIVE__P3-03_Context_Baseline_Readiness.md` | No status token; no version | same |
| `Copy of _ACTIVE__P3-03_Logic_Inventory_QualityGate.md` | No status token; no version | same |

**Note on the DOC-P3-05/P3-03 completion set:** unlike the REPO-WP series, these do not carry a lifecycle word at all (no DRAFT/DESIGNED/EXECUTED) — Directives 1–2 only resolved documents that *had* such a word. These six remain genuinely unclassified and are not covered by the Founder's directives as given.

## 2. Correctly-preserved historical versions (not exceptions — working as intended)

| File | Why it correctly keeps its status |
|---|---|
| `[SUPERSEDED]_REPO-WP-03_Seed_Readiness_Engineering_v1.0.md` | Its own header says "⚠️ SUPERSEDED BY v1.1"; v1.1 is `[ACTIVE]`. This is the naming standard working correctly — historical versions must keep their true status, not be pulled to ACTIVE by directive 1 (which applies only to the *latest* version). |
| `[SUPERSEDED]_Project_Baseline_Register_v1.1.docx` | Explicit `Supersedes:` chain confirms v1.5 (now `[ACTIVE]_Project_Baseline_Register_v1.5.md`) replaced it. Same reasoning. |

## 3. Resolved in the second pass (no longer exceptions)

For traceability: `REPO-WP-02` (EXECUTED→ACTIVE), `REPO-WP-03D`/`04B`/`04DA`/`04DB`/`04DC` (DESIGNED→ACTIVE), `AGR-005`/`AGR-006` (RESOLVED→ACTIVE), `Repository_Recovery_Work_Package_Plan` (DESIGNED→ACTIVE) — per Founder Directives 1–2 (a DESIGNED/EXECUTED/RESOLVED document that is the current, non-superseded version of its subject is final and carries no unresolved review gate, so it collapses to ACTIVE like FROZEN does). Also resolved: 13 Product/Architecture/Governance/Roadmap/Visuals files, previously held as "binary, out of scope," once plain-text extraction produced real DRAFT-header evidence (Directive 4) — see the updated Normalization Report.

## Critical Self-Review

- **Considered** applying the same DESIGNED/EXECUTED/RESOLVED→ACTIVE collapse to the DOC-P3-05/P3-03 completion set. **Rejected** — those documents contain no lifecycle word at all; extending the directive to them would be inventing a classification the Founder did not state, which the standard forbids.
- **Considered** guessing which SESSION_HANDOFF file is canonical. **Rejected** — this is a genuine, previously-flagged identity conflict (G-6), not a naming-format question; resolving it wrongly could misrepresent project history.

## Versioning & Placement

`[ACTIVE]_Repository_Naming_Exception_Register_v1.0.md` → docs/governance/.

## Founder Sign-off

Founder acceptance of the Exception Register: _______________________ Date: ___________
