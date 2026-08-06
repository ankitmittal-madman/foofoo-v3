"""
ghar_re_core.preference — s_pref, the master formula's `+ w_pref·S_pref` term (Phase 3).

LEARNED MODEL SLOT, disabled until a governed artifact passes the real-feedback readiness and
evaluation gates. The slot is registry-wired (phase="pref" in
ghar_re_core.modules_default.DEFAULT_REGISTRY), while its numeric contribution stays exactly 0.0
until startup loads a versioned artifact and config explicitly enables it. No synthetic labels or
placeholder fit are shipped.

s_pref(dish, theta, ctx) returns 0.0 whenever ANY of the following is true (belt-and-suspenders,
each check independently sufficient to force the neutral value):
  - CONFIG.pref_model_enabled is False (the master switch, pref_model.yaml `enabled`) — the
    real-world default, and the state of every deployment today.
  - ghar_re_core.model_provider.active_model().artifact is None (no trained artifact loaded).
Only when BOTH a real artifact is loaded AND the flag is explicitly on does this compute real
features (ghar_re_core.features.extract_features) and call the loaded model's `predict_proba`.
"""

from __future__ import annotations

from ghar_re_core.config import CONFIG
from ghar_re_core.model_provider import PREF_MODEL


def loaded_preference_score(dish, theta, ctx) -> float | None:
    """Score the loaded artifact without deciding whether it may affect ranking.

    This is the only entry point shadow instrumentation uses. Returning None distinguishes "no
    model loaded" from a legitimate prediction of 0.0.
    """
    model = PREF_MODEL.artifact
    if model is None:
        return None
    from ghar_re_core.features import extract_features

    features = extract_features(dish, theta, ctx)
    return float(model.predict_proba(features))


def s_pref(dish, theta, ctx) -> float:
    """The `S_pref(x)` term of the master formula — [0,1] learned preference score, or exactly
    0.0 (the neutral/unfit value) when disabled or no artifact is present, which today is always.
    Confidence is handled separately by modules_default.py's BoundModule wrapper (pinned 1.0,
    matching prior_boost's pattern — this function returns only the raw value, never a
    confidence)."""
    if not CONFIG.pref_model_enabled:
        return 0.0
    prediction = loaded_preference_score(dish, theta, ctx)
    return 0.0 if prediction is None else prediction
