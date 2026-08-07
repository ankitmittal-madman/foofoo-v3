from types import SimpleNamespace

from ghar_re_core import temporal


def _dish(name="Paneer Butter Masala", cuisine="punjabi", richness=None, methods=None):
    return SimpleNamespace(
        name=name,
        cuisine=cuisine,
        richness=richness or ["creamy", "buttery"],
        cooking_method=methods or ["simmered"],
    )


def _row(**overrides):
    value = {
        "meal_slot": "lunch",
        "day_type": "weekday",
        "dimension_code": "dish",
        "entity_key": "paneer butter masala",
        "explicit_positive_count_28d": 1,
        "explicit_negative_count_28d": 0,
        "exposure_count_14d": 0,
        "positive_meal_dates_28d": ["2026-08-05"],
        "negative_meal_dates_28d": [],
        "exposure_meal_dates_14d": [],
    }
    value.update(overrides)
    return value


def _context(rows, **overrides):
    value = {
        "slot": "lunch",
        "weekday": "Friday",
        "date": "2026-08-07",
        "temporal_attribute_state": rows,
    }
    value.update(overrides)
    return value


def test_recent_dish_outcome_penalizes_only_matching_meal_moment():
    dish = _dish()
    lunch = temporal.dish_contribution(dish, _context([_row()]))
    dinner = temporal.dish_contribution(dish, _context([_row()], slot="dinner"))
    assert lunch["explicit"] < 0
    assert lunch["total"] < 0
    assert dinner["total"] == 0


def test_same_date_is_not_treated_as_prior_history():
    row = _row(positive_meal_dates_28d=["2026-08-07"])
    assert temporal.dish_contribution(_dish(), _context([row]))["total"] == 0


def test_repeated_observed_spacing_can_make_a_dish_gently_due():
    row = _row(
        explicit_positive_count_28d=2,
        positive_meal_dates_28d=["2026-07-28", "2026-08-02"],
        mean_positive_spacing_days=5,
    )
    result = temporal.dish_contribution(_dish(), _context([row]))
    assert 0 < result["due"] <= 0.08
    assert result["total"] == result["due"]


def test_exposure_pressure_is_weaker_than_explicit_dish_spacing():
    explicit = temporal.dish_contribution(_dish(), _context([_row()]))
    exposure_row = _row(
        explicit_positive_count_28d=0,
        positive_meal_dates_28d=[],
        exposure_count_14d=4,
        exposure_meal_dates_14d=["2026-08-05"],
    )
    exposure = temporal.dish_contribution(_dish(), _context([exposure_row]))
    assert explicit["total"] < exposure["total"] < 0


def test_attribute_enrichment_density_cannot_multiply_one_dimension():
    creamy = _row(
        dimension_code="richness",
        entity_key="creamy",
        positive_meal_dates_28d=["2026-08-06"],
    )
    buttery = _row(
        dimension_code="richness",
        entity_key="buttery",
        positive_meal_dates_28d=["2026-08-06"],
    )
    one = temporal.dish_contribution(_dish(), _context([creamy]))
    two = temporal.dish_contribution(_dish(), _context([creamy, buttery]))
    assert two["total"] == one["total"]
    assert len(two["dimensions"]) == 1


def test_weekday_and_weekend_cuisine_rhythms_are_separate():
    row = _row(
        dimension_code="cuisine",
        entity_key="punjabi",
        positive_meal_dates_28d=["2026-08-05"],
    )
    weekday = temporal.dish_contribution(_dish(), _context([row]))
    weekend = temporal.dish_contribution(
        _dish(), _context([row], weekday="Saturday", date="2026-08-08")
    )
    assert weekday["total"] < 0
    assert weekend["total"] == 0
