# [ACTIVE]_WP-6A-6D_Knowledge_Mapping_and_Seed_Pipeline_v1.0

**Status:** ACTIVE — DESIGNED (execution-design only). No database touched, no seed SQL generated, no schema changed.
**Version:** v1.0
**Date:** 2026-07-14
**Placement:** docs/project-history/work-packages/[ACTIVE]_WP-6A-6D_Knowledge_Mapping_and_Seed_Pipeline_v1.0.md
**Supersedes:** None. Executes against `[ACTIVE]_WP-6_Canonical_Knowledge_Engineering_Plan_v1.0` (the master plan).
**Covers:** WP-6A (Knowledge Blueprint), WP-6B (Product Decision Validation), WP-6C (Canonical Mapping), WP-6D (Seed Engineering design).
**Provenance rule (standing, Founder-directed 2026-07-14):** every transformation, mapping, classification, and business rule in this document cites its exact source — a research document, source spreadsheet, Architecture Freeze section, migration file, or frozen architecture section.

---

## Executive Summary

Progressive execution ran WP-6A → WP-6D. The knowledge blueprint, the decision re-validation, the canonical source-to-target mapping, and the seed-pipeline engineering design are complete **as design artifacts**. No seed SQL was generated, because execution reached a genuine, evidence-based blocker that no engineering step may resolve without a Founder decision.

**Headline results:**
- **WP-6B — nine of the ten historical Founder decisions have disappeared.** They are already implemented in the live, GREEN-certified schema (migrations 021–028) or resolved-by-design in the frozen architecture. Verified against live files, not inherited from the frozen research (which still lists several as "open").
- **WP-6C — content-domain mapping is complete and column-level** (ingredients, tags, cuisines, dishes, junctions, combos) with transformation rules and provenance; `re_engine` reference tables map sheet→table with all row counts confirmed present at full scale (direct load, no generation).
- **WP-6D — the deterministic seed pipeline is fully designed** (load-order DAG, idempotency, rollback, error handling, validation, certification approach). Migrations are deliberately **not** generated (see blocker).
- **GENUINE BLOCKER (STOP):** the dish content catalog (`dishes.xlsx`, 810 dishes) covers only **~17%** of the dishes referenced by `re_class_dish_options` (S-08) and **~2%** of those referenced by `re_addon_dish_options` (S-10). These two Seed Gates cannot be met without either the missing dish content or a Founder decision on the authoritative dish catalog. This is *evidence unavailable + product ambiguity*, not an engineering choice — so no data was fabricated.

**Data-Gate readiness:** GREEN for config, reference/persona/cohort/weekly-plan/regional domains; **RED for the class-dish and addon-dish linkage** until the catalog gap is resolved. **Confidence: HIGH** in the diagnosis and the design; the blocker is specific and quantified.

---

## WP-6A — Knowledge Blueprint (validated)

**Source inventory, authority, target, load order, provenance.** Sources and authority per `Phase3_5_Phase2_Knowledge_Acquisition_v1.2` §2 (SHA-256 checksummed at intake); targets per the frozen migrations that implement `DOC-P3-04 v1.3`.

| # | Source file | Authority | Target table(s) | Load tier |
|---|---|---|---|---|
| 1 | `ingredients_v5.csv` (191) | Master | `public.ingredients` | T2 (content ground truth) |
| 2 | `tags_v4.csv` (111) | Reference (vocab) | `public.tags` | T2 |
| 3 | `cuisines_v4.csv` (65) + `cuisine_groups_v4 2.csv` (22) | Master/Reference | `public.cuisines` (`cuisine_group` denormalized) | T2 |
| 4 | `dishes.xlsx` `dishes_810` (810) | Master | `public.dishes` (+ derived cols via trigger) | T3 (needs T2) |
| 5 | `dishes.xlsx` `Ingredients` col | Master | `public.dish_ingredients` | T4 (fires derivation) |
| 6 | `dishes.xlsx` tag columns | Master | `public.dish_tags` | T4 (fires vector) |
| 7 | `dish_combos_v2` (35) / `dish_combo_items_v2` (74) | Master | `public.dish_combos` / `dish_combo_items` | T4 |
| 8 | `Indian_Meal_Cohort_Persona_DB_v3.xlsx` (22 sheets) | Mixed | 15 `re_engine` reference tables | T1 (states→…) + T5 (options) |
| 9 | `region_food_affinity.csv` (136) | Reference | `re_engine.re_dish_regional_affinity` | T5 (needs dishes) |

**Documentation/provenance/QA sheets never become seed data** (README, Data_Dictionary_v3, Weekly_Plan notes, DB_Implementation_v3, `Sources_v3`, `QA_Checks_v3`) — permanent Founder rule, `Phase3_5_Phase2_Knowledge_Acquisition_v1.2` §11. `dishes.xlsx` `Sheet1` is Founder-directed-ignore (same §11, Rule 1).

**Provenance/lineage discipline:** every generated seed row must cite the `MAP-*` ID it derives from (Permanent Lineage Chain, `Batch1_Mapping_Package_v1.1` §6E: `OBS→CAN→MAP→GAP→RES→SEED`). PIR §confirmed 0 orphan lineage across 6 batches.

---

## WP-6B — Product Decision Validation

Every historical decision re-classified against **live repository evidence** (per Founder instruction: "repository evidence supersedes historical assumptions"). Classes: Implemented / Resolved-by-design / Deferred / **Needs Founder**.

| Historical decision (origin) | Live status | Evidence (provenance) |
|---|---|---|
| **Cuisine destination** (PIR Decision 1; Freeze Pack A) | **Implemented** | `migration 021_cuisines_reference.sql` creates `public.cuisines` + `cuisine_id` FK on `dishes` and `dish_combos`. Freeze §3 Pack A recommended option (a). |
| **Tag `vector_position` algorithm** (PIR Decision 2/3; Freeze Pack B) | **Implemented** | `migration 023` creates `fn_assign_tag_vector_positions()` — deterministic `ORDER BY tier, dimension, tag_name`; exactly the drafted algorithm (Freeze §4 Pack B; `Batch3` B3-RES-004). |
| **Tag uniqueness collision** (`"light"/"none"`, B3-GAP-003) | **Implemented** | `migration 023` drops global `tags_tag_name_key`, adds `UNIQUE(dimension, tag_name)`. |
| **Combo role vocabulary** (PIR Decision 3-combo; Freeze Pack C) | **Implemented** | `migration 025` adds `dish_combo_items.component_type` (8-value CHECK), `role` unchanged. Freeze §5 Pack C option (C). |
| **Snack + compound meal-slot** (GC-AGR-002 / GAP-007) | **Implemented + verified** | `migration 025` converts `re_meal_classes.slot`→`text[]` domain `{breakfast,lunch,dinner,snack}`. Source `Meal_Class_Master_v3.slot_group` = {Breakfast 26, Lunch/Dinner 68, Snack 22, Dinner 15} — all representable (`Lunch/Dinner`→`ARRAY['lunch','dinner']`, `Snack`→`ARRAY['snack']`). |
| **Weekly-plan reduced fidelity** (GAP-004) | **Resolved-by-design** | `DOC-P3-03 LF-B02`: `generateClassPlan() → 21 class assignments` = 7 days × 3 primary slots. `Architecture_Decision_Review §5` did **not** elevate GAP-004 to any blocker group. `migration 004` `re_weekly_class_plans` = 3 primary class codes. Snack→`re_household_addon_plans`; secondary/tertiary→runtime `re_class_dish_options`. |
| **Regional-affinity table** (PIR Decision 4; Freeze Pack B) | **Implemented** | `migration 024_re_dish_regional_affinity.sql`. |
| **Dish attributes** (calories/serving/tier1; PIR Decision 5) | **Implemented** | `migration 022` adds `calories`, `serving_size`, `food_dna_tier_1`; spice/sweetness/heaviness are tier-2 tag rows (no DDL) per `migration 022` note. |
| **Alias/synonym unification** (PIR Decision 6; Freeze Pack A) | **Deferred (documented)** | Freeze §3 Pack A option (c): keep as-is for Phase 9, revisit post-launch SER. No `ingredient_aliases`/`term_synonyms` table exists (confirmed: grep of all migrations). WP-6 loads `cuisine_group` as denormalized text; does not load aliases/synonyms. |
| **Allergen bitmask encoding** (B2-GAP-006) | **Resolved (encoding) / Needs Founder (scope)** | Encoding authoritative & frozen: `DOC-P3-03 §07` (line 163): 7 bits — 0 Nuts/peanuts, 1 Dairy, 2 Gluten, 3 Shellfish, 4 Egg, 5 Soy, 6 Sesame; consistent with `profiles.allergen_flags` (`migration 005`) and CDM Invariant 3. **Residual (see §Founder Items):** source `ingredients_v5` has 2 allergen types with no frozen bit — `fish` (6 rows), `mustard` (2 rows). |

**Result: 9 of 10 historical decisions have disappeared** (implemented or resolved-by-design). One residual (allergen *scope* for fish/mustard) plus one **new** blocker discovered during mapping (dish catalog coverage, below) remain.

---

## WP-6C — Canonical Mapping (source → target, with provenance)

Transformation-rule IDs per `DOC-P3-10 §20A` (TR-001 whitespace, TR-002 case, TR-003 Hindi↔English, TR-004 regional naming, TR-005 plural/singular, TR-006 synonym merge). New rules proposed below as `TR-007+`.

### C.1 `public.ingredients` ← `ingredients_v5.csv` (191)
| Target column | Source | Transformation | Provenance |
|---|---|---|---|
| `name` | `name` | TR-001/002 | `migration 002` |
| `is_veg` | `diet_type` | `= (diet_type == 'veg')` → `non_veg`/`egg` yield false | `migration 002`; source diet_type ∈ {veg 177, non_veg 13, egg 1} |
| `is_vegan` | `is_vegan` | `Y→true` | `Batch2` B2-CAN-RULE-002 (`is_vegan⟹diet_type=veg`, 0 exceptions) |
| `is_jain_excluded` | `is_jain_compatible` | **polarity inversion** `Y→false` (**TR-007, new**) | `Batch2` Attribute Matrix |
| `allergen_flags` | `is_allergen`+`allergen_type` | bitwise OR of type→bit (**TR-008, new**): peanuts/tree_nuts→bit0, dairy→1, gluten→2, shellfish→3, egg_allergen→4, soy→5, sesame→6 | `DOC-P3-03 §07` L163; `Batch2` B2-CAN-RULE-001 |
| `can_substitute_id` | — | not sourced (source has no substitute data) | `Batch2` reverse-observation |
| `seasonal_peak` | — | not sourced | — |

### C.2 `public.tags` ← `tags_v4.csv` (111)
| Target | Source | Transformation | Provenance |
|---|---|---|---|
| `tag_name` | `value` | TR-001/002 | `migration 002` |
| `dimension` | `category` | direct | `migration 002`; resolves collision via `UNIQUE(dimension,tag_name)` (`migration 023`) |
| `tier` | `tier` | `'tier_1'→1` etc. (**TR-009, new**) | `migration 002` CHECK tier∈{1,2,3} |
| `is_user_facing` | `is_user_facing` | `Y→true` | `migration 002` |
| `vector_position` | — | **computed post-load** by `fn_assign_tag_vector_positions()` | `migration 023` (must run before any dish genome vector) |

### C.3 `public.cuisines` ← `cuisines_v4.csv` (65) + groups (22)
`name`,`display_name`,`cuisine_group`,`parent_cuisine`,`state_origin`,`description`,`tier`,`is_user_facing`,`is_active` map directly (TR-001/002). `cuisine_group` is denormalized text (no FK to a groups table — Freeze Pack A). `state_origin` is **not** FK'd to `re_states` (63 values incl. non-Indian vs 36) — `Batch3` finding; left as text per schema (`migration 021` has no such FK). Provenance: `migration 021`; `Batch3_Pipeline_Package`.

### C.4 `public.dishes` ← `dishes.xlsx` `dishes_810` (810 → 802 dishes + 8 combos)
Displayed values authoritative; Excel formulas never read (`Phase2` §11 Rule 2). 8 combo-flagged rows excluded (`Batch4` B4-CAN-EX-001) → routed to combo tables.
| Target | Source col | Transformation | Provenance |
|---|---|---|---|
| `name` | `Dish Name` | TR-001 | `migration 008` |
| `name_hindi`/`name_regional` | `Alternate Names` | first 2 of comma list (excess dropped; ≤17 dishes affected) | `Batch4` B4-GAP-002; Freeze Pack A opt (c) |
| `meal_occasion` | `Meal Types` | split comma → `text[]` | `migration 008` |
| `cook_time_minutes` | `Total Mins` | direct (choice: Total, not Prep/Cooks — **needs ratify, TR-010**) | `Batch4` B4-GAP-004 (`Prep+Cooks=Total`, 0/810 exceptions) |
| `difficulty` | `Difficulty` | map to {beginner,intermediate,advanced} | `migration 008` CHECK |
| `calories` | `Calories` | direct | `migration 022` |
| `serving_size` | `Serving Size` | direct | `migration 022` |
| `food_dna_tier_1` | `tier_1` | direct | `migration 022` |
| `cuisine_id` | `Cuisines` | resolve to `cuisines.id` (TR-004) | `migration 021` |
| `diet_type`,`is_jain`,`allergen_flags`,`genome_vector` | — | **DERIVED — never seeded** | CDM Invariant 6; `migration 008` REVOKE; trigger `fn_derive_dish_attributes` (`migration 010`) |
| `popularity_score`,`acceptance_rate_*` | — | trigger/CRON only | `migration 008` |

### C.5 `public.dish_ingredients` ← `dishes.xlsx` `Ingredients` (comma tokens)
Split tokens → resolve each to `ingredients.id` (TR-004 naming normalization, e.g. `basmati_rice`→`rice_basmati`). **Safety-critical** (allergen source of truth, CDM Invariant 3). 4 orphan tokens must resolve or be added before load (`Batch4_Technical_Review §2A`). Firing this junction triggers derivation (`migration 009`/`010`).

### C.6 `public.dish_tags` ← `dishes.xlsx` genome columns
Columns `Spice Level, Sweetness, Heaviness, Primary Taste, Texture, Richness, Mouthfeel, Aroma Profile, Fermentation, Serving Temp, Weather Affinity, Cooking Method, Dish Category` → tag rows (dimension=column, tag_name=value), `confidence=1.0`. Tier-1 completeness (7 mandatory tags @≥0.85) required before a dish enters `re_class_dish_options` (`DOC-P3-03 LF-K04`). Firing updates genome vector (`migration 010`). 3 orphan texture values reconciled per `Batch4_Technical_Review §2B` (`juicy`=mislabeled mouthfeel).

### C.7 Combos ← `dish_combos_v2` (35) / `dish_combo_items_v2` (74)
`combo_type`→CHECK {inseparable,base_with_sides,thali}; `role`→3-value CHECK; `component_type`→8-value CHECK (`migration 025`). Item `dish_name`→`dishes.id`. Provenance: `migration 008/009/025`; `Batch5_Pipeline_Package`.

### C.8 `re_engine` reference tables ← `Indian_Meal_Cohort_Persona_DB_v3.xlsx` (sheet→table)
All row counts confirmed present at full scale by direct workbook introspection (this session) — **direct load, no generation**:
| Seed Gate | Table | Source sheet (rows) | Key transformation | Provenance |
|---|---|---|---|---|
| S-01 | `re_states` (36) | `State_Profile_v3` (36) | `state_id`→`state_code`; region archetype→`region` (5-value) | `Batch1`; Project Checkpoint (region domain) |
| S-02 | `re_main_cohorts` (5) | `Main_Cohort_Hierarchy` | fixed set MC_SOLO… | `seed 101` (already complete) |
| S-03 | `re_personas` (41) | `Persona_Master_v3` (41) | `persona_id`,`main_cohort_id`,`nonveg_mode`→`primary_diet` | `Batch1` Mapping §0 |
| S-04 | `re_subcohorts` (41) | `Subcohort_Routing` | direct | `Batch1` |
| S-05 | `re_routing_rules` (8) | `Routing_Rules_v3` | direct | `seed 101` (already complete) |
| S-06 | `re_meal_classes` (131) | `Meal_Class_Master_v3` (131) | `slot_group`→`slot text[]`; `planning_role_v3`→`planning_role` (1:1: MAIN_PRIMARY 118/ADDON 12/COMBO 1) | `migration 025`; this session's vocab extraction |
| S-07 | `re_meal_class_overlap_rules` (13) | `Meal_Class_Overlap_Resolution` | direct | `Batch1` |
| **S-08** | `re_class_dish_options` (1,050) | `Class_Dish_Options_v3` (1,050) | `dish_name`→`dish_id` **← BLOCKER** | see §Blocker |
| S-09 | `re_addon_classes` (24) | `Addon_Component_Class_Master` | direct | `Batch1` |
| **S-10** | `re_addon_dish_options` (142) | `Addon_Dish_Options` (142) | `dish_or_component_name`→`dish_id` **← BLOCKER** | see §Blocker |
| S-11 | `re_cohorts` (2,952) | `Cohort_Matrix_v3` (2,952) | persona×state×diet; `prior_weight` default 1.0 (no source → default) | `Batch1` CAN-RULE-012 (2,952/2,952 unique, re-verified) |
| S-12 | `re_weekly_class_plans` (20,664) | `Weekly_Class_Plan_v3` (20,664) | project {breakfast,lunch,dinner}_primary_class only (GAP-004 resolved-by-design) | `DOC-P3-03 LF-B02`; `migration 004` |
| S-13 | `re_household_addon_plans` (7,992) | `Household_Addon_Component_Plan` (7,992) | direct | `Batch1` |
| S-14 | `re_nonveg_logic` (36) | `NonVeg_Logic_v3` (36) | state→slots/preferred | `Batch1` |
| S-15 | `re_city_migration_overlays` (324) | `City_Migration_Overlay_v3` (324) | home_state×city×band→weight | `Batch1`; CDM Invariant 7 (`home+city=1.0`) |

### C.9 `re_engine.re_dish_regional_affinity` ← `region_food_affinity.csv` (136)
`state_code`+`dish_name`→`dish_id`+`affinity_score` (0–1 CHECK). **131/134 dishes (98%) resolve** to content — 3 unmatched (`chole bhature` [combo], `dhuska`, `rugda`). Low-impact; unmatched rows logged, not guessed. Provenance: `migration 024`; this session's coverage analysis.

### C.10 Config tables (`seed 100`) — already complete
Values `[CONFIRMED]` from `DOC-P3-03 §16`. Two tables genuinely unsourced: `re_context_multipliers` (full matrix) and `re_festival_calendar` — RE fallbacks documented (`context_proximity`→null at MVP; festival = Phase-2 feature; `seed 100` notes). `re_cohort_class_priors` unsourced → fallback 0.50 neutral (`DOC-P3-03 LF-E02`). **Recommend formal deferral, no fabrication.**

---

## WP-6D — Seed Engineering (pipeline design)

Reuses the existing numbered-migration discipline (`DOC-P3-05 Part a`; every forward migration paired with `_rollback.sql`, `DOC-P3-07 §32`). Seed band is `1NN` (`CLAUDE.md`).

**Deterministic load-order DAG** (FK + trigger dependency):
```
100–102 (existing config/illustrative)  →  [103] ingredients  →  [104] tags → CALL fn_assign_tag_vector_positions()
   →  [105] cuisines (+ groups as text)
   →  [106] dishes (core cols only; derived cols untouched)
   →  [107] dish_ingredients   ── fires fn_derive_dish_attributes (diet_type/is_jain/allergen_flags)
   →  [108] dish_tags          ── fires fn_update_dish_genome_vector
   →  [109] dish_combos + dish_combo_items
   →  [110] re_states → re_main_cohorts → re_subcohorts → re_personas → re_persona_assignment_rules
   →  [111] re_meal_classes (+ public mirror) → overlap_rules → re_addon_classes
   →  [112] re_cohorts → re_weekly_class_plans → re_household_addon_plans → re_nonveg_logic
             → re_city_migration_overlays → re_cohort_class_priors(defer)
   →  [113] re_class_dish_options   ← BLOCKED (dish_id coverage)
   →  [114] re_addon_dish_options   ← BLOCKED (dish_id coverage)
   →  [115] re_dish_regional_affinity (131/134)
```
The `103–102` supersede the illustrative rows in `101/102` (never edited in place — new migrations, `DOC-P3-10 §23`).

**Idempotency:** each seed migration guarded (`INSERT … ON CONFLICT DO NOTHING` on natural keys / truncate-and-reload within a transaction for reference tables) so a re-run converges to the same state. **Rollback:** paired `1NN_..._rollback.sql` deletes exactly its band's rows in reverse FK order. **Error handling:** load inside a single transaction per migration; any FK/CHECK failure aborts the band without partial state. **Environment:** `foofoo-staging` only; production promotion is a separate Founder-approved step (`DOC-P3-08 §15`).

**Certification approach (WP-6F preview):** run `900` (Check 7 = 15 Seed Gates), `901–904`, and the 4 safety gates (must return 0 rows, P0 per `DOC-P3-08 §16`); provenance-completeness audit (every row cites a `MAP-*`); then a Data-Gate certificate `REPO-CERT-00N` with real output.

**Migrations were NOT generated in this session** — genuinely not yet required (`DOC-P3-10`: generate only when required): the central content↔RE linkage is blocked, and the allergen scope + three TR ratifications are pending. Generating full seeds now would risk fabrication of the 758 missing dishes — explicitly forbidden.

---

## Genuine Blocker (STOP) — Dish Catalog Coverage

**Finding (quantified this session, aggressive normalization: parentheticals/punctuation removed, alternate names included):**

| RE table | Distinct dishes referenced | Present in `dishes_810` content | Missing |
|---|---|---|---|
| `re_class_dish_options` (S-08, 1,050 rows) | 916 | **158 (17%)** | **758** |
| `re_addon_dish_options` (S-10, 142 rows) | 123 | **3 (2%)** | 120 |
| `re_dish_regional_affinity` | 134 | 131 (98%) | 3 |

**Interpretation:** `region_food_affinity` was built against the dish content set and resolves. But `Class_Dish_Options_v3` and `Addon_Dish_Options` reference a **largely disjoint, larger dish universe (~900+ distinct dishes)** that is not present in `dishes.xlsx`. `dish_id` is a required (soft) reference for both tables (`migration 004` §03.27), so S-08 and S-10 cannot be seeded with valid references.

**Why this supersedes the frozen research:** `Batch5` B5-RES-002 / `Batch6` treated `dish_name→dish_id` as a *matching-algorithm* task (Architecture-owned). Live data shows a **catalog-coverage** gap (83–98% of referenced dishes absent), which no matching algorithm can bridge. This is a new, evidence-based finding (provenance: this session's normalized coverage analysis over `Class_Dish_Options_v3`, `Addon_Dish_Options`, `dishes_810`).

**Founder decision required — options (no option chosen; no data fabricated):**
- **(A)** `dishes.xlsx` (810) is a curated subset; the authoritative full dish catalog (~900+) is a **missing source file** to be supplied → then S-08/S-10 load directly. *(Evidence-unavailable path.)*
- **(B)** The ~900+ dish names in `Class_Dish_Options_v3`/`Addon_Dish_Options` **are** the catalog to build; `dishes.xlsx` seeds only the 810 with full attributes, and the remainder are created as content (attributes TBD) → large content-authoring effort, and Tier-1 tagging (`LF-K04`) would gate their eligibility.
- **(C)** MVP scopes `re_class_dish_options`/`re_addon_dish_options` to only the dishes present in content (~158/~3), formally revising Seed Gate targets S-08/S-10 downward → changes a frozen Seed Gate (governance action).

This blocks the class-dish and addon-dish linkage only; everything upstream (config, ingredients, tags, cuisines, dishes, combos, states/personas/cohorts/weekly-plans/nonveg/city overlays, regional affinity) is unblocked and designed.

---

## Secondary Founder Item (safety-scope, non-blocking to design)

**Allergen coverage for `fish` (6 ingredients) and `mustard` (2).** The frozen 7-bit model (`DOC-P3-03 §07` L163) has no bit for fish or mustard; `profiles.allergen_flags` and OB-05 onboarding use the same 7-bit model, so the model is internally consistent (these allergens are out of MVP scope on both sides). **Recommendation: Option A — load faithful to the frozen 7-bit model; `fish`/`mustard` contribute no bit** (documented scope boundary). Extending to fish/mustard is a coordinated SER touching `ingredients` + `profiles` + onboarding — not a WP-6 change. Surfaced for explicit Founder confirmation because a naive reader expects `is_allergen=Y` to always produce a flag.

**Also pending (minor, ratify in WP-6C sign-off):** TR-007 (jain polarity inversion), TR-008 (allergen bit map), TR-010 (`cook_time_minutes` = `Total Mins`). All deterministic, evidence-backed; listed for traceability, not blocking.

---

## Risk Register (delta from WP-6 plan §8)

| # | Risk | Status |
|---|---|---|
| R5 | `dish_ingredients` completeness → false-negative allergen safety | Open; 4 orphan tokens to resolve in load prep |
| R6 | `dish_name→dish_id` non-resolution | **Realized as the blocker** — quantified above |
| R-new | Fish/mustard allergens unrepresentable → safety-scope gap | Open; Founder confirmation (Option A recommended) |
| R2 | Fabricating unsourced values | Mitigated — nothing fabricated; deferrals documented |

---

## Data-Gate Readiness

| Domain | Readiness | Note |
|---|---|---|
| Config (S-none) | ✅ Loaded/confirmed | 2 tables deferred with RE fallbacks |
| Ingredients / Tags / Cuisines | ✅ Designed, ready | pending TR-007/008 ratify + fish/mustard confirm |
| Dishes / junctions / combos | ✅ Designed, ready | derived cols via trigger; orphan tokens to resolve |
| States/Personas/Cohorts/Weekly/Nonveg/City (S-01..07,09,11..15) | ✅ Designed, ready | direct load, counts confirmed |
| **Class-dish + addon-dish (S-08, S-10)** | ❌ **Blocked** | dish catalog coverage |
| Regional affinity | ✅ Designed (131/134) | 3 logged unmatched |

---

## Critical Self-Review

- **Repository-first, verified not assumed.** Nine "open" historical decisions were closed by reading the live migrations, not by trusting the frozen research. The one big finding that *stops* execution (dish coverage) was discovered by directly parsing the source files this session — it contradicts the frozen research's "matching-algorithm" framing, and live evidence wins.
- **No fabrication.** The 758 missing dishes were not invented; the blocker is surfaced with exact counts. Unsourced config tables are deferred with documented fallbacks, not filled.
- **Provenance throughout.** Every mapping row and rule cites a migration, frozen doc section, or research ID, per the standing Founder rule.
- **Limits:** dish-name coverage used normalized string matching; a Founder-supplied crosswalk or a larger catalog could raise the match rate, but not from 17% to complete — the gap is structural. Column-level `re_engine` transformations are specified at sheet→table granularity; per-column SQL is WP-6D-generation work, deferred until the blocker and TR ratifications clear.

---

## Versioning & Placement

First issue (v1.0). DESIGNED work package in `docs/project-history/work-packages/`; will read COMPLETED only with a companion execution certificate carrying real 900-series output (CLAUDE.md Lifecycle Rules). No certificate is generated now — nothing was executed against a database. Naming per WP-5AA standard.

---

Founder Sign-off: _______________________ Date: ___________
