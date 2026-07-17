# REPO-CERT-021 — WP-10 FD-12/FD-11/FD-13 Schema Evolution Batch Execution v1.0

**Status:** ACTIVE — Execution Certificate.
**Version:** v1.0
**Date:** 2026-07-17
**Placement:** docs/project-history/certificates/[ACTIVE]_REPO-CERT-021_WP-10_Schema_Evolution_Batch_v1.0.md
**Attests:** [ACTIVE]_WP-10_FD12_FD11_FD13_Schema_Evolution_Batch_v1.0.md
**Dependencies:** `[ACTIVE]_SER-002_dish_ingredients_main_ingredient_flag_v1.0.md`, `[ACTIVE]_SER-003_interaction_events_idempotency_key_v1.0.md`.

---

## Certification

Two Founder-approved Schema Evolution Requests (SER-002, SER-003) are certified **implemented and run live**, and the FD-12 combo-cuisine data fix is certified **applied**, all against the live Supabase database, with validation against the existing structural/behavioral suite plus targeted checks. **No code changes, no frozen-document changes, and no out-of-scope schema or data changes** (FD-07 seeding, FD-11 ingredient data, the 7 orphaned combos, and the Kerala Rice Meals mistagging all remain untouched, as scoped).

## Basis (directly executed this session, live Supabase)

- **Migration 031** (`mcp__supabase__apply_migration`, name `031_dish_ingredients_main_ingredient_flag`): `ALTER TABLE public.dish_ingredients ADD COLUMN is_main_ingredient boolean NOT NULL DEFAULT false;` — applied successfully. Paired rollback written.
- **Migration 032** (`mcp__supabase__apply_migration`, name `032_interaction_events_dedup_key`): `ALTER TABLE public.interaction_events ADD COLUMN dedup_key uuid;` + partitioned unique index `idx_ie_dedup_key (dedup_key, occurred_at) WHERE dedup_key IS NOT NULL` — applied successfully. Paired rollback written.
- **FD-12 data fix:** one row inserted into `public.cuisines` (`multi_regional`); `cuisine_id` updated on exactly 7 `dish_combos` rows (Kerala Rice Meals, Biryani Raita, Chole Bhature, Dosa Sambar, Masala Dosa Set, Poha Jalebi, Puri Aloo).

## Verification performed (live queries, this session)

| Check | Result |
|---|---|
| `dish_ingredients.is_main_ingredient` column shape | `boolean`, `NOT NULL`, `default false` — confirmed via `information_schema.columns` |
| Existing `dish_ingredients` rows unaffected | 7,108 total, 0 `true` / 7,108 `false` — no fabricated data |
| `interaction_events.dedup_key` column shape | `uuid`, nullable — confirmed via `information_schema.columns` |
| Partitioned unique index propagation | `idx_ie_dedup_key` present and `indisvalid=true` on the parent AND all 3 existing partitions (`_2026_07`, `_2026_08`, `_2026_09`) — confirmed via `pg_inherits`/`pg_index`, not assumed |
| `900` Check 1 — base-table count | 62/62, pass (unaffected — columns added, no tables added/dropped) |
| `900` Check 5 — RLS coverage | 0 of 33 public tables without RLS, pass |
| Seed gates S-06/S-11 (spot re-check) | `re_meal_classes`=131, `re_cohorts`=2,952, both pass, unaffected |
| `901` derived-column trigger checks (Bharli Vangi nut bit, Butter Chicken non-veg) | Both produced their documented expected result — `dish_ingredients` ALTER did not disturb `fn_derive_dish_attributes` |
| FD-12 combo/cuisine fix | Exactly 7 named combos now resolve to `cuisine_name='multi_regional'`; `dish_combos` total still 35 (7 with cuisine, 28 without — the 21 trivial + 7 orphaned, untouched); `cuisines` count 65→66 (exactly one new row) |

## Findings certified

- Both SERs implemented exactly as approved — no scope drift, no additional columns/constraints beyond what was specified.
- FD-12 fix touched exactly the 7 named combos and inserted exactly one new cuisine row; the 21 trivial-cuisine combos and 7 orphaned combos are verified unchanged.
- No regression in any existing structural, RLS, seed-gate, or trigger-behavior check.

## Scope & limits (what is NOT certified)

Does **not** certify: FD-07 seeding (deliberately not done — ratified as out of scope); FD-11's actual `is_main_ingredient=true` data (pending Founder deliverable); resolution of the 7 orphaned `dish_combos` (pending Founder deliverable); correction of the Kerala Rice Meals dish mistagging (pending human content review); any application code consuming either new column (`CandidateRepository.mainIngredientClass`, `POST /v1/events` dedup logic) — both remain unbuilt, per WP-8E/WP-10's own carried scope.

## Consequence

**WP-10 batch COMPLETE and validated against the live database.** The two schema changes and the one data fix are live; nothing else changed. Production runtime for the features these enable (main-ingredient-aware variety scoring, idempotent event ingestion, combo-level cuisine display) still depends on unbuilt application code, unchanged by this certificate.

## Critical Self-Review

- **Execution real?** Yes — both migrations applied live via `mcp__supabase__apply_migration`; the data fix applied live via `mcp__supabase__execute_sql`; every verification query in this certificate was run live this session, not assumed from the migration text.
- **Anything invented?** No — column shapes match their SERs exactly; the `multi_regional` cuisine row uses only fields the `cuisines` table requires, following the existing `street_food_generic` pan-Indian precedent for `state_origin`.
- **Frozen artifacts touched?** No — no existing migration, seed, or validation file was edited.
- **Honest limit:** the partitioned unique index guarantees dedup only within a partition; the full 24h cross-partition guarantee depends on an app-level check that doesn't exist yet (Epic 5, unbuilt) — disclosed in SER-003 and re-stated here, not glossed over.

## Versioning & Placement

v1.0, docs/project-history/certificates/ per the Placement Rule; naming per WP-5AA. Attests the WP-10 work package.

## Founder Countersignature

Founder acceptance of WP-10 schema evolution batch execution: _______________________ Date: ___________
