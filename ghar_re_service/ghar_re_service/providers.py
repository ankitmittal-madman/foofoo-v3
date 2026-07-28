"""
Provider interfaces (RE-DOC-11 §1/§2) — the seams that let the RE's data sources change over 5–10
years without touching any recommendation math.

v1 ships EXACTLY ONE adapter per interface (RE-DOC-11 "What NOT to over-build"):
  - LocalSnapshotCatalogueProvider  — the golden-sample catalogue from ghar_re_core.fixtures
  - YamlFileConfigProvider          — the data/source/*.yaml + community_priors.csv config layer
  - EnvAuthConfigProvider           — the shared service-to-service secret (RE-DOC-10 §9)

Every ghar_re_core module depends only on the returned CatalogueSnapshot / EngineConfig objects,
never on file paths or "how" the data arrived. A future PostgresCatalogueProvider / RemoteConfig-
Provider is a new class here with zero changes to derivation/scoring/pairing.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from ghar_re_core import config as core_config
from ghar_re_core.catalogue import Catalogue, Dish
from ghar_re_core.config import Config
from ghar_re_service.auth import DEFAULT_MAX_SKEW_SECONDS


# ---------------------------------------------------------------------------
# Catalogue
# ---------------------------------------------------------------------------
@runtime_checkable
class CatalogueSnapshot(Protocol):
    """The immutable, in-memory catalogue the engine reads. (ghar_re_core.catalogue.Catalogue
    satisfies this.)"""

    dishes: list[Any]

    def get_dish(self, dish_id: str) -> Dish | None: ...
    def by_zone(self, zone: str) -> list[Dish]: ...
    def by_hero_role(self, role: str) -> list[Dish]: ...


@runtime_checkable
class CatalogueProvider(Protocol):
    def load(self) -> CatalogueSnapshot: ...


class LocalSnapshotCatalogueProvider:
    """The one v1 adapter: loads the golden-sample fixtures into a ghar_re_core Catalogue snapshot.
    (Matches RE-DOC-10 §8's 'immutable snapshot loaded at startup' — here the snapshot is the
    bundled golden sample rather than a DB export; the interface is identical either way.)"""

    def __init__(self, dish_dicts=None):
        self._dish_dicts = dish_dicts  # None -> ghar_re_core.fixtures.DISHES

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
        cfg = Config()  # reads the YAML/CSV config layer
        core_config.set_active_config(cfg)  # inject: core modules now read THIS config
        return cfg


# ---------------------------------------------------------------------------
# Auth (service-to-service signature, RE-DOC-10 §9)
# ---------------------------------------------------------------------------
# The shared secret is read through a provider like everything else — NOT a bare os.environ read
# at the call site (RE-DOC-11 §2). That keeps the "where does this value come from" decision in one
# swappable place: a future SecretsManagerAuthConfigProvider is a new class here and nothing in
# auth.py or main.py changes.

# The same dev-only secret the Edge Function falls back to (see supabase/functions/_shared/config/
# config.ts GHAR_RE_DEV_SECRET). Both sides must agree or local dev can't call the RE at all.
# NEVER reachable in production — load() raises instead (see below).
DEV_INSECURE_SECRET = "dev-insecure-ghar-re-secret"


@dataclass(frozen=True)
class AuthConfig:
    """Resolved auth settings for the signature middleware."""

    secret: str
    max_skew_seconds: int = DEFAULT_MAX_SKEW_SECONDS


@runtime_checkable
class AuthConfigProvider(Protocol):
    def load(self) -> AuthConfig: ...


class EnvAuthConfigProvider:
    """The one v1 adapter: reads the shared secret from the environment.

    Fail-closed in production: if FOOFOO_ENV marks this a production process and no secret is set,
    startup RAISES rather than quietly falling back to the well-known dev secret — shipping the dev
    secret to production would make the signature check theatre, since the value is in this file.
    Mirrors the Edge Function's identical production guard in config.ts.
    """

    SECRET_VAR = "GHAR_RE_SERVICE_SECRET"
    SKEW_VAR = "GHAR_RE_SIGNATURE_MAX_SKEW_SECONDS"
    ENV_VAR = "FOOFOO_ENV"

    def __init__(self, environ: dict | None = None):
        # Injectable so tests can exercise the production guard without mutating os.environ.
        self._environ = environ if environ is not None else os.environ

    def load(self) -> AuthConfig:
        raw_env = (self._environ.get(self.ENV_VAR) or "local").strip().lower()
        is_production = raw_env in ("production", "prod", "foofoo-mvp")

        secret = (self._environ.get(self.SECRET_VAR) or "").strip()
        if not secret:
            if is_production:
                raise RuntimeError(
                    f"[auth] {self.SECRET_VAR} is required when {self.ENV_VAR}={raw_env}. "
                    "Refusing to start with the insecure dev secret in production."
                )
            secret = DEV_INSECURE_SECRET

        raw_skew = (self._environ.get(self.SKEW_VAR) or "").strip()
        skew = int(raw_skew) if raw_skew else DEFAULT_MAX_SKEW_SECONDS

        return AuthConfig(secret=secret, max_skew_seconds=skew)
