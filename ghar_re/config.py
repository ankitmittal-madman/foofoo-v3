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
SRC = os.path.join(ROOT, "data", "source")

_CACHE = {}


def _load(name):
    if name not in _CACHE:
        with open(os.path.join(SRC, name)) as f:
            _CACHE[name] = yaml.safe_load(f)
    return _CACHE[name]


class Config:
    """Immutable-at-runtime view over the YAML configs (frozen in memory once loaded)."""

    def __init__(self):
        self.base = _load("base_weights.yaml")
        self.distance = _load("distance_weights.yaml")
        self.q15 = _load("q15_weights.yaml")
        self.pairing = _load("pairing_rules.yaml")
        self.weather = _load("weather_rules.yaml")
        self.filters = _load("filters.yaml")
        self.derivation = _load("derivation_params.yaml")
        self.versions = dict(spine="Spine v1.0", kb="KB v0.2",
                             config="Config v%s" % self.base["config_version"])

    # --- BASE weights (base_weights.yaml <- Core Spine §S2 §B9) ---
    def W(self, key):
        try:
            return self.base["base_weights"][key]
        except KeyError:
            raise KeyError(
                f"BASE weight '{key}' not in base_weights.yaml — refusing to invent a value "
                f"(Task 3 rule: flag missing params, never hardcode)."
            )

    @property
    def all_conf_k(self):
        # v1 pins every module confidence to 1.0 (base_weights.yaml + README rule 4).
        return self.base["confidence"]["all_conf_k"]

    # --- Q15 gain (q15_weights.yaml <- §S3) ---
    def gamma(self, objective):
        g = self.q15["gamma"].get(objective)
        if g is None:
            raise KeyError(f"Q15 objective '{objective}' not in q15_weights.yaml gamma table.")
        return g

    @property
    def kappa_v1(self):
        return self.q15["kappa"]["v1_value"]      # pinned 1.0 in v1

    @property
    def gain_bounds(self):
        return tuple(self.q15["gain_bounds"])

    @property
    def default_objective(self):
        return self.q15["default_objective"]

    # --- pairing (pairing_rules.yaml <- §S4) ---
    @property
    def lambda_pair(self):
        return self.pairing["plate"]["lambda_pair"]

    @property
    def theta_region(self):
        return self.pairing["hard_gates"]["theta_region"]

    def soft(self, key):
        return self.pairing["soft_terms"][key]

    # --- weather (weather_rules.yaml <- §S2 m_weather + KB §Z2) ---
    @property
    def weather_thresholds(self):
        return self.weather["thermal_thresholds"]

    @property
    def weather_magnitude(self):
        return self.weather["magnitude"]           # = W_WEATHER, signed

    # --- filters / normalization (filters.yaml <- §S2 PART A + §S1) ---
    @property
    def T_CAP(self):
        return self.filters["T_CAP"]

    # --- derivation params (derivation_params.yaml <- D1-D7) ---
    def D(self, node):
        return self.derivation[node]


# Single frozen instance.
CONFIG = Config()
