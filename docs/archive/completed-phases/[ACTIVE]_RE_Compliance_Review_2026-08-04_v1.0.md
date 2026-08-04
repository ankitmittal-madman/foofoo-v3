# Ghar RE v1.0 — Compliance Review & Gap Closure (2026-08-04)

**Status:** ACTIVE — completed engineering review, filed under `docs/archive/completed-phases/`
per this repo's active/archive documentation policy (`docs/active/`). Cross-reference:
`docs/active/OPEN_ITEMS.md` (item P1-6, cosine-distance wiring) is now resolved by this review's
Item 2 fix.

**Scope:** Close genuine implementation gaps against the frozen Core Spine only. No redesign,
no new features, no production/database integration (FD-RE-001 respected throughout — the
isolated `ghar_re_core`/`ghar_re_service` implementation is the only thing touched; no production
Supabase table was read or written for this review).

---

## Review findings and actions

| # | Item | Status | Reason | Evidence | Files changed | Risk |
|---|---|---|---|---|---|---|
| 1 | Scoring formulas | **PARTIAL → FIXED (Category A)** | `_cuis(x,S)` implemented only 3 of the spec's 4 graded tiers (1.00/0.40/0.0), missing the 0.70 "same parent_cuisine" tier. The spec's 0.15 "adjacent zone" tier requires a zone-adjacency table that exists nowhere in any frozen source — implementing it would mean inventing data, which the task explicitly forbids, so it is **not implemented** and is flagged as a genuine Founder-Decision item (Category B), not silently applied. | Spec `ghar_re_v1_0_core_spine_FROZEN.md:297-301`; code `ghar_re_core/scoring.py::_cuis()` | `ghar_re_core/scoring.py`, `ghar_re_core/knowledge.py` (added `CUISINE_STATE_ORIGIN`/`CUISINE_PARENT`, transcribed verbatim from `data/source/cuisines_v4.csv`, not invented) | Low — additive branch only, golden-master unaffected (none of the 39 golden-sample dishes hit the new tier) |
| 1b | `m_season` monsoon branch | **FAIL → FIXED (Category A)** | Spec: "monsoon -> +1 rainy/comfort, 0 else" (line 318) — a non-rainy dish must score 0, not the 0.5 neutral default the code returned. | Spec line 318; code `scoring.py::m_season()` | `ghar_re_core/scoring.py` | Medium — real scoring-value change; golden-master regenerated, diff reviewed (one household's monsoon-context plate scores changed) |
| 2 | Pairing similarity (`same_base`) | **FAIL → FIXED (Category A)** | Spec (line 555): `same_base(d,l) = cosine(base-ingredient vectors) > theta_base` (theta_base=0.6, line 641). Code used a hand-written coconut/dal/tomato-onion set-intersection proxy instead — a different, simplified heuristic, not the frozen formula. Replaced with the real IDF-weighted cosine gate; `theta_base` added to `pairing_rules.yaml` at its spec-given value (not invented). | Spec lines 555, 641; code `ghar_re_core/pairing.py::same_base()` | `ghar_re_core/pairing.py`, `ghar_re_core/config.py`, `data/source/pairing_rules.yaml` | Low — golden-master unaffected (verified identical output on the 39-dish sample both before and after) |
| 3 | Weather scoring | **PASS — no change** | Signed boost directions/conditions for rain/heatwave/cold-snap, the household's-own-comfort-hero resolution rule, and `PRIOR[zone][slot]`'s separateness from `m_weather` all match the frozen formula exactly. | Spec lines 342-348; code `scoring.py::m_weather()`, `_comfort_heroes_for()` | None | N/A |
| 4 | D1-D7 field schema | **PASS — no change** | The companion frozen doc (`ghar_re_v1_0_derivation_D1_D7_FROZEN.md`) defines the required field shape as `value/confidence/source/kind/stability/version/timestamp` — the code's `field()` helper produces exactly these 7 keys under these exact names. No naming mismatch exists; the task's hinted possibility of one did not hold up on inspection. | Spec companion doc lines 29-39; code `ghar_re_core/derivation.py::field()` | None | N/A |
| 5 | Explanation generation | **FAIL → FIXED (Category A)** | Of the 6 required explainable things, only eligibility (as an aggregate funnel) and plate-level winners/alternatives were surfaced. BASE contributors, Q15 contribution, weather contribution, and pairing contribution were all computed internally (via `Contribution` objects, `gain_q15()`, `m_weather()`, `compat()`) but discarded before reaching any object handed back to a caller. Added `scoring.explain_dish()`/`explain_eligibility()` and `pairing.explain_pairing()` — new, additive, read-only functions that call the exact same scoring functions (never recompute or approximate), and wired them into `decision_log.build_decision_trace()` as an opt-in `winners[i]["explanation"]` field (only populated when the caller supplies `theta`+`idf`, which `assemble_7(with_trace=True)` now does) so no existing caller's trace shape changes. | Task item 5; code `ghar_re_core/decision_log.py`, `modules.py::Contribution` | `ghar_re_core/scoring.py`, `ghar_re_core/pairing.py`, `ghar_re_core/decision_log.py` | Low — strictly additive; `LOGGING-ONLY` guarantee preserved (never influences scoring/ranking/filtering) |
| 6 | Test coverage | **Expanded (Category A, frozen behavior only)** | Added 11 tests covering: the new 0.70/1.00/0.0 `_cuis` tiers, `theta_base` config value, the corrected monsoon branch (both rainy and non-rainy cases), `explain_eligibility`'s rejected-filter reporting, `explain_dish`'s numeric agreement with the live `base()`/`gain_q15()`/`m_weather()` computations, `explain_pairing`'s agreement with live `compat()`/`same_base()`, and the decision-trace's opt-in explanation shape. No tests added for anything in the Do-Not-Implement list. | — | `ghar_re_core/tests/test_pipeline.py` | None |
| 7 | Schema | **PASS — no change** | Every DB object the frozen core-spine doc itself names (`allergen_hidden_derivative(s)`, `calories`, `dish_macro`, the substitution/variant graph with its named `veg_swap`/`jain`/`vegan` types) exists in the migrations under names that reconcile cleanly with the spec's own naming. Per FD-RE-001, no production table was touched or even queried for this review — this check was against migration files only. | Spec lines 244, 269, 601, 690-693; `database/migrations/034_...sql`, `036_...sql` | None | N/A |

## Category B — Founder Decision (left unchanged, flagged only)
- **`cuis(x,S)`'s 0.15 "adjacent zone" tier** — cannot be implemented without a zone-adjacency table, which exists in no frozen source. Needs a Founder-authored adjacency definition before this can be closed; not guessed at here.
- **The frozen spec's master score equation does not name `s_cohort`/`s_foreign`** (`w_cohort=0` in v1/v2 per the spec) — the shipped code has both active and non-zero in v1. This is a pre-existing architectural decision from before this review (already ratified elsewhere per this repo's own governance record, FD-19) — noted here as a cross-check, not re-opened or touched.

## Category C — Future Roadmap (untouched, status only)
Per the Do-Not-Implement list, the following exist in code exactly as before, confirmed untouched this session: `s_pref` personalization (wired, numerically inert — `enabled: false`), cohort learning (already live in v1, a pre-existing architectural fact, not modified here), D7 latent (still `{}`), production analytics/feedback collection, nutrition expansion, festival/health-condition recommendation, variant-graph population (schema exists, still near-empty), production API/frontend/Supabase wiring.

---

## Verification run this session

```
$ python -m pytest ghar_re_core ghar_re_service -q
190 passed

$ python -m ghar_re_service.scripts.export_bundle --check
[build_catalogue] 810 dishes transformed.
[build_catalogue] incomplete ING-blocks: 0
[build_catalogue] unresolved cuisines: 0
[build_catalogue] sig_band matched from sig_scores_v1.csv: 810; unmatched (join failed): 0
OK: bundle is current
```

No production database was queried or written for this review (FD-RE-001).

## IMPORTANT — process anomaly, not part of the requested work

While this review was in progress, a concurrent process (not invoked by me, not part of this
task) committed and **pushed to origin/main** (commit `c1ab212`) a change that included some of
the same files this review was editing (`scoring.py`, `knowledge.py`, `pairing.py`, a golden-master
file, `pairing_rules.yaml`). This happened without my running `git commit` or `git push` — the
repository shows evidence of another active session working in this same directory. **The
explicit instruction for this task was "Do NOT push to main"; I have not pushed anything myself,
but main already contains a push I did not make and cannot undo without risking other people's
work.** I stopped short of committing my own remaining changes (see `git status`) specifically
because of this — they are left as an uncommitted working-tree diff, exactly as the stop
condition requires ("wait for Founder review before any additional work"). This needs your
attention independently of the review findings above: someone or something else has push access
to `main` and is using it while this task was running.
</content>
