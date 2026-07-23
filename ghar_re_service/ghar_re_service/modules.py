"""
ScoringModule protocol + registry (RE-DOC-11 §6/§7).

Each BASE component from ghar_re_core.scoring (m_palette, m_slot, m_season, sig, m_age,
m_household, m_weather, prior_boost) is WRAPPED — never re-implemented — as a ScoringModule.
An ordered registry iterates them to compose BASE, and the same iteration directly produces the
response's open `contributions[]` array (one module → one contribution entry, no mapping step).

Adding a new signal later (s_pref, an ML term, a negative-prior demotion) = append one module +
its config weight; the composition loop and the wire format never change. This makes
"BASE = Σ_k W_k·conf_k·m_k, form invariant across versions" (Core Spine) type-enforced, not a
documentation promise.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, Any, Dict, List, Tuple, Callable

from ghar_re_core import scoring as S


@dataclass
class ModuleResult:
    value: float                       # the module's raw m_k(x) output
    confidence: float = 1.0            # conf_k (v1 pinned 1.0)
    metadata: Dict[str, Any] = field(default_factory=dict)
    explanation: str = ""


class ScoringModule(Protocol):
    name: str
    weight_key: str | None             # config base_weights key; None => additive weight 1.0

    def score(self, dish, profile, context) -> ModuleResult: ...


# --- one wrapper per existing BASE component (calls ghar_re_core.scoring; no math here) ---
class _FnModule:
    """Adapts a ghar_re_core.scoring function (with its own arg pattern) to the ScoringModule shape."""

    def __init__(self, name: str, weight_key: str | None, fn: Callable, arg_kind: str):
        self.name = name
        self.weight_key = weight_key
        self._fn = fn
        self._arg_kind = arg_kind       # 'dish' | 'dish_theta' | 'dish_ctx' | 'dish_theta_ctx'

    def score(self, dish, profile, context) -> ModuleResult:
        if self._arg_kind == "dish":
            v = self._fn(dish)
        elif self._arg_kind == "dish_theta":
            v = self._fn(dish, profile)
        elif self._arg_kind == "dish_ctx":
            v = self._fn(dish, context)
        else:  # dish_theta_ctx
            v = self._fn(dish, profile, context)
        return ModuleResult(value=float(v), confidence=1.0, explanation=self.name)


def build_registry() -> List[ScoringModule]:
    """The ordered BASE registry (matches ghar_re_core.scoring.base()'s term order exactly)."""
    return [
        _FnModule("m_palette",   "W_PALETTE", S.m_palette,   "dish_theta"),
        _FnModule("m_slot",      "W_SLOT",    S.m_slot,      "dish_ctx"),
        _FnModule("m_season",    "W_SEASON",  S.m_season,    "dish_ctx"),
        _FnModule("sig",         "W_SIG",     S.sig,         "dish"),
        _FnModule("m_age",       "W_AGE",     S.m_age,       "dish_theta"),
        _FnModule("m_household", "W_HOUSE",   S.m_household, "dish_theta"),
        _FnModule("m_weather",   "W_WEATHER", S.m_weather,   "dish_theta_ctx"),   # signed
        _FnModule("prior_boost", None,        S.prior_boost, "dish_theta_ctx"),   # additive, weight 1.0
    ]


def compose_base(dish, theta, ctx, config, registry: List[ScoringModule]) -> Tuple[float, List[dict]]:
    """Iterate the registry to compute BASE for one dish AND emit its contributions[].
    Returns (base_total, contributions). base_total is Σ (weight · value), identical by construction
    to ghar_re_core.scoring.base() (a parity test asserts this)."""
    conf_k = config.all_conf_k
    contributions: List[dict] = []
    base_total = 0.0
    for m in registry:
        r = m.score(dish, theta, ctx)
        weight = (config.W(m.weight_key) * conf_k) if m.weight_key else 1.0
        base_total += weight * r.value
        contributions.append({
            "module": m.name,
            "value": round(r.value, 6),
            "weight": round(weight, 6),
            "confidence": r.confidence,
        })
    return base_total, contributions
