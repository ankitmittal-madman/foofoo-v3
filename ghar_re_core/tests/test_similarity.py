"""
Tests for ghar_re_core.similarity (Core Spine SP-F6, Founder-directed closeout 2026-08-04).
"""
import json
import os

from ghar_re_core import similarity as SIM
from ghar_re_core.catalogue import Catalogue

_BUNDLE_PATH = os.path.normpath(os.path.join(
    os.path.dirname(__file__), "..", "..", "ghar_re_service", "data", "bundle", "catalogue.json"
))


def _real_catalogue():
    with open(_BUNDLE_PATH) as f:
        dishes = json.load(f)
    return Catalogue(dishes)


def test_cosine_of_identical_vectors_is_one():
    vec = {"onion": 1.5, "tomato": 0.8}
    assert abs(SIM.cosine(vec, vec) - 1.0) < 1e-9


def test_cosine_of_disjoint_vectors_is_zero():
    assert SIM.cosine({"onion": 1.0}, {"rice": 1.0}) == 0.0


def test_cosine_of_empty_vector_is_zero_not_an_error():
    assert SIM.cosine({}, {"onion": 1.0}) == 0.0
    assert SIM.cosine({}, {}) == 0.0


def test_idf_gives_rarer_ingredients_higher_weight():
    cat = _real_catalogue()
    idf = SIM.build_idf(cat)
    # 'salt' is in almost every dish; a rare regional ingredient should score higher.
    assert idf["salt"] < idf.get("bamboo_shoot", idf["salt"] + 1)


def test_cross_cuisine_similar_never_returns_same_cuisine_or_self():
    cat = _real_catalogue()
    idf = SIM.build_idf(cat)
    dish = cat.get("Butter Chicken")
    assert dish is not None
    results = SIM.cross_cuisine_similar(dish, cat, idf=idf, top_n=5)
    assert len(results) > 0
    for other, sim in results:
        assert other.cuisine != dish.cuisine
        assert other.name != dish.name
        assert 0.0 < sim <= 1.0
    # sorted descending
    sims = [s for _, s in results]
    assert sims == sorted(sims, reverse=True)


def test_cross_cuisine_similar_builds_its_own_idf_if_not_given():
    cat = _real_catalogue()
    dish = cat.get("Butter Chicken")
    results = SIM.cross_cuisine_similar(dish, cat, top_n=3)
    assert len(results) <= 3
