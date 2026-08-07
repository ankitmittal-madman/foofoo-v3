from types import SimpleNamespace

from ghar_re_core import contextual


def dish(*, total_mins=30, richness=None, methods=None, calories=300, heaviness=1, diet="veg", category=None):
    return SimpleNamespace(
        total_mins=total_mins,
        richness=richness or ["light"],
        cooking_method=methods or ["steamed"],
        calories=calories,
        heaviness=heaviness,
        diet=diet,
        dish_category=category or ["dal_lentil"],
    )


def signal(code, value, *, authority, allowed_use, confidence=1, correction="active"):
    return {
        "feature_code": code,
        "value": value,
        "authority": authority,
        "confidence": confidence,
        "sources": ["q15_objective" if code == "health_objective" else "q2_working_professionals"],
        "allowed_use": allowed_use,
        "correction_state": correction,
        "feature_version": "governed-context-v1",
    }


def test_no_governed_context_is_exact_noop():
    assert contextual.dish_contribution(dish(), {})["total"] == 0


def test_explicit_health_goal_prefers_light_candidate_without_filtering():
    ctx = {"governed_context_signals": [signal(
        "health_objective", "healthy_living", authority="explicit", allowed_use="strong_rank"
    )]}
    light = contextual.dish_contribution(dish(), ctx)
    rich = contextual.dish_contribution(
        dish(total_mins=70, richness=["creamy"], methods=["deep_fried"], calories=750, heaviness=3),
        ctx,
    )
    assert light["explicit"] > rich["explicit"]
    assert -0.05 <= rich["explicit"] <= light["explicit"] <= 0.05


def test_time_pressure_is_weaker_weekday_only_and_rejected_is_noop():
    pressure = signal(
        "weekday_time_pressure", 1, authority="inferred", allowed_use="soft_rank", confidence=0.65
    )
    quick = contextual.dish_contribution(
        dish(total_mins=25), {"weekday": "Monday", "governed_context_signals": [pressure]}
    )
    slow = contextual.dish_contribution(
        dish(total_mins=75), {"weekday": "Monday", "governed_context_signals": [pressure]}
    )
    weekend = contextual.dish_contribution(
        dish(total_mins=25), {"weekday": "Sunday", "governed_context_signals": [pressure]}
    )
    rejected = contextual.dish_contribution(
        dish(total_mins=25),
        {"weekday": "Monday", "governed_context_signals": [{**pressure, "correction_state": "rejected"}]},
    )
    assert 0 < quick["inferred"] <= 0.04
    assert -0.04 <= slow["inferred"] < 0
    assert weekend["total"] == 0
    assert rejected["total"] == 0


def test_geography_and_working_count_are_not_rank_features_by_themselves():
    context_only = signal(
        "working_professionals", 2, authority="explicit", allowed_use="context_input"
    )
    ctx = {
        "q3_home_state": "MP",
        "q4_current_city": "Mumbai",
        "governed_context_signals": [context_only],
    }
    assert contextual.dish_contribution(dish(), ctx)["total"] == 0


def test_health_goal_reaches_weekly_meal_class_ranking_as_bounded_context():
    ctx = {"day_type": "weekday", "governed_context_signals": [signal(
        "health_objective", "into_fitness", authority="explicit", allowed_use="strong_rank"
    )]}
    protein = contextual.class_contribution(
        "LD_HIGH_PROTEIN_VEG_PLATE", {"category": "modern_health"}, ctx
    )
    festive = contextual.class_contribution(
        "LD_FESTIVE_THALI", {"category": "festive_rich"}, ctx
    )
    assert protein["explicit"] == 0.08
    assert festive["explicit"] == -0.04
