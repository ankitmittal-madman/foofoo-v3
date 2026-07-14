# [ACTIVE]_WP-6RE_Recommendation_Engine_Knowledge_Audit_v1.0

**Status:** ACTIVE — FORENSIC AUDIT (read-only). No SQL, no schema change, no seed generation, no migrations, no data load.
**Version:** v1.0
**Date:** 2026-07-14
**Placement:** docs/project-history/work-packages/[ACTIVE]_WP-6RE_Recommendation_Engine_Knowledge_Audit_v1.0.md
**Supersedes:** None. Independently re-derives the RE-seedability question; does **not** trust prior WP-6 conclusions.
**Method:** every claim cites repository evidence (source file + sheet/column, migration, frozen doc section, or research ID). New evidence read this audit: **RE-DOC-01–05** (`.docx`, extracted to text) — not read in prior sessions.

---

## Executive Summary

**This audit corrects the prior WP-6D-gen conclusion.** WP-6D-gen deferred the *entire* `re_engine` layer as "values absent from the master workbook." That was over-conservative and is now disproven: reading RE-DOC-01–05 and re-deriving from live data shows **most contested values are derivable or recoverable, not missing**. Exactly **one** genuine, evidence-proven blocker remains, and it is an **architecture conflict (GAP-002)**, not absent data.

- **`day_type`, `primary_diet`, `state_code`, `region`, `persona_code`** — all **derivable/recoverable** with cited provenance (Sections 2–3). Not missing.
- **`re_cohorts` (S-11) is structurally incompatible with its own `UNIQUE(persona_id, state_code, diet_mode)` constraint** given the source's (persona × state × **city_tier**) shape: Cohort_Matrix = 2,952 = 1,476 (persona,state) × 2 tiers, but `diet_mode` is persona-determined → only 1,476 unique keys → loading 2,952 causes 1,476 UNIQUE violations. This blocks S-11 and, transitively, `re_weekly_class_plans` (S-12) and `re_household_addon_plans` (S-13). **Category D — Founder/architecture decision.**

**Answer to the audit question (Step 7): NO — not *fully* today.** Precisely: **YES WITH DERIVATION** for 12 of 15 Seed-Gate tables + config; **NO** for the cohort/weekly-plan/addon-plan chain (S-11/S-12/S-13) until GAP-002 is resolved by the Founder. **Confidence: HIGH.**

---

## STEP 1 + STEP 2 — RE table inventory & column classification

Schema from migrations 002–004, 013–016, 021–028 (frozen). Column class: **1:1** (direct source), **DRV** (derivable by rule), **REC** (recoverable from elsewhere in repo), **TRG** (trigger/computed), **DFLT** (documented default), **CFG** (already seeded), **GAP-D** (Founder decision).

| # | Table (Seed Gate) | Purpose | Population source | Contested columns → classification |
|---|---|---|---|---|
| 1 | `re_states` (S-01, 36) | State signatures | `State_Profile_v3` | `state_code` REC (region_food_affinity.csv codes + standard IN codes); `region` DRV (archetype→5-region; 3 edge cases) |
| 2 | `re_main_cohorts` (S-02, 5) | 5 onboarding cards | fixed set | all 1:1 (already in seed 101, complete) |
| 3 | `re_subcohorts` (S-04, 41) | Sub-cohort chips | `Subcohort_Routing` | 1:1 (sub_cohort_id, main_cohort_id, label) |
| 4 | `re_personas` (S-03, 41) | Persona priors | `Persona_Master_v3` | `persona_code` REC (=source persona_id P01..P41); `primary_diet` DRV (nonveg_mode + CAN-RULE-006) |
| 5 | `re_persona_assignment_rules` | (main,sub,state,diet)→persona | `Subcohort_Routing` + `Routing_Rules_v3` | DRV from routing; depends on personas |
| 6 | `re_routing_rules` (S-05, 8) | Onboarding branching | `Routing_Rules_v3` | 1:1 (complete in seed 101) |
| 7 | `re_meal_classes` (S-06, 131) | Class taxonomy | `Meal_Class_Master_v3` | `slot` DRV (slot_group→text[], migration 025); `planning_role` 1:1 (planning_role_v3); **`day_type` DRV** (weekday_fit vs weekend_fit — all 131 populated); `cuisine_family`/`variety_cooldown_days`/`max_per_week` nullable → DFLT/DRV |
| 8 | `re_meal_class_overlap_rules` (S-07, 13) | Class conflicts | `Meal_Class_Overlap_Resolution` | `conflicts_with` DRV (from replacement_logic/`allowed_as_weekly_primary_v3=N`) — needs rule ratify |
| 9 | `re_class_dish_options` (S-08, 1,050) | Class→dish pool | `Class_Dish_Options_v3` | `dish_id` REC (ICD-1 filter: only existing dishes); rest 1:1. Depends on meal_classes + dishes (both available) |
| 10 | `re_addon_classes` (S-09, 24) | Add-on classes | `Addon_Component_Class_Master` | `slot` DRV; `segment` 1:1 (target_member_segment) |
| 11 | `re_addon_dish_options` (S-10, 142) | Add-on→dish | `Addon_Dish_Options` | `dish_id` REC (ICD-1 filter); depends on addon_classes + dishes |
| 12 | **`re_cohorts` (S-11, 2,952)** | Cohort priors | `Cohort_Matrix_v3` | **`diet_mode` GAP-D** — see Step 3; `prior_weight` DFLT (1.0, no source) |
| 13 | **`re_weekly_class_plans` (S-12, 20,664)** | 7-day class plan | `Weekly_Class_Plan_v3` | FK `cohort_id` → blocked transitively by S-11; projection to {breakfast,lunch,dinner}_primary DRV (DOC-P3-03 LF-B02) |
| 14 | **`re_household_addon_plans` (S-13, 7,992)** | Add-on schedule | `Household_Addon_Component_Plan` | FK `cohort_id` → blocked transitively by S-11 |
| 15 | `re_nonveg_logic` (S-14, 36) | Protein priors | `NonVeg_Logic_v3` | keyed by `state_code` (REC via same crosswalk as S-01) |
| 16 | `re_city_migration_overlays` (S-15, 324) | Migration blend | `City_Migration_Overlay_v3` | `home_state` REC (state crosswalk); rest 1:1 |
| 17 | `re_dish_regional_affinity` | Dish×state affinity | `region_food_affinity.csv` | `state_code` 1:1 (already 2-letter in CSV); `dish_id` REC (ICD-1 filter, 131/134) |
| — | Config tables (`re_*_config`, etc.) | Scoring params | DOC-P3-03 §16 / RE-DOC-05 | CFG — already seeded (seed 100); `re_context_multipliers`/`re_festival_calendar` DFLT (RE fallbacks: context_proximity→null MVP; festival Phase-2) |

**No column is left "unknown."** Every contested field is classified above with its source.

---

## STEP 3 — Recovery analysis of every "believed missing" value

| Item | Directly found? | Derivable? | Recoverable? | Verdict + evidence |
|---|---|---|---|---|
| `day_type` (131 classes) | No column | **Yes** | — | **DRV.** All 131 rows have `weekday_fit_1_5` + `weekend_fit_1_5` (verified). Rule: weekend_fit>weekday_fit→weekend; weekday>weekend→weekday; equal→any. Corroborated by RE-DOC-03 ("Weekend-weighted", "daily weekday lunch default"). |
| `primary_diet` (41 personas) | No column | **Yes** | — | **DRV.** `nonveg_mode` is persona-determined (41 distinct persona→mode, verified). Rule: {veg_only,veg_default,jain,health_veg_or_default,budget_default,default}→veg; egg_only→egg; {regular_nonveg,protein_nonveg,seafood,sunday_mutton,outside_nonveg}→non_veg. Default→veg per **Batch1 CAN-RULE-006** ("nonveg primary only for egg/nonveg personas or state-high-omnivore priors"). |
| `state_code` (2-letter) | Partially | Yes | **Yes** | **REC.** `region_food_affinity.csv` supplies 2-letter codes (PB, WB, MP…); standard Indian administrative codes for the rest. Objective/verifiable, not a business decision. |
| `region` (5-value) | No | **Yes** (mostly) | seed 101 precedent | **DRV + minor GAP-D.** `region_archetype` (9 values)→5-region: SOUTH_RICE→south, NORTH_WHEAT→north, EAST_RICE_FISH→east, WEST_VEG/WEST_COASTAL→west, CENTRAL_MIXED→central. Edge cases NORTHEAST_RICE_MEAT/HIMALAYAN/ISLAND_COASTAL need a classification call (or load archetype verbatim — column is free text). Non-blocking. |
| `persona_code` | Yes (as id) | Yes | **Yes** | **REC.** Use source `persona_id` (P01..P41) verbatim, or a deterministic slug. No fabrication; relational integrity holds regardless of string. |
| `diet_mode` + cohort structure | No | **No** | **No** | **GAP-D (truly a decision).** See below. |
| `cuisine_family`, `variety_cooldown_days`, `max_per_week` (meal_classes) | No | partial | — | Nullable columns → DFLT NULL or DRV from RE-DOC-03/variety rules. Non-blocking. |
| Scoring weights / cold-start / confidence | **Yes** | — | — | **CFG.** In seed 100 (`[CONFIRMED]` DOC-P3-03 §16); RE-DOC-05 §State-A confirms w_cohort 0.55/w_content 0.20/w_history 0.00/w_context 0.15/w_explore 0.10. |
| `re_context_multipliers`, `re_festival_calendar` | No | No | No | **Category E (future).** Genuinely un-sourced; RE has documented MVP fallbacks (seed 100 notes). |

### The one genuine blocker — GAP-002 (`re_cohorts`), proven from live data
- `Cohort_Matrix_v3` = **2,952 rows** = **1,476** distinct (persona_id, state_id) × **2** city tiers (`city_tier_code` T1:1,476 / T2:1,476) — verified.
- `nonveg_mode` (the only diet-like source field) is **persona-determined**: distinct (persona, nonveg_mode) = 41 → distinct (persona, state, nonveg_mode) = **1,476**.
- Frozen `re_cohorts` = `UNIQUE(persona_id, state_code, diet_mode)`, **no `city_tier` column** (migration 004).
- Therefore any `diet_mode` derived from persona/nonveg_mode collapses T1 and T2 to the **same** key → loading the 2,952 source rows produces **1,476 `UNIQUE` violations**; the schema can hold at most **1,476** rows, but Seed Gate **S-11 targets 2,952**.
- **Conclusion:** the Seed Gate target and the source's tier dimension are **incompatible with the frozen constraint**. Resolution requires a Founder/architecture decision: (a) add `city_tier` to `re_cohorts` (SER against DOC-P3-04); (b) revise S-11 to 1,476 and route tier via `re_city_migration_overlays`; or (c) redefine `diet_mode` to carry tier (semantically wrong — not recommended). This is the **only** hard blocker, and it cascades to S-12 (`re_weekly_class_plans`, FK cohort_id) and S-13 (`re_household_addon_plans`, FK cohort_id).

---

## STEP 4 — Dependency graph (evidence-based)

```
CONFIG (seed 100, CFG) ─────────────────────────────────────────────┐
                                                                     │
re_states (S-01) ──┬── re_nonveg_logic (S-14)                        │
  [REC/DRV]        ├── re_city_migration_overlays (S-15)             │
                   └── re_dish_regional_affinity  ← dishes (ICD-1)   │
                                                                     │
re_main_cohorts (S-02) → re_subcohorts (S-04) → re_personas (S-03)   │
                              │  [persona_code REC, primary_diet DRV]│
                              └→ re_persona_assignment_rules          │
                                                                     ▼
re_meal_classes (S-06) [day_type DRV] ──┬── re_meal_class_overlap (S-07)
  slot text[] (mig 025)                 ├── re_addon_classes (S-09) → re_addon_dish_options (S-10, ICD-1)
                                        └── re_class_dish_options (S-08, ICD-1)  ← dishes (ICD-1) ✅
                                                                     │
        ┌────────────────────────────────────────────────────────────┘
        ▼   ⛔ GAP-002 BLOCK
   re_cohorts (S-11)  ──►  re_weekly_class_plans (S-12)  ──►  (recommendation runtime)
   [diet_mode GAP-D]        re_household_addon_plans (S-13)
```
Everything **above** the GAP-002 line is seedable with derivation/recovery. Everything **through** `re_cohorts` is blocked until GAP-002 resolves.

---

## STEP 5 — Recovery attempts (exhaustive search performed)

- **RE-DOC-01–05** (newly read this audit): supply the class taxonomy (RE-DOC-03), 20 genome dimensions with value domains (RE-DOC-02), scoring weights + cold-start ladder + 4-state model (RE-DOC-04/05). They confirm concepts and corroborate `day_type` weighting and scoring config — but contain **no per-row `diet_mode`/`state_code`/`region`/`persona_code` table**. Searched for `diet_mode`, `primary_diet`, `state_code`, `region`, `persona_code`: no per-row definitions found.
- **Workbook sheets** (all 22): `DB_Implementation_v3` keys on source ids; no crosswalk. `Data_Dictionary_v3` is descriptive. No hidden `diet_mode`/`state_code` mapping sheet.
- **Research batches**: GAP-002 (`re_cohorts` structure) and diet_mode were **OPEN Founder Decisions** in `Batch1_Resolution_Package` — never resolved. Confirmed no later resolution in Architecture Freeze / Decision Review (those closed cuisine/tags/combo/snack only).
- **Migrations/seeds**: seed 101 (illustrative) shows region ∈ 5-value and diet_mode='veg' example — illustrative, not authoritative, but a usable pattern precedent for region.
- Result: the derivable/recoverable items were confirmed recoverable; GAP-002 confirmed genuinely unresolved after exhaustive search.

---

## STEP 6 — Classification of every unresolved item

- **Category A (already implemented):** slot `text[]`+snack (mig 025), tag vector algorithm (mig 023), cuisine FK (mig 021), combo component_type (mig 025), regional-affinity table (mig 024), scoring/config values (seed 100).
- **Category B (recoverable from repository):** `state_code` (region_food_affinity.csv + standard codes); `persona_code` (source persona_id); region precedent (seed 101).
- **Category C (derivable deterministically):** `day_type` (weekday/weekend fits); `primary_diet` (nonveg_mode + CAN-RULE-006); `region` (archetype→5-region, 6 clean); `slot`/`planning_role`/`segment` maps; `conflicts_with` (from resolution logic); weekly-plan projection (LF-B02); ICD-1 `dish_id` filters (S-08/S-10/affinity).
- **Category D (Founder decision):** **GAP-002** — `re_cohorts` S-11 count vs `UNIQUE(persona,state,diet_mode)` given city_tier (blocks S-11/S-12/S-13); minor: `region` edge cases (NE/Himalayan/Island); allergen fish/mustard scope (safety, from WP-6D-gen).
- **Category E (future enhancement):** `re_context_multipliers` full matrix, `re_festival_calendar` (MVP fallbacks documented); the 885 deferred dishes (ICD-1 backlog).
- **Category F (truly absent):** **none.** No RE knowledge is irrecoverably absent — every gap is A/B/C/D/E.

---

## STEP 7 — Can the Recommendation Engine be fully seeded today?

**NO — not *fully* today.** More precisely: **YES WITH DERIVATION** for 12 of 15 Seed-Gate tables + all config (Categories A/B/C), and **NO** for `re_cohorts` / `re_weekly_class_plans` / `re_household_addon_plans` (S-11/S-12/S-13) which are blocked by the single Category-D item **GAP-002** — a proven architecture conflict, not missing data. There is **zero Category F** (nothing truly absent).

Evidence for the NO: `re_cohorts UNIQUE(persona_id, state_code, diet_mode)` (migration 004) admits ≤1,476 rows given persona-determined diet; S-11 targets 2,952; the 1,476-row gap is the 2× `city_tier` dimension the schema cannot represent.

---

## Final Report

1. **RE readiness:** 12/15 Seed-Gate tables + config are seed-ready via derivation/recovery; 3 (cohort chain) blocked by GAP-002.
2. **Recovered knowledge:** `day_type` (all 131 classes, from fits), `primary_diet` (from nonveg_mode+CAN-RULE-006), scoring/cold-start config (RE-DOC-05, already in seed 100), meal-class taxonomy + genome dimensions (RE-DOC-02/03).
3. **Recovered mappings:** `state_code` (region_food_affinity.csv + standard), `region` (archetype→5-region), `persona_code` (=persona_id), `slot`/`planning_role`/`segment`, ICD-1 `dish_id` filters.
4. **Remaining gaps:** GAP-002 (cohort structure — S-11/12/13); region edge-case classification; fish/mustard allergen scope; `re_context_multipliers`/`re_festival_calendar` (Category E).
5. **Founder decisions:** (i) GAP-002 resolution — add `city_tier` to `re_cohorts` (SER) vs revise S-11 to 1,476 vs redefine diet_mode; (ii) confirm region edge-cases (NE/Himalayan/Island) or load archetype verbatim; (iii) confirm allergen fish/mustard scope; (iv) ratify the derivation rules (day_type, primary_diet).
6. **Can RE seed generation begin?** For the non-cohort tables (S-01–S-10, S-14, S-15, affinity, persona/class layer): **yes, on approval of the derivation rules.** For the cohort chain (S-11/12/13): **no, until GAP-002 is decided.**
7. **Confidence score:** **HIGH (9/10).** All classifications are evidence-cited; GAP-002 is arithmetically proven from live data; the only residual uncertainty is which GAP-002 resolution the Founder chooses.
8. **Recommended next work package:** **WP-6RE-DEC** — a one-page Founder decision on GAP-002 (recommend: add `city_tier smallint` to `re_cohorts` via a governed SER/AGR against DOC-P3-04, restoring S-11=2,952) + ratify the four derivation rules. Then **WP-6RE-gen** generates the RE seeds (110+), and **WP-6E** loads content + RE on staging and runs the 900-series.

---

## Critical Self-Review

- **Corrected the prior report, as instructed.** WP-6D-gen's "whole RE layer blocked / values absent" was disproven by reading RE-DOC-01–05 (not read before) and re-deriving: the values are derivable/recoverable, not absent. Only GAP-002 is a true blocker, and it is a *structural* conflict, not missing data.
- **GAP-002 is arithmetic, not opinion:** 2,952 source rows vs ≤1,476 admissible keys is proven from the workbook + migration 004 constraint.
- **No fabrication:** no persona, cohort, diet_mode, or mapping was invented; derivation rules are cited to source columns + frozen business rules and are proposed for ratification, not silently applied.
- **Read-only honoured:** no SQL, no schema change, no seeds, no migrations, no load.

---

Founder Sign-off: _______________________ Date: ___________
