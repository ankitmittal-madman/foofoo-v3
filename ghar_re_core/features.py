"""
ghar_re_core.features — s_pref feature extraction (Phase 3, not fit, not shipped).

`extract_features(dish, theta, ctx)` is the ONE feature vector both `ghar_re_core.preference`
(inference, when a real artifact is eventually loaded) and `ghar_re_core.training.train_pref_model`
(training, offline, against a real feedback export) must call — so training and inference can
never silently drift onto two different feature definitions.

Per the plan's §3.3 spec, this concatenates:
  1. Structured household/context features already available to every other module (no new data
     source): diet, region, slot, season, weekday, interaction_count. `household_size` has no
     literal field anywhere in theta/ctx today (grep confirms derive_theta never materializes a
     member-count int) — `household_type` (theta's own explicit q1 answer, e.g. "single",
     "couple_kids") is used as the honest categorical proxy instead of inventing a count that
     doesn't exist in the data model; documented here rather than silently substituted.
  2. Every OTHER registered ScoringModule's raw `value` (not the final weighted score), read
     straight from ScoringRegistry.combine()'s own Contribution[] — reuses Phase 1's plumbing
     rather than recomputing anything, and automatically stays in sync if a BASE/cohort module is
     ever added or removed.

Label extraction (accepted = 1/0, ambiguous rows excluded) is intentionally NOT here — it is
training-time-only logic and lives in ghar_re_core/training/train_pref_model.py, never importable
from the inference path (FD-11: no label-shaped data ever touches a live scoring call).
"""
from __future__ import annotations

from typing import Any


def extract_features(dish, theta, ctx) -> dict[str, Any]:
    """The full s_pref feature vector for one (dish, theta, ctx) triple. Deliberately excludes
    phase="pref" itself (s_pref cannot be a feature of s_pref) — every OTHER registered module's
    raw value is included, so this stays correct automatically as the registry evolves."""
    # Imported lazily to avoid a circular import: modules_default imports scoring, and this
    # module is imported by both inference (preference.py) and training code.
    from ghar_re_core.modules_default import DEFAULT_REGISTRY

    features: dict[str, Any] = {
        "diet": theta["diet"]["value"],
        "region": theta["region"]["value"],
        "slot": ctx.get("slot"),
        "season": ctx.get("season"),
        "weekday": ctx.get("weekday"),
        "interaction_count": ctx.get("interaction_count", 0),
        # No literal household-size count exists in theta/ctx (see module docstring) —
        # household_type is the honest, explicit-answer proxy, not a fabricated count.
        "household_size": theta["household_type"]["value"],
    }

    # Deliberately NOT DEFAULT_REGISTRY.combine(dish, theta, ctx) (phase=None, "all phases") —
    # that would invoke the phase="pref" module's own score(), i.e. ghar_re_core.preference.s_pref,
    # which (once a real artifact exists) calls extract_features() itself: infinite recursion.
    # Iterating modules directly and skipping phase="pref" avoids ever calling s_pref.score() here.
    for m in DEFAULT_REGISTRY.modules():
        if m.phase == "pref":
            continue
        r = m.score(dish, theta, ctx)
        features[f"module__{m.name}"] = r["value"]

    return features
