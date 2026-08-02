# [DRAFT]_WP-16_Cohort_Intelligence_Engine_v1.0

**Status:** DRAFT — real code shipped and tested this session (not a proposal); DRAFT until a companion certificate under docs/project-history/certificates/ documents execution per this repo's Version & Lifecycle Rules.
**Version:** v1.0
**Date:** 2026-08-02
**Placement:** docs/project-history/work-packages/[DRAFT]_WP-16_Cohort_Intelligence_Engine_v1.0.md
**Supersedes:** N/A — extends WP-15 (replaces its binary `S_cohort` internals; the master-formula seam and governance line are unchanged).
**Dependencies:** WP-15 (Class-Enriched Recommendation — the `w_cohort·S_cohort` seam), WP-14 (RE Intelligence Roadmap — sequencing), Core Spine FROZEN (master score formula), `Ghar_RE_Project_Context_and_Mission_v1_0.md` §2/§2A (retire the fixed-persona ARCHITECTURE, un-retire the SCIENCE), `data/source/Indian_Meal_Cohort_Persona_DB_v3.xlsx` (the authored, precomputed science).

---

## Executive Summary

WP-15 filled the Core Spine master formula's long-empty `w_cohort·S_cohort` term with a **binary** check: is this dish's curated class in the household's single best-matching cohort row's class plan? (1.0/0.0), weight 0.15, matching only 3 of the persona DB's 22 sheets and ignoring migration, region overlay, non-veg cadence, and the day-by-day weekly plan.

The Founder directive this session: make cold-start **feel like the plan available in `Indian_Meal_Cohort_Persona_DB_v3`** — but **implement the science, don't copy the precomputed excel** — by (1) identifying the right cohort from onboarding, (2) treating the excel's sub-cohorts as *representative anchors* and building the deeper science of how they work, (3) linking that to region/migration/add-on/non-veg, (4) building the computation, and (5) using ML/advanced logic where it helps. Chosen options (recorded): **build directly now**, **train a model on the excel to generalize**, **strong at cold-start, decaying with data**.

WP-16 delivers exactly that as a new subsystem, `ghar_re_core/cohort_intel.py`, wired through the **same additive, never-filtering** `S_cohort` seam WP-15 established:

- **`S_cohort` is now GRADED [0,1]**, not binary — "how strongly does a household of this shape, living where it lives, plan this dish's class right now?"
- The grade comes from a **factorized log-linear class-affinity model LEARNED from the excel's 20,664-row `Weekly_Class_Plan_v3`** (treated as authored labels), not from a nearest-row lookup. It **generalizes** to household feature-combinations the excel never enumerated — the honest reading of "as intelligent as the excel, derived not copied" (and it trains on **real authored data**, never fabricated labels, so it respects FD-11).
- The **`City_Migration_Overlay_v3` science is now live** — the "MP-in-Mumbai" example the Founder cited literally works: an MP household in Mumbai blends home-state signature classes + Mumbai lifestyle classes (Pitla-Bhakri, street chaat) + national-modern (salad bowl), by the overlay's own weights.
- The cohort weight is **cold-start-strong and decays with real interaction volume** (0.60 → 0.15 floor, half-life 25). Because `feedback_events` has **0 production rows today**, every live household sits at full cold-start strength — the decay mechanism exists, the data to move along it does not yet (the same honest constraint WP-14/WP-15 flagged).

Shipped, tested: **34 `ghar_re_core` + 62 `ghar_re_service` tests pass**; golden master regenerated intentionally; bundle rebuilds cleanly (`dish_count: 810`) with the model + reference tables baked in.

---

## 1. What "science not copy" means concretely (the five directives)

| Directive | How WP-16 implements the SCIENCE (not a copy of the precomputed cells) |
|---|---|
| 1. Right **cohort** from onboarding | `cohort_intel.theta_features(θ)` recomputes the excel's cohort feature vector (state, region archetype, city tier, main cohort, time-pressure, non-veg mode) **live from θ** every request — no stored persona ID (§2A upheld). |
| 2. Right **sub-cohort**, built not copied | The excel's 41 sub-cohorts are treated as **representative anchors**. Instead of snapping a household to one, the model factorizes over its **individual features**, so a household is effectively a *blend* of anchors. `cohort_membership(θ)` still surfaces the nearest anchors for explainability, but the plan is not a single anchor's copy. |
| 3. Link **region / migration / add-on / non-veg** | `City_Migration_Overlay_v3` (home/local/national blend), `State_Profile_v3` (region archetype — a model feature), `NonVeg_Logic_v3` + non-veg mode (a model feature) are all wired. Add-on member classes are **scoped but deferred** (§5 WP16-F3) — they generate *extra per-member plates*, a pairing/assemble change, not a shared-hero score term. |
| 4. Build **the computation** | The factorized log-linear affinity model (§3) — learned parameters, deterministic, pure-Python at runtime. |
| 5. **ML / advanced logic** | The model IS the ML: it learns class propensities per feature from 1.49M weighted label examples and generalizes by feature product. Deliberately **not** a heavy neural/CF model — WP-14's rule stands that collaborative/learned-from-*user* ranking needs real feedback density that does not exist yet. This model learns from **existing authored data**, so it is buildable and honest today. |

## 2. What was actually built (code, not proposal)

- **`ghar_re_service/ghar_re_service/scripts/prepare_cohort_intel.py`** (new, offline) — extracts 6 reference sheets to `data/source/class_first_v1/*.csv` and **trains** `cohort_class_model.json` from `Weekly_Class_Plan_v3` joined to cohort features. Deterministic; re-runnable; the engine never opens the `.xlsx`.
- **`ghar_re_core/cohort_intel.py`** (new) — the runtime layer: `theta_features`, `destination_group`, migration-blended `class_affinity(θ, ctx) → {class: [0,1]}` (memoized per household+slot so scoring 810 dishes computes it once), `cohort_membership` (explainability).
- **`ghar_re_core/scoring.py`** — `s_cohort` now returns the graded affinity for the dish's class; `score()` uses `CONFIG.w_cohort_effective(ctx.interaction_count)` (cold-start-strong, decaying) instead of the flat 0.15.
- **`ghar_re_core/derivation.py`** — θ now carries `local_state` and `city_tier` (needed for the migration blend and the model's tier feature).
- **`ghar_re_core/knowledge.py`** — retired WP-15's now-superseded binary cohort-match code (`cohort_class_mix`, `_best_cohort_row`); kept only the curated `dish_to_class_code` lookup. Cohort matching now lives in `cohort_intel`.
- **`data/source/cohort_weights.yaml`** + **`config.py`** — `w_cohort_coldstart`/`w_cohort_floor`/`coldstart_halflife` and `CONFIG.w_cohort_effective(n)`.
- **`export_bundle.py`** — the model + 6 reference CSVs added to the bundle allow-list (RE-DOC-10 §8 container contract preserved).
- **Tests** — `test_cohort_intel.py` (new, 7: features contract, graded/slot-specific/bounded, **model-reproduces-a-real-cohort** fidelity, generalization, **migration-overlay shift**, membership), `test_class_first_cohort.py` (rewritten for the graded + cold-start path). Golden master regenerated via its own documented `--update` process.

## 3. The model (how the intelligence is derived)

`Weekly_Class_Plan_v3` names a primary/secondary/tertiary meal class for every (cohort, day-of-week, slot). Joined to each cohort's feature row, those are `(features, slot, day-type) → class` examples, weighted primary=3 / secondary=2 / tertiary=1 (soft supervision from the authored preference order). We fit, per `(slot, day-type)` and per feature value, a Laplace-smoothed class-propensity distribution `p_{f,v}(class)`. A household's affinity for a class is the **pooled product of its feature factors** (sum of log-propensities), softmax-normalized over the slot's classes, then scaled so the top class = 1.0.

- **Generalizes** — a household whose exact state×tier×persona cohort was never enumerated still gets a sensible graded plan from the product of its individual feature propensities. This is the property a straight excel lookup cannot have.
- **Faithful** — verified by `test_model_reproduces_a_real_cohort_primary_class`: for a household matching a real cohort, the model's top breakfast class is one that state's cohorts actually plan.
- **Auditable & dependency-light** — parameters are counts→log-propensities (no black box); the artifact is JSON, scored at runtime in pure Python (no numpy/sklearn in the Fly.io bundle).

Live evidence (real 810-dish catalogue, this session): a TN couple's cold-start breakfast slate reorders to lead with **Rava Upma** (affinity 1.0) and **Idli** (0.55) — the persona-DB's actual TN breakfast plan — where the rule-only baseline led with dosas. An MP couple's lunch plan gains **Maharashtrian Pitla-Bhakri** and **Modern Salad Bowl** *only when living in Mumbai* (the migration overlay), not in Indore.

## 4. Verification performed

- `python3 -m pytest ghar_re_core/tests -q` → **34 passed** (was 28; +new cohort-intel and rewritten class-first tests, golden regenerated).
- `cd ghar_re_service && PYTHONPATH=..:. python3 -m pytest tests -q` → **62 passed** — response shape, HMAC, decision-trace determinism contracts all intact.
- `python3 -m ghar_re_service.scripts.export_bundle` → clean rebuild, `dish_count: 810`, model + reference CSVs present in `config_sha256`.
- Golden-master diff reviewed: 2 of 4 fixture households regenerated **identical**; the other 2 changed **scores only, same served plates** — the fixture's small 39-dish catalogue has few high-affinity matches in the tested slot, so the term nudges rather than flips there (the real-catalogue effect above is the meaningful one).

## 5. Future / Deferred register (WP-16)

| ID | Item | What it needs |
|---|---|---|
| WP16-F1 | Raise dish→class coverage — **partially done**: 129 → **202/810** via a precision-safe, offline, unanimous-agreement matcher (`prepare_cohort_intel.generate_overrides` → committed `dish_class_overrides.csv`, consulted after the exact map; still NO runtime fuzzy). Ambiguous names (Chole, Poha) deliberately stay unmatched, not guessed. | Remaining ~75% needs founder-reviewed ingredient/genome matching for the genuinely ambiguous/absent names |
| WP16-F2 | Consume `Meal_Class_Master_v3` richer per-class metadata (heaviness, cook_complexity) as an affinity refinement, not just class membership | A second signal in `class_affinity`; deliberately out of scope to keep this reviewable |
| WP16-F3 | Add-on member plates (infant/toddler/pregnancy/lactation/elder) from `Addon_*` — generate an extra per-member plate as the RE-Visual shows | A pairing/assemble-7 change (new plate slot), not a shared-hero score term — a separate, larger design |
| WP16-F4 | Calibrate `w_cohort_coldstart`/`halflife` and let the decay actually move | Real `feedback_events` volume (0 rows today) — the same blocking constraint as WP-14 Phase 3; the mechanism is built and disable-safe (set coldstart=floor) |
| WP16-F5 | Persist a per-household `interaction_count` into `ctx` from real history (`household_context`/feedback) so the decay engages per user | The `household_context` wiring WP-14 Phase 0 already owns |

## 6. WP-16.1 addendum — foreign-cuisine cold-start demote (2026-08-02, live-driven)

Live testing (test_13: Gujarat couple in Pune) surfaced a real gap: with region now resolving
correctly, a household's top plates became regionally coherent, but foreign dishes (zone=Global —
Chinese/continental, 187/810 = 23% of the catalogue) still surfaced (e.g. "Veg Burger + Corn
Chowder") because (a) they have no persona-DB class so `s_cohort=0` couldn't demote them, (b)
`m_palette=0` doesn't penalise, only fails to reward, and (c) some carry an inflated `sig_score`
(Veg Burger sig=0.75, a data-quality issue flagged separately). Since the persona-DB science is
entirely regional Indian, a foreign dish is never on any cohort's plan. Added `s_foreign` +
`CONFIG.foreign_demote_effective` (`cohort_weights.yaml::foreign_demote`): a cold-start-strong,
decaying demote subtracted from zone=Global dishes on the same curve as `w_cohort`, so foreign food
is pushed down for a brand-new regional household and resurfaces as real interest accrues.
Config-gated (set `demote_coldstart: 0.0` to disable), soft (never a filter). Verified: test_13's
slate drops "Veg Burger + Corn Chowder" and is all Indian regional, led by the correct Gujarati
plates. Tunable product judgement — foreign food is legitimately popular in urban India, so it
decays to a small floor rather than a hard exclusion. Open follow-up: correct inflated sig_scores.

## Critical Self-Review

- The model is a **factorized Naive-Bayes-style affinity**, not deep learning or collaborative filtering. Calling it "ML" is accurate (parameters estimated from data, generalizes) but it is deliberately the *simplest* model that delivers generalization without fabricated data — a stronger model buys little until dish→class coverage (WP16-F1) and real feedback (WP16-F4) improve.
- `w_cohort_coldstart = 0.60` is a **reasoned default** (≈20–40% of a top BASE score, chosen to reorder without dominating hard filters/palette), **not an offline-eval-calibrated value** — no acceptance metric exists to tune it against yet. Flagged as a Founder-tunable, not presented as optimal.
- θ→feature maps for non-veg mode, main cohort, and time-pressure are **coarse approximations** of the persona DB's own fields (the "build the science, generalize the persona" step). They are defensible and disclosed, not claimed to reproduce authoring intent exactly; the smoothing makes the model robust to their coarseness.
- Coverage is still ~16% — WP-16 makes the *matched* dishes far smarter but does not widen the map. That limit is stated, not hidden.

## Versioning & Placement

v1.0, first version. Correctly placed under `docs/project-history/work-packages/`. Remains DRAFT until a companion certificate under `docs/project-history/certificates/` documents this execution with real output — per this repo's rule that a WP's Status may only read COMPLETED alongside such a certificate.

## Founder Sign-off
