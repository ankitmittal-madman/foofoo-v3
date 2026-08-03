"""
ghar_re_core.modules — ScoringModule registry (Phase 1, score-neutral refactor).

Introduces a uniform `ScoringModule` shape (name, phase, score(dish,theta,ctx) -> ModuleResult)
so every term the Core Spine master formula currently sums by hand (7 BASE terms + prior_boost +
s_cohort + s_foreign) becomes one registry entry, combined by a single weighted-sum `combine()`.

Nothing in this file changes any module's MATH — `ghar_re_core/scoring.py`'s existing functions
(m_palette, m_slot, ..., s_cohort, s_foreign, prior_boost) keep their exact bodies. This file only
adds the wrapper/registry plumbing around them (wired up in `ghar_re_core/modules_default.py`),
which is what makes the refactor score-neutral by construction rather than by luck.

Combination is a plain weighted SUM, order-independent (RE-DOC-11 §7) — `combine()` never applies
modules sequentially or lets one module's result influence another's inputs.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional, Protocol, TypedDict


class ModuleResult(TypedDict):
    """One ScoringModule's raw output for one (dish, theta, ctx) call.

    value: m_k(x) raw output — [0,1] for most BASE terms, [-1,1] for signed modules (e.g.
        m_weather), unrestricted for additive-authored terms (e.g. prior_boost).
    confidence: conf_k, [0,1]. Pinned to CONFIG.all_conf_k (1.0 in v1) for most modules; a module
        can override this (e.g. prior_boost's fixed 1.0) via BoundModule's confidence_fn.
    metadata: free-form per-module extra detail, empty dict when a module has none to add.
    explanation: short plain-English string describing what this module contributed and why.
    """
    value: float
    confidence: float
    metadata: dict[str, Any]
    explanation: str


class ScoringModule(Protocol):
    """Uniform shape every registry entry satisfies. `name` is a stable identifier (e.g.
    "m_palette", "s_cohort") used in Contribution[] and decision-trace output; `phase` tags which
    part of the Core Spine master formula this module feeds ("base" | "cohort" | "pref" | ...),
    used by ScoringRegistry.combine()'s optional phase filter."""
    name: str
    phase: str

    def score(self, dish, theta, ctx) -> ModuleResult: ...
    def weight(self, ctx) -> float: ...


@dataclass(frozen=True)
class Contribution:
    """One module's contribution to a combine() call, kept for decision-trace/observability use —
    NOT used to recompute the total (combine() sums directly); this is a reporting-only record."""
    module: str
    value: float
    weight: float          # effective weight actually applied = raw_weight * confidence
    confidence: float


class BoundModule:
    """Wraps an existing scoring.py function into the ScoringModule protocol, with ZERO change to
    that function's own math. `fn` must already be pre-adapted (in modules_default.py) to the
    uniform call shape `fn(dish, theta, ctx) -> float` — each existing scoring.py function has a
    different real arity (m_palette takes (dish,theta); m_weather takes (dish,theta,ctx); sig
    takes (dish); s_foreign takes (dish)), so modules_default.py supplies a small per-module
    lambda adapter rather than this class trying to introspect arity generically.

    weight_key: a base_weights.yaml key (e.g. "W_PALETTE") looked up via CONFIG.W() at call time
        (so runtime config changes are always reflected — no weight is captured/cached at import).
    weight_fn: overrides weight_key entirely — called as weight_fn(ctx) -> float. Used for
        s_cohort/s_foreign, whose effective weight is a context-dependent decay
        (CONFIG.w_cohort_effective/foreign_demote_effective), and for prior_boost, whose weight is
        the constant 1.0 (authored-additive, no W_k in config — Task 3 rule: never invent a
        weight that doesn't exist).
    confidence_fn: overrides the default CONFIG.all_conf_k confidence — called as
        confidence_fn(dish, theta, ctx) -> float. Used for prior_boost's fixed 1.0.
    """

    def __init__(
        self,
        name: str,
        fn: Callable[[Any, Any, Any], float],
        phase: str,
        weight_key: Optional[str] = None,
        weight_fn: Optional[Callable[[Any], float]] = None,
        confidence_fn: Optional[Callable[[Any, Any, Any], float] ] = None,
    ):
        if weight_key is None and weight_fn is None:
            raise ValueError(f"BoundModule '{name}': need either weight_key or weight_fn.")
        self.name = name
        self.phase = phase
        self._fn = fn
        self._weight_key = weight_key
        self._weight_fn = weight_fn
        self._confidence_fn = confidence_fn

    def weight(self, ctx) -> float:
        """The raw (pre-confidence) weight for this module given the current ctx — a static
        base_weights.yaml lookup for most BASE modules, or a context-dependent function
        (cohort/foreign decay, prior_boost's constant 1.0) when weight_fn was supplied. Public so
        ScoringRegistry.combine() can ask every ScoringModule the same way, without reaching into
        BoundModule internals."""
        # Imported lazily to avoid a hard import-order dependency at module load time.
        from ghar_re_core.config import CONFIG
        if self._weight_fn is not None:
            return self._weight_fn(ctx)
        return CONFIG.W(self._weight_key)

    def _confidence(self, dish, theta, ctx) -> float:
        from ghar_re_core.config import CONFIG
        if self._confidence_fn is not None:
            return self._confidence_fn(dish, theta, ctx)
        return CONFIG.all_conf_k

    def score(self, dish, theta, ctx) -> ModuleResult:
        value = self._fn(dish, theta, ctx)
        conf = self._confidence(dish, theta, ctx)
        weight = self.weight(ctx)
        return ModuleResult(
            value=value,
            confidence=conf,
            metadata={},
            explanation=f"{self.name}={value!r} (weight={weight!r}, confidence={conf!r})",
        )


class ScoringRegistry:
    """Ordered list of ScoringModule instances. combine() is a weighted SUM (order-independent by
    construction — RE-DOC-11 §7), NOT sequential application, matching the Core Spine master
    formula. Registration order only affects Contribution[] ordering for observability, never the
    numeric total."""

    def __init__(self):
        self._modules: list[ScoringModule] = []

    def register(self, module: ScoringModule) -> None:
        self._modules.append(module)

    def modules(self, phase: Optional[str] = None) -> list[ScoringModule]:
        """The registered modules, optionally filtered to one phase tag."""
        if phase is None:
            return list(self._modules)
        return [m for m in self._modules if m.phase == phase]

    def combine(self, dish, theta, ctx, phase: Optional[str] = None) -> tuple[float, list[Contribution]]:
        """Weighted sum of every registered module (optionally filtered to `phase`), returning
        (total, contributions). Each module computes its own weight/confidence/value; combine()
        itself does no phase-specific math — a module tagged phase="cohort" with a NEGATIVE
        effective weight (e.g. s_foreign) is simply added like every other module, which is what
        keeps this a uniform weighted sum with no special-cased subtraction."""
        total = 0.0
        contributions: list[Contribution] = []
        for m in self.modules(phase):
            r = m.score(dish, theta, ctx)
            # ModuleResult itself only carries value/confidence/metadata/explanation — weight is
            # a property of the module (static config lookup or a context-dependent decay fn),
            # so combine() asks the module directly via the ScoringModule.weight(ctx) hook, the
            # same call BoundModule.score() makes internally to build its own explanation string.
            weight = m.weight(ctx)
            weighted = weight * r["confidence"] * r["value"]
            total += weighted
            contributions.append(Contribution(
                module=m.name,
                value=r["value"],
                weight=weight * r["confidence"],
                confidence=r["confidence"],
            ))
        return total, contributions


DEFAULT_REGISTRY = ScoringRegistry()  # populated in ghar_re_core/modules_default.py, imported once
