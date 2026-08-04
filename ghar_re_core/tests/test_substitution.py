"""
Tests for ghar_re_core.substitution (Core Spine SP-F14, Founder-directed closeout 2026-08-04).
"""
import json
import os

from ghar_re_core import substitution as SUB


def test_veg_swap_lookup_returns_curated_pair():
    subs = SUB.find_substitutes("Butter Chicken", "veg_swap")
    assert ("Paneer Butter Masala", "veg_swap", subs[0][2]) in subs


def test_unknown_dish_returns_empty_not_a_guess():
    assert SUB.find_substitutes("Some Dish That Does Not Exist") == []


def test_has_substitute_convenience():
    assert SUB.has_substitute("Chicken Curry") is True
    assert SUB.has_substitute("Chicken Curry", "veg_swap") is True
    assert SUB.has_substitute("Chicken Curry", "jain") is False


def test_variant_type_filter_narrows_results():
    all_subs = SUB.find_substitutes("Chicken Curry")
    veg_only = SUB.find_substitutes("Chicken Curry", "veg_swap")
    protein_only = SUB.find_substitutes("Chicken Curry", "protein_swap")
    assert len(veg_only) + len(protein_only) == len(all_subs)
    assert all(v == "veg_swap" for _, v, _ in veg_only)
    assert all(v == "protein_swap" for _, v, _ in protein_only)


def test_every_curated_pair_resolves_against_the_real_catalogue():
    """Every from_dish/to_dish in the curated CSV must exist in the real 810-dish catalogue —
    a stale/typo'd dish name would silently never fire, which is worse than an empty result.
    Reads the committed bundle directly (no ghar_re_service import) to keep this a pure
    ghar_re_core test."""
    bundle_path = os.path.normpath(os.path.join(
        os.path.dirname(__file__), "..", "..", "ghar_re_service", "data", "bundle", "catalogue.json"
    ))
    with open(bundle_path) as f:
        dishes = json.load(f)
    names = {d["name"] for d in dishes}
    checked = 0
    for frm, to, _vtype, _note in SUB._SUBSTITUTIONS:
        assert frm in names, "from_dish %r not in real catalogue" % frm
        assert to in names, "to_dish %r not in real catalogue" % to
        checked += 1
    assert checked == len(SUB._SUBSTITUTIONS)
    assert checked >= 13
