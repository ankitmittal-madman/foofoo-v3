# REPO-WP-04DB_Validation_Execution_Certification_v1.0
 
**Repository Engineering Work Package #4DB — Execute Validation Suite + First Behavioral Certification**
**Project:** FooFoo (`apverse-labs/foofoo-v3`) · **Supabase:** `slsqtlygeekdppuyiiff`
**Placement:** `docs/project-history/REPO-WP-04DB_Validation_Execution_Certification_v1_0.md`
**Date:** 2026-07-10 · **Status:** DESIGNED — awaiting Founder approval to execute
**Prerequisites:** WP-4A ✅, WP-4B ✅, WP-4C ✅, Migration 027 ✅, Migration 028 ✅, WP-4DA ✅ (all independently re-verified this session)
 
---
 
## 1. Executive Assessment
 
Every prerequisite was independently re-verified live, from scratch, before this package was designed — nothing was re-trusted from any earlier report.
 
| Item | Verification | Result |
|---|---|---|
| 28 migrations applied (through 028) | Live `supabase_migrations.schema_migrations` query | ✅ Confirmed |
| WP-4DA's 4 corrections actually on `main` | Full re-read of both corrected files, fresh from GitHub | ✅ All 4 present, textually exact — Check 3 counts by trigger-attachment, Check 5 reports both live figures, Test 1 expects `'vegan'` with complete reasoning |
| Check 4 (privilege finding) left untouched | Confirmed still reads `should_be_false` unmodified | ✅ Correctly undisturbed, as WP-4DA was scoped |
| Check 1's "62 tables" still accurate | Live recount | ✅ Still 62 |
| Database contents (143 rows, 27 tables) | Re-swept live | ✅ Unchanged since WP-4C |
 
**Repository is ready for its first live behavioral certification.** One test-robustness observation was found during this reconstruction and is noted below — it does not block execution.
 
### New Finding — Test Non-Determinism in `904`'s Smoke Test (not previously flagged)
 
Tracing `904`'s smoke test step-by-step rather than assuming it "will just work": its persona lookup uses `LIMIT 1` **with no `ORDER BY`**, on a query that currently matches **2 valid personas** (both `MC_NUCLEAR_FAMILY`/`veg`). Both personas have a cohort, but only **one** of the two cohorts has a Monday `weekly_class_plans` row loaded.
 
**Consequence:** depending on which of the two equally-valid personas Postgres returns first (unspecified without an `ORDER BY`), this step will report either `PASS` ("resolved a real weekly plan row") or `PARTIAL` ("cohort found but no Monday plan row exists yet"). **Both outcomes are already anticipated and gracefully handled by the script's own design** — neither reads as a failure. This is not a defect requiring a fix; it is a test-robustness observation the certificate should note explicitly, so a future re-run reporting the other outcome is not mistaken for a regression.
 
**Classification:** expected illustrative-scale test behavior (not a script issue, not a data issue, not a schema issue, not a genuine repository defect).
 
**No other stale assumptions found** after re-tracing `902`'s referenced objects, `903`'s policy names, and `904`'s full script text against live data, column-by-column.
 
---
 
## 2. Current Repository State
 
- 28 migrations applied (001–026, plus 027 and 028)
- 62 tables (`public` + `re_engine`, partitions excluded)
- 143 rows loaded across 27 tables (WP-4B + WP-4C combined)
- `public.profiles` = 0 rows (fixture-dependent tests will `SKIP` by design)
- Both corrected validation files (`900`, `901`) confirmed live and accurate on `main`
## 3. Dependency Graph
 
```
900 (structural)   — independent, run first, establishes baseline
901 (trigger)      — needs dishes/dish_ingredients (present) — run after 900
902 (safety gates) — needs dishes/re_class_dish_options (present); Test 4 needs profiles (absent)
903 (RLS)          — first 2 tests need profiles (absent); last 2 need nothing extra
904 (config/smoke) — needs re_weight_ladder_config, re_event_weights, personas/cohorts (all present)
```
 
## 4. Validation Execution Order
 
`900` → `901` → `902` → `903` → `904`, each run in full, no skipping.
 
## 5. Expected PASS
 
- `900`: Checks 1, 2, 3, 4, 6, 8, 9, 10, 11, 12
- `901`: all 5 tests
- `902`: Tests 1–3
- `903`: last 2 tests (anon write-block, schema invisibility)
- `904`: all 3 config tests; smoke test Step 1 and (one of two equally valid outcomes for) Step 2
## 6. Expected FAIL
 
`900` Check 7: all 15 seed gates — illustrative volume will not meet production targets. Report as **EXPECTED FAIL**, never plain FAIL.
 
## 7. Expected SKIP
 
`902` Test 4, `903`'s first two tests — no `profiles` fixture exists. Report as **EXPECTED SKIP**, never PASS.
 
## 8. Stop Conditions
 
- Any check/test expected to `PASS` instead genuinely `FAIL`s
- Any `SKIP` occurs for a reason other than fixture-absence
- Check 7 unexpectedly `PASS`es at illustrative volume (would mean stale targets, the opposite of expected)
- Check 4 (privilege finding) — if it re-confirms the discrepancy, report as a **new/confirmed repository finding**, do not investigate further, do not let it block the rest of the run
- Any result suggesting a genuine, previously-unknown security or correctness issue beyond what's already tracked
## 9. Acceptance Criteria
 
- All 5 files executed in full, live, for the first time
- Every result classified exactly as `PASS`/`EXPECTED FAIL`/`EXPECTED SKIP`/`FAIL` — no ambiguous or omitted results
- The Step-2 smoke-test non-determinism noted if it occurs, not treated as a surprise
## 10. Exit Criteria
 
Repository Validation Certificate produced with an explicit GO/NO-GO; **STOP — WP-4 fully closed pending Founder review.**
 
## 11. Founder Approval Requirements
 
- Approval to execute (read/write only insofar as `904` Test 2's rollback-tested bad-insert and Test 4's deliberate mutation-and-revert on `Peanuts` are concerned — no permanent data change)
- Acknowledgment that the Check 4 privilege finding remains a separately-tracked item, unaffected by this execution
## 12. Scope
 
**In scope:** executing `900`–`904` live, in order, producing a certification document with explicit PASS/EXPECTED FAIL/EXPECTED SKIP/FAIL classification for every result.
 
**Out of scope:**
- Modifying any validation script
- Modifying schema
- Creating auth fixtures
- Modifying data beyond what `904`'s own self-reverting tests perform
- Loading production dishes or `dishes.xlsx`
- Investigating the previously-observed privilege discrepancy (Check 4) — noted only, not acted on
- Designing WP-5
## 13. Risks
 
- Treating an `EXPECTED SKIP` or `EXPECTED FAIL` as equivalent to a plain `PASS`/`FAIL` in the final certificate — mitigated by requiring explicit, separate labeling for all four categories throughout
- Misreading the `904` Step 2 non-determinism as a defect on a future re-run — mitigated by documenting both valid outcomes in advance, in this package and in the certificate
## 14. Rollback Strategy
 
No permanent state change is expected from this package. `904`'s Test 2 (invalid insert) is rejected by the CHECK constraint and never persists; Test 4's ingredient mutation is explicitly reverted within the same script run. If any unexpected persistent change is found during Phase A/B, halt and report before proceeding.
 
## 15. Validation Strategy
 
The live execution of `900`–`904` **is** the validation for this package — there is no separate validation-of-validation step, consistent with prior WP-4 packages.
 
## 16. Critical Self-Review
 
- **Considered:** treating this package as a simple "run the scripts" exercise since the corrections were already applied in WP-4DA — rejected; re-tracing `904`'s actual join logic surfaced a genuine, previously-unflagged non-determinism that no prior session had caught, confirming that "corrected" and "fully audited" are not the same claim.
- **Considered:** silently picking one of the two valid `904` Step 2 outcomes as "the expected" one to simplify the certificate — rejected; both are legitimately possible under the script as written, and asserting only one as canonical would misrepresent what the test actually guarantees.
- **Considered:** including the Check 4 privilege finding as part of this package's stop conditions in a way that halts the entire run — rejected; per the Founder's explicit instruction, this finding must not influence execution. It is confirmed/reported factually within the certificate, without blocking the other four files' independent results.
---
 
## Versioning & Placement
 
`REPO-WP-04DB_Validation_Execution_Certification_v1_0.md` → `docs/project-history/`, committed before execution begins, per established WP-3/WP-4 pattern.
 
## Sign-off
 
Founder approval to execute WP-4DB: _______________________ Date: ___________