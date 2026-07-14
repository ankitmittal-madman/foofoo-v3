# [ACTIVE]_WP-6_Canonical_Knowledge_Engineering_Plan_v1.0

**Status:** ACTIVE — DESIGNED (planning only; not executed). No SQL generated, no data loaded, no schema changed.
**Version:** v1.0
**Date:** 2026-07-14
**Placement:** docs/project-history/work-packages/[ACTIVE]_WP-6_Canonical_Knowledge_Engineering_Plan_v1.0.md
**Supersedes:** None (first Data-Gate work package).
**Dependencies (all read for this plan):**
- Governance: `DOC-P3-09_Knowledge_Integration_Governance_v1.3`, `DOC-P3-10_Seed_Data_Integration_Framework_v1.1`, `Phase3_5_Architecture_Freeze_v1.0`, `DOC-P3-05_Architecture_Gap_Register_v1.1`.
- Architecture: `DOC-P3-02_Conceptual_Domain_Model_v1.1` (CDM invariants 1–14), `DOC-P3-03_Business_Logic_Specification_v1.0`, `DOC-P3-04_Data_Architecture_ERD_v1.3` (via the frozen migrations that implement it), `DOC-P3-06/07/08`.
- Research: `Batch1–6` packages, `Phase3_5_Project_Integration_Review_v1.0` (PIR), `DOC-P3-11_Discovery_Execution_Register_v1.20`, `Phase3_5_Phase2_Knowledge_Acquisition_v1.2`.
- Live repository: migrations `001–029`, seeds `100–102`, validation `900–904`; source files in `data/source/`.
- Baseline: repository is GREEN-certified at commit `a89eab5` (`REPO-CERT-006`). Repository Gate PASSED; next gate is the **Data Gate**.

---

## Executive Summary

WP-6 is the **Data Gate**: turn the 11 Founder-supplied source files in `data/source/` into a fully governed, provenance-tagged, validated knowledge layer that meets every Seed Gate row-count target (S-01 … S-15) and passes the 900-series validation with the four safety gates returning zero rows. It replaces the current *illustrative* seeds (`100–102`) with the full-volume canonical seed set.

This is **not** "load the spreadsheets." It is the execution of Phase 3.5 Phases 9–11 (Seed Generation → Validation → Closure), which every one of the six frozen research batches explicitly deferred. The discovery, canonicalization, mapping, and gap analysis are already done and frozen; WP-6 is the first phase where seed SQL actually exists, and therefore the first phase where Category C2 (implementation-vs-design) conflicts can be detected at all.

**Central finding (verified against live repository, not inherited from summaries):** the blocker that stalled seeding for months — IDR-001, "the master workbook is missing" — is **resolved**: `Indian_Meal_Cohort_Persona_DB_v3.xlsx` and all content files are physically present in `data/source/`. Furthermore, the four architecture decisions the PIR named as gating Phase 9 (cuisine destination, tag vector-position algorithm, combo role model, and the `snack`/compound-slot problem) were **approved in the Architecture Freeze and are already implemented in migrations 021–028**. The schema is genuinely ready.

**What genuinely remains before a full load** is small and specific (Section 7): one permanent encoding to confirm (allergen bitmask), a handful of genuinely-unsourced datasets to formally defer with documented RE fallbacks, and a set of deterministic value-normalization rules to ratify. None require schema change; all are decision-bound, not research-bound.

**Confidence: HIGH** that the knowledge layer can be fully seeded and pass the Data Gate, conditional on the four Founder decisions in Section 7. Recommended first execution package after approval: **WP-6A (Knowledge Blueprint & Source-to-Target Contract).**

---

## 1. What FooFoo Knows, and What the Knowledge Layer Must Contain

FooFoo is a **class-first** recommendation engine: it never picks a dish directly. It resolves household → persona → cohort → a per-slot **meal class**, then draws dishes only from that class's pool, filters by hard constraints, scores, diversifies, and safety-gates. (`DOC-P3-03` §02–10.) The knowledge layer therefore splits cleanly into two halves with different exposure and different sources:

**A. Content knowledge (`public` schema — public-read, RLS-enabled):**
| Table | What it holds | Primary source |
|---|---|---|
| `ingredients` | 191 ingredients: `allergen_flags`, `is_veg/is_vegan/is_jain_excluded`, substitute, seasonal peak | `ingredients_v5.csv` |
| `tags` | 111 genome/controlled-vocab tags: `dimension`, `tier`, `vector_position` | `tags_v4.csv` |
| `cuisines` | 65 cuisines (+22 groups as denormalized `cuisine_group` text) | `cuisines_v4.csv`, `cuisine_groups_v4 2.csv` |
| `dishes` | 802 canonical dishes (of 810; 8 are combos) + attributes | `dishes.xlsx` sheet `dishes_810` |
| `dish_ingredients` | dish→ingredient junction (**safety-critical**, allergen source of truth) | `dishes.xlsx` `Ingredients` column |
| `dish_tags` | dish→tag junction with confidence (feeds `genome_vector`) | `dishes.xlsx` tag columns |
| `dish_combos` / `dish_combo_items` | 35 combos, 74 items with `role` + `component_type` | `dish_combos_v2`, `dish_combo_items_v2` |

**B. Recommendation-engine reference & plan data (`re_engine` schema — service-role only):** the 15 Seed-Gate tables plus config. Sourced almost entirely from the 22 sheets of `Indian_Meal_Cohort_Persona_DB_v3.xlsx`, whose canonical row counts match the Seed Gate targets **exactly** (Batch 1 Mapping §0): `re_states` (36), `re_main_cohorts` (5), `re_personas` (41), `re_subcohorts` (41), `re_routing_rules` (8), `re_meal_classes` (131), `re_meal_class_overlap_rules` (13), `re_class_dish_options` (1,050), `re_addon_classes` (24), `re_addon_dish_options` (142–143), `re_cohorts` (2,952–2,953), `re_weekly_class_plans` (20,664), `re_household_addon_plans` (7,992), `re_nonveg_logic` (36), `re_city_migration_overlays` (324). Plus `re_dish_regional_affinity` from `region_food_affinity.csv` (136 rows).

**Derived, never seeded (CDM Invariant 6):** `dishes.diet_type`, `dishes.is_jain`, `dishes.allergen_flags`, `dishes.genome_vector`, `popularity_score`, `acceptance_rate_*`. These are written only by trigger `fn_derive_dish_attributes` / `fn_update_dish_genome_vector` (migration 010) and CRON — WP-6 must load the *inputs* (ingredients, `dish_ingredients`, `dish_tags`, tag `vector_position`) and let the pipeline compute the rest. `tags.vector_position` is assigned deterministically by `fn_assign_tag_vector_positions()` (migration 023) at seed time.

---

## 2. Current State of the Knowledge Layer (evidence)

- Seeds `100–102` are **illustrative only**. File 101's own header states IDR-001 applies and it "does NOT fabricate the missing ~30,000 rows … leaves every full-volume table explicitly short of its Seed Gate target." Validation Check 7 is therefore expected to FAIL today by design.
- Config table values (seed `100`) are largely `[CONFIRMED]` from `DOC-P3-03` §16 and are **complete**, except two tables explicitly awaiting source data: `re_context_multipliers` (4 illustrative rows) and `re_festival_calendar` (2 illustrative rows).
- Schema is frozen and GREEN-certified; all target tables for the knowledge layer exist (verified by direct read of migrations 002–029).

---

## 3. Source Assessment (11 assets, authority classified)

All are Founder-supplied and SHA-256 checksummed at Phase 2 intake. Classification per `Phase3_5_Phase2_Knowledge_Acquisition_v1.2`:

| Src | File | Scale | Authority | Target |
|---|---|---|---|---|
| SRC-002 | `cuisines_v4.csv` | 65×12 | Master | `public.cuisines` |
| SRC-001 | `cuisine_groups_v4 2.csv` | 22×8 | Reference | `cuisines.cuisine_group` (denormalized text) |
| SRC-006 | `ingredients_v5.csv` | 191×15 | Master | `public.ingredients` |
| SRC-005 | `ingredient_aliases_v2.csv` | 167×7 | Reference | **No MVP destination — deferred (Sec 7.4)** |
| SRC-009 | `term_synonyms_v2.csv` | 121×8 | Reference | **No MVP destination — deferred (Sec 7.4)** |
| SRC-008 | `tags_v4.csv` | 111×9 | Reference (vocab) | `public.tags` |
| SRC-010 | `dishes.xlsx` `dishes_810` | 810×35 | Master | `public.dishes` (+ junctions). `Sheet1` = Founder-directed ignore |
| SRC-004 | `dish_combos_v2` | 35×9 | Master | `public.dish_combos` |
| SRC-003 | `dish_combo_items_v2` | 74×10 | Master | `public.dish_combo_items` |
| SRC-007 | `region_food_affinity.csv` | 136×8 | Reference (affinity, not availability) | `re_engine.re_dish_regional_affinity` |
| SRC-011 | `Indian_Meal_Cohort_Persona_DB_v3.xlsx` | 22 sheets | Mixed | 15 `re_engine` Seed-Gate tables |

**Within SRC-011:** Master/Reference/Planning sheets become seed data; the README, Data_Dictionary, Weekly_Plan notes, DB_Implementation, `Sources_v3`, and `QA_Checks_v3` sheets are **documentation/provenance/QA and never become seed data** (permanent Founder rule).

**Genuinely-unsourced data (present in no file — cannot be fabricated):** the full `re_context_multipliers` matrix, the full `re_festival_calendar`, `re_cohort_class_priors`, and a numeric source for `re_cohorts.prior_weight`. Also confirmed *declared absent* (not assumed missing): seasonality, festival influence, language variants, diet-adaptation in the affinity data.

---

## 4. Complete Understanding — Dependency Map

- **RE → content (read-only):** `/v1/recommendations` reads `re_class_dish_options`, `re_cohorts`, `re_weekly_class_plans`, `dishes`, `dish_ingredients`; every recommendable dish must resolve to a stable UUID and a `class_code`. (`DOC-P3-06` §13.)
- **Genome / Food DNA:** `dish_tags` (tiered, confidence-scored) compile into `dishes.genome_vector`, ordered by the `tags` master `tag_id`/`vector_position` sequence. Reordering the tag master silently corrupts every stored vector — so tag load + `vector_position` assignment is load-bearing and must happen before any dish vector is computed. Tier-1 completeness (7 mandatory tags at confidence ≥ 0.85) is required before a dish may enter `re_class_dish_options` (`LF-K04`).
- **Allergen safety is ingredient-level, not dish-level:** the 6 hard constraints and 4 safety gates read through `dish_ingredients → ingredients.allergen_flags`. Dish-level flags are a derived summary only. This is why `dish_ingredients` completeness is launch-blocking, not cosmetic.
- **Ingestion path (infrastructure):** manual content-ops + DB triggers + **numbered migrations with paired rollbacks**, loaded on `foofoo-staging` first, promoted to `foofoo-mvp` only under explicit Founder approval. The 3 safety-gate SQL queries (diet/allergen/Jain = 0 rows) are a **P0 CI release blocker** (`DOC-P3-08` §16). No vector/embedding infrastructure exists or is in scope.

---

## 5. The Knowledge Pipeline (design, not implementation)

```
SOURCE (11 files, checksummed)
   │  read displayed values only; never Excel formulas (Founder Rule 2)
   ▼
NORMALIZATION  — TR-001..006 (+ new TR-NNN as needed): whitespace/case, Hindi↔English,
   │             regional naming, plural/singular, known-synonym merge, polarity inversion
   ▼             (is_jain_compatible→is_jain_excluded), allergen_type→bitmask
CANONICAL MAPPING — each value → frozen schema column, citing its MAP-* lineage ID
   │               (OBS→CAN→MAP→GAP→RES→SEED chain preserved; every seed row cites a MAP-*)
   ▼
VALIDATION (pre-load) — FK resolvability, enum/CHECK conformance, uniqueness, count vs Seed Gate
   ▼
CONFLICT RESOLUTION — A auto-load; B/C→Founder (never auto-resolve C; never fabricate a fact)
   ▼
TRANSFORMATION → deterministic seed SQL (numbered 103+; paired _rollback.sql)
   ▼
DATABASE LOAD (foofoo-staging) — strict order: reference/vocab → content → junctions
   │   (triggers derive diet_type/is_jain/allergen_flags/genome_vector) → tag vector_position
   │   → re_engine reference → generated cohorts/plans → affinity
   ▼
VERIFICATION — 900 structural (Check 7 = 15 Seed Gates), 901–904 behavioural, 4 safety gates = 0
   ▼
CERTIFICATION — Data Gate certificate (REPO-CERT-00N) + Phase 3.5 Closure Report; then, and only
                 then, Founder-approved promotion to foofoo-mvp
```

**Load order is dictated by FK + trigger dependency**, not file convenience: ingredients & tags first → assign `vector_position` → dishes → `dish_ingredients` + `dish_tags` (this fires derivation) → cuisines/combos → `re_engine` reference tiers (states→cohorts→personas→classes) → class-dish options → generated cohort/weekly/addon plans → regional affinity.

---

## 6. Proposed WP-6 Execution Roadmap (sub-packages)

Each sub-package ends at a Founder-review gate per `DOC-P3-10` §26–28. Names refined from the Founder's suggested A–F.

| WP | Name | Purpose | Exit criterion |
|---|---|---|---|
| **WP-6A** | Knowledge Blueprint & Source-to-Target Contract | Freeze the authoritative source→column map for all ~30k rows, the MAP-* lineage index, and the load-order DAG. No SQL. | Founder-approved mapping contract; every target column has a named source or a documented "derived"/"deferred"/"unsourced" status. |
| **WP-6B** | Source Assessment & Pre-Seed Decisions | Resolve the four open decisions in Section 7 (allergen bitmask; unsourced-data deferrals; diet/value normalization; alias/synonym deferral). | All four decisions recorded with Decision Authority = Founder. |
| **WP-6C** | Canonical Mapping & Transformation Rules | Per-domain mapping report; ratify the TR-NNN library additions; classify every field A/B/C1/C2/C3. | Zero unclassified fields; zero un-provenanced planned seed rows. |
| **WP-6D** | ETL & Seed-Generation Framework | Author numbered seed migrations (103+) and paired rollbacks from the approved mapping only; deterministic, re-runnable. | Seed SQL generated; supersedes 101/102 illustrative rows; not yet applied to any shared DB. |
| **WP-6E** | Master Data Load (staging) | Apply on `foofoo-staging` in dependency order; let triggers derive; assign tag vectors. | All 15 Seed Gates meet target counts on staging. |
| **WP-6F** | Knowledge Validation & Data-Gate Certification | Run 900–904 + 4 safety gates; provenance-completeness audit; produce Data-Gate certificate + Phase 3.5 Closure Report. | 900 Check 7 all-pass; safety gates 0 rows; certificate written. Production promotion is a separate Founder-approved step. |

**Dependency:** 6A → 6B (decisions) → 6C → 6D → 6E → 6F. 6B is the true critical path; 6E/6F cannot certify until 6B's allergen-bitmask decision is made (it is a permanent, safety-relevant encoding).

---

## 7. What Genuinely Remains Before a Full Load (the only real gate)

Verified against live schema — the historical "four blockers" are **closed** (cuisine FK 021, tag vector algorithm 023, combo `component_type` 025, `snack`/compound slot as `text[]` 025, regional-affinity table 024; all per Architecture Freeze Packs A/B/C, Founder-signed 3-Jul-26). The remaining decision-bound items:

1. **Allergen bitmask encoding (Category B — permanent, safety-relevant).** `ingredients.allergen_flags` and `profiles.allergen_flags` are integer bitmasks; the source supplies 10 allergen *type names* but no bit positions. A frequency-ordered scheme is drafted (`dairy=0 … egg=9`) but **unconfirmed**. Must be Founder-ratified before load, because it is permanent and the safety gates depend on it. **No fabrication permitted.**
2. **Genuinely-unsourced datasets (Category B/C2 — recommend documented deferral).** `re_context_multipliers` (full matrix), `re_festival_calendar` (multi-year regional), `re_cohort_class_priors`, and `re_cohorts.prior_weight` numeric source do not exist in any file. The RE has documented fallbacks (cohort prior → 0.50 neutral; `context_proximity` returns null at MVP; festival is a Phase-2 feature). **Recommendation:** seed the confirmed subset, formally defer the rest with the documented fallback, and log each as an open data gap — do not invent values.
3. **Deterministic value normalization (Category A/B).** Diet vocabulary reconciliation (source `veg/nonveg/mixed/egg` ↔ schema enums `veg/non_veg/egg/vegan`; `re_cohorts.diet_mode`), cook-time field selection (3 source columns → one `cook_time_minutes`), and Jain polarity inversion. These are deterministic TR-rule ratifications, not research.
4. **Alias / synonym / cuisine-group depth (deferred, documented).** `ingredient_aliases`, `term_synonyms`, and a normalized `cuisine_groups` table have **no MVP destination by design** — Architecture Freeze Pack A chose "keep as-is for Phase 9, revisit as post-launch SER." WP-6 loads `cuisine_group` as denormalized text and does not load aliases/synonyms; this is a recorded deferral, not a gap to fix now.

**Also carry forward (not a WP-6 blocker):** `AGR-P3-07-001` (DPDP under-13 age gate) is OPEN and launch-blocking, but it gates the *production release*, not the staging knowledge load.

---

## 8. Risk Assessment

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Allergen bitmask seeded before Founder confirms bit positions | Medium | **High** (permanent + safety) | WP-6B hard gate; load blocked until ratified |
| R2 | Fabricating unsourced values (context multipliers, priors) to "complete" a gate | Medium | High | Governance forbids it; defer with documented fallback (Sec 7.2); gates may legitimately show deferred tables short |
| R3 | Trigger-derived columns seeded manually, corrupting Invariant 6 | Low | High | Load inputs only; never write `diet_type/is_jain/allergen_flags/genome_vector`; 902 verifies derivation |
| R4 | Tag `vector_position` assigned after dish vectors computed → corrupt vectors | Low | High | Enforce load order (Sec 5): tags + `fn_assign_tag_vector_positions()` before any dish tagging |
| R5 | `dish_ingredients` incomplete → false-negative allergen safety | Medium | **Critical** | Ingredient-token resolution audit in WP-6C; 4 orphan tokens (Batch 4) resolved before load; safety gates as final backstop |
| R6 | Dish-name → `dish_id` matching for `re_class_dish_options`/affinity is non-deterministic | Medium | High | Deterministic matching algorithm (Architecture-owned per Batch 5/6) ratified in WP-6C; unresolved names logged, never guessed |
| R7 | UUID instability on re-load orphans future behavioural history/audit | Low | Medium | Deterministic keys / never-delete discipline; re-runnable idempotent seeds |
| R8 | Cross-batch auto-merge (Batch 2 synonyms vs Batch 4 alternate names) | Low | Medium | Never auto-merge; Founder-gated (CBD-001) |
| R9 | Seed load performed against production instead of staging | Low | High | `foofoo-staging` only; production promotion is a separate Founder-approved gate (`DOC-P3-08` §15) |
| R10 | Free-tier 500MB DB ceiling with full content + images | Low | Medium | Capacity check in WP-6E; images via Cloudinary CDN, not DB |

---

## 9. Success & Acceptance Criteria

**Success (WP-6 overall):**
- All 15 Seed Gates (S-01…S-15) meet their target counts on `foofoo-staging` (`900` Check 7 all `pass = true`), except any table formally deferred under Section 7.2 with a recorded Founder decision.
- `901–904` behavioural validation pass; the **four safety gates return 0 rows**.
- Every loaded seed row is traceable to a `MAP-*` lineage ID with a complete 10-field provenance record and a `TR-NNN` transformation reference.
- Derived columns are trigger-produced (never seeded); `dish_tags` Tier-1 completeness holds for every dish in `re_class_dish_options`.

**Acceptance (Data Gate):** a companion execution certificate (`REPO-CERT-00N`) records real 900-series output proving the above, plus a Phase 3.5 Closure Report closing IDR-001. Only then may promotion to `foofoo-mvp` be proposed (separately, Founder-approved).

**Estimated execution order:** 6A → 6B (decisions — critical path) → 6C → 6D → 6E → 6F. WP-6A/6B are documentation + decisions (no DB); 6D generates SQL; 6E/6F touch `foofoo-staging` only.

---

## 10. Critical Self-Review

- **Repository-first, not memory-first.** The single most important claim here — that the four PIR blockers are resolved — was **not** taken from the frozen research (which still lists them open); it was verified by directly reading migrations 021–028 and cross-checking against the Architecture Freeze recommendations. Where frozen docs and live schema disagreed, live schema won, as the session-resume discipline requires.
- **What I did not do:** I did not open every cell of the two workbooks (I read sheet inventories, dimensions, headers, and samples, plus the fully-canonicalized row counts the frozen research already established). Exhaustive per-row source validation is WP-6C's job, not this plan's.
- **Honest limits:** the exact numeric expansion logic for the large generated tables (`re_cohorts` 2,952; `re_weekly_class_plans` 20,664; `re_household_addon_plans` 7,992) is asserted by Batch 1 to exist in the workbook's planning sheets at full scale; I confirmed the sheets exist and the counts match Seed Gates, but did not re-derive the expansion. WP-6A must confirm these load directly vs. require generation.
- **No fabrication.** Every gap in Section 7 is left open for a Founder decision rather than filled with a plausible value; this is deliberate and per `DOC-P3-09` §14 / `DOC-P3-10` §19.
- **Scope discipline.** This document plans; it generates no SQL, changes no schema, and touches no database, per the Founder's explicit STOP condition.

---

## 11. Versioning & Placement

First issue (v1.0). Placed in `docs/project-history/work-packages/` as a DESIGNED work package; it will read COMPLETED only when a companion certificate with real execution output exists (per CLAUDE.md Version & Lifecycle Rules). Naming follows the ratified WP-5AA standard. No existing document superseded.

---

Founder Sign-off: _______________________ Date: ___________
