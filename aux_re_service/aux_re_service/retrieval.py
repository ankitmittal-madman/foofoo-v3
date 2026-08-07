"""Local candidate pools and optional locally hosted Qdrant retrieval."""

from __future__ import annotations

import hashlib
import json
import math
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import Settings
from .knowledge_graph import LocalFoodKnowledgeGraph
from .schemas import Candidate, RecommendationRequest

REGION_GROUPS = {
    "maharashtra": "west",
    "gujarat": "west",
    "goa": "west",
    "rajasthan": "north",
    "punjab": "north",
    "delhi": "north",
    "haryana": "north",
    "uttar pradesh": "north",
    "uttarakhand": "north",
    "himachal pradesh": "north",
    "karnataka": "south",
    "kerala": "south",
    "tamil nadu": "south",
    "telangana": "south",
    "andhra pradesh": "south",
    "west bengal": "east",
    "odisha": "east",
    "bihar": "east",
    "assam": "east",
    "madhya pradesh": "central",
    "chhattisgarh": "central",
}


def local_embedding(text: str, dimensions: int = 64) -> list[float]:
    """Stable feature-hash embedding; local, dependency-free, and deterministic."""
    vector = [0.0] * dimensions
    for token in text.casefold().split():
        digest = hashlib.sha256(token.encode()).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        vector[index] += -1.0 if digest[4] & 1 else 1.0
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


class CandidateRetriever:
    def __init__(self, settings: Settings):
        self.settings = settings

    def retrieve(self, request: RecommendationRequest) -> RetrievalResult:
        candidates = [candidate.model_copy(deep=True) for candidate in request.candidates]
        sources = ["request"] if candidates else []
        failures: dict[str, str] = {}
        if self.settings.candidate_pool_path:
            try:
                candidates.extend(self._from_file(Path(self.settings.candidate_pool_path)))
                sources.append("precomputed_pool")
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                failures["precomputed_pool"] = type(exc).__name__
        if self.settings.qdrant_url and self.settings.qdrant_enabled:
            try:
                candidates.extend(self._from_qdrant(request))
                sources.append("qdrant")
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                failures["qdrant"] = type(exc).__name__
        if self.settings.knowledge_graph_path:
            try:
                graph = LocalFoodKnowledgeGraph(Path(self.settings.knowledge_graph_path))
                candidates.extend(graph.expand(candidates, request, request.candidate_limit * 3))
                sources.append("knowledge_graph")
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                failures["knowledge_graph"] = type(exc).__name__

        deduplicated: dict[str, Candidate] = {}
        for candidate in candidates:
            deduplicated.setdefault(candidate.id, candidate)
        return RetrievalResult(list(deduplicated.values()), sources, failures)

    @staticmethod
    def _from_file(path: Path) -> list[Candidate]:
        payload = json.loads(path.read_text())
        rows = payload if isinstance(payload, list) else payload.get("candidates", [])
        return [Candidate.model_validate(row) for row in rows]

    def _from_qdrant(self, request: RecommendationRequest) -> list[Candidate]:
        base = self.settings.qdrant_url or ""
        parsed = urllib.parse.urlparse(base)
        if parsed.scheme not in {"http", "https"} or parsed.hostname not in {
            "localhost",
            "127.0.0.1",
            "::1",
            "qdrant",
        }:
            raise ValueError("AUX_REC_QDRANT_URL must point to the local Qdrant service")
        query = " ".join(
            [
                request.meal_slot,
                request.region or "",
                request.season or "",
                request.occasion or "",
                request.day_type or "",
                *request.preferences,
                *request.pantry_items,
                *request.leftover_items,
            ]
        )
        must: list[dict[str, Any]] = [{"key": "meal_slots", "match": {"any": [request.meal_slot]}}]
        if request.region:
            region = request.region.casefold()
            must.append(
                {
                    "key": "regions",
                    "match": {"any": sorted({region, REGION_GROUPS.get(region, region)})},
                }
            )
        restrictions = {value.casefold() for value in request.restrictions}
        if restrictions & {"vegetarian", "veg"}:
            must.append({"key": "diet_types", "match": {"any": ["vegetarian", "vegan", "jain"]}})
        elif "vegan" in restrictions:
            must.append({"key": "diet_types", "match": {"any": ["vegan"]}})
        elif "jain" in restrictions:
            must.append({"key": "diet_types", "match": {"any": ["jain"]}})
        forbidden_allergens = sorted(
            {value.casefold().replace("groundnut", "peanut") for value in request.allergies}
        )
        unavailable = sorted({value.casefold() for value in request.unavailable_ingredients})
        must_not = []
        if forbidden_allergens:
            must_not.append({"key": "allergens", "match": {"any": forbidden_allergens}})
        if unavailable:
            must_not.append({"key": "ingredients", "match": {"any": unavailable}})
        query_filter: dict[str, Any] = {"must": must}
        if must_not:
            query_filter["must_not"] = must_not
        body = json.dumps(
            {
                "query": local_embedding(query),
                "limit": min(request.candidate_limit * 5, 100),
                "with_payload": True,
                "filter": query_filter,
            }
        ).encode()
        url = f"{base.rstrip('/')}/collections/{self.settings.qdrant_collection}/points/query"
        req = urllib.request.Request(url, data=body, headers={"content-type": "application/json"})
        with urllib.request.urlopen(
            req, timeout=self.settings.retrieval_timeout_seconds
        ) as response:  # noqa: S310 - local URL checked
            result: dict[str, Any] = json.load(response)
        result_body = result.get("result", {})
        points = result_body.get("points", []) if isinstance(result_body, dict) else result_body
        candidates = []
        for point in points:
            payload = dict(point.get("payload") or {})
            payload.setdefault("id", str(point.get("id")))
            candidates.append(Candidate.model_validate(payload))
        return candidates


@dataclass(frozen=True)
class RetrievalResult:
    candidates: list[Candidate]
    sources: list[str]
    failures: dict[str, str]
