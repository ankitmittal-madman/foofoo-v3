"""
ghar_re.catalogue — in-memory dish catalogue built from the golden fixtures.

Mirrors what ghar_re.dishes + joins hold in Postgres, so the pipeline/tests run without a live DB
while staying faithful to the seeded schema. Zone is resolved cuisine -> cuisine_group -> zone_map
(KB §R1), exactly as the DB would via ghar_re.zone_map.
"""
from ghar_re import fixtures as F
from ghar_re import knowledge as K

# cuisine -> cuisine_group (from fixtures.CUISINES)
_CUISINE_GROUP = {c[0]: c[2] for c in F.CUISINES}
# cuisine -> state_origin
_CUISINE_STATE = {c[0]: c[4] for c in F.CUISINES}
# cuisine_group -> zone (KB §R1)
_GROUP_ZONE = {z[0]: z[1] for z in K.ZONE_MAP}


class Dish:
    def __init__(self, d):
        self.__dict__.update(d)
        self.id = "md5:" + d["name"]
        self.cuisine_group = _CUISINE_GROUP.get(d["cuisine"])
        self.state_origin = _CUISINE_STATE.get(d["cuisine"])
        self.zone = _GROUP_ZONE.get(self.cuisine_group)
        self.sig_score = K.BAND_TO_SCORE[d["sig_band"]]
        # ingredient token set (main + all) for ING-block / same-base / allergen work
        self.ingredient_names = [i for i, _ in d["ingredients"]]
        self.main_ingredients = [i for i, m in d["ingredients"] if m]

    def has_tag(self, field, value):
        return value in getattr(self, field, []) or []

    def __repr__(self):
        return f"<Dish {self.name} [{self.zone}/{self.hero_role}] sig={self.sig_score}>"


class Catalogue:
    def __init__(self, dish_dicts=None):
        self.dishes = [Dish(d) for d in (dish_dicts or F.DISHES)]
        self.by_name = {d.name: d for d in self.dishes}

    def __iter__(self):
        return iter(self.dishes)

    def get(self, name):
        return self.by_name.get(name)


# ingredient master attributes (real, from ingredients_v5.csv) for jain/allergen derivation
import csv as _csv, os as _os
_ING = {}
with open(_os.path.join(_os.path.dirname(__file__), "..", "data", "source", "ingredients_v5.csv")) as _f:
    for _r in _csv.DictReader(_f):
        _ING[_r["name"]] = dict(
            category=_r["category"],
            is_allergen=_r["is_allergen"] == "Y",
            allergen_type=_r["allergen_type"] or None,
            is_jain_compatible=_r["is_jain_compatible"] == "Y",
        )


def ingredient_info(name):
    return _ING.get(name, {})


def dish_allergens(dish):
    """Explicit-ingredient allergen set (A3 BASIC pass; hidden-derivative layer is out of scope)."""
    out = set()
    for ing in dish.ingredient_names:
        info = ingredient_info(ing)
        if info.get("is_allergen") and info.get("allergen_type"):
            out.add(info["allergen_type"])
    return out
