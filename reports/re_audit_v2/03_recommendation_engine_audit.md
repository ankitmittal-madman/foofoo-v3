# Recommendation Engine Audit (fresh, 2026-08-04)

Spec: `docs/architecture/ghar-re/ghar_re_v1_0_core_spine_FROZEN.md` (read in full). Implementation:
`ghar_re_core/*.py` (read in full for scoring/derivation/pairing/preference/exploration/similarity/
pipeline/meal_planner/cohort_intel; knowledge.py read for its data tables).

| # | Area | Status | Evidence |
|---|---|---|---|
| 1 | Household derivation (D1-D7) | Implemented | `derivation.py:52-241`, D7 correctly pinned empty per spec |
| 2 | Hard filters/eligibility | Implemented | `scoring.py:16-159`, A1-A6 all present |
| 3 | BASE scoring | Implemented | 7 W_k modules + prior_boost, registry-wrapped, score-neutral |
| 4 | Pairing/meal-class distance | **Partially implemented / different from spec** | `same_base()` is a set-intersection proxy, not the spec's IDF-cosine `d(a,b)`; the real cosine machinery exists (`similarity.py`) but is wired only to a separate discovery helper, not into pairing or the meal-class distance the spec defines it for |
| 5 | Q15/gain | Implemented (v1 scope); kappa-decay correctly absent (v2, spec-deferred) |
| 6 | Assembly (assemble-7) | Implemented, plus an undocumented-in-spec exploration swap (additive, safe-defaulted to no-op) |
| 7 | Ranking/final score | Implemented, extended beyond frozen spec's v1 default (`s_cohort`/`s_foreign` are non-zero, spec says `w_cohort=0` in v1) — a real, disclosed deviation |
| 8 | Personalization (`s_pref`) | **Stubbed** — wired into scoring as a real registry phase, confirmed numerically 0.0 (`enabled: false`, only `NullModelArtifactProvider` ever constructed) |
| 9 | Feedback loop | **Stubbed/dead in production** — full training CLI exists, unit-tested, never run against real data (0 rows historically, 9 rows as of this session's live check — still below any reasonable training threshold) |
| 10 | Cold start | Implemented — `rho_disc`, `cold_start_top15()`, cohort_intel affinity blending, all real and live |
| 11 | Weather-awareness | Mocked/injected by design, confirmed at both `ghar_re_core` and `ghar_re_service` layers — no live weather API call exists anywhere |
| 12 | Comfort-hero mapping | **Partially implemented** — 39 KB rows / 36 distinct hero names, only **17 (47%)** resolve to a real dish in the 810-dish catalogue (reconciled count, verified directly this session) |
| 13 | Knowledge graph/ontology in `ghar_re_core` | Tabular only — flat dicts/lists (`ZONE_MAP`, `CUISINE_GROUP_MAP`, `PRIOR_ZONE_SLOT`, etc.), no node/edge graph structure anywhere |
| 14 | Seed data in the engine | Implemented — 810 real dishes in the baked bundle, full documented field set present (macros mostly null, matching the spec's own known gap) |
| 15 | Explainability | Implemented at plate/alternatives level (`decision_log.build_decision_trace`, real rejection reasons); per-module BASE contribution breakdown exists in code (`modules.Contribution`) but isn't threaded into the externally-visible trace payload |
| 16 | Exploration/diversity | Implemented as epsilon-greedy class-level swap (real, live, non-zero production default); the frozen spec's v2 four-axis diversity/bandit machinery is correctly absent (spec marks it OPEN) |

## Test health (executed this session)
```
python3 -m pytest ghar_re_core/tests/ -q   → 111 passed
python3 -m pytest ghar_re_service/tests/ -q → 69 passed
```
Both orderings of the previously-flagged `test_calibration.py`/`test_golden_master.py` interaction
were run explicitly this session and passed cleanly — no flakiness observed in this run, but treat
as a known historical risk, not a cleared one.

## Single most consequential finding
The gap between "the cosine-similarity code exists" and "the cosine-similarity code is used where
the spec says it should be" (item 4) is the most concrete, fixable algorithmic gap found. It does
not affect current test-passing status (golden-master locks the current proxy behavior), but it
means the frozen spec's own documented meal-pairing-quality mechanism is not actually running.
</content>
