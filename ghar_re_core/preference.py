"""
ghar_re_core.preference — s_pref, the master formula's `+ w_pref·S_pref` term (Phase 3).

UNFIT MODEL STUB, per the plan's explicit framing: this closes the "only in the score() docstring"
gap (§0 ground truth — no S_pref term existed anywhere in code before this) by making the slot
REAL and registry-wired (phase="pref" in ghar_re_core.modules_default.DEFAULT_REGISTRY), while its
actual numeric contribution stays exactly 0.0 until a real trained artifact + real feedback data
justify turning it on. Nothing here is fit, nothing here is shipped-as-active; the slot simply
EXISTS. This satisfies FD-11 (no synthetic/fabricated labels) by construction.

s_pref(dish, theta, ctx) returns 0.0 whenever ANY of the following is true (belt-and-suspenders,
each check independently sufficient to force the neutral value):
  - CONFIG.pref_model_enabled is False (the master switch, pref_model.yaml `enabled`) — the
    real-world default, and the state of every deployment today.
  - ghar_re_core.model_provider.active_model().artifact is None (no trained artifact loaded) —
    the real-world state today regardless of the flag above, since NullModelArtifactProvider is
    the only provider ever actually constructed anywhere in this repo.
Only when BOTH a real artifact is loaded AND the flag is explicitly on does this compute real
features (ghar_re_core.features.extract_features) and call the loaded model's `predict_proba`.
"""
from __future__ import annotations

from ghar_re_core.config import CONFIG
from ghar_re_core.model_provider import PREF_MODEL


def s_pref(dish, theta, ctx) -> float:
    """The `S_pref(x)` term of the master formula — [0,1] learned preference score, or exactly
    0.0 (the neutral/unfit value) when disabled or no artifact is present, which today is always.
    Confidence is handled separately by modules_default.py's BoundModule wrapper (pinned 1.0,
    matching prior_boost's pattern — this function returns only the raw value, never a
    confidence)."""
    if not CONFIG.pref_model_enabled:
        return 0.0
    model = PREF_MODEL.artifact
    if model is None:
        return 0.0

    # Only reachable once a real artifact is loaded AND pref_model.yaml.enabled is true — neither
    # is true anywhere in this repo today (Phase 3 ships the stub, not an active model).
    from ghar_re_core.features import extract_features

    features = extract_features(dish, theta, ctx)
    return float(model.predict_proba(features))
