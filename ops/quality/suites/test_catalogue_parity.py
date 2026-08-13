"""Unit tests for the WP-24 A.1 catalogue parity comparison.

Covers the behaviours the report's credibility depends on: that a systemic hardcoded default is
distinguishable from scattered per-dish drift, that "richer" is reported in both directions, and
that 0/False are never confused with "value absent".
"""

from ops.recommendation import catalogue_parity as parity


def _dish(name: str, **overrides: object) -> dict[str, object]:
    """Build a minimal dish in Ghar's catalogue-constructor shape."""
    base: dict[str, object] = {
        "name": name,
        "diet": "veg",
        "jain_compatible": "N",
        "farali_compatible": False,
        "vegan_compatible": False,
        "sig_band": "state_icon",
        "spice_level": 2,
        "sweetness": 0,
        "heaviness": 3,
        "hero_role": "single",
        "cuisine": "punjabi",
        "state_origin": "punjab",
        "meal_type": ["lunch"],
        "cooking_method": ["sauteed"],
        "texture": ["soft"],
        "richness": ["rich"],
        "weather_affinity": ["winter"],
        "scope_tier": "core",
        "prep_mins": 10,
        "cook_mins": 20,
        "total_mins": 30,
        "difficulty": "medium",
        "calories": 300,
        "serving_size": "1 bowl",
        "primary_taste": ["savoury"],
        "mouthfeel": ["creamy"],
        "aroma_profile": ["herby"],
        "fermentation": "none",
        "serving_temp": "hot",
    }
    base.update(overrides)
    return base


def test_identical_catalogues_report_no_deltas():
    dishes = [_dish("Butter Chicken"), _dish("Dal Makhani")]
    report = parity.compare_catalogues(dishes, [_dish(d["name"]) for d in dishes])
    assert report.matched_count == 2
    assert report.deltas == []
    assert report.bundle_only_names == []
    assert report.publication_only_names == []


def test_name_matching_is_case_and_whitespace_insensitive():
    report = parity.compare_catalogues(
        [_dish("Butter  Chicken")],
        [_dish("butter chicken")],
    )
    assert report.matched_count == 1
    assert report.bundle_only_names == []


def test_set_differences_are_reported_in_both_directions():
    report = parity.compare_catalogues(
        [_dish("Only In Bundle"), _dish("Shared")],
        [_dish("Shared"), _dish("Only In Publication")],
    )
    assert report.bundle_only_names == ["only in bundle"]
    assert report.publication_only_names == ["only in publication"]
    assert report.matched_count == 1


def test_missing_publication_value_is_bundle_richer():
    report = parity.compare_catalogues(
        [_dish("Shared", sig_band="national_icon")],
        [_dish("Shared", sig_band=None)],
    )
    (delta,) = [d for d in report.deltas if d.field_name == "sig_band"]
    assert delta.direction == parity.DIRECTION_BUNDLE_RICHER
    assert delta.severity == "scoring"


def test_missing_bundle_value_is_publication_richer():
    report = parity.compare_catalogues(
        [_dish("Shared", aroma_profile=[])],
        [_dish("Shared", aroma_profile=["smoky"])],
    )
    (delta,) = [d for d in report.deltas if d.field_name == "aroma_profile"]
    assert delta.direction == parity.DIRECTION_PUBLICATION_RICHER


def test_two_present_but_different_values_are_a_conflict():
    report = parity.compare_catalogues(
        [_dish("Shared", diet="veg")],
        [_dish("Shared", diet="non_veg")],
    )
    (delta,) = [d for d in report.deltas if d.field_name == "diet"]
    assert delta.direction == parity.DIRECTION_CONFLICT
    assert delta.severity == "safety"


def test_zero_is_a_real_value_not_an_absence():
    """A spice_level of 0 differing from 3 is a conflict, never 'publication missing a value'.

    Collapsing 0 into "empty" would hide exactly the default-substitution this tool exists to find.
    """
    report = parity.compare_catalogues(
        [_dish("Shared", spice_level=3)],
        [_dish("Shared", spice_level=0)],
    )
    (delta,) = [d for d in report.deltas if d.field_name == "spice_level"]
    assert delta.direction == parity.DIRECTION_CONFLICT


def test_list_fields_compare_order_insensitively():
    report = parity.compare_catalogues(
        [_dish("Shared", meal_type=["lunch", "dinner"])],
        [_dish("Shared", meal_type=["dinner", "lunch"])],
    )
    assert [d for d in report.deltas if d.field_name == "meal_type"] == []


def test_systemic_field_is_separated_from_scattered_drift():
    """A field wrong on every dish is a mapping bug; one wrong on a single dish is data drift."""
    bundle = [_dish(f"Dish {index}") for index in range(10)]
    # sig_band absent on all 10 (the WP-24 §3 hardcoded-default shape); calories differ on one.
    publication = [_dish(f"Dish {index}", sig_band=None) for index in range(10)]
    publication[0] = _dish("Dish 0", sig_band=None, calories=999)

    report = parity.compare_catalogues(bundle, publication)
    systemic = report.systemic_fields()
    assert "sig_band" in systemic
    assert "calories" not in systemic
    assert report.deltas_by_field()["sig_band"] == 10
    assert report.deltas_by_field()["calories"] == 1


def test_severity_counts_group_correctly():
    report = parity.compare_catalogues(
        [_dish("Shared", diet="veg", sig_band="national_icon", prep_mins=10, calories=300)],
        [_dish("Shared", diet="non_veg", sig_band=None, prep_mins=0, calories=None)],
    )
    counts = report.deltas_by_severity()
    assert counts["safety"] == 1
    assert counts["scoring"] == 1
    assert counts["effort"] == 1
    assert counts["display"] == 1


def test_duplicate_bundle_names_do_not_silently_overwrite():
    """First occurrence wins; a collision must not change the matched count."""
    report = parity.compare_catalogues(
        [_dish("Same Name", calories=100), _dish("Same Name", calories=200)],
        [_dish("Same Name", calories=100)],
    )
    assert report.bundle_count == 1
    assert report.matched_count == 1
    assert [d for d in report.deltas if d.field_name == "calories"] == []


def test_format_report_names_systemic_fields():
    bundle = [_dish(f"Dish {index}") for index in range(5)]
    publication = [_dish(f"Dish {index}", sig_band=None) for index in range(5)]
    text = parity.format_report(parity.compare_catalogues(bundle, publication))
    assert "SYSTEMIC" in text
    assert "sig_band" in text
    assert "Matched by name:     5" in text
