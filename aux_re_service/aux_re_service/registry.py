"""Pluggable model registry. Heavy frameworks are optional and never downloaded at runtime."""

from __future__ import annotations

import importlib.util
from dataclasses import asdict, dataclass
from pathlib import Path

from .config import Settings


@dataclass(frozen=True)
class ModelEntry:
    name: str
    kind: str
    enabled: bool
    available: bool
    local_only: bool = True
    status: str = "ready"
    version: str | None = None


class ModelRegistry:
    def __init__(self, settings: Settings):
        recbole = importlib.util.find_spec("recbole") is not None
        lightfm = importlib.util.find_spec("lightfm") is not None
        qdrant = bool(settings.qdrant_url) and settings.qdrant_enabled
        artifacts = settings.model_artifact_dir
        scaffold_status = "scaffold_only" if artifacts else "artifact_not_configured"
        recbole_status = scaffold_status if recbole else "package_missing"
        lightgcn_status = (
            "readiness_gate_blocked" if settings.lightgcn_enabled and recbole else recbole_status
        )
        kgat_status = (
            "readiness_gate_blocked" if settings.kgat_enabled and recbole else recbole_status
        )
        lightfm_artifact = bool(
            settings.lightfm_artifact_path and Path(settings.lightfm_artifact_path).is_file()
        )
        lightfm_ready = settings.lightfm_enabled and lightfm and lightfm_artifact
        if not lightfm:
            lightfm_status = "package_missing"
        elif not lightfm_artifact:
            lightfm_status = "artifact_not_configured"
        elif settings.lightfm_enabled:
            lightfm_status = "configured"
        else:
            lightfm_status = "disabled"
        self.entries = (
            ModelEntry("Existing Engine", "dependency", True, True, status="input_dependency"),
            ModelEntry(
                "Qdrant Retriever",
                "retriever",
                qdrant,
                qdrant,
                status="configured" if qdrant else "not_configured",
            ),
            ModelEntry(
                "LightFM Baseline",
                "ranker",
                lightfm_ready,
                lightfm and lightfm_artifact,
                status=lightfm_status,
                version="lightfm-warp-v2" if lightfm_artifact else None,
            ),
            ModelEntry(
                "LightGCN / RecBole-GNN",
                "ranker",
                settings.lightgcn_enabled,
                False,
                status=lightgcn_status,
            ),
            ModelEntry("KGAT", "ranker", settings.kgat_enabled, False, status=kgat_status),
            ModelEntry("RecBole-FairRec", "policy", False, False, status=recbole_status),
            ModelEntry("RecBole-Debias", "policy", False, False, status=recbole_status),
            ModelEntry("RecBole-CDR", "ranker", False, False, status=recbole_status),
            ModelEntry("RecBole-DA", "augmentation", False, False, status=recbole_status),
            ModelEntry(
                "Recipe2Vec-inspired Embedder",
                "embedder",
                settings.embedder_enabled,
                True,
                status="built_in_feature_hash",
                version="feature-hash-v1",
            ),
            ModelEntry(
                "Local Food Knowledge Graph",
                "retriever",
                bool(settings.knowledge_graph_path),
                bool(settings.knowledge_graph_path),
                status="configured" if settings.knowledge_graph_path else "not_configured",
                version="indian-food-graph-v2",
            ),
            ModelEntry(
                "Local Reranker",
                "reranker",
                settings.use_local_reranker,
                True,
                version="weighted-mmr-v1",
            ),
            ModelEntry("Rule Engine", "policy", True, True, version="rules-v1"),
            ModelEntry("Diversity Engine", "policy", True, True, version="mmr-v1"),
            ModelEntry("Nutrition/Safety Engine", "policy", True, True, version="safety-v1"),
            ModelEntry("Exploration Engine", "policy", False, False, status="not_implemented"),
        )

    def metadata(self) -> list[dict[str, object]]:
        return [asdict(entry) for entry in self.entries]
