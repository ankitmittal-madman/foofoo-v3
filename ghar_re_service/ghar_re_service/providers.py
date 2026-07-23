"""
Provider interfaces (RE-DOC-11 §1/§2) — the seams that let the RE's data sources change over 5–10
years without touching any recommendation math.

v1 ships EXACTLY ONE adapter per interface (RE-DOC-11 "What NOT to over-build"):
  - LocalSnapshotCatalogueProvider  — the golden-sample catalogue from ghar_re_core.fixtures
  - YamlFileConfigProvider          — the data/source/*.yaml + community_priors.csv config layer

Every ghar_re_core module depends only on the returned CatalogueSnapshot / EngineConfig objects,
never on file paths or "how" the data arrived. A future PostgresCatalogueProvider / RemoteConfig-
Provider is a new class here with zero changes to derivation/scoring/pairing.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable, List, Optional, Any

from ghar_re_core.catalogue import Catalogue, Dish
from ghar_re_core import config as core_config
from ghar_re_core.config import Config


# ---------------------------------------------------------------------------
# Catalogue
# ---------------------------------------------------------------------------
@runtime_checkable
class CatalogueSnapshot(Protocol):
    """The immutable, in-memory catalogue the engine reads. (ghar_re_core.catalogue.Catalogue
    satisfies this.)"""
    dishes: List[Any]

    def get_dish(self, dish_id: str) -> Optional[Dish]: ...
    def by_zone(self, zone: str) -> List[Dish]: ...
    def by_hero_role(self, role: str) -> List[Dish]: ...


@runtime_checkable
class CatalogueProvider(Protocol):
    def load(self) -> CatalogueSnapshot: ...


class LocalSnapshotCatalogueProvider:
    """The one v1 adapter: loads the golden-sample fixtures into a ghar_re_core Catalogue snapshot.
    (Matches RE-DOC-10 §8's 'immutable snapshot loaded at startup' — here the snapshot is the
    bundled golden sample rather than a DB export; the interface is identical either way.)"""

    def __init__(self, dish_dicts=None):
        self._dish_dicts = dish_dicts   # None -> ghar_re_core.fixtures.DISHES

    def load(self) -> CatalogueSnapshot:
        return Catalogue(self._dish_dicts)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
# EngineConfig is the strongly-typed config object the engine consumes. ghar_re_core.config.Config
# IS that type (a typed view over the YAML shape), so we alias rather than re-declare — keeping ONE
# definition of the config contract.
EngineConfig = Config


@runtime_checkable
class ConfigProvider(Protocol):
    def load(self) -> EngineConfig: ...


class YamlFileConfigProvider:
    """The one v1 adapter: builds an EngineConfig from data/source/*.yaml + community_priors.csv,
    and installs it as ghar_re_core's active config so every core call site uses it (the injection
    seam in ghar_re_core.config)."""

    def load(self) -> EngineConfig:
        cfg = Config()                       # reads the YAML/CSV config layer
        core_config.set_active_config(cfg)   # inject: core modules now read THIS config
        return cfg
