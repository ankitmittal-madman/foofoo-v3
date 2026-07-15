# REPO-CERT-013 — WP-8D Pre-Implementation Reconciliation & Decision v1.0

**Status:** ACTIVE — Investigation Certificate (read-only; no code, schema, DB, migration, seed, validation-SQL, or security change).
**Version:** v1.0
**Date:** 2026-07-15
**Placement:** docs/project-history/certificates/[ACTIVE]_REPO-CERT-013_WP-8D_Pre_Implementation_Reconciliation_v1.0.md
**Attests:** [ACTIVE]_WP-8D_Pre_Implementation_Architecture_Reconciliation_v1.0.md
**Dependencies:** DOC-P3-03 §02–16, DOC-P3-03A, DOC-P3-04, DOC-P3-06 v1.2, DOC-P4-00, DOC-P4-02 (DRAFT), REPO-CERT-007/010/011/012.

---

## Certification

A final pre-implementation architecture reconciliation of the FooFoo Recommendation Engine was
performed against live repository evidence (documents + database seed/validation layer + backend
code), **without relying on conversation context**. The investigation is certified **executed and
evidence-complete**, with a single governed decision: **STOP before WP-8D coding**, pending two
Founder/data decisions.

## What was verified (evidence)

- **RE algorithm completeness:** DOC-P3-03 §06–11 read from source — candidate generation + 6 hard
  constraints (§06), 5-signal FinalScore + weight-ladder interpolation + cosine ContentMatch +
  PersonalHistory (λ=0.05) + ContextFit + Thompson-sampling ExplorationBonus + Not-Today penalty
  (§07), MMR (λ=0.70) + 5 variety rules (§08), suppression (§09), 4 safety-gate SQL queries (§10),
  context assembly (§11), config (§16). **Fully specified inline; implementable without the binary
  RE-DOC .docx files and without invention.**
- **RE ownership:** single reusable engine, shared by `/v1/recommendations` (live) and
  `_cron/nightly-plan` (DOC-P4-00 §5/§14; DCR-P3-06-007, Resolved).
- **Onboarding→plan boundary (the specific question):** ACTIVE documents disagree — DOC-P3-06
  §06.2/§14.1 present a `first_week_plan` in the onboarding response, while DOC-P3-06 §12/§13,
  DOC-P3-03A §02, and DOC-P3-03 §14 place plan generation outside onboarding (LF-L01 nightly CRON).
  This is the open, unratified **AD-01** (REPO-CERT-012; DOC-P4-02 DRAFT).
- **Seed coverage:** `re_cohort_class_priors` (CohortPrior, w=0.55 cold start) and
  `re_segment_addon_rule` are **NOT seeded**; `re_context_multipliers` IS seeded (100).

## Findings

1. **WP-8D is spec-ready** (algorithm + ownership proven) — but **HELD**, not started.
2. **STOP condition met:** weekly-plan persistence ownership is unclear (AD-01) and ACTIVE documents
   contradict (§06.2 vs §12/§13). Per the WP-8D prompt's own rules and project governance, coding
   does not proceed.
3. **Option 2 (onboarding returns the plan) requires a Founder-authorized DCR against frozen
   DOC-P3-06 §12/§13.** Option 1 (defer plan to LF-L01/WP-8E; onboarding returns a `plan_pending`
   handle) is the only frozen-consistent option and is recommended.
4. **New data gap:** `re_cohort_class_priors` unseeded → cold-start CohortPrior collapses to the
   neutral 0.50 fallback; `re_segment_addon_rule` unseeded (addon-mechanism ambiguity vs seeded
   `re_household_addon_plans`).

## Decision — STOP (do not implement WP-8D this session)

Unblock requires: (1) Founder ratifies AD-01 (Option 1 recommended; Option 2 needs a DCR against
frozen DOC-P3-06 §12/§13); and (2) disposition the `re_cohort_class_priors` seed gap (seed it, or
Founder-accept the ICD-1 neutral-prior fallback with a documented limitation). After both, WP-8D
implements the **caller-agnostic RE core** (resolvers + ICD/eligibility/ranking + safety + DTOs +
services + unit/fake-integration tests + docs + certificate), with **no onboarding wiring**.

## Deliverables NOT produced (and why)

Per the STOP decision, the WP-8D implementation, tests, and execution certificate are **held**. This
is honest scope discipline, not omission — the prompt requires STOP when ACTIVE documents disagree.

## Action taken this session

- Authored the WP-8D Pre-Implementation Reconciliation Report (18-transition runtime map; specific-
  question answer; RE-ownership confirmation; algorithm-readiness; data-gap findings; decision).
- KNOWLEDGE.html updated (Session 23).
- Branch `feat/wp-8d-re-core-reconciliation`; **not pushed**; one local commit.

## Critical Self-Review

- **Evidence-only, no invention:** confirmed — RE algorithm cited to DOC-P3-03 §06–11; the
  undecidable boundary surfaced, not fabricated.
- **AD-01 not resolved unilaterally:** confirmed — recommendation given, ratification left to Founder.
- **Frozen artifacts untouched:** confirmed — zero SQL/schema/security change; no frozen doc modified.
- **Honest limits:** validation PASS per REPO-CERT-007/010 (not re-run); `.docx` RE-DOC cited via
  DOC-P3-03 formalization.

## Versioning & Placement

v1.0, docs/project-history/certificates/ per the Placement Rule; naming per WP-5AA. Attests the
WP-8D Pre-Implementation Reconciliation Report.

## Founder Countersignature

Founder direction on AD-01 and the `re_cohort_class_priors` disposition: _______________________ Date: ___________
