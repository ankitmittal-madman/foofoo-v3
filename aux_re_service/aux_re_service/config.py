"""Environment-only configuration, reloaded for every request for instant rollback."""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import StrEnum


class Mode(StrEnum):
    SHADOW = "shadow"
    COMPARE = "compare"
    ACTIVE = "active"


def _bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized not in {"true", "false"}:
        raise ValueError(f"{name} must be true or false")
    return normalized == "true"


def _float(name: str, default: float, *, minimum: float = 0.0, maximum: float = 1.0) -> float:
    value = float(os.getenv(name, str(default)))
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return value


@dataclass(frozen=True)
class Settings:
    enabled: bool
    mode: Mode
    min_delta: float
    min_confidence: float
    require_constraint_pass: bool
    use_local_reranker: bool
    log_all: bool
    allow_override: bool
    qdrant_url: str | None
    qdrant_collection: str
    candidate_pool_path: str | None
    model_artifact_dir: str | None

    @classmethod
    def from_env(cls) -> Settings:
        mode_raw = os.getenv("AUX_REC_MODE", "shadow").strip().lower()
        try:
            mode = Mode(mode_raw)
        except ValueError as exc:
            raise ValueError("AUX_REC_MODE must be shadow, compare, or active") from exc
        return cls(
            enabled=_bool("AUX_REC_ENABLED", False),
            mode=mode,
            min_delta=_float("AUX_REC_MIN_DELTA", 0.05),
            min_confidence=_float("AUX_REC_MIN_CONFIDENCE", 0.55),
            require_constraint_pass=_bool("AUX_REC_REQUIRE_CONSTRAINT_PASS", True),
            use_local_reranker=_bool("AUX_REC_USE_LOCAL_RERANKER", True),
            log_all=_bool("AUX_REC_LOG_ALL", True),
            allow_override=_bool("AUX_REC_ALLOW_OVERRIDE", False),
            qdrant_url=os.getenv("AUX_REC_QDRANT_URL") or None,
            qdrant_collection=os.getenv("AUX_REC_QDRANT_COLLECTION", "foofoo_recipes"),
            candidate_pool_path=os.getenv("AUX_REC_CANDIDATE_POOL_PATH") or None,
            model_artifact_dir=os.getenv("AUX_REC_MODEL_ARTIFACT_DIR") or None,
        )
