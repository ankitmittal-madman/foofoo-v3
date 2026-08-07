"""Safe optional loader and scorer for locally trained LightFM artifacts."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .schemas import Candidate, RecommendationRequest


class LightFMArtifactError(RuntimeError):
    """Artifact is missing, malformed, incompatible, or not eligible for this mode."""


@dataclass(frozen=True)
class LightFMScoreTrace:
    applied: bool
    scored_candidates: int
    model_version: str | None
    reason: str


class LightFMScorer:
    def __init__(self, artifact: dict[str, Any], *, allow_synthetic: bool, allow_unpromoted: bool):
        metadata = artifact.get("metadata", {})
        if metadata.get("format") not in {"foofoo-lightfm-v1", "foofoo-lightfm-v2"}:
            raise LightFMArtifactError("unsupported artifact format")
        if metadata.get("synthetic_only") and not allow_synthetic:
            raise LightFMArtifactError("synthetic artifact activation is disabled")
        if not metadata.get("promotion_gate_passed", False) and not allow_unpromoted:
            raise LightFMArtifactError("artifact did not pass promotion gates")
        self.artifact = artifact
        self.model = artifact["model"]
        self.user_features = artifact["user_features"]
        self.item_features = artifact["item_features"]
        self.user_id_map: dict[str, int] = artifact["user_id_map"]
        self.item_id_map: dict[str, int] = artifact["item_id_map"]
        self.version = str(metadata["model_version"])
        self.synthetic_only = bool(metadata.get("synthetic_only"))

    @classmethod
    def load(
        cls,
        path: Path,
        *,
        allow_synthetic: bool = False,
        allow_unpromoted: bool = False,
    ) -> LightFMScorer:
        if not path.is_file():
            raise LightFMArtifactError("artifact file does not exist")
        try:
            import joblib
        except ImportError as exc:
            raise LightFMArtifactError("joblib package is unavailable") from exc
        try:
            artifact = joblib.load(path)
        except Exception as exc:
            raise LightFMArtifactError("artifact could not be loaded") from exc
        if not isinstance(artifact, dict):
            raise LightFMArtifactError("artifact root must be a mapping")
        return cls(
            artifact,
            allow_synthetic=allow_synthetic,
            allow_unpromoted=allow_unpromoted,
        )

    def _user_index(self, household_id: str) -> int | None:
        for candidate in (household_id, f"dataset_1:{household_id}", f"dataset_2:{household_id}"):
            if candidate in self.user_id_map:
                return self.user_id_map[candidate]
        return None

    def apply(
        self,
        candidates: list[Candidate],
        request: RecommendationRequest,
        *,
        blend_weight: float,
    ) -> tuple[list[Candidate], LightFMScoreTrace]:
        user_index = self._user_index(request.household_id)
        if user_index is None:
            return candidates, LightFMScoreTrace(False, 0, self.version, "unknown_household")
        matched = [candidate for candidate in candidates if candidate.id in self.item_id_map]
        if not matched:
            return candidates, LightFMScoreTrace(False, 0, self.version, "no_known_candidates")
        try:
            import numpy as np
        except ImportError as exc:
            raise LightFMArtifactError("numpy package is unavailable") from exc
        item_indices = np.array([self.item_id_map[candidate.id] for candidate in matched])
        user_indices = np.full(len(item_indices), user_index)
        raw_scores = self.model.predict(
            user_indices,
            item_indices,
            user_features=self.user_features,
            item_features=self.item_features,
            num_threads=1,
        )
        normalized = [1.0 / (1.0 + math.exp(-float(score))) for score in raw_scores]
        by_id = dict(zip((candidate.id for candidate in matched), normalized, strict=True))
        output = []
        for candidate in candidates:
            clone = candidate.model_copy(deep=True)
            if candidate.id in by_id:
                clone.collaborative_score = max(
                    0.0,
                    min(
                        1.0,
                        (1.0 - blend_weight) * candidate.collaborative_score
                        + blend_weight * by_id[candidate.id],
                    ),
                )
            output.append(clone)
        return output, LightFMScoreTrace(True, len(matched), self.version, "scored")
