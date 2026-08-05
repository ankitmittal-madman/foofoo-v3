from ghar_re_core import fixtures
from ghar_re_core.catalogue import Catalogue
from ghar_re_core.meal_episode import (
    EPISODE_MODEL_VERSION,
    build_class_meal_episodes,
    build_meal_episodes,
    infer_intent,
)
from ghar_re_core.pipeline import make_context, recommend


def _household():
    return dict(fixtures.HOUSEHOLDS[0])


def test_intent_is_normalized_and_context_sensitive():
    household = _household()
    normal = infer_intent(household, make_context(slot="dinner", weekday="Monday"))
    rushed = infer_intent(
        household,
        {
            **make_context(slot="dinner", weekday="Monday", is_raining=True),
            "time_budget_minutes": 20,
        },
    )
    assert abs(sum(normal.values()) - 1.0) < 1e-5
    assert abs(sum(rushed.values()) - 1.0) < 1e-5
    assert rushed["quick"] > normal["quick"]
    assert rushed["comfort"] > normal["comfort"]


def test_episode_is_complete_replayable_and_practicality_ranked():
    household = _household()
    ctx = {**make_context(slot="dinner", weekday="Monday"), "time_budget_minutes": 35}
    result = recommend(household, ctx, Catalogue())
    episodes = build_meal_episodes(result["plates"], household, ctx)

    assert episodes
    assert [item["rank"] for item in episodes] == list(range(1, len(episodes) + 1))
    assert len({item["episode_hash"] for item in episodes}) == len(episodes)
    assert all(item["components"] for item in episodes)
    assert all(item["grammar_code"] in {"SINGLE_PRIMARY", "BASE_WITH_SIDES"} for item in episodes)
    assert all(item["grammar_version"] == 1 for item in episodes)
    assert all(
        component["grammar_role"] in {"primary", "side"}
        for item in episodes
        for component in item["components"]
    )
    assert all(0 <= item["predictions"]["p_success"] <= 1 for item in episodes)
    assert all(item["predictions"]["model_version"] == EPISODE_MODEL_VERSION for item in episodes)
    assert all(item["practicality"]["active_minutes"] >= 0 for item in episodes)
    assert [item["predictions"]["p_success"] for item in episodes] == sorted(
        [item["predictions"]["p_success"] for item in episodes], reverse=True
    )


def test_episode_hash_is_deterministic_for_same_content():
    household = _household()
    ctx = make_context(slot="dinner", weekday="Monday")
    result = recommend(household, ctx, Catalogue())
    first = build_meal_episodes(result["plates"], household, ctx)
    second = build_meal_episodes(result["plates"], household, ctx)
    assert [item["episode_hash"] for item in first] == [item["episode_hash"] for item in second]


def test_class_episode_fallback_preserves_selected_class():
    from ghar_re_core import knowledge

    household = _household()
    catalogue = Catalogue()
    ctx = make_context(slot="dinner", weekday="Monday")
    source = recommend(household, ctx, catalogue)
    class_code = knowledge.dish_to_class_code(
        source["plates"][0].get("hero", source["plates"][0].get("dry")).name
    )
    assert class_code
    episodes = build_class_meal_episodes(household, ctx, class_code, catalogue, count=3)
    assert episodes
    assert all(
        class_code in knowledge.dish_to_class_codes(component["dish_name"])
        for episode in episodes
        for component in episode["components"]
        if component["dish_id"] is not None
    )
