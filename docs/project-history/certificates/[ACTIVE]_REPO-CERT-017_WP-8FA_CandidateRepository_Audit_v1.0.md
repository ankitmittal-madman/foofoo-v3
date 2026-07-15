# REPO-CERT-017 — WP-8FA CandidateRepository Architecture Audit Certification v1.0

**Status:** ACTIVE — Audit Certificate (evidence reconciliation; read-only).
**Version:** v1.0
**Date:** 2026-07-15
**Placement:** docs/project-history/certificates/[ACTIVE]_REPO-CERT-017_WP-8FA_CandidateRepository_Audit_v1.0.md
**Attests:** [ACTIVE]_WP-8FA_CandidateRepository_Architecture_Audit_v1.0.md
**Supersedes analysis of:** WP-8F blocker report (REPO-CERT-016) — corrected where new evidence warranted.

---

## Certification

The CandidateRepository blocker set is **fully reconciled against repository evidence**. All 17
`DishCandidate` fields are traced source→implementation; each of the five blockers has exactly one
evidence-backed verdict. **No runtime code, schema, migration, seed, or database was changed.**

## Basis (read this session from source)

- `services/re/types.ts` (`DishCandidate`, 17 fields), `re/constraints.ts`, `re/variety.ts`,
  `re/scoring.ts`, `adapters/supabase-stores.ts`.
- **RE-DOC-02 §02 — the 20 genome dimensions — extracted from the `.docx` the WP-8F author could
  not read.** RE-DOC-03/04/05; DOC-P3-03 §06/§07/§08.
- Migrations 002/003/008/009/021/022/024; seeds 100/103/104; source `cuisines_v4.csv`,
  `ingredients_v5.csv`, `dishes.xlsx`.

## Findings certified

- **14 of 17 `DishCandidate` fields are fully proven** against the seeded schema.
- **8F-01 Cuisine Family → B (derivable):** RE-DOC-02 dim 2 "Regional origin" = `cuisines.cuisine_group`; `dishes.cuisine_id` join. No schema change.
- **8F-02 Main Ingredient Class → D (Founder SER/decision):** RE-DOC-02 dim 11 defined; `ingredients.category` exists in source but is not seeded and doesn't map 1:1; the "dominant ingredient" rule is unspecified. Only genuine blocker.
- **8F-03 Religious beef/pork → B (derivable):** canonical `beef`/`pork` ingredient rows exist and are seeded; `hasBeef`/`hasPork` = clean `dish_ingredients` membership join (corrects WP-8F "unprovable"). **halal → C** (certification unmodelled; documented MVP limitation + onboarding-UX safety note).
- **8F-04 Seasonal Affinity → C (intentional MVP deferral):** dish season unsourced (Batch6 "declared absent"); weather affinity (dim 15) drives ContextFit; seasonal boost/reactivation deferred.
- **8F-05 Cold-start Cohort Prior → C (intentional MVP deferral):** `re_cohort_class_priors` empty by design; LF-E02 neutral 0.50 fallback implemented in `scoring.ts`; populated post-launch (RE-DOC-04 / LF-J08).

## Consequence

The true blocker set collapses from "four unprovable + one" to **one Founder decision (8F-02) +
three documented MVP deferrals (halal, seasonal, cohort-priors) + one onboarding-UX safety note.**
CandidateRepository implementation for 8F-01 and beef/pork can proceed on approval; it must not
proceed for 8F-02 until the dominant-ingredient rule + realization are ruled.

## Scope & limits

Read-only evidence audit. Does not implement CandidateRepository, change schema, or write to any
database. `deno task verify` state unchanged (no code touched). Halal, seasonal, and cohort-prior
deferrals are engineering recommendations pending Founder acknowledgment.

## Certified by

CPTO-level architecture audit (WP-8FA), 2026-07-15. No production or schema touched.

## Founder Countersignature (decision required: 8F-02)

Founder acceptance + 8F-02 ruling: _______________________ Date: ___________
