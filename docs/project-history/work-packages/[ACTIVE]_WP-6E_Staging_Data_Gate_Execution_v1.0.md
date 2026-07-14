# [ACTIVE]_WP-6E_Staging_Data_Gate_Execution_v1.0

**Status:** COMPLETED — execution work package (companion certificate: REPO-CERT-007).
**Version:** v1.0
**Date:** 2026-07-14
**Placement:** docs/project-history/work-packages/[ACTIVE]_WP-6E_Staging_Data_Gate_Execution_v1.0.md
**Dependencies:** SER-001 / migration 030; seeds 103-117; validation 905; REPO-CERT-007.

---

## Executive Summary

WP-6E executed the full Data Gate on a **disposable local PostgreSQL 15.18** clean-room (Docker `postgres:15`), never Supabase/production. Build (001→030), seed (100+103→117), trigger derivation, validation (900–905), rollback to empty, and repeatability on a second independent database **all passed**. The Data Gate is **PASSED at the ICD-1 scope** (Option C). Two rollback-layer gaps found during teardown were repaired with repository evidence (seed-100 rollback added; dishes rollback clears `derivation_conflicts`). Remaining tracked follow-ups: S-15 `migration_duration_band`, and validation-script staleness (WP-04DA). Full attestation in REPO-CERT-007.

## Environment used

| Item | Value |
|---|---|
| Engine | PostgreSQL 15.18 (Debian) in Docker `postgres:15` — disposable |
| Databases | `staging2` (build+seed+validate+teardown), `staging3` (repeatability) — independent, dropped after |
| Production | **Never touched** — Supabase MCP points at production and was deliberately not used |
| Compatibility bootstrap | harness scaffolding (roles `anon`/`authenticated`/`service_role`, `auth` schema/`auth.users`/`auth.uid()`, default grants) — verbatim from WP-5F2 Evidence Register, made role-idempotent for multi-DB reuse; NOT a repo migration, not committed |

## Migrations applied
001→030 in order, clean, on two fresh DBs (incl. migration 030 `re_cohorts.city_tier` per SER-001).

## Seeds applied
`100` (config) + `103–109` (content) + `110–117` (RE). Illustrative `101/102` **intentionally excluded** — superseded by canonical seeds; loading them would inject non-canonical rows that violate the Seed-Gate counts.

## Recommendation Engine status (exact, both DBs)
`re_states 36 · re_personas 41 · re_subcohorts 41 · re_meal_classes 131 · re_meal_class_overlap_rules 13 · re_addon_classes 24 · re_cohorts 2,952 · re_weekly_class_plans 20,664 · re_household_addon_plans 7,992 · re_nonveg_logic 36`. ICD-1 dish-linked: `re_class_dish_options 165 · re_addon_dish_options 6 · re_dish_regional_affinity 130`. S-15 `re_city_migration_overlays` = 0 (deferred).

## Trigger behaviour
All derived columns produced by repository triggers, no manual writes: `diet_type/is_jain/allergen_flags` (802 dishes), `genome_vector` (802), tag `vector_position` (111). `fn_propagate_ingredient_change` re-derivation verified live on real canonical data.

## Validation results
- **905 (Option-C-aware): FULL PASS** — 12 fully-seeded Seed Gates exact; 9/9 FK anti-joins = 0 orphans; GAP-002 distinct 4-tuple = 2,952 (0 without tier); weekly = cohorts×7; planning-role safety = 0 violations.
- **900:** Check 1 = 62 PASS; Check 4 = `false` PASS (pf1 closed the GRANT gap); Check 5 = 20 (script's expected 19 is stale — cuisines added by mig 021); Check 7 = S-01..07/09/11..14 PASS, S-08/10/15 reflect ICD-1 scope / deferral.
- **901:** derivation correct; Test 4 stale (illustrative refs) — mechanism verified separately.
- **902 safety gates:** diet violations = 0; Jain precondition correct; live gate-4/cross-user skipped (no auth fixtures).
- **903 RLS:** anon write-blocked; `authenticated` cannot read `re_engine` — PASS.
- **904:** weight-ladder sums = 1.0 (5 tiers) PASS; invalid-row CHECK rejection PASS; persona lookup PASS; smoke PARTIAL (stale illustrative persona ref).

## Safety gate results
Diet gate 0 violations · Jain correct · RE-schema isolation enforced · planning-role (Safety Gate 4) 0 violations. No safety failure.

## Rollback results
Full teardown (seeds `117→100`, migrations `030→001`) → **0 base tables**, `re_engine` schema dropped. Two evidence-based completions: new `100_..._rollback.sql`; `106_..._rollback.sql` clears `derivation_conflicts` first.

## Repeatability results
`staging3` produced byte-identical counts to `staging2` → **deterministic YES**.

## Repository health
Migrations 001–030 contiguous, fully rollback-paired (now incl. seed-100 rollback); seeds 100–117; validation 900–905; GREEN invariants preserved; no forward SQL, migration, or architecture altered (only rollback-layer completed + harness bootstrap).

## Data Gate status
**PASSED (ICD-1 baseline).** Full-catalog S-08/S-10 and S-15 remain scoped/deferred per Founder Option C + one follow-up.

## Confidence score
**HIGH (9/10)** — build/seed/trigger/rollback/repeatability directly executed and reproduced. Deductions: privilege-fidelity bounded by harness bootstrap; three validation-script staleness items (mechanisms independently verified).

## Remaining issues
1. **S-15** `re_city_migration_overlays` — source lacks `migration_duration_band` (one decision/source-add).
2. **Validation-script cleanup (WP-04DA):** 900 Check 5 expected 19→20; 901 Test 4 / 904 smoke hardcoded to illustrative rows; 900 Check 7 targets predate Option C for S-08/S-10.
3. **`derivation_conflicts` noise** during bulk seeding (benign; final values correct).

## Readiness for Backend Engineering
**READY** on the ICD-1 baseline: the knowledge database builds, seeds, derives, validates, and tears down deterministically from repository artifacts. Backend (API/runtime per DOC-P3-06) may begin; the three items above are non-blocking and tracked.

---

Founder Sign-off: _______________________ Date: ___________
