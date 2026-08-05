"""
Regression test for the West-MH rain comfort-hero data gap (RE plumbing plan §0.3).

Before this fix, COMFORT_HERO_MAP's West-MH rain row used "Pithla-Bhakri" (hyphenated), which
does not exist anywhere in the real catalogue (the seeded dish is "Pithla", no "Bhakri" at all —
database/seeds/106_seed_dishes.sql), and "Kanda Bhaji" had no real catalogue equivalent at all
(COMFORT_HERO_TO_DISH mapped it to itself, a nonexistent name). Both were silent no-ops in
_comfort_heroes_for(): the returned set never matched any real dish, so the comfort-hero lift for
this zone/weather combination never fired in production.

This test locks the fix: for a West-MH household in the rain, _comfort_heroes_for() must return a
non-empty set that actually intersects the real catalogue's dish names — so this exact class of
data-sync gap can never silently regress again.
"""

import json
import os
import re

from ghar_re_core import fixtures as F
from ghar_re_core import knowledge
from ghar_re_core.derivation import derive_theta
from ghar_re_core.scoring import _comfort_heroes_for

HH = {h["id_key"]: h for h in F.HOUSEHOLDS}

# The production seed file (not ghar_re_core.fixtures' small 39-dish golden sample, which this
# specific fix's "Pakora (Mixed Veg)" replacement dish doesn't happen to be part of) is the "real
# catalogue" the plan means — WP-8/RE plumbing plan §0.3's own ground truth locates the gap
# against this exact file.
_SEEDS_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "database",
    "seeds",
    "106_seed_dishes.sql",
)


def _real_catalogue_dish_names() -> set[str]:
    with open(_SEEDS_PATH) as f:
        text = f.read()
    # Every seed row is `INSERT INTO public.dishes (...) VALUES ('Dish Name', ...)` — the dish
    # name is always the first single-quoted literal after VALUES (.
    return set(re.findall(r"INSERT INTO public\.dishes \([^)]*\) VALUES \('([^']+)'", text))


def test_west_mh_rain_comfort_heroes_resolve_to_real_catalogue_dishes():
    # couple_toddler_pune (fixtures.py) is the golden West-MH household — Maharashtra/Pune —
    # already used by test_golden_master.py's monsoon+is_raining case, so it's the natural
    # existing fixture to reuse here rather than inventing a new one.
    theta = derive_theta(HH["couple_toddler_pune"])
    heroes = _comfort_heroes_for(theta, "rainy")

    assert heroes, "West-MH rain must resolve to at least one comfort hero (was a silent no-op)"

    catalogue_names = _real_catalogue_dish_names()
    resolved = heroes & catalogue_names
    assert resolved, (
        f"none of the resolved comfort heroes {heroes} exist in the real catalogue — "
        "the comfort-hero lift for West-MH rain would still be a silent no-op"
    )
    # The two concrete fixes this test locks in: "Pithla" (was "Pithla-Bhakri", a pure spelling
    # bug) and "Pakora (Mixed Veg)" (the domain-owner-confirmed "Kanda Bhaji" remap).
    assert "Pithla" in resolved
    assert "Pakora (Mixed Veg)" in resolved


def test_new_production_comfort_aliases_exist_in_real_catalogue():
    """Production-only spellings must never regress into silent no-op targets."""
    bundle_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "ghar_re_service", "data", "bundle", "catalogue.json"
    )
    with open(bundle_path) as handle:
        catalogue_names = {row["name"] for row in json.load(handle)}
    expected = {
        "Kadhi Pakora",
        "Dal Dhokli",
        "Pazhampori",
        "Gajar Ka Halwa",
        *{
            alias
            for aliases in knowledge.COMFORT_HERO_CATALOGUE_ALIASES.values()
            for alias in aliases
        },
    }
    missing = expected - catalogue_names
    assert not missing


def test_production_catalogue_resolves_at_least_23_unique_comfort_heroes():
    """Lock the measured 23/36 coverage gain without fabricating absent dish substitutions."""
    bundle_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "ghar_re_service", "data", "bundle", "catalogue.json"
    )
    with open(bundle_path) as handle:
        catalogue_names = {row["name"] for row in json.load(handle)}
    authored_heroes = {row[2] for row in knowledge.COMFORT_HERO_MAP}
    resolved = {
        hero
        for hero in authored_heroes
        if (
            {knowledge.COMFORT_HERO_TO_DISH.get(hero, hero)}
            | knowledge.COMFORT_HERO_CATALOGUE_ALIASES.get(hero, set())
        )
        & catalogue_names
    }
    assert len(authored_heroes) == 36
    assert len(resolved) >= 23
