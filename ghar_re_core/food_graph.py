"""Traversable dish–ingredient–substitution graph over the versioned catalogue snapshot."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from ghar_re_core.catalogue import (
    HIDDEN_DERIVATIVE_ALLERGENS,
    Catalogue,
    canonical_allergen,
    dish_allergens,
    ingredient_info,
)
from ghar_re_core.substitution import find_substitutes


@dataclass(frozen=True)
class GraphEdge:
    source: str
    target: str
    relation: str
    provenance: str


class FoodGraph:
    """Bounded traversal without introducing a second source of truth or unsafe inferred edges."""

    def __init__(self, catalogue: Catalogue | None = None):
        self.catalogue = catalogue or Catalogue()
        self._ingredient_to_dishes: dict[str, list[str]] = {}
        for dish in self.catalogue:
            for ingredient in dish.ingredient_names:
                self._ingredient_to_dishes.setdefault(ingredient, []).append(dish.name)

    def neighbors(self, node: str) -> list[GraphEdge]:
        if node.startswith("ingredient:"):
            ingredient = node.removeprefix("ingredient:")
            return [
                GraphEdge(node, name, "ingredient_of", "catalogue.dish_ingredients")
                for name in sorted(self._ingredient_to_dishes.get(ingredient, []))
            ]
        edges = [
            GraphEdge(node, substitute, variant_type, f"dish_substitutions_v1.csv: {note}")
            for substitute, variant_type, note in find_substitutes(node)
        ]
        dish = self.catalogue.get(node)
        if dish is None:
            return edges
        edges.extend(
            GraphEdge(node, f"ingredient:{ingredient}", "contains", "catalogue.dish_ingredients")
            for ingredient in sorted(dish.ingredient_names)
        )
        return edges

    def find_path(self, source: str, target: str, max_depth: int = 4) -> list[GraphEdge]:
        """Breadth-first, cycle-safe path lookup bounded to protect request latency."""
        if max_depth < 1 or max_depth > 6:
            raise ValueError("max_depth must be between 1 and 6")
        queue: deque[tuple[str, list[GraphEdge]]] = deque([(source, [])])
        visited = {source}
        while queue:
            node, path = queue.popleft()
            if len(path) >= max_depth:
                continue
            for edge in self.neighbors(node):
                next_path = [*path, edge]
                if edge.target == target:
                    return next_path
                if edge.target not in visited:
                    visited.add(edge.target)
                    queue.append((edge.target, next_path))
        return []

    def allergen_provenance(self, dish_name: str) -> dict[str, list[str]]:
        """Return each propagated allergen with the ingredient nodes that caused it."""
        dish = self.catalogue.get(dish_name)
        if dish is None:
            return {}
        allergens = dish_allergens(dish)
        result: dict[str, list[str]] = {allergen: [] for allergen in allergens}
        for ingredient in dish.ingredient_names:
            info = ingredient_info(ingredient)
            allergen = (
                canonical_allergen(info.get("allergen_type"))
                if info.get("is_allergen") and info.get("allergen_type")
                else None
            )
            hidden = canonical_allergen(HIDDEN_DERIVATIVE_ALLERGENS.get(ingredient, "")) or None
            for value in (allergen, hidden):
                if value in result:
                    result[value].append(f"ingredient:{ingredient}")
        return result
