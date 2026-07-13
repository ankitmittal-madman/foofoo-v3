# [ACTIVE]_Repository_Naming_Exception_Register_v1.0

**Status:** ACTIVE — exception register
**Version:** v1.0
**Date:** 2026-07-13
**Placement:** docs/governance/[ACTIVE]_Repository_Naming_Exception_Register_v1.0.md
**Supersedes:** None
**Dependencies:** [ACTIVE]_Repository_Naming_Standard_v1.0; [ACTIVE]_Repository_Normalization_Report_v1.0.

---

## Executive Summary

Every file deliberately **left unchanged** in the WP-5AA normalization pass, with the reason (evidence-based) and recommended action. Per the Naming Standard §4, ambiguity or a non-token lifecycle status means "do not rename; record here; never guess." No file below was renamed.

## 1. Exceptions — non-token lifecycle status (REPO-WP series + AGRs)

These carry a status word that is **not** one of the five allowed tokens, so no token could be assigned without guessing.

| File | Header status | Recommended action |
|---|---|---|
| `REPO-WP-02_Schema_Baseline_Establishment_v1.0.md` | EXECUTED | Founder to confirm EXECUTED→[FROZEN] (or [ACTIVE]) mapping |
| `REPO-WP-03_Seed_Readiness_Engineering_v1.0.md` | SUPERSEDED (by v1.1) | Founder to confirm; normalize the pair together with v1.1 |
| `REPO-WP-03_Seed_Readiness_Engineering_v1.1.md` | DESIGNED | Founder to confirm DESIGNED→[DRAFT] |
| `REPO-WP-03D_Seed_Readiness_Certification_v1_0.md` | DESIGNED | same |
| `REPO-WP-04B_Seed_Loading_v1.1.md` | DESIGNED | same |
| `REPO-WP-04DA_Validation_Script_Corrections_v1_0.md` | DESIGNED | same |
| `REPO-WP-04DB_Validation_Execution_Certification_v1.0.md` | DESIGNED | same |
| `REPO-WP-04DC_RLS_Diagnostic_v1_0.md` | DESIGNED | same |
| `AGR-005_routing_rules_nullable_show_key.md` | RESOLVED (no version) | Founder to confirm RESOLVED→[ACTIVE] + assign version |
| `AGR-006_weight_ladder_numeric_conversion.md` | RESOLVED (no version) | same |
| `Repository_Recovery_Work_Package_Plan_v1_0.md` | DESIGNED | Founder to confirm DESIGNED→[DRAFT] |

**Recommendation:** ratify one mapping — `DESIGNED→[DRAFT]`, `EXECUTED→[FROZEN]`, `RESOLVED→[ACTIVE]` — then normalize this whole set in a short follow-up. Held back here to avoid embedding a lifecycle interpretation the standard doesn't define.

## 2. Exceptions — no version and/or no status token

| File | Reason |
|---|---|
| `Copy of _ACTIVE__SESSION_HANDOFF-4.md` | No version; body says "Status: Founder to assign exact phases" — status genuinely unset |
| `Copy of _ACTIVE__Project_Checkpoint_v1_0.md` | No explicit Status header line |
| `Copy of _ACTIVE__DOC-P3-05_Part_B_Completion_Summary_1_0.md` | Status is a completion phrase ("Files 001–009 complete"), not a token |
| `Copy of _ACTIVE__DOC-P3-05_Part_C_Completion_Summary.md` | Completion phrase; no version |
| `Copy of _ACTIVE__DOC-P3-05_Part_D_Completion_Summary.md` | Completion phrase; no version |
| `Copy of _ACTIVE__DOC-P3-05_Regression_Validation_AGR002_003.md` | No status token; no version |
| `Copy of _ACTIVE__P3-03_Context_Baseline_Readiness.md` | No status token; no version |
| `Copy of _ACTIVE__P3-03_Logic_Inventory_QualityGate.md` | No status token; no version |

**Recommendation:** Founder to classify these completion/readiness records (likely `[FROZEN]` or `[ARCHIVED]`) and assign versions where missing; then normalize.

## 3. Exceptions — binary / non-.md format (out of scope)

19 `.docx` and 4 `.html` files (product/architecture docs, RE-DOC/RE-Visual set, PM-SUPP docx twins, session handoff docx). Reason: the standard's document form is `.md`; `.docx→.md` conversion is content rewriting, explicitly out of WP-5AA scope, and their governance status is not header-verifiable without opening the binaries. **Recommended action:** a dedicated conversion + normalization work package. (Note: several already carry `[ACTIVE]_` from an earlier era, e.g. RE-DOC/RE-Visual; left untouched pending that WP.)

## Critical Self-Review

- **Considered** mapping DESIGNED→[DRAFT] etc. automatically. **Rejected** — the standard permits only the five tokens and forbids guessing; a lifecycle-word mapping is a governance decision, surfaced here rather than silently applied.
- **Limitation:** this register reflects header evidence at commit `12213b5`; a Founder reclassification supersedes any row.

## Versioning & Placement

`[ACTIVE]_Repository_Naming_Exception_Register_v1.0.md` → docs/governance/. New file.

## Founder Sign-off

Founder acceptance of the Exception Register: _______________________ Date: ___________
