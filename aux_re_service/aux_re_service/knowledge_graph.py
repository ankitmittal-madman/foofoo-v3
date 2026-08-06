"""Small local Indian-food graph used for deterministic candidate expansion."""

from __future__ import annotations

import json
from pathlib import Path

from .schemas import Candidate, RecommendationRequest


class LocalFoodKnowledgeGraph:
    """Loads governed candidate nodes and typed adjacency from a local JSON artifact.

    Format: ``{"candidates": {"dish-id": {...}}, "relations": {"dish-id": ["other-id"]}}``.
    The artifact is loaded per request today so environment rollbacks are immediate; a versioned,
    immutable startup cache is an explicit production follow-up.
    """

    def __init__(self, path: Path):
        raw = json.loads(path.read_text())
        self.candidates = {
            key: Candidate.model_validate({"id": key, **value})
            for key, value in raw.get("candidates", {}).items()
        }
        self.relations = {
            key: tuple(str(target) for target in targets)
            for key, targets in raw.get("relations", {}).items()
        }

    def expand(
        self, seeds: list[Candidate], request: RecommendationRequest, limit: int
    ) -> list[Candidate]:
        ids: list[str] = []
        for seed in seeds:
            ids.extend(self.relations.get(seed.id, ()))

        # Cold-start lookup: deterministic contextual node match when there are no seed edges.
        if not ids:
            region = request.region.casefold() if request.region else None
            slot = request.meal_slot.casefold()
            ids.extend(
                candidate_id
                for candidate_id, candidate in self.candidates.items()
                if (
                    not candidate.meal_slots
                    or slot in {value.casefold() for value in candidate.meal_slots}
                )
                and (not region or region in {value.casefold() for value in candidate.regions})
            )
        seen = {seed.id for seed in seeds}
        return [
            self.candidates[candidate_id].model_copy(deep=True)
            for candidate_id in ids
            if candidate_id in self.candidates and candidate_id not in seen
        ][:limit]
