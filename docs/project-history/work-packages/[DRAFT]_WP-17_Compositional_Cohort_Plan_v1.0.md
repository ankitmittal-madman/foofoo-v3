# [DRAFT]_WP-17_Compositional_Cohort_Plan_v1.0

**Status:** DRAFT — real code shipped and tested this session (not a proposal); DRAFT until a companion certificate under docs/project-history/certificates/ documents execution per this repo's Version & Lifecycle Rules. Companion: [ACTIVE]_REPO-CERT-025_WP-17_Compositional_Cohort_Plan_v1.0.md.
**Version:** v1.0
**Date:** 2026-08-03
**Placement:** docs/project-history/work-packages/[DRAFT]_WP-17_Compositional_Cohort_Plan_v1.0.md
**Supersedes:** N/A — extends WP-16 (adds a compositional plan layer in front of the learned model; the master-formula `w_cohort·S_cohort` seam and governance line are unchanged). Retires `dish_class_overrides.csv` (WP16-F1) in favour of the full-coverage `dish_class_map.csv`.
**Dependencies:** WP-16 (Cohort Intelligence — the learned `class_affinity` this fuses with), WP-15 (the `S_cohort` seam), Core Spine FROZEN (master score formula), `data/source/Indian_Meal_Cohort_Persona_DB_v3.xlsx` masters (Persona_Master_v3, State_Profile_v3, City_Migration_Overlay_v3, Meal_Class_Master_v3, Class_Dish_Options_v3).

---

## Executive Summary

WP-16 shipped a **learned factorized frequency model** (`cohort_intel.class_affinity`) that reproduces the persona-DB weekly plan by generalizing over feature counts. It works, but — as measured this session — it **plateaus at ~37% class overlap** with a specific precomputed cohort (e.g. **S14_T1_P10**, a Maharashtra family-with-toddler). The reason is structural, not a bug: a frequency model favours classes that are **common across all cohorts** (Dal-Roti is everywhere) over the **state-distinctive, persona-distinctive** classes that make a plan its own (Pitla-Bhakri for a Maharashtra household, Khichdi/child-mild plates for a toddler). Reproducing a *persona-specific* plan needs **composition, not frequency**.

The Founder directive this session, in two parts:

1. **Fix #5 first** — self-analyse / build a logic layer that maps **every** dish to its right meal class, acting as an **expert nutritionist and chef**. (Coverage was the ceiling: only 202/810 dishes had a class, so 608 dishes could never be surfaced or suppressed by any cohort plan.)
2. **Build the compositional derivation layer** — resolve persona (household_type + lifecycle_stage + health) → persona `boost_classes` as the **plan core** ∩ **State_Profile** regional pools + **City_Migration** overlay for migrants → filtered by **spine science** (spice ceiling, lifecycle, diet) → the cohort class plan, then dishes within classes.

WP-17 delivers both, wired through the **same additive, never-filtering** `S_cohort` seam:

- **`classify_dishes.py`** (nutritionist/chef classifier) → `dish_class_map.csv`: **810/810 dishes mapped** (up from 202), each tagged `method` (curated_exact / chef_rubric) + `confidence`. Coverage is no longer the ceiling.
- **`cohort_plan.py`** (compositional derivation) → `class_plan(theta, ctx)`: a graded, regionally-grounded, lifecycle-reshaped class plan composed **live from the masters**, not copied from any precomputed Cohort_Matrix row.
- **`cohort_intel.class_affinity`** now **fuses** the compositional plan (weight 0.70, primary) with the WP-16 learned model (0.30, smoothing) — the plate feels like the persona-DB plan while still generalizing.

**Benchmark result:** a MH/Pune dual-income family with a toddler (the S14_T1_P10 shape) now **self-arrives** at persona **P10 `family_with_toddler`** (match 1.0) and a plan led by child/mild classes grounded in Maharashtra regional classes (**Pitla-Bhakri, Coconut-Stew**) across all three main slots — exactly the target shape, derived not copied.

---

## 1. #5 — The nutritionist/chef dish→class classifier

### 1.1 The problem
The runtime cohort layer plans in **meal classes** (131 behavioural classes in `Meal_Class_Master_v3`). A dish only participates in a household's plan if it is mapped to a class (`knowledge.dish_to_class_code`). Prior coverage:
- 129 dishes — exact `Class_Dish_Options_v3` name match
- +73 dishes — WP16-F1 precision-safe unanimous-token overrides
- = **202/810 (25%)**; the other **608 dishes carried `S_cohort = 0.0`** and were invisible to the plan.

### 1.2 The approach (acting as expert nutritionist/chef)
`ghar_re_service/scripts/classify_dishes.py` reads each class's **authored profile** (slot, diet, heaviness, category, cooking style, region) and its **curated exemplar dishes** (`Class_Dish_Options_v3` + `Meal_Class_Master.example_dishes`) as ground truth, then scores every catalogue dish against every **slot-and-diet-compatible** class on:

1. **Exemplar token overlap** (idf-weighted) — the strongest signal; a class's exemplars *are* the expert's own examples of it, so a dish sharing their vocabulary belongs to the class. idf down-weights generic tokens (rice, masala) and up-weights distinctive ones (pitla, dhokla, litti).
2. **Hero-ingredient anchors** — a dish's *defining* ingredient dictates its class more than any regional/category hint (a chef classifies "Fish Curry" by the fish, not by it being a curry). Protein anchors (fish/chicken/mutton/prawn/egg) and veg anchors (paneer/rajma/chole/khichdi/dosa/…) give a strong boost to the matching class and a **penalty to wrong-protein nonveg classes** — so a fish dish can never land in a chicken class.
3. **dish_category → class-family alignment**, **heaviness match**, **regional cuisine grounding** (Maharashtrian → Pitla-Bhakri; Bengali → dal-bhaat/fish) as secondary/tie-break signals.
4. **Lifecycle/diet gating** — child/jain/fasting/infant/diabetic and add-on-only classes are only matched when the dish's own attributes support them (mild spice, soft, jain-compatible), so a general dish never lands in a member-specific add-on class.

### 1.3 Result & honesty
**810/810 mapped** (98 `curated_exact` reproducing authored truth, 712 `chef_rubric` derived, 87 low-confidence <0.4 — dominated by desserts/beverages/chutneys that legitimately don't anchor a main meal class). Every derived row is **diet-gated** (a test asserts no veg dish is chef-mapped to an egg/nonveg class). This is **derivation, not fabrication** (FD-11): each `chef_rubric` row is a transparent, deterministic consequence of the dish's own attributes matched against the authored class definitions, tagged with method + confidence for review. No runtime fuzzy matching — the classification is a reviewed, checked-in offline artifact.

---

## 2. The compositional cohort plan (`cohort_plan.py`)

`class_plan(theta, ctx) → {meal_class_code: [0,1]}` composes the plan exactly per the Founder's recipe:

1. **Resolve persona** live from theta — score all 41 `Persona_Master_v3` anchors on main-cohort, **lifecycle_stage** (weighted highest — it is what separates a toddler family from the family average), diet family, and time-pressure band; take the top-k blended by match fraction. No stored persona id; recomputed each call.
2. **Persona `{slot}_boost_classes` = plan core**, rank-weighted (the child-friendly / mild / regional classes the persona plans). Dinner also draws on the persona's LD boosts (a family eats lunch-type dishes at dinner too).
3. **∩ State_Profile pools** — the household's home-state slot class pool grounds the plan regionally; a class in **both** persona core and state pool is **reinforced** (the intersection — persona plan grounded in regional reality); a state-only class enters at a moderate regional-default weight. Nonveg households also draw the state's nonveg pool.
4. **+ City_Migration overlay** — national-modern overlay classes are added **only for a genuine migrant** (local state ≠ home state); a home-state resident's plan stays regionally pure (the WP-16.2 migrant-gating rule, reused).
5. **Spine science filter** — a class-level **diet gate** (veg households never plan an egg/nonveg class; dish-level filters still enforce per dish) and a **lifecycle/heaviness reshaping**: for infant/toddler/school_child/elder households, mild/child/soft/light classes are boosted and heavy/rich/indulgent classes demoted; a heaviness ceiling (senior present) demotes heavy classes. This is the "enhanced computation" that makes the plan lead with the right shape rather than the regional average.
6. **Normalize** top class to 1.0.

### 2.1 Fusion with the learned model
`cohort_intel.class_affinity` now returns `fused = 0.70·compositional + 0.30·learned`, normalized. The compositional plan carries the persona-specific, regionally-grounded **structure** a frequency model washes out; the learned model keeps the plan **graded and generalizing** over classes the composition doesn't name. Weights live in `cohort_weights.yaml` (`class_plan.compositional_weight / learned_weight`); the feature degrades cleanly to learned-only if the block is absent.

---

## 3. The seven masters, and how each is used (Founder's §1–§7)

| # | Master | Role in WP-17 |
|---|--------|---------------|
| 1 | Main_Cohort_Hierarchy | household_type → MC1–5 (persona resolution key) |
| 2 | Subcohort_Routing / sub-cohort | resolved compositionally from theta (lifecycle + diet + time-pressure), not looked up |
| 3 | Persona_Master (own) | the **plan core** — `{slot}_boost_classes` per resolved persona |
| 4 | State_Profile + City_Migration | regional grounding (∩ pools) + migrant overlay |
| 5 | Meal_Class_Master | class attributes drive the classifier (#5) **and** the spine-science reshaping; audited — every one of the 810 dishes is now scientifically class-mapped |
| 6 | Class_Dish_Options | authored exemplars = the classifier's ground truth (curated_exact precedence) |
| 7 | Cohort_Matrix (target) | **not copied** — the plan is composed from #3/#4/#5 and validated *against* S14_T1_P10, which the engine self-arrives at |

---

## 4. Validation

- **Benchmark (S14_T1_P10):** MH/Pune couple + toddler, veg → resolves **P10 family_with_toddler (1.0)**; lunch plan leads `LD_CHILD_MILD_PLATE` and carries `LD_MAHARASHTRIAN_PITLA_BHAKRI`; dinner leads `DN_CHILD_FRIENDLY_DINNER` / `DN_LIGHT_DAL_RICE`. Mild/child/traditional-Maharashtrian classes lead across all slots.
- **Tests:** 43 core (incl. 7 new `test_cohort_plan.py` + updated coverage/affinity tests) + 62 service — all pass. Golden master regenerated (4 cases incl. `couple_toddler_pune`, `migrant_bihar_mumbai`).
- **Gates:** ruff (both packages) + ruff format + mypy (35 files) + `export_bundle --check` — all green. Bundle rebuilt with `dish_class_map.csv`, old `dish_class_overrides.csv` retired.
- **Per-user logs:** `ops/logs/session-log/{test_10,test_13,test_14}.md` regenerated, now showing resolved persona + compositional plan + fused affinity.

---

## 5. Critical Self-Review

- **Is this a copy of the excel?** No. The plan is composed from the authored *masters* (persona boost classes, state pools, migration overlay, class attributes) resolved live from theta. Cohort_Matrix is the *target we validate against*, never read at runtime.
- **Is the classifier fabrication?** No. `curated_exact` reproduces authored truth; `chef_rubric` is a deterministic attribute-derived classification tagged with method + confidence, diet-gated, reviewable in the checked-in CSV. Low-confidence rows are honestly flagged, not hidden.
- **Does it over-fit S14_T1_P10?** The compositional logic is generic (any persona × any state × any lifecycle); S14_T1_P10 is one validated instance. The migration and diet tests cover other shapes (MP-in-Mumbai migrant, veg gate).
- **Known gaps (honest):** (a) the 87 low-confidence dish mappings are mostly support dishes — acceptable (they contribute weak `S_cohort`), reviewable in the map; (b) `feedback_events` still has 0 rows, so `w_cohort_effective` = cold-start for every live household (the decay mechanism exists, the data to move along it does not — same WP-14/15/16 constraint); (c) DN_ behavioural classes have few catalogue dishes, so dinner dishes mostly resolve via LD classes (by design — LD classes are in the state dinner pool).

---

## 6. Versioning & Placement

New (this WP): `ghar_re_core/cohort_plan.py`, `ghar_re_service/scripts/classify_dishes.py`, `data/source/class_first_v1/dish_class_map.csv`, `ghar_re_core/tests/test_cohort_plan.py`, `cohort_weights.yaml` `class_plan` block, `config.class_plan_weights`. Modified: `cohort_intel.class_affinity` (fusion), `knowledge.dish_to_class_code` (map source), `session_log.py` (compositional sections), `export_bundle.CLASS_FIRST_FILES`, `prepare_cohort_intel.main`. Retired: `dish_class_overrides.csv`. Placement validated against CLAUDE.md Folder Structure; no new top-level folder (no RACR needed).

---

## Founder Sign-off

