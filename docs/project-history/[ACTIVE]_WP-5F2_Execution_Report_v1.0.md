# WP-5F2 Clean-Room Execution Report v1.0

**Status:** ACTIVE — execution report (real execution against a disposable local database)
**Version:** v1.0
**Date:** 2026-07-13
**Placement:** docs/project-history/[ACTIVE]_WP-5F2_Execution_Report_v1.0.md
**Supersedes:** None
**Dependencies:** WP-5F Clean-Room Validation Report (simulation baseline); WP-5E Validation Remediation (SEED-01/VALIDATION-01 fixes under test); WP-5C Rollback Recovery; WP-04DA/WP-04DC (validation-script + RLS findings). Companions: WP-5F2 Work Package, Execution Certificate (REPO-CERT-003), Validation Report, Evidence Register, Decision Log.

---

## Executive Summary

WP-5F2 replaced WP-5F's paper simulation with **real execution**. Migrations 001–028, seeds 100–102, validation 900–904 and rollbacks 028→001 were run against a **disposable, empty, local PostgreSQL 15 container — never Supabase, never production.** Result: **the repository builds and tears down cleanly from scratch.** All 28 migrations apply in order (62 base tables + 6 partitions), all 3 seeds load (the WP-5E SEED-01 fix confirmed live), and all 28 rollbacks reverse to a fully empty database. The corrected validation Check 1 passes (62). Execution also **definitively resolved the long-open SEC-901T5 question** and surfaced three validation-script defects that only execution could reveal.

## 1. Environment (STEP 2)

| Item | Value |
|---|---|
| Engine | PostgreSQL 15.18 (Debian) in Docker (`postgres:15`) |
| Host | GitHub Codespace; container `foofoo_cleanroom` / `foofoo_teardown` DB |
| Production touched? | **No.** Supabase MCP (pinned to production `slsqtlygeekdppuyiiff`) was NOT used. Zero Supabase calls. |
| Start state | completely empty (0 base tables verified) |
| Timestamp | 2026-07-13 (container date confirmed) |
| Compatibility bootstrap | documented harness scaffolding reproducing Supabase platform prerequisites (roles `anon`/`authenticated`/`service_role`, `auth` schema, `auth.users`, `auth.uid()`, default public grants). NOT a repository migration; not committed to `database/`. Full text in the Evidence Register. |

## 2. Migration Execution (STEP 3) — 28/28 PASS

All 28 migrations applied sequentially with `ON_ERROR_STOP=1`, no error, no unexpected warning. Per-file time ~92–180 ms. End state: **62 base tables** (matches WP-5E-corrected Check 1) + **6 partition children** (migration 017: 3 months × interaction_events/suggestion_logs). No dependency issue, no ordering issue.

## 3. Seed Execution (STEP 4) — 100/101/102 PASS

| Seed | Result | Evidence |
|---|---|---|
| 100 config | PASS | weight-ladder, scoring, event weights, etc. loaded |
| 101 reference | **PASS** | **SEED-01 fix confirmed live:** all 9 `re_meal_classes.slot` loaded as `text[]` — `{snack}` (ADDON_INFANT, ADDON_DIABETIC), `{breakfast}`/`{lunch}`/`{dinner}` otherwise. Pre-WP-5E this statement would have failed. |
| 102 content | PASS | 3 dishes, 11 dish_ingredients |

**Trigger behaviour (derived, not seeded):** Poha→`diet_type=vegan, allergen=0`; Aloo Poha→`vegan, allergen=1` (nut bit); Butter Chicken→`non_veg, allergen=2`. Confirms `fn_derive_dish_attributes` fires on `dish_ingredients` insert. (`genome_vector` null — no `dish_tags` seeded, so `fn_update_dish_genome_vector` correctly did not fire.)

## 4. Validation Execution (STEP 5)

| Check | Result | Classification | Note |
|---|---|---|---|
| 900-1 table count | 62/62 | **PASS** | WP-5E VALIDATION-01 fix vindicated by execution |
| 900-2 safety-critical FKs | 0 rows returned | **DEFECT (VAL2-01)** | `conrelid::regclass::text` yields unqualified names in search_path; the `IN ('public.dish_ingredients',…)` filter matches nothing → check is vacuous, verifies nothing, and doesn't error |
| 900-3 fns/triggers | 5 fns / 4 triggers | **STALE (confirms WP-04DA #1)** | counts `fn_%` by name → includes non-trigger `fn_assign_tag_vector_positions`; 4 real triggers correct |
| 900-4 derived-col REVOKE | `should_be_false = TRUE` | **FINDING (confirms WP-04DA "Sixth")** | `authenticated` HOLDS column UPDATE — see §6 |
| 900-5 RLS-enabled count | 20 | **STALE (VAL2-02)** | script expects 19; actual 20 (19 from mig 019 + `cuisines` from 021) |
| 900-6 re_engine lockdown | false (correct) | **PASS** | `authenticated` has no `re_engine` USAGE |
| 900-7 seed gates | S-02,S-05 pass; 13 fail | **EXPECTED-FAIL** | illustrative seed volume per IDR-001 |
| 901-1 Poha diet_type | `vegan` | **CONFIRMS WP-04DA #3** | script comment says `veg`; trigger correctly derives `vegan` (all-vegan ingredients) |
| 901-2 allergen union | nut bit set | **PASS** | |
| 901-3 Butter Chicken | `non_veg` | **PASS** | |
| 901-4 propagate re-derive | allergen 1→33 | **PASS** | `fn_propagate_ingredient_change` works end-to-end (AGR-003) |
| 901-5 privilege enforcement | raised FAIL | **TEST-DESIGN DEFECT** | resolved by §6 diagnostic — data is safe |
| 902-1..3 gate preconditions | correct | **PASS** | data dependencies for Gates 1/3/4 sound |
| 902-4 live Gate 4 | skipped | **SKIP** | no auth.users profile fixture |
| 903 cross-user RLS | skipped | **SKIP** | needs ≥2 profile fixtures |
| 903 anon write block | blocked | **PASS** | anon cannot INSERT into dishes (RLS) |
| 903 re_engine invisibility | blocked | **PASS** | authenticated cannot read re_engine |
| 904-1 weight sums | all 1.00 | **PASS** | numeric type (mig 028/AGR-006) gives exact 1.00 for all 5 tiers |
| 904-2 invalid insert | rejected | **PASS** | CHECK constraint active |
| 904-3 event weights | correct | **PASS** | dish_not_today λ=0.35 distinct from 0.05 |
| 904 smoke test | persona+plan resolved | **PASS** | data model supports onboarding→persona→class-plan path |

## 5. Rollback Execution (STEP 6)

- **Loud-fail on seeded data (as designed):** rollback 028 → `ERROR: check constraint "re_weight_ladder_config_check" is violated by some row`; rollback 027 → `ERROR: column "show_question_key" contains null values`. Confirms the WP-5C Rollback Confidence Matrix MEDIUM/loud-fail classifications by execution.
- **Pristine teardown (fresh unseeded rebuild):** all 28 rollbacks 028→001 **PASS**. End state: **0 base tables, re_engine schema dropped, 0 `fn_` functions, 0 partition children** — fully empty. The repository's down-path is execution-proven.

## 6. SEC-901T5 — Definitive Resolution (STEP 7 highlight)

The WP-04DC diagnostic (never previously executed) was run directly:

- `has_column_privilege('authenticated','public.dishes','diet_type','UPDATE')` = **TRUE** → the GRANT-level gap is **real**: Supabase's default table-level `GRANT ALL` to `authenticated` survives migration 008's *column-level* `REVOKE UPDATE(diet_type,…)` (a column REVOKE cannot subtract from a table grant). This reproduces WP-04DA's live "Sixth Finding" in the clean room.
- Measured row count of the `authenticated` UPDATE inside a rolled-back transaction = **`UPDATE 0`** → **RLS default-deny held** (no UPDATE policy on `dishes` → 0 rows). Data was never at risk.

**Conclusion (WP-04DC decision tree, row-count = 0 branch):** 901 Test 5 is a **test-design defect** (it expected `insufficient_privilege`; the real protection is RLS returning 0 rows). The GRANT gap is a genuine **defense-in-depth** deficiency — the second lock is open, only the first (RLS) holds — and its fix is the applied-but-missing `pf1_security_hardening` migration (**PROD-PARITY / WP-5D**).

## 7. Deviations

- STEP 2 mandated a disposable DB and forbade production. The configured Supabase MCP points at **production**; a Supabase branch is production-derived and non-empty. A **local Docker Postgres** was therefore used — fully disposable, empty, and isolated from Supabase. This satisfies the brief's intent; it is documented, not a silent substitution.
- A Supabase-compatibility bootstrap was required because vanilla Postgres lacks `auth.users`, the platform roles, and `auth.uid()` that migrations 005/019 assume. It is harness scaffolding, clearly separated from repository SQL. Privilege/RLS test fidelity is bounded by this bootstrap (flagged in the Validation Report).

## 8. Confidence

**HIGH** for build/seed/teardown (directly executed, deterministic, reproducible). **HIGH** for the SEC-901T5 resolution (the row-count is a direct measurement and converges with WP-04DA's independent live finding). **MEDIUM** only on the absolute fidelity of privilege internals to production (bounded by the documented bootstrap) — but the convergence with the live WP-04DA observation makes the direction certain.

## 9. Repository state after execution

Repository files **unchanged** (WP-5F2 executes; it does not modify the repo). The disposable containers are removed after evidence capture. No Supabase/production object touched. Git HEAD unchanged by execution; only this WP-5F2 documentation set is added.

## Critical Self-Review

- **Considered** using a Supabase preview branch to maximise fidelity. **Rejected** — it is created from production, is not empty, and its creation is a billable/consequential action on the production project; the brief forbids touching production. A local disposable Postgres is the faithful, safe reading of "disposable database."
- **Considered** reporting 901 Test 5 as a plain FAIL. **Refined** — the direct row-count diagnostic shows data is safe (RLS held); the honest classification is "test-design defect + real defense-in-depth GRANT gap", not "security breach."
- **Limitation:** three validation tests self-skipped for lack of `auth.users` profile fixtures (902-4, 903 cross-user); their logic was inspected but not exercised end-to-end. Seeding auth fixtures is a reasonable future add, out of WP-5F2's execute-as-is scope.

## Founder Sign-off

Founder acceptance of the WP-5F2 Execution Report: _______________________ Date: ___________
