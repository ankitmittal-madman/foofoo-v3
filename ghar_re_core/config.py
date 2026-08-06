"""
ghar_re.config — loads the FROZEN-spec configuration from data/source/*.yaml.

Runtime contract (data/source/README.md): Load -> validate -> freeze in memory -> run.
NO parameter appears in engine code that isn't in these files (or the KB, via ghar_re.knowledge).
If a needed parameter is absent from every config AND the KB, the engine RAISES rather than
inventing a number silently (Task 3 rule).
"""
import os
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# Where the YAML/CSV config layer is read from.
#
# Default: <repo>/data/source — correct when running from a checked-out repo (the reference
# pipeline, the tests, local dev).
#
# Override via GHAR_RE_CONFIG_DIR: required in a CONTAINER, where ghar_re_core is pip-installed
# into site-packages and `ROOT` therefore resolves to site-packages — a directory that has no
# data/source beneath it. This is the concrete reason RE-DOC-10 §8 calls for a baked bundle: the
# service points this at the bundle's config/ directory at startup. Unset, behaviour is byte-for-
# byte what it was before this seam existed (the golden-master test pins that).
CONFIG_DIR_VAR = "GHAR_RE_CONFIG_DIR"
SRC = os.environ.get(CONFIG_DIR_VAR) or os.path.join(ROOT, "data", "source")

# Parsed-YAML cache, keyed by config file name.
_CACHE: dict[str, object] = {}


def _load(name):
    """Read and parse one YAML config file from SRC by filename, caching the result so the same
    file is never re-parsed twice in a process. `name` is a bare filename like
    'base_weights.yaml', not a full path."""
    if name not in _CACHE:
        with open(os.path.join(SRC, name)) as f:
            _CACHE[name] = yaml.safe_load(f)
    return _CACHE[name]


class Config:
    """Immutable-at-runtime view over the YAML configs (frozen in memory once loaded)."""

    def __init__(self):
        """Load every YAML config file this engine needs (weights, pairing rules, weather rules,
        filters, derivation params) plus community_priors.csv, all in one go, so a Config
        instance is a complete, ready-to-use snapshot of "the rules the engine runs on right
        now"."""
        self.base = _load("base_weights.yaml")
        self.distance = _load("distance_weights.yaml")
        self.q15 = _load("q15_weights.yaml")
        self.pairing = _load("pairing_rules.yaml")
        self.weather = _load("weather_rules.yaml")
        self.filters = _load("filters.yaml")
        self.derivation = _load("derivation_params.yaml")
        self.cohort = _load("cohort_weights.yaml")
        self.bandit = _load("bandit_weights.yaml")
        self.pref = _load("pref_model.yaml")
        self.versions = dict(spine="Spine v1.0", kb="KB v0.2",
                             config="Config v%s" % self.base["config_version"])
        self._community_priors = None

    # --- BASE weights (base_weights.yaml <- Core Spine §S2 §B9) ---
    def W(self, key):
        """Look up one named BASE-score weight (e.g. 'W_PALETTE', 'W_SIG') from
        base_weights.yaml. Raises KeyError (rather than defaulting to 0 or guessing) if the
        weight isn't configured, per the project's "never invent a number" rule."""
        try:
            return self.base["base_weights"][key]
        except KeyError as e:
            raise KeyError(
                f"BASE weight '{key}' not in base_weights.yaml — refusing to invent a value "
                f"(Task 3 rule: flag missing params, never hardcode)."
            ) from e

    @property
    def all_conf_k(self):
        """The confidence multiplier applied to every BASE-score term. Pinned to 1.0 for v1
        (base_weights.yaml + README rule 4) — a future version could vary this per module."""
        # v1 pins every module confidence to 1.0 (base_weights.yaml + README rule 4).
        return self.base["confidence"]["all_conf_k"]

    # --- Q15 gain (q15_weights.yaml <- §S3) ---
    def gamma(self, objective):
        """The gamma weight table for one Q15 objective (e.g. 'awesome_taste',
        'healthy_living') — how much each gain-score component (indulgence/light/protein)
        should count for a household with that stated objective. Raises KeyError if the
        objective isn't configured."""
        g = self.q15["gamma"].get(objective)
        if g is None:
            raise KeyError(f"Q15 objective '{objective}' not in q15_weights.yaml gamma table.")
        return g

    @property
    def kappa_v1(self):
        """The v1-pinned kappa scaling constant used in the GAIN_Q15 formula (always 1.0 in
        this version)."""
        return self.q15["kappa"]["v1_value"]      # pinned 1.0 in v1

    @property
    def gain_bounds(self):
        """The (min, max) clamp applied to a dish's final GAIN_Q15 multiplier, so no objective
        can push a dish's score arbitrarily high or low."""
        return tuple(self.q15["gain_bounds"])

    @property
    def default_objective(self):
        """The Q15 objective to use when a household hasn't stated one (q15_objective is
        empty/missing)."""
        return self.q15["default_objective"]

    # --- pairing (pairing_rules.yaml <- §S4) ---
    @property
    def lambda_pair(self):
        """The weight controlling how much a pair's compat() bonus/penalty can move its combined
        plate score, in the plate_score formula (§S4.3)."""
        return self.pairing["plate"]["lambda_pair"]

    @property
    def theta_region(self):
        """The maximum allowed cuisine distance between a dry and liquid dish before the
        cuisine-coherence hard gate rejects the pair (pairing.allowed())."""
        return self.pairing["hard_gates"]["theta_region"]

    @property
    def theta_base(self):
        """The same-base exclusion threshold (Core Spine FROZEN §S4 line 641, default 0.6):
        pairing.same_base(d,l) rejects a pair when cosine(base-ingredient vectors) exceeds this,
        i.e. the dry and liquid dish are too similar in their defining/main ingredients."""
        return self.pairing["hard_gates"]["theta_base"]

    def soft(self, key):
        """Look up one named soft pairing term (e.g. 'b_balance', 'b_protein', 'p_sametaste')
        from pairing_rules.yaml — the small bonuses/penalties compat() adds up."""
        return self.pairing["soft_terms"][key]

    # --- weather (weather_rules.yaml <- §S2 m_weather + KB §Z2) ---
    @property
    def weather_thresholds(self):
        """The temperature (°C) cut-offs that classify the injected weather context as
        'hot_weather' or 'cold_weather'."""
        return self.weather["thermal_thresholds"]

    @property
    def weather_magnitude(self):
        """The signed weight (W_WEATHER) applied to the weather-comfort term in the BASE score —
        how much a matching/mismatching dish is boosted or demoted for the current weather."""
        return self.weather["magnitude"]           # = W_WEATHER, signed

    # --- filters / normalization (filters.yaml <- §S2 PART A + §S1) ---
    @property
    def T_CAP(self):
        """The normalization cap used when scaling raw scores into their final range
        (filters.yaml)."""
        return self.filters["T_CAP"]

    # --- derivation params (derivation_params.yaml <- D1-D7) ---
    def D(self, node):
        """Look up the full parameter block for one D1-D7 derivation node (e.g. 'D1_income',
        'D5_household') from derivation_params.yaml — everything derivation.py needs to compute
        that node's household-profile fields."""
        return self.derivation[node]

    # --- class-first cohort weight (cohort_weights.yaml <- WP-15 / master-formula w_cohort) ---
    @property
    def w_cohort(self):
        """The legacy WP-15 w_cohort weight (= the WP-16 decay floor). Kept for back-compat; live
        scoring uses w_cohort_effective() below, which is cold-start-strong and decays with data."""
        return self.cohort["cohort"]["w_cohort"]

    @property
    def class_plan_weights(self):
        """WP-17 (compositional_weight, learned_weight) for cohort_intel.class_affinity's fusion of
        the compositional persona/state plan with the learned frequency model. Compositional-dominant
        defaults if the class_plan block is absent (feature degrades to learned-only, never crashes)."""
        cp = self.cohort.get("class_plan") or {}
        return cp.get("compositional_weight", 0.7), cp.get("learned_weight", 0.3)

    def w_cohort_effective(self, interaction_count=0):
        """WP-16 cold-start-strong, decaying w_cohort weight for the master formula's
        `w_cohort·S_cohort` term. At interaction_count=0 (a brand-new household — the state of
        EVERY live household today, feedback_events being empty) this returns the strong cold-start
        weight so the slate feels like the persona-DB plan; it decays toward the floor with a
        configured half-life as real accept/reject signal accrues. All three numbers come from
        cohort_weights.yaml — nothing hardcoded (Task 3 rule)."""
        c = self.cohort["cohort"]
        coldstart = c.get("w_cohort_coldstart", c["w_cohort"])
        floor = c.get("w_cohort_floor", c["w_cohort"])
        half = c.get("coldstart_halflife", 25)
        n = max(0, interaction_count or 0)
        return floor + (coldstart - floor) * (2.0 ** (-n / half))

    def foreign_demote_effective(self, interaction_count=0):
        """WP-16.1 cold-start-strong, decaying demote subtracted from any foreign (zone=Global)
        dish — the persona-DB science is entirely regional Indian, so foreign food has no cohort
        anchor and should be pushed down for a brand-new regional household, resurfacing as real
        interest accrues. Returns 0.0 if the foreign_demote block is absent (feature off)."""
        fd = self.cohort.get("foreign_demote")
        if not fd:
            return 0.0
        coldstart = fd.get("demote_coldstart", 0.0)
        floor = fd.get("demote_floor", 0.0)
        half = fd.get("halflife", 25)
        n = max(0, interaction_count or 0)
        return floor + (coldstart - floor) * (2.0 ** (-n / half))

    # --- selection-stage epsilon-greedy exploration (bandit_weights.yaml <- Phase 2) ---
    @property
    def bandit_epsilon(self):
        """Probability [0,1] that ghar_re_core.exploration's epsilon-greedy selection swap
        explores an under-served meal class instead of taking the greedy top pick. The YAML
        default (bandit_weights.yaml) is 0.15; the CODE-LEVEL SAFETY DEFAULT — used whenever the
        file or the `exploration.epsilon` key is missing — is 0.0 (a hard no-op), never a
        guessed non-zero rate (Task 3 rule)."""
        return (self.bandit or {}).get("exploration", {}).get("epsilon", 0.0)

    @property
    def bandit_exploration_boost(self):
        """Small additive tie-break weight [0,1] ghar_re_core.exploration uses ONLY to choose
        which under-served-class candidate to swap in when several are eligible (never applied
        to any dish's actual score). Code-level safety default 0.0 if missing."""
        return (self.bandit or {}).get("exploration", {}).get("exploration_boost", 0.0)

    # --- s_pref ScoringModule stub (pref_model.yaml <- Phase 3, not fit, not shipped) ---
    @property
    def pref_model_enabled(self):
        """Master switch for ghar_re_core.preference.s_pref. CODE-LEVEL SAFETY DEFAULT is False
        if pref_model.yaml or this key is ever missing — s_pref must never silently turn itself
        on (Task 3 rule)."""
        return bool((self.pref or {}).get("enabled", False))

    @property
    def pref_model_artifact_path(self):
        """Path to the trained s_pref artifact, or None if no artifact is configured yet (the
        real-world state today — see ghar_re_core/model_provider.py). Code-level safety default
        None if pref_model.yaml or this key is missing."""
        return (self.pref or {}).get("model_artifact_path")

    @property
    def w_pref(self):
        """The master formula's `w_pref·S_pref` weight (score()'s `+ w_pref·S_pref` term).
        Belt-and-suspenders code-level safety default 0.0 if pref_model.yaml or this key is
        missing — mirrors foreign_demote_effective's "absent block -> 0.0" pattern, so a mistaken
        `enabled: true` without an explicit weight decision still contributes exactly 0.0."""
        return (self.pref or {}).get("w_pref", 0.0)

    # --- training_readiness (pref_model.yaml <- the density gate WP-14 left unset) ---
    @property
    def pref_training_min_events(self):
        """Minimum real, non-ambiguous labeled feedback rows (fleet-wide) required before
        ghar_re_core.training.train_pref_model will fit anything — see
        ghar_re_core.training.dataset.check_training_readiness. CODE-LEVEL SAFETY DEFAULT is a
        never-satisfiable sentinel if pref_model.yaml or this key is missing: an unset threshold
        must block training, not silently permit it (same fail-closed direction as every other
        code-level safety default in this file — never guessed permissive)."""
        return (self.pref or {}).get("training_readiness", {}).get("min_real_events", 10**9)

    @property
    def pref_training_min_households(self):
        """Minimum distinct households contributing to the labeled export required before
        training — see check_training_readiness. Same fail-closed code-level safety default
        (a never-satisfiable sentinel) as pref_training_min_events if missing."""
        return (self.pref or {}).get("training_readiness", {}).get("min_households", 10**9)

    @property
    def pref_evaluation_min_holdout_events(self):
        """Minimum household-isolated evaluation rows. Missing governance blocks promotion."""
        return (self.pref or {}).get("evaluation_readiness", {}).get(
            "min_holdout_events", 10**9
        )

    @property
    def pref_evaluation_min_auc(self):
        """Minimum holdout ROC AUC. A missing threshold is deliberately impossible to pass."""
        return (self.pref or {}).get("evaluation_readiness", {}).get("min_auc", 1.1)

    @property
    def pref_evaluation_min_class_recall(self):
        """Minimum recall required independently for positive and negative feedback."""
        return (self.pref or {}).get("evaluation_readiness", {}).get(
            "min_class_recall", 1.1
        )

    # --- community priors (community_priors.csv <- KB §C1) ---
    # Loaded HERE, at the config-loader boundary, so core math modules (derivation) never open a
    # file themselves (RE-DOC-11 §1/§2). Keyed by state -> {state, zone, diet_lean, cadence}.
    @property
    def community_priors(self):
        """State -> community dietary-prior row (state, zone, diet_lean, default_non_veg_cadence)
        from community_priors.csv, loaded once and cached. This is the soft default derivation.py
        falls back to when a household hasn't explicitly answered Q5-Q8 in enough detail."""
        if self._community_priors is None:
            import csv
            self._community_priors = {}
            with open(os.path.join(SRC, "community_priors.csv")) as f:
                for r in csv.DictReader(f):
                    self._community_priors[r["state"]] = r
        return self._community_priors


# ---------------------------------------------------------------------------
# Active-config injection seam (RE-DOC-11 §2).
#
# Core math modules do `from ghar_re_core.config import CONFIG` and use `CONFIG.*`. To let the
# service inject a Config produced by a ConfigProvider WITHOUT changing any of those call sites,
# CONFIG is a thin proxy that delegates to the current active Config. The default active config is
# the YAML-from-data/source load (used by the reference pipeline + tests); the service replaces it
# at startup via `set_active_config(provider.load())`. A future RemoteConfigProvider is then a new
# adapter with zero changes to scoring/derivation/pairing.
# ---------------------------------------------------------------------------
_active = None


def active_config():
    """Return the Config currently in effect, creating the default YAML-from-data/source Config
    the first time it's needed. This is what CONFIG (the proxy every core module imports)
    delegates to on every attribute access."""
    global _active
    if _active is None:
        _active = Config()
    return _active


def set_active_config(cfg):
    """Inject the Config the engine should use (called by the service's ConfigProvider)."""
    global _active
    _active = cfg


class _ConfigProxy:
    """Delegates every attribute/method access to the current active Config."""
    def __getattr__(self, name):
        """Forward any attribute/method lookup (e.g. CONFIG.W(...), CONFIG.lambda_pair) to
        whichever Config is currently active, so callers never hold a stale reference."""
        return getattr(active_config(), name)


# What every core module imports; resolves to the active Config on each access.
CONFIG = _ConfigProxy()
