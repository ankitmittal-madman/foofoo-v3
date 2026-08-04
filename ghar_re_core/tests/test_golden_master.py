"""
Golden-master regression test (Phase E Task 1, RE-DOC-10 phase table).

Locks the pipeline's scored output for a small fixed set of household+context inputs as
committed JSON files under tests/golden/. Any change to scoring behaviour — intentional or
accidental — changes this output, so this test fails the moment it does. That's the point: a
silent drift in D1-D7/BASE/pairing math can no longer merge unnoticed. An INTENTIONAL scoring
change just requires regenerating the golden file in the same PR (`python -m
ghar_re_core.tests.test_golden_master --update`), so the diff is visible in review.

Only fields that describe the actual recommendation (form, score, heroes, support, calories,
which dishes were picked) are locked. Raw `theta` signals carry a wall-clock `timestamp` per
field (non-deterministic across runs) and `heroes`/dish objects are Python sets/objects whose
repr ordering depends on hash-seed randomization — neither belongs in a byte-for-byte lock, so
both are excluded/normalized by _canonicalize() below.
"""
import argparse
import json
import os

from ghar_re_core import config as cfgmod
from ghar_re_core import fixtures as F
from ghar_re_core.catalogue import Catalogue
from ghar_re_core.pipeline import recommend, make_context

_HERE = os.path.dirname(__file__)
_GOLDEN_DIR = os.path.join(_HERE, "golden")

CAT = Catalogue()
HH = {h["id_key"]: h for h in F.HOUSEHOLDS}

# Fixed household+context inputs covering distinct pipeline behaviours (non-veg default,
# Jain hard filter, weaning A4 floor + monsoon weather, migrant blend + lunch slot).
GOLDEN_CASES = {
    "single_professional_blr": dict(slot="dinner", season="transitional"),
    "jain_couple_ahmedabad": dict(slot="dinner", season="transitional"),
    "couple_toddler_pune": dict(slot="dinner", season="monsoon", is_raining=True),
    "migrant_bihar_mumbai": dict(slot="lunch", season="transitional"),
}


def _canonicalize_plate(p):
    dry = p.get("dry")
    liquid = p.get("liquid")
    hero = p.get("hero")
    return {
        "form": p["form"],
        "score": round(p["score"], 6),
        "heroes": sorted(p["heroes"]),
        "support": p.get("support"),
        "plate_calories": p["plate_calories"],
        "dry": dry.name if dry else None,
        "liquid": liquid.name if liquid else None,
        "hero_dish": hero.name if hero else None,
    }


def _canonicalize(res):
    return {
        "household": res["household"],
        "plates": [_canonicalize_plate(p) for p in res["plates"]],
    }


def _compute(id_key, ctx_kw):
    # Pin epsilon-greedy exploration (Phase 2, ghar_re_core.exploration) OFF for this lock.
    # Golden-master exists to lock scoring/pairing MATH (see module docstring) — exploration is a
    # selection-stage, intentionally-probabilistic swap that runs on top of already-scored,
    # already-ranked output, and these fixtures set no _rng_seed. Running it under the real
    # bandit_weights.yaml epsilon (0.15) would make this lock flaky by design, not by bug: with no
    # dish_feedback_counts (every golden household here), every meal class is equally "0 served",
    # so a genuinely under-served-history household is exactly the case Phase 2's exploration
    # exists to handle — appropriately, not a scoring regression this test should ever catch.
    orig = cfgmod.active_config().bandit
    try:
        cfgmod.active_config().bandit = {"exploration": {"epsilon": 0.0, "exploration_boost": 0.0}}
        ctx = make_context(**ctx_kw)
        res = recommend(HH[id_key], ctx, CAT)
        return _canonicalize(res)
    finally:
        cfgmod.active_config().bandit = orig


def _golden_path(id_key):
    return os.path.join(_GOLDEN_DIR, f"{id_key}.json")


def _load_golden(id_key):
    with open(_golden_path(id_key)) as f:
        return json.load(f)


def test_golden_master_no_drift():
    for id_key, ctx_kw in GOLDEN_CASES.items():
        actual = _compute(id_key, ctx_kw)
        expected = _load_golden(id_key)
        assert actual == expected, (
            f"golden-master mismatch for '{id_key}' — pipeline output changed. "
            f"If this is an INTENTIONAL scoring change, regenerate with "
            f"`python -m ghar_re_core.tests.test_golden_master --update` and commit the new "
            f"golden file in this PR so the diff is visible in review."
        )


def _update():
    os.makedirs(_GOLDEN_DIR, exist_ok=True)
    for id_key, ctx_kw in GOLDEN_CASES.items():
        canonical = _compute(id_key, ctx_kw)
        with open(_golden_path(id_key), "w") as f:
            json.dump(canonical, f, indent=2, sort_keys=True)
            f.write("\n")
        print(f"wrote {_golden_path(id_key)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--update", action="store_true", help="regenerate golden files")
    args = parser.parse_args()
    if args.update:
        _update()
    else:
        parser.print_help()
