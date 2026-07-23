"""
Startup lifecycle (RE-DOC-10 §7): load config → load catalogue → build indices → mark ready.
Each step is logged (structured). /readyz flips to 200 only after this completes successfully.
"""
from __future__ import annotations

import json
import logging
import sys
import time
from dataclasses import dataclass, field
from typing import Optional, List

from ghar_re_service.providers import (
    CatalogueProvider, ConfigProvider,
    LocalSnapshotCatalogueProvider, YamlFileConfigProvider,
)
from ghar_re_service.modules import build_registry


# --- structured JSON logging (RE-DOC-10 §10 — logs span two languages, so no plain text) ---
def _make_logger() -> logging.Logger:
    logger = logging.getLogger("ghar_re_service")
    if not logger.handlers:
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(h)
        logger.setLevel(logging.INFO)
    return logger


LOG = _make_logger()


def log_event(event: str, **fields):
    LOG.info(json.dumps({"event": event, **fields}))


@dataclass
class AppState:
    """Process-wide state built at startup and read by the routes."""
    config_provider: ConfigProvider = field(default_factory=YamlFileConfigProvider)
    catalogue_provider: CatalogueProvider = field(default_factory=LocalSnapshotCatalogueProvider)
    config: Optional[object] = None
    catalogue: Optional[object] = None
    registry: Optional[List] = None
    ready: bool = False


def startup(state: AppState) -> AppState:
    """Runs the load sequence. Sets state.ready=True only if every step succeeds."""
    t0 = time.time()
    log_event("startup.begin")

    # 1. config
    state.config = state.config_provider.load()
    log_event("startup.config_loaded", config_version=state.config.versions["config"])

    # 2. catalogue
    state.catalogue = state.catalogue_provider.load()
    log_event("startup.catalogue_loaded", dishes=len(state.catalogue.dishes))

    # 3. in-memory indices (the Catalogue builds by_id/by_zone/by_hero_role in its ctor)
    zones = sorted({d.zone for d in state.catalogue.dishes if d.zone})
    roles = sorted({d.hero_role for d in state.catalogue.dishes})
    log_event("startup.indices_built", zones=zones, hero_roles=roles)

    # 4. scoring registry
    state.registry = build_registry()
    log_event("startup.registry_built", modules=[m.name for m in state.registry])

    # 5. ready
    state.ready = True
    log_event("startup.ready", elapsed_ms=round((time.time() - t0) * 1000, 1))
    return state
