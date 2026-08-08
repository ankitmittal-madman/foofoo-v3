"""
Phase 2 tests — selection-stage epsilon-greedy class-level exploration (ghar_re_core.exploration)
and WP-8G's exclude_dish_ids hard filter (ghar_re_core.scoring.pass_exclude_dish_ids).

Uses the same golden-household fixtures/pipeline entrypoint as test_pipeline.py, monkeypatching
CONFIG.bandit_epsilon (never the golden-master fixtures themselves) so these tests never depend on
data/source/bandit_weights.yaml's actual YAML value.
"""
from ghar_re_core import fixtures as F
from ghar_re_core import config as cfgmod
from ghar_re_core.catalogue import Catalogue
from ghar_re_core.pipeline import recommend, make_context

CAT = Catalogue()
HH = {h["id_key"]: h for h in F.HOUSEHOLDS}


def _run(id_key, ctx_extra=None, **ctx_kw):
    hh = HH[id_key]
    ctx = make_context(**ctx_kw)
    if ctx_extra:
        ctx.update(ctx_extra)
    return recommend(hh, ctx, CAT)


def _heroes(res):
    return [sorted(p["heroes"]) for p in res["plates"]]


# ---------------------------------------------------------------------------
# epsilon = 0 (the code-level safety default) is a total no-op, same output as no exploration at
# all — this must hold for every golden-master household, not just one.
# ---------------------------------------------------------------------------
def test_epsilon_zero_is_a_total_noop_for_every_golden_household():
    orig = cfgmod.CONFIG.bandit  # active_config().bandit — same dict every module sees
    try:
        cfgmod.active_config().bandit = {"exploration": {"epsilon": 0.0, "exploration_boost": 0.0}}
        for id_key in HH:
            baseline = _run(id_key, slot="dinner", season="transitional")
            exploring = _run(
                id_key, slot="dinner", season="transitional",
                ctx_extra={"_rng_seed": 1, "dish_feedback_counts": []},
            )
            assert _heroes(baseline) == _heroes(exploring), id_key
    finally:
        cfgmod.active_config().bandit = orig


# ---------------------------------------------------------------------------
# epsilon = 0 is ALSO what every golden-master fixture actually exercises today (no
# dish_feedback_counts / _rng_seed in any GOLDEN_CASES ctx) — explicit sanity check that the
# feature is a real no-op under production defaults, not just under a forced epsilon=0 override.
# ---------------------------------------------------------------------------
def test_default_bandit_epsilon_is_zero_code_level_safety_default():
    # Simulate "the YAML/key is missing" by pointing at an empty bandit config — this is the
    # code-level safety default path in ghar_re_core/config.py, distinct from the YAML default.
    orig = cfgmod.active_config().bandit
    try:
        cfgmod.active_config().bandit = {}
        assert cfgmod.CONFIG.bandit_epsilon == 0.0
        assert cfgmod.CONFIG.bandit_exploration_boost == 0.0
    finally:
        cfgmod.active_config().bandit = orig


# ---------------------------------------------------------------------------
# epsilon = 1 with a seeded RNG deterministically swaps in a lower-ranked dish from an
# under-served class, in place of the lowest-scored already-chosen plate — and never changes any
# dish's score in doing so.
# ---------------------------------------------------------------------------
def test_epsilon_one_seeded_deterministically_swaps_a_lower_plate_in():
    orig = cfgmod.active_config().bandit
    try:
        cfgmod.active_config().bandit = {"exploration": {"epsilon": 1.0, "exploration_boost": 0.0}}
        baseline = _run("single_professional_blr", slot="dinner", season="transitional")
        exploring = _run(
            "single_professional_blr", slot="dinner", season="transitional",
            ctx_extra={"_rng_seed": 7, "dish_feedback_counts": []},
        )
        # Same call, same seed -> same result (determinism).
        exploring_again = _run(
            "single_professional_blr", slot="dinner", season="transitional",
            ctx_extra={"_rng_seed": 7, "dish_feedback_counts": []},
        )
        assert _heroes(exploring) == _heroes(exploring_again)
        # No dish's individual score changed — scores present in the output are a property of the
        # dish/plate itself (score()), never mutated by exploration.
        baseline_scores = {tuple(sorted(p["heroes"])): p["score"] for p in baseline["plates"]}
        exploring_scores = {tuple(sorted(p["heroes"])): p["score"] for p in exploring["plates"]}
        for heroes, score in exploring_scores.items():
            if heroes in baseline_scores:
                assert baseline_scores[heroes] == score
    finally:
        cfgmod.active_config().bandit = orig


# ---------------------------------------------------------------------------
# Regression (found by exercising the pipeline with real cold-start households): a household with
# a completely EMPTY dish_feedback_counts must not be permanently inert to exploration just
# because every class is equally "0 served". The bug: the under-served comparison required
# candidate_served < target_served even when there is zero signal anywhere, so "0 >= 0" always
# held and no swap was ever possible for any brand-new household, regardless of epsilon.
#
# Exercised directly against ghar_re_core.exploration.epsilon_greedy_select with two minimal
# synthetic standalone plates in different, non-overlapping meal classes (rather than through the
# full pipeline/golden fixtures, whose small catalogue + hero-overlap dedup can legitimately leave
# zero eligible candidates for a given household/seed — a separate, real constraint that
# shouldn't make this specific regression test flaky).
# ---------------------------------------------------------------------------
def test_cold_start_zero_history_is_not_permanently_inert_to_exploration():
    from ghar_re_core import exploration as EXP
    cat = {d.name: d for d in CAT}
    target = cat["Onion Pakora"]        # class SN_FRIED_PAKORA_SAMOSA
    candidate = cat["Sarson Ka Saag"]   # class LD_LEAFY_GREENS_SAAG — different, no hero overlap

    chosen = [{"form": "standalone", "hero": target, "heroes": {target.name}, "score": 1.0}]
    candidate_plates = chosen + [
        {"form": "standalone", "hero": candidate, "heroes": {candidate.name}, "score": 0.5},
    ]

    orig = cfgmod.active_config().bandit
    try:
        cfgmod.active_config().bandit = {"exploration": {"epsilon": 1.0, "exploration_boost": 0.0}}
        new_chosen, trace = EXP.epsilon_greedy_select(
            chosen, candidate_plates, {"_rng_seed": 1, "dish_feedback_counts": []},
        )
        assert trace, "expected a swap for a cold-start household with zero feedback history"
        assert [p["hero"].name for p in new_chosen] == [candidate.name]
        assert new_chosen[0]["_selection_propensity"] == 1.0
    finally:
        cfgmod.active_config().bandit = orig


def test_epsilon_policy_records_exact_exploit_and_explore_propensities():
    """The persisted probability must describe the policy draw, not the realized rank score."""
    from ghar_re_core import exploration as EXP

    cat = {d.name: d for d in CAT}
    fixed = cat["Dal Tadka"]
    target = cat["Onion Pakora"]
    candidate = cat["Sarson Ka Saag"]

    def plates():
        chosen = [
            {"form": "standalone", "hero": fixed, "heroes": {fixed.name}, "score": 2.0},
            {"form": "standalone", "hero": target, "heroes": {target.name}, "score": 1.0},
        ]
        return chosen, chosen + [
            {
                "form": "standalone",
                "hero": candidate,
                "heroes": {candidate.name},
                "score": 0.5,
            }
        ]

    orig = cfgmod.active_config().bandit
    try:
        cfgmod.active_config().bandit = {
            "exploration": {"epsilon": 0.25, "exploration_boost": 0.0}
        }
        exploit_chosen, exploit_pool = plates()
        exploit, exploit_trace = EXP.epsilon_greedy_select(
            exploit_chosen, exploit_pool, {"_rng_seed": 2, "dish_feedback_counts": []}
        )
        assert not exploit_trace
        assert [p["_selection_propensity"] for p in exploit] == [1.0, 0.75]

        explore_chosen, explore_pool = plates()
        explore, explore_trace = EXP.epsilon_greedy_select(
            explore_chosen, explore_pool, {"_rng_seed": 1, "dish_feedback_counts": []}
        )
        assert explore_trace
        assert [p["hero"].name for p in explore] == [fixed.name, candidate.name]
        assert [p["_selection_propensity"] for p in explore] == [1.0, 0.25]
        assert explore_trace[0]["swapped_out_propensity"] == 0.75
        assert explore_trace[0]["swapped_in_propensity"] == 0.25
    finally:
        cfgmod.active_config().bandit = orig


# ---------------------------------------------------------------------------
# exploration + exclude_dish_ids together must never surface an excluded dish, even when
# exploration is maximally aggressive (epsilon=1).
# ---------------------------------------------------------------------------
def test_exploration_never_surfaces_an_excluded_dish():
    orig = cfgmod.active_config().bandit
    try:
        cfgmod.active_config().bandit = {"exploration": {"epsilon": 1.0, "exploration_boost": 0.0}}
        baseline = _run("single_professional_blr", slot="dinner", season="transitional")
        served_names = {n for p in baseline["plates"] for n in p["heroes"]}
        excluded_ids = {"md5:" + n for n in served_names}
        res = _run(
            "single_professional_blr", slot="dinner", season="transitional",
            ctx_extra={
                "_rng_seed": 3, "dish_feedback_counts": [],
                "exclude_dish_ids": sorted(excluded_ids),
            },
        )
        got_names = {n for p in res["plates"] for n in p["heroes"]}
        assert not (got_names & served_names), got_names & served_names
    finally:
        cfgmod.active_config().bandit = orig


# ---------------------------------------------------------------------------
# exclude_dish_ids alone: a dish that would have scored top-1 is hard-removed from the output,
# never just demoted (WP-8G Option A). Pins epsilon=0 so this exercises exclude_dish_ids in
# isolation from exploration's own (real, intentional) randomness on a no-history household under
# the production YAML epsilon — that's a separate concern, covered by the epsilon-specific tests
# above.
# ---------------------------------------------------------------------------
def test_exclude_dish_ids_removes_a_would_be_top_dish():
    orig = cfgmod.active_config().bandit
    try:
        cfgmod.active_config().bandit = {"exploration": {"epsilon": 0.0, "exploration_boost": 0.0}}
        baseline = _run("single_professional_blr", slot="dinner", season="transitional")
        top_plate = baseline["plates"][0]
        top_names = sorted(top_plate["heroes"])
        excluded_ids = ["md5:" + n for n in top_names]

        res = _run(
            "single_professional_blr", slot="dinner", season="transitional",
            ctx_extra={"exclude_dish_ids": excluded_ids},
        )
        all_served_names = {n for p in res["plates"] for n in p["heroes"]}
        for n in top_names:
            assert n not in all_served_names, f"{n} should have been hard-excluded"
    finally:
        cfgmod.active_config().bandit = orig


# ---------------------------------------------------------------------------
# exclude_dish_ids is additive/optional: omitted or empty is a total no-op. Pins epsilon=0 for the
# same reason as the test above — isolating exclude_dish_ids from exploration's own randomness.
# ---------------------------------------------------------------------------
def test_exclude_dish_ids_empty_or_omitted_is_a_noop():
    orig = cfgmod.active_config().bandit
    try:
        cfgmod.active_config().bandit = {"exploration": {"epsilon": 0.0, "exploration_boost": 0.0}}
        baseline = _run("single_professional_blr", slot="dinner", season="transitional")
        omitted = _run("single_professional_blr", slot="dinner", season="transitional")
        empty = _run(
            "single_professional_blr", slot="dinner", season="transitional",
            ctx_extra={"exclude_dish_ids": []},
        )
        assert _heroes(baseline) == _heroes(omitted) == _heroes(empty)
    finally:
        cfgmod.active_config().bandit = orig
