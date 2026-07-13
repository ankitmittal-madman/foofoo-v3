# REPO-WP-04DA_Validation_Script_Corrections_v1.0

**Repository Engineering Work Package #4DA — Validation Script Corrections Only**
**Project:** FooFoo (`apverse-labs/foofoo-v3`) · **Supabase:** `slsqtlygeekdppuyiiff`
**Placement:** `docs/project-history/REPO-WP-04DA_Validation_Script_Corrections_v1_0.md`
**Date:** 2026-07-10 · **Status:** DESIGNED — awaiting Founder approval to execute
**Supersedes:** the "Part B" corrections section of the original `WP-4D v1.0` draft (split out into its own gated package per Founder governance request)
**Prerequisites:** WP-4A ✅, WP-4B ✅, WP-4C ✅, Migration 027 ✅, Migration 028 ✅ (all independently re-verified in prior sessions)

---

## Pre-Design Independent Re-Verification Summary

Every finding from the prior WP-4D design session was independently re-checked live, from scratch, before this package was designed — none were re-trusted from any earlier report, including this project's own.

| # | Finding | Fresh evidence this session | Verdict |
|---|---|---|---|
| 1 | `900` Check 3 function count | `pg_proc` re-queried live: 5 functions match `fn_%`. Cross-checked via a join to `pg_trigger.tgfoid`: exactly 4 are genuinely attached to a trigger; `fn_assign_tag_vector_positions` has `attached_trigger = NULL`. **Root cause refined:** the check counts by *name pattern*, not by *actual trigger attachment* — that is the real defect, not simply "a function was added." | Confirmed; the fix must query trigger-attachment directly, not just patch a number |
| 2 | `900` Check 3 trigger count | Fresh query joining `pg_trigger` → `pg_class` → `pg_namespace`: exactly 4 triggers in `public`, 5 unrelated platform triggers in `realtime`/`storage`. The unscoped query returns 9. | Confirmed; the fix is schema-scoping |
| 3 | `901` Test 1 diet_type | Read `fn_derive_dish_attributes`'s actual live source (not re-trusted from any report): branch order is `non_veg` → `egg` → `vegan` (all-vegan) → `veg` (fallback). Poha's 4 ingredients are all `is_vegan=true`, so `'vegan'` is the correct, already-proven value. | Confirmed |
| 4 | `901` Test 1 is_jain reasoning | **Refined, not just confirmed:** `DOC-P3-04` §03.6A documents that `is_jain` requires `diet_type='veg'` as an explicit precondition — this is intentional, documented design, not an oversight. Poha's `is_jain=false` is therefore true for **two independent reasons** (onion is jain-excluded, AND `diet_type='vegan'` not `'veg'`), but the test's current comment cites only the first. | The comment is incomplete, not just the expected value — both need correcting |
| 5 | `900` Check 5's RLS count | Live: 33 tables have RLS enabled; 24 distinct policies exist. The script still says "expect 19." This exact ambiguity was raised once before, during WP-3C, as an open Founder question — flagged then, never actually corrected. | New, additional correction — confirmed stale, previously deferred, not previously actioned |

**Also checked and found clean (no correction needed):** `902`'s referenced objects (`ADDON_INFANT` planning_role, `DIN_NON_VEG_MAIN`/Butter Chicken join) — both correct live; `903`'s referenced RLS policy names (`profiles_select_own`, `hm_all_own`, `dishes_public_read`) — all exist exactly as named; `904`'s persona lookup (`MC_NUCLEAR_FAMILY`/veg) — resolves correctly against live data.

## A Sixth Finding — Explicitly Out of Scope for This Package

This session also found that `public.dishes` columns `diet_type`/`is_jain`/`allergen_flags` currently show `authenticated` **and `anon`** holding direct `UPDATE`/`INSERT` privilege, via `information_schema.column_privileges` (independently cross-verified via `has_column_privilege()` and confirmed not a role-inheritance artifact via `pg_auth_members`). This directly contradicts the REVOKE statement in `008_content_core.sql` (AGR-001), which is confirmed present in that migration file and confirmed applied.

**This is a possible live security gap, not a validation-script staleness issue, and it is deliberately excluded from this package.** WP-4DA is scoped to validation-script text corrections only; fixing a privilege discrepancy requires a GRANT/REVOKE (a schema/privilege action), which is out of scope by this package's own definition. It is documented here for visibility and will need its own governance artifact (likely a new AGR) and Founder decision before any fix is designed, separately from WP-4DA/WP-4DB.

---

## 1. Objective

Correct the 4 confirmed stale validation-script expectations in `900_structural_validation.sql` and `901_behavioral_trigger_validation.sql`. Nothing else.

## 2. Scope

**In scope:** editing `900_structural_validation.sql` (Check 3, Check 5) and `901_behavioral_trigger_validation.sql` (Test 1) — text/query corrections only.

**Out of scope:**
- Running any of `900`–`904`
- Any schema or privilege change (including the Check 4 / REVOKE finding above)
- Any seed data
- Any auth or profiles fixture
- Any certification
- Any WP-5 work

## 3. The 4 Corrections

1. **Check 3, function count:** replace the name-pattern-only count with a query that joins `pg_proc` to `pg_trigger` (via `tgfoid`), reporting the true trigger-function count (4) plus an explicit, named callout of `fn_assign_tag_vector_positions` as a real, correct, non-trigger function (migration 023) — not hidden or miscounted.
2. **Check 3, trigger count:** scope the trigger query to `nspname IN ('public','re_engine')` via a join through `pg_class`/`pg_namespace`, so Supabase's platform triggers are correctly excluded.
3. **Check 5, RLS count:** replace "expect 19" with two separately-labeled live figures — RLS-enabled table count (33) and distinct policy count (24) — matching the labeling convention already adopted for this exact ambiguity during WP-3C.
4. **Test 1 (`901`):** correct expected `diet_type` to `'vegan'`; correct the `is_jain` explanation to cite both the onion jain-exclusion and the `diet_type='veg'` precondition failure.

## 4. Founder Approval Section — What Changes and Why

| File | Change | Why |
|---|---|---|
| `900_structural_validation.sql` | Check 3 rewritten to count by trigger attachment, not name pattern; scoped to `public`/`re_engine` | The old check would give a false "off by one" reading forever, for any future `fn_`-named helper function that isn't a trigger — this fixes the *method*, not just today's number |
| `900_structural_validation.sql` | Check 5's expected value corrected from a stale "19" to two accurate, live-derived figures | "19" was never re-verified after RLS/policy counts changed; reporting one honest number risked conflating two different things (tables-with-RLS vs. policies) — this was flagged once before and is now actually fixed |
| `901_behavioral_trigger_validation.sql` | Test 1's expected value and reasoning corrected | The trigger's real, already-proven-correct behavior (`'vegan'`) was being compared against a wrong expectation — this would have caused a false FAIL the first time `901` ever actually ran live |

**Separately flagged, NOT part of this approval, NOT part of WP-4DA:** the Check 4 privilege discrepancy (`authenticated`/`anon` currently hold `UPDATE` on `dishes.diet_type`/`is_jain`/`allergen_flags`, contradicting the documented REVOKE). This requires its own Founder decision and likely its own governance artifact (an AGR) before any fix is designed — it is a possible live security gap, not a script staleness issue, and touching it is explicitly outside a "validation scripts only" package.

## 5. Founder Decisions Required

1. **Approve the 4 corrections** listed in Section 3/4 above.
2. **Acknowledge the Check 4 finding** (Section "A Sixth Finding") as a separate, tracked item requiring its own future governance artifact — no action requested on it within this package.

## 6. Risks

Editing `900`/`901` without running them afterward means the corrections themselves go unverified by execution — mitigated by requiring the Claude Code prompt to re-read the edited files back and confirm the text matches intent, even though it must not execute them.

## 7. Stop Conditions

- Any of the 4 corrections, once drafted, would require touching anything other than these 2 files
- Any attempt (even accidental) to execute `900`–`904`
- Any temptation to also "fix" the Check 4 finding while in the file — explicitly forbidden, out of scope

## 8. Acceptance Criteria

- All 4 corrections applied exactly as specified
- Both files re-read post-edit to confirm the changes are textually correct
- Neither file executed
- Check 4 finding documented separately, not silently folded in or fixed

## 9. Exit Criteria

Both files corrected and committed; Execution Report produced; **STOP — awaiting Founder decision on the Check 4 finding, and awaiting approval to proceed to WP-4DB.**

## 10. Rollback Strategy

Both edits are git-tracked script changes — `git revert` if needed. No database schema, data, or privilege is modified by this package.

## 11. Validation Strategy

Post-edit re-read of both files (Section "Acceptance Criteria") is the only validation performed in this package — actual execution of the corrected checks is explicitly deferred to WP-4DB, per the governance split requested.

## 12. Critical Self-Review

- **Considered:** folding the Check 4 privilege finding into this package's correction list, since it was found during the same audit pass — rejected. It is a fundamentally different category of issue (a live privilege/security discrepancy, not a stale check expectation), and fixing it requires schema-level DDL, which this package's own scope explicitly excludes. Bundling it in would blur exactly the governance boundary this WDA/WDB split was requested to enforce.
- **Considered:** treating the RLS "expect 19" issue as already closed, since it was raised once before during WP-3C — rejected; raising a question is not the same as resolving it, and live re-verification this session confirmed the script text was never actually updated. Treating "previously discussed" as "previously fixed" would have been exactly the kind of unverified assumption this operating model exists to catch.
- **Considered:** only patching Check 3's specific numeric mismatch (5 vs. 4) rather than fixing the underlying counting method — rejected; the root cause is that the check counts by name pattern, not by trigger attachment. A future function sharing the `fn_` prefix would reproduce the same false mismatch. Fixing the method, not just today's number, closes the actual defect.

---

## Versioning & Placement

`REPO-WP-04DA_Validation_Script_Corrections_v1_0.md` → `docs/project-history/`, committed before execution begins, per established WP-3/WP-4 pattern.

## Sign-off

Founder approval to execute WP-4DA (Section 5, item 1): _______________________ Date: ___________
Acknowledgement of Check 4 finding as a separate tracked item (Section 5, item 2): _______________________
