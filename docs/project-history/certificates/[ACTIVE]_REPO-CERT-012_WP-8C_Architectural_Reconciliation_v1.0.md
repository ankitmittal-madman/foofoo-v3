# REPO-CERT-012 — WP-8C Architectural Reconciliation & Decision v1.0

**Status:** ACTIVE — Investigation Certificate (read-only reconciliation; no code, schema, DB, migration, seed, validation-SQL, or security change).
**Version:** v1.0
**Date:** 2026-07-14
**Placement:** docs/project-history/certificates/[ACTIVE]_REPO-CERT-012_WP-8C_Architectural_Reconciliation_v1.0.md
**Attests:** [ACTIVE]_WP-8C_Architectural_Reconciliation_Report_v1.0.md (Phases 1–5) and the authoring of [DRAFT]_DOC-P4-02_Service_and_Edge_Function_Specifications_v1.0.md.
**Dependencies:** DOC-P3-03/03A/04/06, DOC-P4-00, REPO-CERT-007/008/009/010/011, Engineering Handover v1.3, Baseline Register v1.5.

---

## Certification

A complete, evidence-backed architectural reconciliation of the onboarding + recommendation-engine
flow was performed against live repository state (documents + database artifacts + backend code).
**No memory or prior-summary was trusted over the repository.** The investigation is certified
**executed and evidence-complete**, with a single governed recommendation.

## What was examined (evidence)

- **Docs (read this session):** DOC-P3-03 §02–05/§14/§15/§16; DOC-P3-03A (full, via focused read); DOC-P3-04 §03.4 + table/migration map; DOC-P3-06 v1.2 (full); DOC-P4-00 (full); CLAUDE.md; certificates 007–011; Handover v1.3.
- **Repository artifacts (inspected):** `database/migrations` (30), `database/seeds` (100–117), `database/rollback`, `database/validation` (900–905), `database/etl`; `supabase/functions/` (scaffold only).
- **Two independent evidence sweeps** (repo-wide keyword/inventory sweep; DOC-P3-03A execution-classification deep read) corroborated the findings.

## Findings (summary; full detail in the Reconciliation Report)

1. **RE data/schema prerequisites: COMPLETE and VALIDATED.** All RE reference/seed tables exist and pass 905 (REPO-CERT-007/010 FULL PASS): personas 41, persona_assignment_rules, main_cohorts 5, cohorts 2,952 (city_tier/GAP-002), subcohorts 41, states 36, meal_classes 131, weekly_class_plans 20,664, household_addon 7,992, nonveg_logic 36, class/addon dish options + regional_affinity (ICD-1), config tables; derived columns/genome/dish_tags trigger-proven; RLS enabled.
2. **Runtime code: ABSENT.** `supabase/functions/` is WP-8B scaffold only. Onboarding and the RE pipeline are unbuilt. Consent/auth (WP-8C) is built on branch `feat/wp-8c-auth-onboarding-consent` (commit `6906dd5`, REPO-CERT-011), not merged to main.
3. **DOC-P4-01 and DOC-P4-02: ABSENT** (grep-confirmed), though both are named as downstream dependents by DOC-P3-06 and DOC-P4-00 §8.
4. **Onboarding→first-plan boundary: UNSPECIFIED.** DOC-P3-06 §06.2/§14.1 present a `first_week_plan` in the onboarding response; DOC-P3-06 §12/§13, DOC-P3-03A §02, and DOC-P3-03 §14 place plan *generation* outside onboarding (LF-L01 nightly CRON; onboarding writes no plan tables). The mechanism/timing is stated by no frozen document.
5. **No Repository Bug or hard contradiction found.** Every disagreement is either an intentional documented deferral (ICD-1 R-05, S-15 R-06, AGR-P3-07-001 R-07, MVP audit limits R-11, DOC-P4-01 R-04) or a specification gap at the DOC-P4-02 layer. One minor naming observation (`re_sub_cohorts` in text vs `re_subcohorts` in schema) flagged for verification, non-blocking.

## Phase 3 boundary — recorded, not resolved

Per instruction, the onboarding-plan boundary conflict was **identified precisely** (Reconciliation Report Phase 3) and **not resolved** in the analysis. Resolution is a Founder-ratified architectural decision, carried as **AD-01** in the newly-authored DOC-P4-02.

## Decision — OPTION B

**Current documents are insufficient; DOC-P4-02 must be authored (and ratified) before onboarding is implemented.** Justification: the missing artifact is exactly the service/edge-function specification the architecture already designates (DOC-P4-00 §8; DOC-P3-06 downstream), and implementing onboarding now would require inventing the plan-timing boundary — forbidden. It is **not** Option A (would require invention) and **not** Option C (no frozen doc is internally contradictory in a way needing reopening; the tensions are reconcilable/deferred). Full evidence in the Reconciliation Report, Phase 5.

## Action taken this session

- Authored the **Reconciliation Report** (Phases 1–5) and **[DRAFT] DOC-P4-02** (surfacing AD-01 as an open, Founder-gated decision with three evidence-consistent options and a recommendation — not a unilateral resolution).
- Updated KNOWLEDGE.html (Session 22).
- All work on branch `feat/wp-8c-architectural-reconciliation`; **not pushed**; local commit only.

## STOP condition asserted

Onboarding implementation is **NOT** proceeding this session. Governance has not approved: DOC-P4-02 is DRAFT and AD-01 is unratified. Per the investigation's own terminal rule, work stops here pending Founder ratification of AD-01 (and, if Option 2 is chosen, until WP-8D exists).

## Critical Self-Review

- **Evidence-only, no invention:** confirmed — every finding cites a file+section; the undecidable boundary was surfaced, not fabricated.
- **Frozen artifacts untouched:** confirmed — zero SQL/schema/security change; no frozen document modified.
- **Recommendation singular and justified:** Option B, with evidence against A and C.
- **Honest limits:** validation "PASS" is per REPO-CERT-007/010 (not re-executed this session); `.docx` sources cited by filename only; WP-8C code assessed on its branch.

## Versioning & Placement

v1.0, docs/project-history/certificates/ per the Placement Rule; naming per WP-5AA. Attests the Reconciliation Report; records the authoring of DOC-P4-02 (DRAFT).

## Founder Countersignature

Founder acceptance of the reconciliation, the Option-B decision, and direction on AD-01: _______________________ Date: ___________
