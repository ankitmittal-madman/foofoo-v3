"""Environment-only configuration, reloaded for every request for instant rollback."""

from __future__ import annotations

import os
import re
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
    catalogue_publication_version: str | None = None
    service_secret: str | None = None
    knowledge_graph_path: str | None = None
    retrieval_timeout_seconds: float = 1.5
    qdrant_enabled: bool = True
    embedder_enabled: bool = True
    lightfm_enabled: bool = False
    lightfm_artifact_path: str | None = None
    lightfm_weight: float = 0.35
    lightfm_allow_synthetic: bool = False
    lightfm_allow_unpromoted: bool = False
    feedback_enabled: bool = False
    feedback_path: str | None = None
    experiment_enabled: bool = False
    experiment_percent: float = 0.0
    experiment_salt: str = "foofoo-aux-v1"
    lightgcn_enabled: bool = False
    kgat_enabled: bool = False

    @classmethod
    def from_env(cls) -> Settings:
        mode_raw = os.getenv("AUX_REC_MODE", "shadow").strip().lower()
        try:
            mode = Mode(mode_raw)
        except ValueError as exc:
            raise ValueError("AUX_REC_MODE must be shadow, compare, or active") from exc
        settings = cls(
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
            catalogue_publication_version=(
                os.getenv("AUX_REC_CATALOGUE_PUBLICATION_VERSION") or None
            ),
            service_secret=os.getenv("AUX_REC_SERVICE_SECRET") or None,
            candidate_pool_path=os.getenv("AUX_REC_CANDIDATE_POOL_PATH") or None,
            model_artifact_dir=os.getenv("AUX_REC_MODEL_ARTIFACT_DIR") or None,
            knowledge_graph_path=os.getenv("AUX_REC_KNOWLEDGE_GRAPH_PATH") or None,
            retrieval_timeout_seconds=_float(
                "AUX_REC_RETRIEVAL_TIMEOUT_SECONDS", 1.5, minimum=0.1, maximum=10.0
            ),
            qdrant_enabled=_bool("AUX_REC_MODEL_QDRANT_ENABLED", True),
            embedder_enabled=_bool("AUX_REC_MODEL_EMBEDDER_ENABLED", True),
            lightfm_enabled=_bool("AUX_REC_MODEL_LIGHTFM_ENABLED", False),
            lightfm_artifact_path=os.getenv("AUX_REC_LIGHTFM_ARTIFACT_PATH") or None,
            lightfm_weight=_float("AUX_REC_LIGHTFM_WEIGHT", 0.35),
            lightfm_allow_synthetic=_bool("AUX_REC_LIGHTFM_ALLOW_SYNTHETIC", False),
            lightfm_allow_unpromoted=_bool("AUX_REC_LIGHTFM_ALLOW_UNPROMOTED", False),
            feedback_enabled=_bool("AUX_REC_FEEDBACK_ENABLED", False),
            feedback_path=os.getenv("AUX_REC_FEEDBACK_PATH") or None,
            experiment_enabled=_bool("AUX_REC_EXPERIMENT_ENABLED", False),
            experiment_percent=_float("AUX_REC_EXPERIMENT_PERCENT", 0.0),
            experiment_salt=os.getenv("AUX_REC_EXPERIMENT_SALT", "foofoo-aux-v1"),
            lightgcn_enabled=_bool("AUX_REC_MODEL_LIGHTGCN_ENABLED", False),
            kgat_enabled=_bool("AUX_REC_MODEL_KGAT_ENABLED", False),
        )
        if settings.feedback_enabled and not settings.feedback_path:
            raise ValueError("AUX_REC_FEEDBACK_PATH is required when feedback is enabled")
        if settings.enabled and not settings.service_secret:
            raise ValueError("AUX_REC_SERVICE_SECRET is required when Aux is enabled")
        if re.fullmatch(r"[A-Za-z0-9_-]+", settings.qdrant_collection) is None:
            raise ValueError("AUX_REC_QDRANT_COLLECTION contains unsupported characters")
        if settings.catalogue_publication_version:
            match = re.fullmatch(r"sha256:([0-9a-f]{64})", settings.catalogue_publication_version)
            if match is None:
                raise ValueError(
                    "AUX_REC_CATALOGUE_PUBLICATION_VERSION must be a full sha256 digest"
                )
            if not settings.qdrant_url:
                raise ValueError(
                    "AUX_REC_QDRANT_URL is required for a catalogue publication version"
                )
            if match.group(1)[:12] not in settings.qdrant_collection:
                raise ValueError(
                    "AUX_REC_QDRANT_COLLECTION must include the publication hash prefix"
                )
        return settings
