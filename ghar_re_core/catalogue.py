"""
ghar_re.catalogue — in-memory dish catalogue built from the golden fixtures.

Mirrors what ghar_re.dishes + joins hold in Postgres, so the pipeline/tests run without a live DB
while staying faithful to the seeded schema. Zone is resolved cuisine -> cuisine_group -> zone_map
(KB §R1), exactly as the DB would via ghar_re.zone_map.
"""

from ghar_re_core import fixtures as F
from ghar_re_core import knowledge as K

# cuisine -> cuisine_group, from K.CUISINE_GROUP_MAP (all 65 real cuisines — data/source/
# cuisines_v4.csv, transcribed in knowledge.py). NOT fixtures.CUISINES (only 10 entries) — that was
# the confirmed Phase G bug: any real-catalogue dish whose cuisine wasn't one of those 10 got
# cuisine_group=None -> zone=None (measured: 536/810, 66%), which silently pushed
# pairing.cuisine_dist()'s cuisine_coherence hard gate into its harshest fallback for most
# cross-cuisine dry+liquid combinations. Verified identical to fixtures.CUISINES for all 10 legacy
# cuisines, so this introduces no drift in the 39-dish golden-master lock.
_CUISINE_GROUP = dict(K.CUISINE_GROUP_MAP)
# cuisine -> state_origin. Deliberately still fixtures.CUISINES-only, NOT switched to
# cuisines_v4.csv's state_origin column: that column uses different string formats for cuisines
# also present in fixtures.CUISINES (e.g. udupi "Karnataka" vs cuisines_v4.csv's
# "Karnataka (Udupi)", mughlai "Delhi" vs "Delhi/UP") and scoring._cuis() does an EXACT string
# match against a household's home state for its highest-value (1.00) term — switching sources
# here would silently change BASE scores for the 39-dish golden sample too, not just add coverage
# for the real catalogue. Real-catalogue dishes' state_origin=None (and the resulting loss of the
# _cuis() same-state 1.00 bonus) is therefore a real, separate, still-open gap — same root cause,
# different consumer, deliberately not fixed in this commit to keep this a single, low-risk,
# zone-resolution-only change.
_CUISINE_STATE = {c[0]: c[4] for c in F.CUISINES}
# cuisine_group -> zone (KB §R1)
_GROUP_ZONE = {z[0]: z[1] for z in K.ZONE_MAP}


def _normalize_name(value):
    return " ".join(str(value).casefold().split())


class Dish:
    """One dish, wrapped from a raw dish dict (fixtures.DISHES shape) into an object with
    computed zone/state-origin/signature-score fields ready for the scoring/pairing modules.

    A PM-relevant summary: this is "one row of the menu" plus the extra context (which region
    it belongs to, how famous/iconic it is) the recommendation engine needs to score it.
    """

    def __init__(self, d):
        """Build a Dish from a raw dish dict, resolving its zone (via cuisine -> cuisine_group ->
        zone_map) and signature score (via its sig_band) at construction time so downstream code
        never has to redo that lookup."""
        self.__dict__.update(d)
        self.id = "md5:" + d["name"]
        self.cuisine_group = _CUISINE_GROUP.get(d["cuisine"])
        # Real-catalogue dish dicts (build_catalogue.py) already carry a resolved state_origin
        # sourced from cuisines_v4.csv's 65-cuisine table (see module docstring above for why that
        # source can't be used for the golden sample without changing its locked BASE scores).
        # Golden-sample dicts (fixtures._dish()) never set this key, so .get() falls through to the
        # legacy 10-cuisine lookup for them, unchanged — this line only ADDS coverage for the real
        # catalogue's other 55 cuisines, it cannot alter any golden-master score.
        self.state_origin = d.get("state_origin") or _CUISINE_STATE.get(d["cuisine"])
        self.zone = _GROUP_ZONE.get(self.cuisine_group)
        # sig_band is None for any dish with no KB-sourced/curated signature score (real-catalogue
        # dishes not yet scored in sig_scores_v1.csv — see ghar_re_service/scripts/build_catalogue.py).
        # That is a legitimate "not yet scored" state, not an error: base()'s W_SIG term is meant to
        # contribute nothing for an unscored dish, matching base_weights.yaml's own additive model
        # (BASE = Σ W_k·conf_k·m_k — an absent term is 0, never a fabricated score).
        sig_band = d["sig_band"]
        self.sig_score = K.BAND_TO_SCORE[sig_band] if sig_band is not None else 0.0
        # ingredient token set (main + all) for ING-block / same-base / allergen work
        self.ingredient_names = [i for i, _ in d["ingredients"]]
        self.main_ingredients = [i for i, m in d["ingredients"] if m]
        # vegan_compatible: computed here (not pre-baked per-dish like jain_compatible/
        # farali_compatible) so both the golden sample and the real catalogue share one derivation,
        # from ingredients_v5.csv's existing is_vegan column (already populated — dairy/honey are
        # correctly N). Same conservative stance as jain_compatible: diet must be 'veg' AND every
        # ingredient must be a KNOWN vegan ingredient — an unresolved/unknown ingredient makes the
        # dish False, never guessed True. A pre-baked "vegan_compatible" key (if one is ever added
        # to a raw dish dict) is honored as an override, matching the state_origin precedent.
        self.vegan_compatible = d.get("vegan_compatible")
        if self.vegan_compatible is None:
            self.vegan_compatible = self.diet == "veg" and all(
                _ING.get(ing, {}).get("is_vegan", False) for ing in self.ingredient_names
            )

    def has_tag(self, field, value):
        """Return True if this dish's `field` (a list attribute, e.g. 'texture' or 'richness')
        contains `value`. Used by scoring/pairing to check tag membership without every caller
        needing to know a field might be missing."""
        return value in getattr(self, field, []) or []

    def __repr__(self):
        """Short human-readable label for debugging/logging, e.g. '<Dish Rajma [North/liquid]
        sig=0.6>' — not used in any scoring decision."""
        return f"<Dish {self.name} [{self.zone}/{self.hero_role}] sig={self.sig_score}>"


class Catalogue:
    """In-memory CatalogueSnapshot. Downstream code depends on THIS object's read methods, never on
    how the data was loaded (RE-DOC-11 §1) — a future PostgresCatalogueProvider returns the same shape."""

    def __init__(self, dish_dicts=None):
        """Build the in-memory catalogue from a list of raw dish dicts (defaults to the golden
        fixtures, F.DISHES, when none is passed) and build the by-name/by-id/by-zone/by-hero-role
        lookup indices used everywhere else in the engine."""
        self.dishes = [Dish(d) for d in (dish_dicts or F.DISHES)]
        self.by_name = {d.name: d for d in self.dishes}
        canonical_candidates = {}
        for dish in self.dishes:
            key = _normalize_name(dish.name)
            prior = canonical_candidates.get(key)
            if prior is not None and prior.name != dish.name:
                raise ValueError(
                    f"canonical dish identity collision: {prior.name!r} and {dish.name!r}"
                )
            canonical_candidates[key] = dish

        # Build aliases separately so catalogue order cannot decide identity. Canonical names
        # always win, uniquely owned aliases resolve, and aliases owned by multiple dishes fail
        # closed. The ambiguity map is diagnostics-only and contains no ranking behavior.
        alias_candidates = {}
        for dish in self.dishes:
            for value in [*(dish.synonyms or []), *(dish.alternate_names or [])]:
                key = _normalize_name(value)
                if not key:
                    continue
                alias_candidates.setdefault(key, {})[dish.name] = dish

        self.by_normalized_name = dict(canonical_candidates)
        self.ambiguous_aliases = {}
        self.shadowed_aliases = {}
        for key, candidates in alias_candidates.items():
            if key in canonical_candidates:
                canonical = canonical_candidates[key]
                shadowed = tuple(sorted(name for name in candidates if name != canonical.name))
                if shadowed:
                    self.shadowed_aliases[key] = shadowed
                continue
            if len(candidates) == 1:
                self.by_normalized_name[key] = next(iter(candidates.values()))
            else:
                self.ambiguous_aliases[key] = tuple(sorted(candidates))
        # in-memory indices (built once; RE-DOC-10 §7 "build in-memory indices")
        self.by_id = {d.id: d for d in self.dishes}
        self._by_zone = {}
        self._by_hero_role = {}
        for d in self.dishes:
            self._by_zone.setdefault(d.zone, []).append(d)
            self._by_hero_role.setdefault(d.hero_role, []).append(d)

    def __iter__(self):
        """Iterate over every dish in the catalogue (lets `for d in catalogue:` work)."""
        return iter(self.dishes)

    def get(self, name):
        """Resolve a canonical name, synonym, or alternate name to its canonical Dish."""
        if not isinstance(name, str):
            return None
        return self.by_name.get(name) or self.by_normalized_name.get(_normalize_name(name))

    # --- CatalogueSnapshot read interface (RE-DOC-11 §1) ---
    def get_dish(self, dish_id):
        """Look up a dish by its stable id (the 'md5:<name>' identifier). Returns None if not
        found — the id format is what a future Postgres-backed catalogue would also use."""
        return self.by_id.get(dish_id)

    def by_zone(self, zone):
        """All dishes whose resolved regional zone (North/South/East/West/...) matches `zone`.
        Returns a new list each call so callers can't accidentally mutate the index."""
        return list(self._by_zone.get(zone, []))

    def by_hero_role(self, role):
        """All dishes with the given hero_role ('dry', 'liquid', 'single', 'standalone', or
        'support') — the grouping the pairing engine uses to build dry+liquid plate pairs."""
        return list(self._by_hero_role.get(role, []))


# ingredient master attributes (real, from ingredients_v5.csv) for jain/allergen derivation.
# Resolved through config.SRC (not a hardcoded ../data/source walk) so it follows
# GHAR_RE_CONFIG_DIR into the baked bundle — this read happens at IMPORT time, so the path must
# already be correct when the module loads, before any provider runs.
import csv as _csv, os as _os
from ghar_re_core import config as _cfg

_ING = {}
with open(_os.path.join(_cfg.SRC, "ingredients_v5.csv")) as _f:
    for _r in _csv.DictReader(_f):
        _ING[_r["name"]] = dict(
            category=_r["category"],
            is_allergen=_r["is_allergen"] == "Y",
            allergen_type=_r["allergen_type"] or None,
            is_jain_compatible=_r["is_jain_compatible"] == "Y",
            is_vegan=_r["is_vegan"] == "Y",
        )


def ingredient_info(name):
    """Look up an ingredient's master attributes (category, whether it's an allergen and which
    kind, whether it's Jain-compatible) by its canonical name. Returns an empty dict if the
    ingredient isn't in the master list — callers treat that as 'no known attributes', not
    an error."""
    return _ING.get(name, {})


# Known hidden-derivative allergen carriers: an ingredient whose OWN is_allergen/allergen_type
# columns in ingredients_v5.csv are correctly blank (pure asafoetida has no gluten) but whose
# COMMERCIAL form commonly carries a hidden allergen as a filler/anti-caking carrier or process
# byproduct. Authored here, not in ingredients_v5.csv, because it's a fact about the commercial
# product's typical composition, not an intrinsic property of the ingredient itself. Add further
# entries here if another hidden-derivative pairing is confirmed — this table, not a report-only
# footnote, is what dish_allergens() (the actual A3 safety filter) reads. Each entry researched and
# cited, not guessed:
#   asafoetida (hing)  -> commercial hing is typically only ~5-20% pure resin, bulked with wheat
#                         flour/gum as an anti-caking carrier.
#   soy_sauce          -> traditionally brewed soy sauce (the common form; tamari is the gluten-free
#                         exception, not the default) is fermented from roughly equal parts soybean
#                         and WHEAT — it is not gluten-free unless the label says tamari/GF.
#   sambar_powder      -> standard sambar podi recipes include hing as a listed spice component
#                         (same wheat-carrier risk as raw asafoetida, inherited via the blend).
#   chaat_masala       -> standard chaat masala recipes likewise list hing as a core ingredient.
HIDDEN_DERIVATIVE_ALLERGENS = {
    "asafoetida": "gluten",
    "soy_sauce": "gluten",
    "sambar_powder": "gluten",
    "chaat_masala": "gluten",
}


def dish_allergens(dish):
    """Explicit-ingredient allergen set (A3 BASIC pass), plus the known hidden-derivative carriers
    in HIDDEN_DERIVATIVE_ALLERGENS above (asafoetida, soy sauce, and the two hing-containing spice
    blends — sambar powder, chaat masala). Still not a full hidden-derivative layer covering every
    possible commercial-product risk, but no longer purely explicit-ingredient-only."""
    out = set()
    for ing in dish.ingredient_names:
        info = ingredient_info(ing)
        if info.get("is_allergen") and info.get("allergen_type"):
            out.add(info["allergen_type"])
        hidden = HIDDEN_DERIVATIVE_ALLERGENS.get(ing)
        if hidden:
            out.add(hidden)
    return out
