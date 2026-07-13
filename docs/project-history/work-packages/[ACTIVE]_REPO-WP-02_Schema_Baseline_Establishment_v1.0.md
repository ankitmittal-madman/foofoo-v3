# REPO-WP-02_Schema_Baseline_Establishment_v1.0

**Repository Engineering Work Package #2 — Schema Baseline Establishment**
**Status:** EXECUTED — filed retroactively (see Execution Status Addendum at end)
**Date authored:** 2026-07-06 · **Executed:** 2026-07-06 (Claude Code, commits `4ed5e91`, `63c8ce2`)
**Placement:** `docs/project-history/` (alongside REPO-BOOT-01/02, continuing the repository-engineering lineage)
**Naming convention note:** This document begins the `REPO-WP-NN` series, superseding the `REPO-BOOT-` prefix for all future implementation work packages (`REPO-WP-03`, `REPO-WP-04`, …).

---

## 1. Objective

Translate the frozen `DOC-P3-04` schema (60 tables) into a live, verified baseline in the empty `foofoo-v3` Supabase database, then layer the 5 Founder-approved Architecture Freeze changes on top as new, additive migrations (021–025). Nothing else — no seed data, no backend, no frontend.

## 2. Context

Repository Bootstrap (WP-1) complete and merged. `foofoo-v3` Supabase project (`slsqtlygeekdppuyiiff`) confirmed empty (0 tables, both schemas). The 20 structural migration files exist in `database/migrations/` with clean `NNN_snake_case.sql` naming. One known documentation-vs-repo discrepancy signal existed at authoring time: `DOC-P3-05 Part A` Phase 16 states file `018` was "retired as an intentionally empty placeholder" (after `meal_classes` → file `003` and `derivation_conflicts` → file `010` reallocations, per AGR-002/003) — the actual repo file's disposition required discovery, not assumption.

## 3. Dependencies

- WP-1 (Repository Bootstrap) — COMPLETE, merged to main
- No dependency on seed data, backend, or frontend work — those belong to future Work Packages

## 4. Authority

Documentation > Repository > Database, per the project's standing hierarchy:
- `docs/architecture/DOC-P3-04_Data_Architecture_ERD_v1_3.md` — sole schema authority (frozen)
- `docs/governance/Phase3_5_Architecture_Freeze_v1_0.md` — sole authority for the 5 approved changes
- `docs/architecture/DOC-P3-05_Part_A_Readiness_Migration_Strategy_v1_2.md` — migration ordering, idempotency, rollback, and traceability rules

Claude Code implements what these specify; it does not redesign, improve, or infer beyond them. Where the repo's actual state contradicts the documents, Claude Code stops and reports rather than silently reconciling either direction.

## 5. Required Documents

| Document | Role in this WP |
|---|---|
| `DOC-P3-04_Data_Architecture_ERD_v1_3.md` | The 60-table schema to instantiate; verification target |
| `DOC-P3-05_Part_A_Readiness_Migration_Strategy_v1_2.md` | 15-group dependency ordering (Phase 5.1), rollback pairing rule (§5.3), AGR-002/003 file allocations (Phase 16) |
| `Phase3_5_Architecture_Freeze_v1_0.md` §3–5 | Source for migrations 021–025 (the 5 approved changes) |
| `docs/governance/batch-migration-pipeline/Batch3_Pipeline_Package_v1_0.md` | The exact `public.tags` naming/uniqueness conflict pair, required by the tag-vector change |
| All 20 files in `database/migrations/` | The frozen structural baseline to apply |

## 6. Required Discovery (before any execution)

1. Read all 20 migration files in full — not by filename alone.
2. Resolve the file-018 discrepancy: empty placeholder (per DOC-P3-05 Phase 16) or real content? Report before proceeding.
3. Confirm `meal_classes` and `derivation_conflicts` are actually allocated to files `003`/`010` per the AGR-002/003 corrections.
4. Independently determine correct file numbers/names for the 5 Freeze changes based on the established dependency-ordering principles — not pre-assigned.

## 7. Execution Strategy

**7.1 — Should 001–020 execute exactly as frozen?** Yes. `DOC-P3-05`'s own Quality Gate (Phase 6) and regression review (Phase 15) confirm zero architectural drift and 100% object allocation. Deviation on an empty database, with no counter-evidence, would be unauthorized scope creep.

**7.2 — 021–025 authored before or after verifying 001–020?** **After.** The 5 Freeze changes reference tables that must already exist in verified-correct shape (e.g., `component_type` is added to `dish_combo_items`, which must exist per spec first). Building 021–025 blind risks compounding an undetected baseline problem into the new migrations.

**7.3 — Validation cadence:** **After logical groups**, matching DOC-P3-05 Phase 5.1's own 15-step grouping (schema/extensions → reference tables → first/second-layer dependents → auth-dependent → profile-dependent → content → junctions → triggers → plan/interaction → config → operational/audit → partitioning → RLS → indexes). Per-file validation (20 checkpoints) is excessive for a pre-verified frozen plan; single end-validation makes late failures hard to trace to origin.

**7.4 — Rollback validation:** Every forward file has a paired rollback (§5.3). WP-2 proves the mechanism by rolling back the last file (020, lowest-risk to reverse) and reapplying it — not by rolling back the entire baseline.

**7.5 — Schema verification against DOC-P3-04:** Direct `information_schema` / `pg_catalog` comparison against the documented inventory: 60 tables, per-table columns, 51 FKs, 31 CHECKs, 9 UNIQUEs, 4 trigger functions, 37 indexes, 42 RLS statements. Exact match or precise discrepancy reported per category — never assumed.

**7.6 — Verifying the 5 Freeze changes post-application:** Each has a checkable signature:
- `public.cuisines` exists with FK shape; `cuisine_id` FK on `dishes` and `dish_combos`
- `calories`/`serving_size`/`food_dna_tier_1` columns on `dishes`; spice/sweetness/heaviness as tier-2 tag dimensions (seed-time rows, no DDL required)
- `tags` uniqueness conflict resolved; `vector_position` mechanism codified per the deterministic algorithm (tier ↑, category, value A–Z, 0–110)
- `re_engine.re_dish_regional_affinity` exists (dish_id FK, state_code FK, affinity_score numeric); `dish_tags.confidence` NOT reused
- `dish_combo_items.component_type` exists with 8-value CHECK; `role`'s original CHECK byte-identical; `re_meal_classes.slot` is `text[]` with 4-value CHECK (`breakfast`,`lunch`,`dinner`,`snack`)

**7.7 — CRITICAL addon-safety requirement:** Every row where `planning_role = 'ADDON_ONLY_NOT_PRIMARY'` must retain a correct, non-empty `slot` array through the conversion — never dropped, nulled, or special-cased. Verified by actual query with reported results, not assertion. (If the table is unseeded at execution time, behavioral proof — insert/reject test rows against the CHECK — substitutes for row-level verification.)

## 8. Acceptance Criteria

1. All 60 frozen tables live and verified matching `DOC-P3-04`
2. File-018 discrepancy resolved and reported
3. All 5 Freeze changes applied, verified, addon-safety confirmed
4. Rollback mechanism proven on at least one migration
5. Full Execution Report produced

## 9. Validation Strategy

Group-level structural checks (§7.3) + final full-schema diff against `DOC-P3-04` (§7.5) + the Freeze-change-specific checks (§7.6–7.7).

## 10. Rollback Strategy

Paired rollback files per `DOC-P3-05` §5.3; one live rollback proof-of-mechanism test on migration 020.

## 11. Deliverables

- Live, verified 60-table baseline in `foofoo-v3` Supabase
- Migrations 021–025 with paired rollbacks, committed
- WP-2 Execution Report

## 12. Exit Criteria

Acceptance criteria met, or explicitly reported as blocked with the specific unresolved item named. No seed data touched. Mission stops at the Execution Report.

## 13. Founder Decisions (only where genuinely required)

One pre-authorized decision point: if discovery finds file `018` contains real, non-empty logic contradicting `DOC-P3-05`'s "retired placeholder" statement, that conflict requires Founder input before Claude Code chooses which document to trust. All other steps are discovery-driven and self-resolving.

---

## Execution Status Addendum (filed retroactively)

**WP-2 was executed on 2026-07-06 by Claude Code before this document was committed to the repository** — the authoring session produced this Work Package's content and the execution prompt together, but the file itself was not committed before the prompt ran. Claude Code correctly flagged the missing document as "Step 0 (unplanned discovery)" in its Execution Report and proceeded on the prompt (which was derived from this document), with no STOP conditions firing. This file is now committed as the permanent record, with the following execution outcomes noted for traceability:

| WP Section | Outcome |
|---|---|
| §6 Discovery | PASS — file 018 confirmed empty placeholder; meal_classes in 003, derivation_conflicts in 010, matching DOC-P3-05 Phase 16 exactly. New finding: zero rollback files existed for 001–020 (specified in §5.3 but never delivered) |
| §7.1 Apply 001–020 | PASS — all 20 applied, all 15 group checkpoints passed, recorded in Supabase migration history |
| §7.5 Baseline verification | 60 tables exact; 50 FKs (doc's "51" off by one vs. both files and DB); 29 CHECKs (doc counting-method gap); 9 UNIQUEs exact on doc's basis; 4 trigger functions exact; 36+1 indexes explained (AGR-004 redundancy); 42 RLS statements exact. DOC-P3-04 §02's headline "38 public / 21 re_engine" prose confirmed internally inconsistent with its own §03 DDL (which the DB matches at 60) |
| §7.4 Rollback proof | PASS — `020_indexes_rollback.sql` authored (none pre-existed), executed (36→0 indexes), reapplied (0→36) |
| §7.6 Migrations 021–025 | All 5 authored with paired rollbacks and applied: `021_cuisines_reference`, `022_dish_display_attributes`, `023_tags_uniqueness_and_vector_positions` (B3-MI-003 conflict resolved via UNIQUE(dimension, tag_name); `fn_assign_tag_vector_positions()` codified as the seed-time mechanism), `024_re_dish_regional_affinity`, `025_combo_component_type_and_slot_array` (legacy `'addon'` maps to `ARRAY['snack']`) |
| §7.7 Addon-safety | Table unseeded (0 rows) at execution — behavioral proof substituted per this document's own §7.7 provision: ADDON row with `['snack']` inserted cleanly, compound `['lunch','dinner']` inserted cleanly, empty array rejected, legacy `'addon'` rejected, test rows removed |
| Commits | Migrations + rollbacks: `4ed5e91` · Knowledge book S2: `63c8ce2` |

**Follow-ups raised by execution (Founder decisions pending, tracked here):**
1. ~~Missing REPO-WP-02 document~~ — **resolved by this filing**
2. Rollback files for 001–019 still need authoring (only 020's exists) — candidate for REPO-WP-03 scope
3. Should `public.meal_classes` (the read-mirror) receive the same multi-slot conversion as `re_meal_classes`? — Founder decision required
4. `DOC-P3-04`'s headline counts (§02 schema split, "51 FK", "31 CHECK", "37 indexes") don't match its own DDL — a documentation correction pass is warranted (doc hygiene, non-blocking)

Founder sign-off: _______________________ Date: ___________
