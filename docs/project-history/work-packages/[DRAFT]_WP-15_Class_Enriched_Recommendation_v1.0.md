# [DRAFT]_WP-15_Class_Enriched_Recommendation_v1.0

**Status:** DRAFT — real code shipped and tested this session (not just proposed); DRAFT until a companion certificate documents execution per this repo's Version & Lifecycle Rules.
**Version:** v1.0
**Date:** 2026-08-02
**Placement:** docs/project-history/work-packages/[DRAFT]_WP-15_Class_Enriched_Recommendation_v1.0.md
**Supersedes:** N/A (additive to WP-14, not a replacement)
**Dependencies:** Core Spine FROZEN (master score formula's `w_cohort·S_cohort` term), RE-DOC-03 (class taxonomy science, retired as candidate-generation architecture — see §2), `Ghar_RE_Project_Context_and_Mission_v1_0.md` §2A (governance amendment, same date), `data/source/Indian_Meal_Cohort_Persona_DB_v3.xlsx` (previously unwired reusable data asset).

---

## Executive Summary

Asked to "revamp the entire recommendation" so the current, working `ghar_re_core`/`ghar_re_service` implementation is "powered with class-level science" from the retired RE-DOC-01–05 series, with **nothing retiring** — i.e. add, don't replace. The literal instruction to un-retire class-first science runs directly against `Ghar_RE_Project_Context_and_Mission_v1_0.md` §2 ("do not resurrect"), so this WP does not silently override that governance note — it amends it explicitly (§2A, same file, same date, old text kept verbatim per this repo's Version & Lifecycle Rules) and draws a precise line: **the class-taxonomy/cohort-prior SCIENCE is un-retired; the 41-FIXED-PERSONA, class-only-candidate-generation ARCHITECTURE §2 objected to stays retired.**

Concretely: the Core Spine FROZEN master formula (`score(x|θ) = BASE×GAIN_Q15 + w_pref·S_pref + w_cohort·S_cohort − PENALTY`) has carried a `w_cohort·S_cohort(x;cohort)` term since Spine v1.0 that was **never implemented** — `scoring.score()` computed only `BASE×GAIN_Q15` before this WP. That is the exact, already-frozen, already-approved seam this WP fills, using real class-taxonomy/cohort data (`Indian_Meal_Cohort_Persona_DB_v3.xlsx` — 41 personas, 131 meal classes, 2952 cohorts, 1050 curated dish→class rows) that has sat in `data/source/` since before this session, listed in the Project Context doc's own §4 "reusable data assets" table, and never loaded by any engine code until now.

This is a real, shipped, tested change — not a proposal. 91/91 tests pass (29 `ghar_re_core` + 62 `ghar_re_service`), the golden-master regression was regenerated intentionally per its own documented process, and the service bundle rebuilds cleanly with the new data included.

---

## 1. What "class-first science, nothing retires" means concretely here

| Retired-vision concept (RE-DOC-01–05) | Stays retired | Un-retired as |
|---|---|---|
| 41 FIXED personas, looked up by ID | **Yes — never reinstated** | A cohort matched **live from θ** every request (home_state + household_type + D2 time_route), never stored/looked-up by a persona ID (`knowledge._best_cohort_row`) |
| Class-first CANDIDATE GENERATION (household → cohort → class plan → dish pool, replacing the filter/score pipeline) | **Yes — never reinstated** | Class-fit is one additive score term (`scoring.s_cohort`), applied *after* the existing hard filters and *alongside* BASE×GAIN — never a gate, never a filter, never bypasses Assemble-7 |
| The interaction-count weight ladder (5 tiers) | Untouched — still not built (κ still pinned 1.0 per Spine v1) | Not addressed by this WP; remains open (see §5) |
| The 4-state DAU evolution model | Untouched — still superseded by RE-DOC-10's phase table | Not addressed by this WP |
| 26/131-class taxonomy as a real, curated science asset | — | **Un-retired**: `Meal_Class_Master_v3` + `Class_Dish_Options_v3` now drive `knowledge.dish_to_class_code()` |
| Cohort-level class *preference* (which classes a household of this shape actually eats, by slot/day-type) | — | **Un-retired**: `Cohort_Matrix_v3`'s per-slot/day-type `class_mix` columns now drive `knowledge.cohort_class_mix()` |

## 2. What was actually built (code, not proposal)

- `ghar_re_core/derivation.py` — added `theta["household_type"]` (a straight pass-through of the already-collected `q1_household_type`; D5 already used this raw field, it just wasn't carried into θ).
- `ghar_re_core/knowledge.py` — new class-first section: `dish_to_class_code(name)` (case-insensitive exact match against the curated 1050-row `Class_Dish_Options_v3` extract — **no fuzzy matching**, by design, so a coverage gap stays an honest 0 rather than a guessed class), `cohort_class_mix(theta, ctx)` (best-effort live cohort match by home_state + household_type keyword + D2 time_route → that cohort's slot/day-type class plan from `Cohort_Matrix_v3`).
- `ghar_re_core/scoring.py` — new `s_cohort(dish, theta, ctx)`: 1.0 if the dish's curated class is in the household's live cohort's class plan for this slot/day-type, else 0.0. Wired into `score()` as `+ CONFIG.w_cohort * s_cohort(...)`, filling the previously-empty `w_cohort·S_cohort` slot in the master formula.
- `ghar_re_core/config.py` + new `data/source/cohort_weights.yaml` — `CONFIG.w_cohort` (default **0.15**, deliberately modest given measured coverage — see §3).
- Data extraction: `data/source/class_first_v1/{meal_class_master,class_dish_options,cohort_matrix}.csv`, a one-time `openpyxl` extraction of the three relevant sheets from `Indian_Meal_Cohort_Persona_DB_v3.xlsx` (131 / 1050 / 2952 rows respectively) — the engine never opens the source `.xlsx` at runtime.
- `ghar_re_service/ghar_re_service/scripts/export_bundle.py` — the new `cohort_weights.yaml` and the `class_first_v1/` CSVs are added to the bundle allow-list and directory copy, so the service's baked-bundle contract (RE-DOC-10 §8: no filesystem dependency outside the bundle in a container) is not silently broken by this change. `knowledge.py`'s loader was written from the start to resolve paths via `ghar_re_core.config.SRC` (the existing `GHAR_RE_CONFIG_DIR`-aware seam), not a path relative to its own file — the same mistake that would have broken RE-DOC-10 §8's container contract for this new data.
- `ghar_re_core/tests/test_class_first_cohort.py` — new, 6 tests: known match/miss, slot-specificity, weekday/weekend variation, honest-zero for unmatched dishes, additive (not multiplicative) score contribution, and a coverage-rate floor check (100–160 of 810, measured 129) so a silent regression to 0 fails loudly without the test becoming brittle to unrelated catalogue edits.
- Golden master (`ghar_re_core/tests/golden/*.json`) regenerated via the test suite's own documented `--update` process — this is an intentional scoring change, visible as a diff in this session's commit, per that test file's own stated discipline.

## 3. Honest coverage disclosure (measured, not estimated)

Exact case-insensitive name match between `Class_Dish_Options_v3`'s 1050 curated dish rows and the real 810-dish catalogue (`ghar_re_service/data/bundle/catalogue.json`) finds a `meal_class_code` for **129 dishes (~16%)**. For the other ~84%, `s_cohort()` returns exactly 0.0 — the identical "an absent term contributes nothing" pattern `base()`'s `W_SIG` already uses for a dish with no curated signature score. This is disclosed, not padded: `w_cohort` is set to a modest 0.15 specifically because of this partial coverage, and the test suite locks the measured rate as a floor rather than asserting full coverage.

The `Cohort_Matrix_v3` cohort-matching itself is a **best-effort live match**, not an exact lookup: it filters by exact home-state match (36 states/UTs covered) and ranks candidates by keyword overlap on `household_stage` + a coarse `time_pressure` band derived from D2's `time_route`. It is not claimed to reproduce the original persona-authoring intent precisely — it is a defensible, disclosed heuristic, open to refinement (see §5).

## 4. Verification performed

- `python3 -m pytest ghar_re_core/tests -q` → **29 passed** (was 23 before this WP; +6 new).
- `cd ghar_re_service && PYTHONPATH=..:. python3 -m pytest tests -q` → **62 passed**, unchanged pass count — confirms the new term didn't break any service-level contract test (response shape, HMAC auth, decision-trace determinism, etc.).
- `python3 -m ghar_re_service.scripts.export_bundle` → bundle rebuilds cleanly, `dish_count: 810`, new `class_first_v1/*.csv` + `cohort_weights.yaml` present in `config_sha256`.
- Golden-master diff reviewed: only the `migrant_bihar_mumbai` case's plate scores changed (a small numeric shift from the new additive term) — the *set* of served dishes for all 4 golden households was manually spot-checked and did not change, meaning `w_cohort=0.15` is currently too small to flip rankings for these particular cases, only to nudge scores. This is consistent with the "nudge, not dominate" design intent in §3.

## 5. Future / Deferred register (WP-15)

| ID | Item | What it needs |
|---|---|---|
| WP15-F1 | Raise dish→class coverage above 16% | Founder-reviewed fuzzy/ingredient-based matching (deliberately NOT done automatically here — see knowledge.py's docstring on why exact-match-only is the safe default) |
| WP15-F2 | Use `Meal_Class_Master_v3`'s richer per-class metadata (heaviness, cook_complexity, weekday/weekend fit) as additional BASE signal, not just the binary class-membership check `s_cohort` does today | A second, separate BASE module registration — deliberately out of scope for this WP to keep the change reviewable |
| WP15-F3 | Replace the coarse household_stage-keyword + time_pressure-band cohort ranking with a more principled distance metric | Needs a defined similarity function and founder sign-off, since it changes which cohort (and therefore which class_mix) every household matches |
| WP15-F4 | Interaction-count weight ladder / κ(confidence) decay (from RE-DOC-04/05, still pinned 1.0 in Spine v1) | Real user feedback data — same blocking constraint WP-14 already identified; unrelated to this WP's scope |
| WP15-F5 | Add-on component classes (24 classes for kids/infants/elderly/pregnancy/recovery in the persona DB) | A separate design decision — these map to per-member add-ons, not the shared-hero plate `s_cohort` scores today; deliberately not touched here |

## Critical Self-Review

- This WP does not implement RE-DOC-03's class taxonomy as originally specified (26 classes, FinalScore formula) — it implements a *different, θ-matched* cohort layer using a *different, richer* real dataset (131 classes) that happened to already exist unwired in the repo. That substitution is a judgement call, stated plainly here rather than presented as "restoring RE-DOC-03."
- 16% coverage is a real, disclosed limitation, not a hidden one. `w_cohort=0.15` is a starting default, not a calibrated value — no offline eval was run to justify that exact number beyond "modest, given partial coverage."
- The cohort-matching heuristic (§3) is defensible but not validated against the original persona-authoring intent; treating its match as authoritative for anything beyond a soft score nudge would be overclaiming.

## Versioning & Placement

v1.0, first version. Correctly placed under `docs/project-history/work-packages/` per the Folder Structure rule (proposed/executed engineering work). Remains DRAFT until a companion certificate under `docs/project-history/certificates/` documents this execution with real output (test run counts, bundle hash) — per this repo's rule that a WP's Status may only read COMPLETED alongside such a certificate.

## Founder Sign-off

