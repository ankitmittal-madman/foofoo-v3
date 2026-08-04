import pytest

from ghar_re_core.food_graph import FoodGraph


def test_substitution_path_carries_provenance():
    path = FoodGraph().find_path("Butter Chicken", "Paneer Butter Masala")
    assert len(path) == 1
    assert path[0].relation == "veg_swap"
    assert "dish_substitutions_v1.csv" in path[0].provenance


def test_graph_can_traverse_dish_to_ingredient_to_related_dish():
    graph = FoodGraph()
    source = graph.catalogue.get("Rajma")
    assert source is not None
    ingredient = source.ingredient_names[0]
    related = [name for name in graph._ingredient_to_dishes[ingredient] if name != source.name]
    if not related:
        pytest.skip("golden catalogue has no second dish for this ingredient")
    path = graph.find_path(source.name, related[0], max_depth=2)
    assert [edge.relation for edge in path] == ["contains", "ingredient_of"]


def test_graph_rejects_unbounded_traversal():
    with pytest.raises(ValueError):
        FoodGraph().find_path("Rajma", "Poha", max_depth=20)
