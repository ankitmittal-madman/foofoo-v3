# DOC-P3-05 Part (b) — Core Schema and Reference Tables: Completion Summary
**Date:** June 2026
**Status:** Files `001`–`009` complete. **One Architecture Gap Report raised — see AGR-001 below.**
**Implements:** DOC-P3-04 v1.2, per the file allocation frozen in DOC-P3-05 Part (a) v1.1

---

## Files produced

| File | Tables created | Lines of DDL | Rollback file |
|---|---|---|---|
| `001_extensions_and_schema_setup.sql` | *(none — schema/extension/privilege setup only)* | 17 | ✅ paired |
| `002_reference_tier0.sql` | `ingredients`, `tags`, `re_states`, `re_main_cohorts` | 32 | ✅ paired |
| `003_reference_tier1.sql` | `re_personas`, `re_subcohorts`, `re_routing_rules`, `re_meal_classes` | 38 | ✅ paired |
| `004_reference_tier2.sql` | `re_meal_class_overlap_rules`, `re_class_dish_options`, `re_addon_classes`, `re_addon_dish_options`, `re_cohorts`, `re_weekly_class_plans`, `re_household_addon_plans`, `re_nonveg_logic`, `re_city_migration_overlays` | 64 | ✅ paired |
| `005_profiles.sql` | `profiles` | 23 | ✅ paired |
| `006_profile_dependent_public.sql` | `household_members`, `onboarding_sessions`, `consent_records` | 38 | ✅ paired |
| `007_re_identity_interaction_history.sql` | `user_re_state`, `user_taste_vectors`, `never_list`, `not_today_suppression`, `variety_window_state`, `re_dish_bandit_state` | 56 | ✅ paired |
| `008_content_core.sql` | `dishes`, `dish_combos` | 44 (incl. AGR-001 flag) | ✅ paired |
| `009_content_junctions.sql` | `dish_ingredients`, `dish_tags`, `dish_combo_items` | 27 | ✅ paired |

**Total: 32 tables created across files 002–009.** File `001` creates zero tables by design (schema/extension/privilege setup only).

---

## Architecture Gap Report — AGR-001

| Field | Detail |
|---|---|
| **Missing/inconsistent architectural element** | DOC-P3-04 v1.2 §03.6 contains the statement `REVOKE UPDATE (...) ON public.dishes FROM authenticated, anon, service_role_app_writer;`. The role `service_role_app_writer` is not defined, created, or referenced anywhere else in DOC-P3-04, nor is it listed among the three platform-provided roles (`anon`, `authenticated`, `service_role`) that DOC-P3-05 Part (a) Phase 13 (Environment Assumptions) names as the complete set this specification can rely on. |
| **Why implementation cannot proceed (as written)** | A `REVOKE ... FROM <role>` statement against a role that does not exist in the target Postgres instance will fail at apply time with a Postgres error (`role "service_role_app_writer" does not exist`). File `008_content_core.sql` therefore **cannot be executed against a live database as currently written** without this being resolved. |
| **Which document must be updated** | DOC-P3-04 (the approved architecture). This is not a Part (a) or Part (b) defect — both faithfully reproduce what P3-04 actually states. The correction belongs upstream. |
| **Recommended architectural resolution (offered, not decided here)** | One of three paths, for the founder/architect to choose: **(1)** Remove `service_role_app_writer` from the REVOKE list — `service_role` already bypasses RLS and column-level grants by Postgres/Supabase convention, so explicitly revoking from it is likely unnecessary regardless, and the intended protection is fully achieved by revoking from `authenticated, anon` alone. **(2)** If a distinct, lower-privileged "application writer" role was intended as a deliberate defense-in-depth layer beneath `service_role` (e.g., so even a compromised backend process couldn't write these columns without a separate elevated grant), that role needs to be formally defined in DOC-P3-04 §13 (Environment Assumptions) and a `CREATE ROLE` statement added to file `001`. **(3)** Confirm the role name was a documentation typo for `service_role` itself, in which case the statement becomes `REVOKE UPDATE (...) FROM authenticated, anon, service_role` (though this would still typically be a no-op against `service_role`, see point 1). |
| **Current state of file 008** | The REVOKE statement is reproduced **verbatim** from the approved P3-04 text, with a prominent inline comment marking it unsafe to execute until AGR-001 is resolved. Nothing was silently corrected. |
| **Blocking?** | **Localized only.** This does not block files `001`–`007` or `009`, none of which reference this role. It blocks the safe execution of `008_content_core.sql` specifically, and transitively blocks any environment-provisioning attempt that runs the full `001`–`009` sequence end-to-end until resolved. |

---

## One-to-one traceability confirmation

Every `CREATE TABLE` statement in files `002`–`009` carries a header comment block (per the convention frozen in Part (a) Phase 4) citing: the specific DOC-P3-04 section it implements, the DOC-P3-03 logical function(s) that justify it, the relevant DOC-P3-03A governance reference, and the CDM entity/invariant it relates to. No table was created without this citation present in its file.

## Mechanical implementation note (not a gap, disclosed for transparency)

File `001` includes one statement — `ALTER DEFAULT PRIVILEGES IN SCHEMA re_engine GRANT ALL ON TABLES TO service_role` — that does not appear as separate literal text in DOC-P3-04. This is necessary purely because DOC-P3-04 presented all `re_engine` DDL as one continuous block (§03.26's `GRANT ALL ON ALL TABLES IN SCHEMA re_engine TO service_role` only affects tables that already exist at the moment it runs), whereas Part (a)'s approved file-splitting strategy spreads `re_engine` table creation across files `002`, `003`, `004`, `007`, and later `013`/`014`/`016`. `ALTER DEFAULT PRIVILEGES` is the standard Postgres mechanism to make a single early grant apply automatically to tables created in later files, without restating the grant in every subsequent file. This implements the **same privilege intent** P3-04 already approved — service_role has full access to everything in `re_engine` — through the mechanism required by the multi-file structure Part (a) itself introduced. It is disclosed here rather than left unstated, but is not treated as an Architecture Gap, since no new privilege decision was made — only the *mechanical means* of applying an already-approved decision across split files.

---

## Completion checklist (per the founder's required closing confirmation)

| Requirement | Status |
|---|---|
| All objects allocated to files `002`–`009` per Part (a) Phase 8.1 were implemented | ✅ 32 of 32 tables, exact match |
| Nothing was omitted | ✅ Confirmed by direct count against Phase 8.1's per-file allocation (4+4+9+1+3+6+2+3 = 32) |
| Nothing new was introduced beyond approved architecture | ⚠️ **One disclosed mechanical exception** (the `ALTER DEFAULT PRIVILEGES` statement, explained above) — implements existing intent, introduces no new privilege decision |
| Implementation remains fully aligned with approved architecture | ⚠️ **One open inconsistency carried forward, not silently resolved** (AGR-001) — everything else fully aligned |
| Part (a) was treated as frozen and not reinterpreted | ✅ All file boundaries, naming, and allocations match Part (a) exactly; no file was renumbered or regrouped differently than specified |
| Ambiguity encountered was surfaced, not silently patched | ✅ AGR-001 raised formally rather than quietly fixed (and an earlier draft of file `008` that *had* silently dropped the unknown role was caught and reverted before delivery) |

**Verdict: Part (b) is complete with one outstanding, non-blocking-to-other-files Architecture Gap Report (AGR-001) requiring founder/architect resolution before `008_content_core.sql` is executed against any real database.** Recommend resolving AGR-001 before proceeding to Part (c), since Part (c)'s trigger-deployment file (`010`) attaches triggers to `dishes` and would compound the same ambiguity if the underlying privilege model is still unresolved at that point.

---

Founder decision on AGR-001 resolution path: ___________________________ Date: _______________
Confirmation to proceed to Part (c): ___________________________ Date: _______________
