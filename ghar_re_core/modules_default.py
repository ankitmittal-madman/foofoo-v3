"""
ghar_re_core.modules_default — builds DEFAULT_REGISTRY, the live ScoringModule registry used by
scoring.base()/score() (Phase 1, score-neutral refactor).

Wraps the 7 existing BASE functions + prior_boost + s_cohort + s_foreign from scoring.py as
BoundModule instances, with ZERO change to any of their bodies — only a thin per-module lambda
adapting each function's real arity to the uniform BoundModule call shape
`fn(dish, theta, ctx) -> float`:
  - m_palette(dish, theta), m_age(dish, theta), m_household(dish, theta) -> drop ctx
  - m_slot(dish, ctx), m_season(dish, ctx)                                -> drop theta
  - sig(dish), s_foreign(dish)                                           -> drop theta, ctx
  - m_weather(dish, theta, ctx), prior_boost(dish, theta, ctx),
    s_cohort(dish, theta, ctx)                                           -> pass through unchanged

Phases:
  "base"   — the 8 terms base() sums (7 W_k-weighted BASE terms + prior_boost, authored-additive).
  "cohort" — s_cohort / s_foreign, the two decaying WP-16 terms score() adds on top of BASE*GAIN.
             s_foreign's effective weight is modeled as NEGATIVE (via weight_fn), so
             ScoringRegistry.combine()'s plain weighted sum needs no special-cased subtraction —
             `score()` still ends up computing base*gain + w*s_cohort - wf*s_foreign exactly as
             before, just via `+ (-wf)*s_foreign` inside combine() instead of an inline `-`.
  "pref"   — Phase 3's s_pref stub. Registered below, but numerically a no-op (value=0.0) until
             a real trained artifact exists and pref_model.yaml.enabled is flipped on — see
             ghar_re_core/preference.py. Registering it here does NOT change base()/score()'s
             default behaviour: base() and score() (scoring.py) each call
             DEFAULT_REGISTRY.combine(..., phase="base"/"cohort") with an EXPLICIT phase filter,
             never combine(..., phase=None), so "pref" never leaks into either call. score()
             separately combines phase="pref" for its own dedicated `+ w_pref·S_pref` term
             (weight defaults to 0.0 regardless — see config.py CONFIG.w_pref).
"""
from ghar_re_core import preference as P
from ghar_re_core import scoring as S
from ghar_re_core.config import CONFIG
from ghar_re_core.modules import BoundModule, ScoringRegistry

DEFAULT_REGISTRY = ScoringRegistry()

# ---- phase="base" — the 7 W_k-weighted BASE terms (Core Spine §S2 PART B) ----
DEFAULT_REGISTRY.register(BoundModule(
    "m_palette", lambda dish, theta, ctx: S.m_palette(dish, theta, ctx),
    phase="base", weight_key="W_PALETTE",
))
DEFAULT_REGISTRY.register(BoundModule(
    "m_slot", lambda dish, theta, ctx: S.m_slot(dish, ctx),
    phase="base", weight_key="W_SLOT",
))
DEFAULT_REGISTRY.register(BoundModule(
    "m_season", lambda dish, theta, ctx: S.m_season(dish, ctx),
    phase="base", weight_key="W_SEASON",
))
DEFAULT_REGISTRY.register(BoundModule(
    "sig", lambda dish, theta, ctx: S.sig(dish),
    phase="base", weight_key="W_SIG",
))
DEFAULT_REGISTRY.register(BoundModule(
    "m_age", lambda dish, theta, ctx: S.m_age(dish, theta),
    phase="base", weight_key="W_AGE",
))
DEFAULT_REGISTRY.register(BoundModule(
    "m_household", lambda dish, theta, ctx: S.m_household(dish, theta),
    phase="base", weight_key="W_HOUSE",
))
DEFAULT_REGISTRY.register(BoundModule(
    "m_weather", lambda dish, theta, ctx: S.m_weather(dish, theta, ctx),
    phase="base", weight_key="W_WEATHER",
))

# prior_boost: authored-additive, no W_k in base_weights.yaml (Task 3 rule — never invent a
# weight that doesn't exist in config). Modeled with weight/confidence both constant 1.0, so it
# fits the registry contract without inventing a number.
DEFAULT_REGISTRY.register(BoundModule(
    "prior_boost", lambda dish, theta, ctx: S.prior_boost(dish, theta, ctx),
    phase="base",
    weight_fn=lambda ctx: 1.0,
    confidence_fn=lambda dish, theta, ctx: 1.0,
))

# ---- phase="cohort" — the two WP-16 decaying terms score() adds on top of BASE*GAIN ----
DEFAULT_REGISTRY.register(BoundModule(
    "s_cohort", lambda dish, theta, ctx: S.s_cohort(dish, theta, ctx),
    phase="cohort",
    weight_fn=lambda ctx: CONFIG.w_cohort_effective(ctx.get("interaction_count", 0)),
))
DEFAULT_REGISTRY.register(BoundModule(
    "s_foreign", lambda dish, theta, ctx: S.s_foreign(dish),
    phase="cohort",
    # NEGATIVE effective weight — score()'s master formula SUBTRACTS wf*s_foreign, so modeling
    # the weight itself as negative keeps combine() a uniform weighted sum with no special-cased
    # subtraction anywhere (RE-DOC-11 §7: combination is order-independent, always a plain sum).
    weight_fn=lambda ctx: -CONFIG.foreign_demote_effective(ctx.get("interaction_count", 0)),
))

# ---- phase="pref" — Phase 3's s_pref stub (not fit, not shipped) ----
# weight_fn reads CONFIG.w_pref (pref_model.yaml, default 0.0) rather than a static weight_key —
# belt-and-suspenders alongside s_pref's own internal enabled/artifact checks (preference.py):
# even a mistaken `enabled: true` flip without an explicit weight decision still contributes 0.0.
DEFAULT_REGISTRY.register(BoundModule(
    "s_pref", lambda dish, theta, ctx: P.s_pref(dish, theta, ctx),
    phase="pref",
    weight_fn=lambda ctx: CONFIG.w_pref,
    confidence_fn=lambda dish, theta, ctx: 1.0,
))
