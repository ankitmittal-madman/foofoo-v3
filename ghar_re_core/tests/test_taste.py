from ghar_re_core.catalogue import Catalogue
from ghar_re_core.taste import TRANSFER_SCALE, canonicalize_names, expand_preferences


def test_alias_feedback_is_canonical_and_exact_signal_wins():
    catalogue = Catalogue()
    # Exercise the same normalized synonym index used by the 810-item serving catalogue.
    catalogue.by_normalized_name["dal fry"] = catalogue.get("Dal Tadka")
    expanded = expand_preferences({"  DAL FRY ": 1.0}, catalogue)
    assert expanded["Dal Tadka"] == 1.0
    assert max(abs(value) for name, value in expanded.items() if name != "Dal Tadka") <= TRANSFER_SCALE


def test_related_dish_gets_bounded_transfer_but_unrelated_dish_does_not():
    catalogue = Catalogue()
    expanded = expand_preferences({"Moong Dal Khichdi": 1.0}, catalogue)

    assert 0 < expanded["Lauki Khichdi"] < 1.0
    assert "Egg Bhurji" not in expanded


def test_negative_feedback_transfers_and_canonicalizes_exclusions():
    catalogue = Catalogue()
    expanded = expand_preferences({"Moong Dal Khichdi": -1.0}, catalogue)

    assert -1.0 < expanded["Lauki Khichdi"] < 0
    assert canonicalize_names(["  moong dal khichdi  ", "Moong Dal Khichdi"], catalogue) == [
        "Moong Dal Khichdi"
    ]


def test_class_and_semantic_tag_affinities_generalize_to_unseen_dishes():
    catalogue = Catalogue()
    expanded = expand_preferences(
        {},
        catalogue,
        preference_by_class={"BF_EGG_FAST": 0.8},
        preference_by_tag={"dish_category:egg_dish": 0.6},
    )

    assert 0 < expanded["Egg Bhurji"] <= TRANSFER_SCALE
    assert "Moong Dal Khichdi" not in expanded


def test_exact_dish_feedback_remains_authoritative_over_semantic_projection():
    catalogue = Catalogue()
    expanded = expand_preferences(
        {"Egg Bhurji": -1.0},
        catalogue,
        preference_by_class={"BF_EGG_FAST": 1.0},
        preference_by_tag={"dish_category:egg_dish": 1.0},
    )

    assert expanded["Egg Bhurji"] == -1.0
