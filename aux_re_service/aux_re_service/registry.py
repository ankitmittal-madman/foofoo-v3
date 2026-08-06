"""Pluggable model registry. Heavy frameworks are optional and never downloaded at runtime."""

from __future__ import annotations

import importlib.util
from dataclasses import asdict, dataclass

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
                False,
                False,
                status=scaffold_status if lightfm else "package_missing",
            ),
            ModelEntry(
                "LightGCN / RecBole-GNN",
                "ranker",
                False,
                False,
                status=recbole_status,
            ),
            ModelEntry("KGAT", "ranker", False, False, status=recbole_status),
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
                version="indian-food-graph-v1",
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
