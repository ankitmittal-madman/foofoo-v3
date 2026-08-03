"""
ghar_re_core.tests.test_scoring_registry — Phase 1 direct per-module neutrality check.

Golden-master (test_golden_master.py) only locks the top-N SERVED result for 4 fixed households —
a refactor that changes every dish's raw score identically, or changes scores in a way that
happens not to reorder the top-N for those 4 fixtures, would slip past it undetected. This test
is the finer-grained check the plan calls for: it recomputes the OLD explicit 7-term-weighted-sum
+ prior_boost formula by hand (independent of DEFAULT_REGISTRY/base()) and asserts
DEFAULT_REGISTRY.combine(..., phase="base")[0] matches it exactly, dish-by-dish, for every golden
household+context fixture. This is what proves the registry refactor is score-neutral by
construction, not by luck of 4 particular households.
"""
import pytest

from ghar_re_core import fixtures as F
from ghar_re_core import scoring as S
from ghar_re_core.catalogue import Catalogue
from ghar_re_core.config import CONFIG
from ghar_re_core.derivation import derive_theta
from ghar_re_core.modules_default import DEFAULT_REGISTRY
from ghar_re_core.pipeline import make_context

CAT = Catalogue()
HH = {h["id_key"]: h for h in F.HOUSEHOLDS}

GOLDEN_CASES = {
    "single_professional_blr": dict(slot="dinner", season="transitional"),
    "jain_couple_ahmedabad": dict(slot="dinner", season="transitional"),
    "couple_toddler_pune": dict(slot="dinner", season="monsoon", is_raining=True),
    "migrant_bihar_mumbai": dict(slot="lunch", season="transitional"),
}


def _old_base(dish, theta, ctx):
    """The exact pre-refactor base() formula (scoring.py lines 296-308 before Phase 1), computed
    independently of DEFAULT_REGISTRY/scoring.base() — the reference this test checks against."""
    cfg = CONFIG
    conf = cfg.all_conf_k
    return (cfg.W("W_PALETTE") * conf * S.m_palette(dish, theta)
            + cfg.W("W_SLOT") * conf * S.m_slot(dish, ctx)
            + cfg.W("W_SEASON") * conf * S.m_season(dish, ctx)
            + cfg.W("W_SIG") * conf * S.sig(dish)
            + cfg.W("W_AGE") * conf * S.m_age(dish, theta)
            + cfg.W("W_HOUSE") * conf * S.m_household(dish, theta)
            + cfg.W("W_WEATHER") * conf * S.m_weather(dish, theta, ctx)
            + S.prior_boost(dish, theta, ctx))


@pytest.mark.parametrize("id_key,ctx_kw", GOLDEN_CASES.items())
def test_base_registry_matches_old_formula(id_key, ctx_kw):
    household = HH[id_key]
    theta = derive_theta(household)
    ctx = make_context(**ctx_kw)
    dishes = list(CAT)
    assert dishes, "expected a non-empty catalogue"
    for dish in dishes:
        expected = _old_base(dish, theta, ctx)
        actual, _ = DEFAULT_REGISTRY.combine(dish, theta, ctx, phase="base")
        assert actual == pytest.approx(expected), (
            f"registry base() diverged from the old hand-summed formula for dish "
            f"'{dish.name}' in fixture '{id_key}' — Phase 1 refactor is not score-neutral."
        )


@pytest.mark.parametrize("id_key,ctx_kw", GOLDEN_CASES.items())
def test_base_registry_matches_scoring_base(id_key, ctx_kw):
    """scoring.base() itself now delegates to the registry — confirm it agrees with the
    registry's own phase="base" combine() output (they should be literally the same call)."""
    household = HH[id_key]
    theta = derive_theta(household)
    ctx = make_context(**ctx_kw)
    for dish in list(CAT)[:25]:
        registry_val, _ = DEFAULT_REGISTRY.combine(dish, theta, ctx, phase="base")
        assert S.base(dish, theta, ctx) == pytest.approx(registry_val)


def test_cohort_phase_matches_old_score_formula():
    """score()'s `w*s_cohort - wf*s_foreign` term, recomputed via the phase="cohort" registry
    combine(), must match the old inline formula — including at a nonzero interaction_count,
    where both decay functions actually move off their cold-start values."""
    household = HH["single_professional_blr"]
    theta = derive_theta(household)
    ctx = make_context(slot="dinner", season="transitional")
    for n in (0, 5, 25, 100):
        ctx_n = dict(ctx, interaction_count=n)
        w = CONFIG.w_cohort_effective(n)
        wf = CONFIG.foreign_demote_effective(n)
        for dish in list(CAT)[:25]:
            expected = w * S.s_cohort(dish, theta, ctx_n) - wf * S.s_foreign(dish)
            actual, _ = DEFAULT_REGISTRY.combine(dish, theta, ctx_n, phase="cohort")
            assert actual == pytest.approx(expected)


def test_registry_module_names_match_expected_set():
    """Light assertion (per the plan §1.3) that the registry's module list is exactly the 8 BASE
    + 2 cohort terms Phase 1 wraps — catches an accidental extra/missing registration without
    needing decision_trace itself to carry the module list (decision_trace's own shape is
    unaffected by Phase 1 — see scoring.py/decision_log.py, unchanged in this refactor)."""
    base_names = {m.name for m in DEFAULT_REGISTRY.modules(phase="base")}
    cohort_names = {m.name for m in DEFAULT_REGISTRY.modules(phase="cohort")}
    assert base_names == {
        "m_palette", "m_slot", "m_season", "sig", "m_age", "m_household", "m_weather",
        "prior_boost",
    }
    assert cohort_names == {"s_cohort", "s_foreign"}
    assert DEFAULT_REGISTRY.modules(phase="pref") == []
