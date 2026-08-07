from __future__ import annotations

import pytest
from aux_re_service.config import Mode, Settings
from aux_re_service.registry import ModelRegistry


def test_safe_environment_defaults(monkeypatch):
    for name in (
        "AUX_REC_ENABLED",
        "AUX_REC_MODE",
        "AUX_REC_ALLOW_OVERRIDE",
        "AUX_REC_QDRANT_URL",
    ):
        monkeypatch.delenv(name, raising=False)
    config = Settings.from_env()
    assert config.enabled is False
    assert config.mode is Mode.SHADOW
    assert config.allow_override is False
    assert config.qdrant_url is None


def test_environment_can_enable_shadow_compare_and_active(monkeypatch):
    monkeypatch.setenv("AUX_REC_ENABLED", "true")
    for mode in Mode:
        monkeypatch.setenv("AUX_REC_MODE", mode.value)
        assert Settings.from_env().mode is mode


@pytest.mark.parametrize(
    ("name", "value"),
    [("AUX_REC_ENABLED", "yes"), ("AUX_REC_MODE", "observe"), ("AUX_REC_MIN_DELTA", "2")],
)
def test_invalid_environment_fails_readiness_validation(monkeypatch, name, value):
    monkeypatch.setenv(name, value)
    with pytest.raises(ValueError):
        Settings.from_env()


def test_invalid_model_switch_fails_configuration_validation(monkeypatch):
    monkeypatch.setenv("AUX_REC_MODEL_EMBEDDER_ENABLED", "sometimes")
    with pytest.raises(ValueError):
        Settings.from_env()


def test_catalogue_publication_configuration_is_version_bound(monkeypatch):
    digest = "a" * 64
    monkeypatch.setenv("AUX_REC_QDRANT_URL", "http://qdrant:6333")
    monkeypatch.setenv("AUX_REC_QDRANT_COLLECTION", f"foofoo_recipes__{digest[:12]}")
    monkeypatch.setenv("AUX_REC_CATALOGUE_PUBLICATION_VERSION", f"sha256:{digest}")
    config = Settings.from_env()
    assert config.catalogue_publication_version == f"sha256:{digest}"

    monkeypatch.setenv("AUX_REC_QDRANT_COLLECTION", "foofoo_recipes__wrong")
    with pytest.raises(ValueError, match="hash prefix"):
        Settings.from_env()


def test_registry_reports_working_and_scaffold_only_paths(monkeypatch):
    monkeypatch.delenv("AUX_REC_MODEL_EMBEDDER_ENABLED", raising=False)
    registry = ModelRegistry(Settings.from_env()).metadata()
    by_name = {row["name"]: row for row in registry}
    assert by_name["Recipe2Vec-inspired Embedder"]["available"] is True
    assert by_name["Recipe2Vec-inspired Embedder"]["version"] == "feature-hash-v1"
    assert by_name["Local Reranker"]["version"] == "weighted-mmr-v1"
    assert by_name["Exploration Engine"]["status"] == "not_implemented"
    assert by_name["LightFM Baseline"]["enabled"] is False
    assert by_name["LightFM Baseline"]["status"] in {
        "package_missing",
        "artifact_not_configured",
    }
