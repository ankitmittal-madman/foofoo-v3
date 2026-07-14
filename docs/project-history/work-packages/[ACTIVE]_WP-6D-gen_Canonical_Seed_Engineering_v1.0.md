# [ACTIVE]_WP-6D-gen_Canonical_Seed_Engineering_v1.0

**Status:** ACTIVE — GENERATED (seed artifacts produced; not yet applied to any database).
**Version:** v1.0
**Date:** 2026-07-14
**Placement:** docs/project-history/work-packages/[ACTIVE]_WP-6D-gen_Canonical_Seed_Engineering_v1.0.md
**Supersedes:** None. Executes `[ACTIVE]_WP-6A-6D_Knowledge_Mapping_and_Seed_Pipeline_v1.0` under the Founder-approved **Option C / ICD-1** decision (2026-07-14).
**Provenance rule (standing):** every transformation is traceable to a source file, frozen doc section, or migration. Each generated migration (103+) carries a header naming source workbook/sheet + checksum, transformation version, generation timestamp, and business rules.

---

## Executive Summary

WP-6D-gen generated the **ICD-1 content-layer canonical seed** deterministically from the Founder-supplied source files, via a committed ETL generator (`database/etl/generate_icd1_seeds.py`). Seven paired seed/rollback migrations (103–109), a Deferred Knowledge Register, and the ETL itself are now in the repository. **Nothing was applied to any database** (that is WP-6E). **Nothing was fabricated.**

Per the Founder's Option C clarification, ICD-1 seeds only dishes present in the canonical master dataset (`dishes.xlsx` / `dishes_810`); recommendation references to dishes absent from that catalog are **deferred** (not invented) into the Deferred Knowledge Register — the official backlog for future knowledge expansion.

**Generated (content layer, `public` schema):** 191 ingredients, 111 tags (+ deterministic vector positions), 65 cuisines, **802 dishes** (8 combo rows correctly excluded to the combo tables), 7,108 dish→ingredient links, 10,456 dish→tag links, 35 combos. All idempotent, all with paired rollbacks.

**Deferred (with provenance):** the `re_engine` persona/cohort/plan/class layer is **not** generated. A distinct, evidence-based finding (separate from the dish-catalog decision): several NOT-NULL `re_engine` columns and key crosswalks have **no value in the master workbook** and cannot be produced without inventing business data. This is recorded as the RE-Reference-Normalization decision set (Section 6).

**Confidence: HIGH** for the content layer (deterministic, source-faithful, lint-clean). WP-6E (staging load + validation) can begin **for the content layer** on approval; the full Data Gate remains gated on the RE-Reference-Normalization decisions.

---

## 1. Engineering Artifacts Generated

| Artifact | Path | Purpose |
|---|---|---|
| ETL generator | `database/etl/generate_icd1_seeds.py` | Deterministic, re-runnable source→SQL generator (the canonical ETL) |
| Seed migrations 103–109 | `database/seeds/103..109_*.sql` | ICD-1 content-layer seeds |
| Paired rollbacks | `database/rollback/103..109_*_rollback.sql` | Reverse each seed band |
| Deferred Knowledge Register | `docs/project-history/work-packages/[ACTIVE]_WP-6_Deferred_Knowledge_Register_v1.0.csv` | 885 deferred dish references + future action |
| This document | (here) | WP-6D-gen execution record |

**Why an ETL generator, not hand-written SQL:** it guarantees the Founder's determinism/repeatability/no-fabrication requirements — the SQL is mechanically derived from checksummed sources, so re-running yields byte-identical output and every value is traceable. Source checksums are embedded in each migration header.

## 2. Seed Migrations Generated (rows prepared)

| Migration | Table | Rows prepared | Key transformations (provenance) |
|---|---|---|---|
| 103 | `public.ingredients` | 191 | is_veg from diet_type; is_jain_excluded = ¬is_jain_compatible (TR-007); allergen_flags bitmask (TR-008; DOC-P3-03 §07 L163) |
| 104 | `public.tags` | 111 | dimension=category, tier int (TR-009); `vector_position` via `fn_assign_tag_vector_positions()` (migration 023) |
| 105 | `public.cuisines` | 65 | direct map; `cuisine_group` denormalized text (Freeze Pack A) |
| 106 | `public.dishes` | **802** | difficulty easy/medium/hard→beginner/intermediate/advanced (TR-010); cuisine_id resolved; derived cols left to trigger (Invariant 6) |
| 107 | `public.dish_ingredients` | 7,108 links | tokens→`ingredients(name)`; 4 orphan tokens skipped, not invented |
| 108 | `public.dish_tags` | 10,456 links | attr value→`tags(dimension,tag_name)`; 3 texture orphans + spice/sweetness/heaviness (no tag vocab) skipped |
| 109 | `public.dish_combos` (+items) | 35 combos | combo_type/role/component_type CHECK-validated (migration 025); unresolved item dishes skipped |

**Total content rows prepared: ~18,668** (449 reference/content + 802 dishes + 17,564 junction links + 35 combos), all against the frozen GREEN schema.

## 3. Rows Deferred

**885 deferred dish references** (Deferred Knowledge Register), because they name dishes absent from the ICD-1 master catalog:
- `Class_Dish_Options_v3` → **760** distinct dishes deferred (of 916 referenced; 158 present were retained conceptually for future S-08 load).
- `Addon_Dish_Options` → **120** distinct dishes deferred.
- `region_food_affinity.csv` → **5** dishes deferred (incl. combos like *Chole Bhature*, and *dhuska*, *rugda*).

These are **not errors** — they are the future knowledge backlog. No missing dish, nutrition value, or recommendation row was fabricated.

## 4. Deferred Knowledge Register — summary

Format: `deferred_dish_name, source_file, reason, reference_count, recommended_future_action`. Each row's recommended action: introduce the dish via curated import / admin addition / future dataset / UGC, then load the deferred recommendation rows referencing it — **no schema redesign required** (the schema already supports these dishes; only the content is absent). This register becomes part of FooFoo's continuous knowledge-engineering process, exactly as the Founder directed.

## 5. Load Order, Idempotency, Rollback (WP-6E readiness)

**Load order (FK + trigger dependency):** 103 ingredients → 104 tags (+vector fn) → 105 cuisines → 106 dishes → 107 dish_ingredients (fires `fn_derive_dish_attributes`) → 108 dish_tags (fires `fn_update_dish_genome_vector`) → 109 combos.
**Idempotency:** every INSERT uses `ON CONFLICT DO NOTHING` on natural keys; junctions use `INSERT…SELECT` guarded joins → re-running converges to the same state. Each migration wrapped in `BEGIN/COMMIT` (transaction-atomic; a CHECK/FK failure aborts the band cleanly).
**Rollback:** each `1NN_*_rollback.sql` deletes exactly its band's rows in reverse FK order (dishes rollback cascades to junctions). Lint-clean: BEGIN/COMMIT balanced across all 14 files.
**Supersession:** 103–109 supersede the illustrative rows in 101/102 for the same tables (new files; 101/102 never edited in place — `DOC-P3-10 §23`).
**Error handling:** unresolved references (orphan ingredient tokens, absent combo-item dishes, deferred class/addon dishes) are silently skipped by guarded `SELECT` joins rather than failing the load or inserting placeholders.

## 6. What Remains Deferred — RE-Reference-Normalization (distinct from the dish-catalog decision)

The `re_engine` persona/cohort/plan/class tables are **not** generated. This is a **separate** blocker from Option C, discovered during generation and reported honestly:

| Table(s) | Missing input (not in master workbook) | Provenance |
|---|---|---|
| `re_meal_classes` (S-06) | `day_type` (weekday/weekend/any), `cuisine_family`, `variety_cooldown_days`, `max_per_week` — no source column | `Meal_Class_Master_v3` columns vs `migration 003` |
| `re_personas` (S-03) | `persona_code` (source uses P01…), `primary_diet` from `nonveg_mode` (`default` ambiguous) | `Persona_Master_v3`; GC-DOC persona naming |
| `re_states` (S-01) | `state_code` (2-letter) + `region` (5-value incl. NE/Himalayan classification) crosswalk | `State_Profile_v3` (S01/full-name/9 archetypes) vs `migration 002` |
| `re_cohorts` (S-11) | `diet_mode` vocabulary + city-tier-vs-diet_mode structure (2,952 = 41×36×2 tiers vs UNIQUE(persona,state,diet_mode)) | GAP-002; `Cohort_Matrix_v3` |
| `re_weekly_class_plans`/`re_household_addon_plans` (S-12/S-13) | depend on `re_cohorts` | transitive |
| `re_class_dish_options`/`re_addon_dish_options` (S-08/S-10) | depend on `re_meal_classes`; also ICD-1 dish filter | transitive + Option C |

**Resolution path (recommended):** extract the RE design docs (`RE-DOC-01..05`, currently `.docx`) to source the class-taxonomy business values, then a short RE-Reference-Normalization decision doc pins `diet_mode`, `primary_diet`, `state_code/region`, and confirms the cohort structure (GAP-002). Then a WP-6D-gen-2 pass generates 110+. **No fabrication until then.**

**Secondary (safety-scope) item:** 8 ingredients carry `fish`/`mustard` allergens with no bit in the frozen 7-bit model; loaded with `allergen_flags=0` for that dimension per the frozen model (recommend confirm; extending is a separate SER touching `ingredients`+`profiles`+onboarding).

## 7. Validation Readiness

- `900` Check 7 (Seed Gates) on the content layer: S-none directly (content tables aren't Seed-Gate-numbered), but dishes/ingredients/tags/cuisines will be populated at full ICD-1 scale.
- `902` safety gates: content is the input the derivation triggers + safety gates read; after WP-6E load, `fn_derive_dish_attributes` computes `diet_type`/`is_jain`/`allergen_flags`, and the diet/Jain/allergen gates can run.
- The 15 numbered Seed Gates (S-01…S-15) are `re_engine`-scoped and remain **RED** until the RE-Reference-Normalization layer is generated and loaded.

## 8. Rollback Readiness

Full: 7 paired rollbacks, reverse-FK order, lint-clean, transaction-wrapped. The content load is fully reversible on staging without touching schema.

## 9. Data-Gate Readiness

| Layer | Status |
|---|---|
| Content (ingredients/tags/cuisines/dishes/junctions/combos) | ✅ Generated, ready for WP-6E staging load |
| `re_engine` reference/persona/cohort/plan/class | ⛔ Deferred — RE-Reference-Normalization decisions required |
| Deferred dish backlog | ✅ Registered (885 rows) |
| Overall Data Gate | 🟡 Partial — content ready; RE layer blocked |

## 10. Critical Self-Review

- **Deterministic + evidenced.** The ETL is committed and re-runnable; every migration cites source + checksum + business rules. Counts reconcile exactly with prior independent analysis (802 dishes, 8 combos excluded by name-match, 4 orphan tokens, 885 deferred).
- **No fabrication.** 885 dish references deferred, not invented; orphan tokens/values skipped; `re_engine` gaps surfaced rather than filled.
- **Not applied.** Generation only; WP-6E (staging apply + 900-series validation) is the safety net and remains Founder-gated.
- **Limits.** dish_tags/dish_ingredients links depend on string matching against the source tokens/vocabulary; matches are exact (normalized), unmatched are skipped and logged — WP-6E validation on staging will confirm derivation-trigger behaviour and safety-gate results against real loaded data.
- **No certificate generated:** nothing was executed against a database, so no execution certificate is warranted yet (one is produced at WP-6F after real 900-series output).

## 11. Versioning & Placement

First issue (v1.0). GENERATED work package; becomes COMPLETED only with a WP-6F execution certificate carrying real 900-series output. Naming per WP-5AA standard. ETL under `database/etl/` (new sub-folder within the existing `database/` top-level — not a new top-level folder, so no RACR required).

---

Founder Sign-off: _______________________ Date: ___________
