# REPO-CERT-007 — WP-6E Data Gate Execution Certification v1.0

**Status:** ACTIVE — Data Gate Certificate (ICD-1 scope).
**Version:** v1.0
**Date:** 2026-07-14
**Placement:** docs/project-history/certificates/[ACTIVE]_REPO-CERT-007_WP-6E_Data_Gate_Execution_v1.0.md
**Dependencies:** SER-001 (migration 030); seeds 103-117; validation 900-905; WP-6RE-GEN.

---

## Certification

The FooFoo knowledge layer, built and seeded **entirely from repository artifacts**, is certified to **PASS the Data Gate at the Founder-approved ICD-1 scope (Option C)**. Executed on a **disposable local PostgreSQL 15.18** clean-room (Docker `postgres:15`), twice, on independent databases. **Production Supabase was never touched** (the configured MCP points at production and was deliberately not used, per WP-5F2 precedent).

## Basis (this session, directly executed)

- **Deterministic build:** migrations **001→030** apply cleanly (incl. SER-001 `city_tier`) → 62 base tables + partitions, on two fresh databases.
- **Deterministic seed:** config `100` + content `103–109` + RE `110–117` load cleanly (illustrative `101/102` intentionally excluded — superseded). Exact counts, identical across both databases: `re_cohorts 2,952 · re_weekly_class_plans 20,664 · re_household_addon_plans 7,992 · dishes 802 · dish_tags 10,456`.
- **Trigger derivation (no manual writes):** `fn_derive_dish_attributes` derived `diet_type/is_jain/allergen_flags` for all 802 dishes (spot-verified: Butter Chicken→non_veg/dairy-bit; Poha→vegan); `fn_update_dish_genome_vector` populated 802 genome vectors; `fn_assign_tag_vector_positions` assigned all 111 tag positions; `fn_propagate_ingredient_change` re-derivation verified live on real canonical data.
- **GAP-002 resolution (live proof):** `re_cohorts` distinct `(persona,state,diet_mode,city_tier)` = **2,952**; 0 rows without tier; `re_weekly_class_plans = re_cohorts × 7 = 20,664`.
- **Validation 900–905:** 905 fully PASS — all 12 fully-seeded Seed Gates exact, **9/9 FK anti-joins = 0 orphans**, GAP-002 uniqueness = 2,952, planning-role safety = **0 violations**. 900 Check 1 = 62 PASS; Check 4 = `false` PASS (migration 029 pf1 closed the GRANT gap).
- **Safety gates:** diet-violation gate = **0**; Jain precondition correct; anon blocked from writing `public.dishes`; `authenticated` cannot read `re_engine` — all PASS.
- **Deterministic rollback:** full teardown (seeds `117→100`, migrations `030→001`) returns to **0 base tables** (empty), after two evidence-based rollback-layer completions (below).
- **Repeatability:** second independent database produced **byte-identical row counts** → deterministic.

## Rollback-layer completions (evidence-based; not architecture/migration/forward-seed changes)

WP-6E teardown surfaced two genuine gaps, repaired with repository evidence:
1. **`100_seed_config_tables_rollback.sql`** (new) — seed 100 (config) had no paired rollback; its post-028 weight-ladder rows violated the pre-028 CHECK during migration-028 down. Now cleared first.
2. **`106_seed_dishes_rollback.sql`** — now clears `public.derivation_conflicts` before deleting dishes (that audit table FK-references `dishes(id)` without cascade).

## Scope & documented limits (honest, non-hidden)

- **ICD-1 scope (Option C, Founder-approved):** `re_class_dish_options` (S-08) seeded **165** and `re_addon_dish_options` (S-10) seeded **6** — only rows whose dish exists in the ICD-1 catalog; the remainder (**885** dish references) are in the Deferred Knowledge Register, not fabricated. Against the *original* full-catalog targets (1,050 / 142) these read "fail" in `900` Check 7; that reflects the pre-Option-C targets, and the Option-C-aware `905` validates them correctly.
- **S-15 `re_city_migration_overlays` — DEFERRED:** source `City_Migration_Overlay_v3` lacks `migration_duration_band` (NOT NULL, part of UNIQUE). One follow-up decision; not fabricated.
- **Validation-script staleness (WP-04DA cleanup, non-blocking):** `900` Check 5 expects 19 RLS tables but the correct count is **20** (migration 021 added `cuisines`); `901` Test 4 and the `904` smoke test are hardcoded to illustrative seed-102 rows (`Aloo Poha with Peanuts`, `MC3_NORTH_VEG`) absent from canonical data — the underlying mechanisms (propagate trigger, persona/plan path) were independently verified on real data.
- **Behavioral note:** `derivation_conflicts` accumulates ~3 rows/dish (2,406 total) during row-by-row `dish_ingredients` seeding — intermediate-derivation audit entries; final values are correct.
- **Privilege-fidelity caveat:** the Supabase-compatibility bootstrap (harness, not repo SQL) bounds absolute privilege fidelity; auth-fixture-dependent tests (902-4 live gate, 903 cross-user) self-skipped, as in the GREEN clean-room.

## Consequence

The **Data Gate is PASSED (ICD-1 baseline).** The repository can deterministically build, seed, derive, validate, and tear down a complete working knowledge database from zero, using only repository artifacts, reproducibly. The project **exits Knowledge Engineering** and is **READY for Backend Engineering (API/runtime)** on the ICD-1 baseline. Two tracked follow-ups (S-15 duration-band source/decision; validation-script cleanup per WP-04DA) remain non-blocking for backend work.

## Certified by

Release Engineering / Data Gate execution (WP-6E), 2026-07-14, on disposable PostgreSQL 15.18. Production untouched.

## Founder Countersignature

Founder acceptance of Data Gate (ICD-1) Certification: _______________________ Date: ___________
