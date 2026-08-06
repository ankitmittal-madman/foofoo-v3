"""Pluggable model registry. Heavy frameworks are optional and never downloaded at runtime."""

from __future__ import annotations

import importlib.util
import os
from dataclasses import asdict, dataclass

from .config import Settings


@dataclass(frozen=True)
class ModelEntry:
    name: str
    kind: str
    enabled: bool
    available: bool
    local_only: bool = True


def _switch(name: str, default: bool = True) -> bool:
    """Per-model ablation switch, e.g. AUX_REC_MODEL_KGAT_ENABLED=false."""
    raw = os.getenv(f"AUX_REC_MODEL_{name}_ENABLED")
    if raw is None:
        return default
    if raw.strip().lower() not in {"true", "false"}:
        raise ValueError(f"AUX_REC_MODEL_{name}_ENABLED must be true or false")
    return raw.strip().lower() == "true"


class ModelRegistry:
    def __init__(self, settings: Settings):
        recbole = importlib.util.find_spec("recbole") is not None
        lightfm = importlib.util.find_spec("lightfm") is not None
        qdrant = bool(settings.qdrant_url)
        self.entries = (
            ModelEntry("Existing Engine", "dependency", True, True),
            ModelEntry("Qdrant Retriever", "retriever", qdrant and _switch("QDRANT"), qdrant),
            ModelEntry("LightFM Baseline", "ranker", lightfm and _switch("LIGHTFM"), lightfm),
            ModelEntry(
                "LightGCN / RecBole-GNN",
                "ranker",
                recbole and _switch("LIGHTGCN"),
                recbole,
            ),
            ModelEntry("KGAT", "ranker", recbole and _switch("KGAT"), recbole),
            ModelEntry("RecBole-FairRec", "policy", recbole and _switch("FAIRREC"), recbole),
            ModelEntry("RecBole-Debias", "policy", recbole and _switch("DEBIAS"), recbole),
            ModelEntry("RecBole-CDR", "ranker", recbole and _switch("CDR"), recbole),
            ModelEntry("RecBole-DA", "augmentation", recbole and _switch("DA"), recbole),
            ModelEntry(
                "Recipe2Vec-inspired Embedder",
                "embedder",
                _switch("EMBEDDER"),
                True,
            ),
            ModelEntry("Local Reranker", "reranker", settings.use_local_reranker, True),
            ModelEntry("Rule Engine", "policy", True, True),
            ModelEntry("Diversity Engine", "policy", True, True),
            ModelEntry("Nutrition/Safety Engine", "policy", True, True),
            ModelEntry("Exploration Engine", "policy", True, True),
        )

    def metadata(self) -> list[dict[str, object]]:
        return [asdict(entry) for entry in self.entries]
