"""Local candidate pools and optional locally hosted Qdrant retrieval."""

from __future__ import annotations

import hashlib
import json
import math
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from .config import Settings
from .schemas import Candidate, RecommendationRequest


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

    def retrieve(self, request: RecommendationRequest) -> tuple[list[Candidate], list[str]]:
        candidates = [candidate.model_copy(deep=True) for candidate in request.candidates]
        sources = ["request"] if candidates else []
        if self.settings.candidate_pool_path:
            candidates.extend(self._from_file(Path(self.settings.candidate_pool_path)))
            sources.append("precomputed_pool")
        if self.settings.qdrant_url:
            candidates.extend(self._from_qdrant(request))
            sources.append("qdrant")

        deduplicated: dict[str, Candidate] = {}
        for candidate in candidates:
            deduplicated.setdefault(candidate.id, candidate)
        return list(deduplicated.values()), sources

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
            [request.meal_slot, request.region or "", *request.preferences, *request.pantry_items]
        )
        body = json.dumps(
            {
                "query": local_embedding(query),
                "limit": min(request.candidate_limit * 5, 100),
                "with_payload": True,
                "filter": {"must": [{"key": "meal_slots", "match": {"any": [request.meal_slot]}}]},
            }
        ).encode()
        url = f"{base.rstrip('/')}/collections/{self.settings.qdrant_collection}/points/query"
        req = urllib.request.Request(url, data=body, headers={"content-type": "application/json"})
        with urllib.request.urlopen(req, timeout=1.5) as response:  # noqa: S310 - local URL checked
            result: dict[str, Any] = json.load(response)
        result_body = result.get("result", {})
        points = result_body.get("points", []) if isinstance(result_body, dict) else result_body
        candidates = []
        for point in points:
            payload = dict(point.get("payload") or {})
            payload.setdefault("id", str(point.get("id")))
            candidates.append(Candidate.model_validate(payload))
        return candidates
