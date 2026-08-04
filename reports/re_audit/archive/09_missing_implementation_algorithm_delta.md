# RE Delta Audit — since db22b6b (RE-DOC-12), Phase 2 items 3-7

Baseline: RE-DOC-12 (2026-07-29, commit `db22b6b`). Commits since: `git log --oneline db22b6b..HEAD
| wc -l` → **195 commits**. Tests: `python3 -m pytest ghar_re_core/tests/ -q` → **93 passed**, no
failures (run on HEAD, repo working tree at session start had only `compose.ts`/`served.ts` modified
— not touched by this audit).

## 3. Does cold-start feedback persistence + s_pref training close the "personal history learning"
   loop (w_history weight ladder)? Is there real bandit exploration wired into the live path?

**No — the personal-history *scoring* loop is still closed, by design, today.** The feedback
persistence pipeline is real and end-to-end (household_context / feedback plumbing → JSONL export →
`ghar_re_core/training/dataset.py` → `train_pref_model.py` → joblib artifact), and it is honestly
gated rather than faked:

- `ghar_re_core/preference.py:11-19` — `s_pref()` returns `0.0` if EITHER `CONFIG.pref_model_enabled`
  is `False` OR `ghar_re_core.model_provider.active_model().artifact is None`.
- `data/source/pref_model.yaml:9` — `enabled: false` (current committed value).
- `ghar_re_core/model_provider.py:33-45` — `NullModelArtifactProvider` is "the ONLY provider actually
  in use anywhere" per its own docstring; `FileModelArtifactProvider` exists as a seam but nothing in
  the repo constructs one against a real path (`model_provider.py:54-55`).
- `ghar_re_core/training/dataset.py:150-174` (`check_training_readiness`) + `pref_model.yaml:31-33`
  (`training_readiness: min_real_events: 10000, min_households: 500`) — the training CLI refuses to
  fit below this density; `train_pref_model.py:14-17` states it "is never invoked against real
  production feedback_events anywhere in this plan."

So: the persistence *plumbing* (`household_context` writes, `dish_feedback_counts` in ctx) exists and
is live (see §4), and the *training pipeline* is real code (not a stub file), but the actual
`w_history·PersonalHistory`-style scored term the older spec (RE-DOC-01-05) describes is **not
active** — `s_pref`'s registry weight (`modules_default.py:97-102`, reading `CONFIG.w_pref`, default
`0.0` per `pref_model.yaml:24-27`) makes this a "byte-for-byte no-op" per `scoring.py:435-440`'s own
docstring. This is a deliberate FD-11 (no fabricated labels) stance, not an oversight — but it means
the "personal history learning loop" the older docs describe is **built but not turned on**: Partial/
Deferred, not Implemented.

**Bandit exploration IS real and live**, but at the *selection* stage, not the scoring stage, and it
is genuinely epsilon-greedy (not Thompson Sampling — no Thompson/Bayesian-posterior code found
anywhere in the repo, confirmed by reading `exploration.py` in full and grepping for
`thompson|beta_dist|posterior` across `ghar_re_core/`, no hits):

- `ghar_re_core/exploration.py:68-160` (`epsilon_greedy_select`) runs AFTER `pairing.assemble_7`'s
  greedy ranking/selection (`pairing.py:232-237`), swapping the lowest-scored already-chosen plate for
  a candidate from a more under-served meal class, gated by `CONFIG.bandit_epsilon`.
- `data/source/bandit_weights.yaml:11` sets `epsilon: 0.15` — a **non-zero production default**, not
  merely a test fixture value (the code-level *safety* default in `config.py` is `0.0` if the file is
  missing, but the file IS present and committed with `0.15`).
- Separately, `meal_planner._diversify()` (`meal_planner.py:115-156`) applies the same
  `CONFIG.bandit_epsilon` at the cold-start-top-15 / slot-options ranking stage, household-seeded via
  `rng` (`cold_start_top15`, `meal_planner.py:189-193`), confirmed by
  `test_cook_capability_bias_reorders_beginner_without_changing_scores` and the top15 exploration test
  referenced in `ghar_re_core/tests/test_meal_planner.py:49-53`.
- This exploration never touches `m_k(x)` scoring math (`exploration.py:1-19` docstring, confirmed by
  reading the function body: it only reorders/swaps already-scored, already-eligible plates).

**Verdict: exploration = Implemented and live in the default config; personal-history learning
(`w_history` weight ladder) = Deferred/inert-by-design, not closed.**

## 4. household_context wiring — was RE-DOC-12's "unwired, no writer" finding fixed?

**Fixed.** `supabase/functions/recommendations/compose.ts`:
- Line 373: `db.from("household_context")` is read (`loadLatestContext`, per the comment at
  `compose.ts:373` and cross-referenced in `handler.ts:53,59,154`).
- Line 484: `db.from("household_context").insert({...})` — an actual writer, in a function whose own
  docstring at `compose.ts:462` states: "Write the context a request actually used into
  `household_context` (§0.2)."
- `handler.ts:154,162` — the write is best-effort (`household_context.record_call_failed` warn-logged
  on failure, not a hard error), and the comment there explicitly frames it as making "the
  household's NEXT call find real history via loadLatestContext" — i.e. the read/write round-trip
  RE-DOC-12 found missing is now closed.
- `cook_capability` (the other half of the commit `e487941` message, "cook_capability ranking bias +
  household_context wiring") is also genuinely wired end-to-end: `database` schema
  (`supabase/functions/household/schema.ts:71`), profile fetch
  (`supabase/functions/recommendations/compose.ts:271,303`), passed into `ghar_re_core` and consumed
  by `meal_planner._apply_cook_capability_bias()` (`meal_planner.py:100-112`, invoked at
  `meal_planner.py:203`), with a dedicated end-to-end test
  (`ghar_re_core/tests/test_meal_planner.py:49-53,99-116`).

This closes the specific RE-DOC-12 gap ("household_context table unwired").

## 5. requireOwnership auth gap — still present, fixed, or unaddressed?

**Fixed.** `supabase/functions/recommendations/handler.ts:107` calls
`requireOwnership(claims, householdId)`, imported at line 15 from
`../_shared/auth/authenticate.ts`. The surrounding comment (`handler.ts:102-106`) explicitly frames
it as "the Sole Surface-B authorization boundary (DOC-P3-06 §05), same as consent/handler.ts: JWT
user_id must equal the target household id. Runs BEFORE any household/context data is fetched, so an
unauthorized caller supplying someone else's household_id never reaches compose.ts at all." This
directly closes RE-DOC-12's flagged auth gap (requireOwnership not called in the recommendations
handler).

## 6. G6 pairing bug in pairing.py — still there?

**Still there, and now explicitly documented/acknowledged in-code as a deliberate non-fix**, not a
silent regression. `pairing.py:99-110` (function `compat`, the G6 protein-veg balance soft term):

```
protein_cat = {"dal_lentil", "kebab", "egg_dish", "curry"}  # noqa: F841 — see note above
l_protein = bool(set(l.dish_category) & {"dal_lentil"}) or l.diet in ("non_veg", "egg")
```

`protein_cat` names four categories but the actual check (`l_protein`) only tests membership in
`{"dal_lentil"}` (plus a diet fallback) — three of the four named categories (`kebab`, `egg_dish`,
`curry`) never actually trigger the `b_protein` bonus unless the dish's `diet` field happens to also
be `non_veg`/`egg`. The comment block at `pairing.py:100-108` states this was "surfaced by ruff F841,
Phase C.5 — flagged, deliberately NOT fixed here" because widening the check "CHANGES SCORING OUTPUT
for affected plates — which is a reviewed recommendation-quality decision for the Founder, not a
lint cleanup," and that the golden-master test will fail loudly the moment someone does fix it. So:
bug confirmed still present, unaddressed in the sense of "not corrected," but now explicitly a
tracked/acknowledged decision rather than an unflagged defect.

## 7. Test run

```
$ python3 -m pytest ghar_re_core/tests/ -q
........................................................................ [ 77%]
.....................                                                    [100%]
93 passed in 3.13s
```
No failures, no errors, no skips. Run directly on the current HEAD state of the repo.

## Summary of the five delta findings

| Item | RE-DOC-12 finding | Current state |
|---|---|---|
| s_pref / w_history learning loop | N/A (didn't exist yet) | Built (real training pipeline + honest FD-11 gates), but numerically inert — `enabled: false`, `w_pref: 0.0`, only `NullModelArtifactProvider` ever constructed |
| Bandit/epsilon-greedy exploration | N/A (didn't exist yet) | Real, live, non-zero production default (`epsilon: 0.15`) — selection-stage only, applied both in `pairing.assemble_7` and `meal_planner._diversify`/`cold_start_top15` |
| household_context wiring | Unwired — no writer | Fixed — read (`compose.ts:373`) and write (`compose.ts:484`) both present, cook_capability also fully wired |
| requireOwnership auth gap | Not called | Fixed — called at `handler.ts:107`, before any data fetch |
| G6 pairing bug | Present | Still present; now explicitly documented as a deliberate, reviewed non-fix (not silently regressed) |
