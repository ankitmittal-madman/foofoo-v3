"""
Phase 3 tests — ghar_re_core.preference.s_pref (the UNFIT model stub), ghar_re_core.model_provider
(ModelArtifactProvider seam), and phase="pref" isolation from base()/score()'s default combine()
calls.

The highest-risk part of Phase 3 is `phase="pref"` accidentally leaking into `base()`/`score()`'s
existing default behaviour (golden-master risk) — several tests here exist specifically to prove
that never happens, independent of the golden-master byte-diff check itself.
"""
import pytest

from ghar_re_core import config as cfgmod
from ghar_re_core import fixtures as F
from ghar_re_core import model_provider as MP
from ghar_re_core import scoring as S
from ghar_re_core.catalogue import Catalogue
from ghar_re_core.derivation import derive_theta
from ghar_re_core.modules_default import DEFAULT_REGISTRY
from ghar_re_core.pipeline import make_context
from ghar_re_core.preference import s_pref

CAT = Catalogue()
HH = {h["id_key"]: h for h in F.HOUSEHOLDS}


def _one_dish_theta_ctx():
    household = HH["single_professional_blr"]
    theta = derive_theta(household)
    ctx = make_context(slot="dinner", season="transitional")
    dish = next(iter(CAT))
    return dish, theta, ctx


# ---------------------------------------------------------------------------
# (a) s_pref returns the neutral/unfit value when no artifact is present.
# ---------------------------------------------------------------------------
def test_s_pref_neutral_value_when_disabled_default_config():
    """The real-world case right now: pref_model.yaml enabled=false, no artifact configured.
    s_pref must return exactly 0.0 regardless of dish/theta/ctx."""
    dish, theta, ctx = _one_dish_theta_ctx()
    assert s_pref(dish, theta, ctx) == 0.0


def test_s_pref_neutral_value_when_enabled_but_no_artifact(monkeypatch):
    """Even if pref_model.yaml.enabled were mistakenly flipped true, with no artifact loaded
    (NullModelArtifactProvider, the only provider ever constructed anywhere in this repo)
    s_pref must still return exactly 0.0 — belt-and-suspenders, independent checks."""
    cfg = cfgmod.active_config()
    monkeypatch.setattr(cfg, "pref", {**cfg.pref, "enabled": True})
    dish, theta, ctx = _one_dish_theta_ctx()
    assert MP.active_model().artifact is None
    assert s_pref(dish, theta, ctx) == 0.0


def test_s_pref_module_registered_with_zero_weight_by_default():
    """s_pref is a REAL registered ScoringModule (phase="pref"), not merely a bare function — but
    its effective weight (CONFIG.w_pref) defaults to 0.0 too, so even the module's own weight()
    hook is neutral, independent of the value check above."""
    pref_modules = DEFAULT_REGISTRY.modules(phase="pref")
    assert [m.name for m in pref_modules] == ["s_pref"]
    ctx = make_context()
    assert pref_modules[0].weight(ctx) == 0.0


# ---------------------------------------------------------------------------
# (b) phase="pref" is excluded from base()/score()'s default combine() calls.
# ---------------------------------------------------------------------------
def test_base_never_includes_pref_phase():
    """base()'s combine() call uses phase="base" explicitly — registering s_pref must not change
    what base() returns for any dish."""
    dish, theta, ctx = _one_dish_theta_ctx()
    total, contributions = DEFAULT_REGISTRY.combine(dish, theta, ctx, phase="base")
    assert all(c.module != "s_pref" for c in contributions)


def test_cohort_phase_never_includes_pref_phase():
    """score()'s cohort combine() call uses phase="cohort" explicitly — s_pref must never appear
    in that filtered view either."""
    dish, theta, ctx = _one_dish_theta_ctx()
    _, contributions = DEFAULT_REGISTRY.combine(dish, theta, ctx, phase="cohort")
    assert all(c.module != "s_pref" for c in contributions)


def test_score_pref_term_is_zero_by_default():
    """score()'s own dedicated phase="pref" combine() call contributes exactly 0.0 in every
    deployment today (no artifact, weight defaults to 0.0) — score() must be numerically
    identical to what it would be if that combine() call were never added."""
    dish, theta, ctx = _one_dish_theta_ctx()
    pref_val, contributions = DEFAULT_REGISTRY.combine(dish, theta, ctx, phase="pref")
    assert pref_val == 0.0
    assert [c.module for c in contributions] == ["s_pref"]
    assert contributions[0].value == 0.0

    objective = None
    without_pref = S.base(dish, theta, ctx) * S.gain_q15(dish, objective) + (
        DEFAULT_REGISTRY.combine(dish, theta, ctx, phase="cohort")[0]
    )
    with_pref = S.score(dish, theta, ctx, objective)
    assert with_pref == pytest.approx(without_pref)


# ---------------------------------------------------------------------------
# (c) ModelArtifactProvider's None-handling.
# ---------------------------------------------------------------------------
def test_null_provider_is_the_default_active_provider():
    provider = MP.active_model()
    assert isinstance(provider, MP.NullModelArtifactProvider)
    assert provider.artifact is None
    assert provider.load() is None


def test_file_provider_returns_none_for_missing_path():
    provider = MP.FileModelArtifactProvider("/nonexistent/path/does-not-exist.joblib")
    assert provider.load() is None
    assert provider.artifact is None


def test_set_active_model_injection_seam(monkeypatch):
    """Mirrors config.py's set_active_config() seam — injecting a provider must be reflected by
    PREF_MODEL/active_model() immediately, and must be restorable (tests never leak state)."""
    sentinel_provider = MP.NullModelArtifactProvider()
    sentinel_provider.artifact = "not-a-real-model-just-a-sentinel-for-this-test"
    MP.set_active_model(sentinel_provider)
    try:
        assert MP.active_model() is sentinel_provider
        assert MP.PREF_MODEL.artifact == "not-a-real-model-just-a-sentinel-for-this-test"
    finally:
        MP.set_active_model(MP.NullModelArtifactProvider())
