# REPO-WP-04B_Seed_Loading_v1.1
 
**Repository Engineering Work Package #4B — Seed Loading (101 Statements 1–10 Only)**
**Project:** FooFoo (`apverse-labs/foofoo-v3`) · **Supabase:** `slsqtlygeekdppuyiiff`
**Placement:** `docs/project-history/REPO-WP-04B_Seed_Loading_v1_1.md`
**Date:** 2026-07-09 · **Status:** DESIGNED — awaiting Founder approval to execute
**Prerequisites:** WP-4A ✅ complete (independently re-confirmed this session — see Pre-Design Verification below)
**Supersedes:** WP-4B v1.0's Section 2/7 — removes intentional execution of statements already known to fail; adds fresh-session persistence verification after every insert
 
---
 
## Change Log — v1.0 → v1.1
 
Two Founder-directed changes, both adopted as substantive evidence-quality improvements, not style preferences:
 
1. **Removed intentional execution of the 4 `102` dependent statements.** v1.0 planned to run 3× `re_class_dish_options` and 1× `re_weekly_class_plans` knowing in advance they would fail on a `public.dishes` FK violation, framing this as an "expected failure" demonstration. This added no new evidence — the dependency was already confirmed by direct FK inspection. v1.1 replaces execution with a **read-only dependency verification** step: confirm live that these 4 statements are blocked *only* by missing `dishes` data (not by anything `re_meal_classes`-related), and defer them cleanly to WP-4C.
2. **Added fresh-session persistence verification.** v1.0's per-statement protocol checked row counts but didn't require a new session/transaction for that check — meaning a `SELECT` run inside the same transaction as the `INSERT` could show a row that was never actually durably committed. v1.1 requires every successful insert to be re-confirmed from a **fresh session**, closing that gap.
---
 
## Pre-Design Verification Summary (this session, independent)
 
| Check | Method | Result |
|---|---|---|
| Schema unchanged since WP-4A | Live query: `supabase_migrations.schema_migrations` | ✅ Still 26/26, identical |
| WP-4A fix genuinely on `main` | Fresh file read of `101_seed_reference_data_framework.sql` | ✅ All 9 `re_meal_classes` rows now `ARRAY[...]`; `'addon'` → `ARRAY['snack']` confirmed correct |
| No other statement in `101` accidentally touched | Full file diff against the WP-3D certificate's audit | ✅ Byte-identical elsewhere |
| Database still genuinely empty | Live row counts across 14 relevant tables | ✅ All 0 |
| The 5 previously-blocked statements correctly identified | Read `102` fresh, traced every FK to `re_meal_classes` by name | ✅ Confirmed: 1 in `101` (`re_meal_class_overlap_rules`), 4 in `102` (3× `re_class_dish_options`, 1× `re_weekly_class_plans`) |
 
No drift, no contradictions with the WP-3D Seed Readiness Certificate. Repository is ready for WP-4B exactly as scoped.
 
---
 
## 1. Objective
 
Load the 9 remaining, non-dependent statements in `101_seed_reference_data_framework.sql` — plus the now-fixed `re_meal_classes` statement itself — for real, with full statement-by-statement verification. Nothing from `102` is executed in this package.
 
## 2. Exact Statement Inventory — `101` Only
 
| # | Statement (table) | Expected rows | Notes |
|---|---|---|---|
| 1 | `re_engine.re_states` | 6 | |
| 2 | `re_engine.re_main_cohorts` | 5 | |
| 3 | `re_engine.re_routing_rules` | 8 | |
| 4 | `re_engine.re_personas` | 5 | |
| 5 | `re_engine.re_subcohorts` | 5 | |
| 6 | `re_engine.re_meal_classes` | 9 | The WP-4A-fixed statement — loaded for real this time, not rolled back |
| 7 | `re_engine.re_meal_class_overlap_rules` | 2 | Depends on #6 |
| 8 | `re_engine.re_addon_classes` | 3 | |
| 9 | `re_engine.re_nonveg_logic` | 3 | |
| 10 | `re_engine.re_city_migration_overlays` | 4 | |
 
**`102`'s 4 dependents are explicitly deferred to WP-4C** (3× `re_class_dish_options`, 1× `re_weekly_class_plans`) — verified, not executed, in this package (see Section 5).
 
## 3. Execution Order
 
`re_states` → `re_main_cohorts` → `re_routing_rules` → `re_personas` → `re_subcohorts` → `re_meal_classes` → `re_meal_class_overlap_rules` → `re_addon_classes` → `re_nonveg_logic` → `re_city_migration_overlays`
 
## 4. Per-Statement Protocol (mandatory, every single statement)
 
After each individual statement executes:
 
1. Confirm statement succeeded (no error)
2. Verify row count matches expected (same-session read)
3. Verify every FK referenced by this statement resolves (no orphaned reference)
4. Verify no other table changed row count unexpectedly (side-effect check against tables already loaded earlier in this same run)
5. **Open a fresh session/transaction** (not the one that executed the INSERT) and re-query the target table's row count from that fresh session. Report this fresh-session count explicitly, alongside the same-session count from step 2. The two numbers must match.
6. **STOP immediately, do not proceed to the next statement**, if any of the above fails — including if the fresh-session count differs from the same-session count, which would indicate a critical persistence failure (e.g., an unnoticed wrapping transaction silently rolling back the commit)
## 5. Dependency Verification for `102` (read-only — replaces execution)
 
After all 10 `101` statements are loaded and persistence-confirmed, perform a **read-only dependency check** on the 4 `102` statements without executing them:
 
- For each of the 3 `re_class_dish_options` statements and the 1 `re_weekly_class_plans` statement, confirm via `information_schema`/`pg_constraint` which tables their FK constraints reference.
- Confirm that every FK target **other than `public.dishes`** is now satisfiable — i.e., the `re_meal_classes` codes they reference (`BF_LIGHT_GRAIN`, `DIN_NON_VEG_MAIN`, `LUNCH_DAL_SABZI_ROTI`, `DIN_CURRY_ROTI`) now exist, confirmed by a live `SELECT` against `re_meal_classes` — not assumed from any prior report.
- Confirm that `public.dishes` is still empty (0 rows), which is the *only* remaining blocker.
- Record this as a plain finding: these 4 statements are ready to execute in WP-4C once `dishes` is loaded — verified, not executed.
## 6. Out of Scope
 
- `100_seed_config_tables.sql` — untouched
- Any `102` statement — including its execution, this session
- Any schema change
- Any full-volume data (illustrative-scale only, per IDR-001)
## 7. Founder Decisions Required
 
None anticipated. Same contingent rule as prior WP-3/4 packages: if any live finding suggests the *schema* itself is wrong (not a seed-file or sequencing issue), that inverts authority and is a Founder-level stop.
 
## 8. Risks
 
- A statement succeeding in its own session but never actually durably committing — mitigated by the fresh-session persistence check in Section 4, Step 5, which is structurally incapable of seeing an uncommitted write.
- `re_meal_class_overlap_rules` depending on `re_meal_classes` loading correctly first — mitigated by strict execution ordering (Section 3) and the FK-resolution check (Section 4, Step 3) before proceeding.
## 9. Stop Conditions
 
- Any row count mismatch, same-session or fresh-session, after any of the 10 statements
- Any FK violation on statements 1–10
- Any unexpected row-count change in a non-targeted table
- Fresh-session count differs from same-session count for any statement
- Any finding during the Section 5 dependency check suggesting the 4 `102` statements are blocked by something other than `public.dishes` (would be new information, not previously identified by the WP-3D certificate)
## 10. Acceptance Criteria
 
- All 10 `101` statements loaded with exact expected row counts, each confirmed via a fresh-session read
- Dependency verification for the 4 `102` statements completed and reported, with none of them executed
- `public.dishes` confirmed still at 0 rows (proving WP-4B didn't drift into WP-4C's territory)
## 11. Exit Criteria
 
All 10 statements loaded and fresh-session-verified; `102` dependency analysis complete; Execution Report produced; **STOP for Founder approval before WP-4C.**
 
## 12. Rollback Strategy
 
Each statement is a direct, permanent data load (unlike WP-4A's isolated test-and-rollback). If a stop condition triggers mid-sequence, the founder decides whether to `DELETE` the partially-loaded rows for the failing table (and any dependents already loaded on top of it) or leave them in place pending investigation — this is a Founder-level call, not automated within this package.
 
## 13. Critical Self-Review
 
- **Considered:** keeping v1.0's plan to execute the 4 `102` statements as a demonstration of "expected failure" — rejected on Founder review; running code you already know will fail produces no new evidence and blurs the WP-4B/WP-4C boundary. The dependency-verification approach in Section 5 gets the same assurance (these statements are blocked only by `dishes`) without executing anything premature.
- **Considered:** treating same-session row-count verification as sufficient, as in v1.0 — rejected; a same-session `SELECT` cannot distinguish a durable commit from an uncommitted write visible only within its own transaction. The fresh-session check in Section 4 closes this gap.
---
 
## Versioning & Placement
 
`REPO-WP-04B_Seed_Loading_v1_1.md` → `docs/project-history/`, committed before execution begins, per established WP-3/WP-4 pattern.
 
## Sign-off
 
Founder approval to execute WP-4B v1.1: _______________________ Date: ___________