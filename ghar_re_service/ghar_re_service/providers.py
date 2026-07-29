"""
Provider interfaces (RE-DOC-11 §1/§2) — the seams that let the RE's data sources change over 5–10
years without touching any recommendation math.

Adapters shipped (RE-DOC-11 "What NOT to over-build" — one per interface, plus the Phase F
bundle pair that makes the service deployable):
  - LocalSnapshotCatalogueProvider  — the golden-sample catalogue from ghar_re_core.fixtures
  - YamlFileConfigProvider          — the data/source/*.yaml + community_priors.csv config layer
  - BundleCatalogueProvider         — catalogue from the baked image bundle (RE-DOC-10 §8)
  - BundleConfigProvider            — config from the baked image bundle (RE-DOC-10 §8)
  - EnvAuthConfigProvider           — the shared service-to-service secret (RE-DOC-10 §9)

The Local*/Yaml* pair reads the checked-out REPO (correct for tests and local dev); the Bundle*
pair reads the immutable snapshot baked into the container image (correct in deployment, and the
only pair that works there — see export_bundle.py's docstring for why). resolve_providers() below
picks between them by looking for a bundle, so neither environment needs to be configured by hand.

Every ghar_re_core module depends only on the returned CatalogueSnapshot / EngineConfig objects,
never on file paths or "how" the data arrived. A future PostgresCatalogueProvider / RemoteConfig-
Provider is a new class here with zero changes to derivation/scoring/pairing.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from ghar_re_core import config as core_config
from ghar_re_core.catalogue import Catalogue, Dish
from ghar_re_core.config import Config
from ghar_re_service.auth import DEFAULT_MAX_SKEW_SECONDS
from ghar_re_service.ratelimit import (
    DEFAULT_MAX_REQUESTS_PER_MINUTE,
    DEFAULT_MAX_TRACKED_CLIENTS,
    DEFAULT_WINDOW_SECONDS,
    SlidingWindowRateLimiter,
)


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
# Bundle providers (Phase F, RE-DOC-10 §8) — the immutable snapshot baked into the image
# ---------------------------------------------------------------------------
# Layout produced by ghar_re_service/scripts/export_bundle.py:
#   <bundle>/manifest.json    bundle_version + per-file checksums
#   <bundle>/catalogue.json   the dish dicts (Catalogue's own constructor shape)
#   <bundle>/config/*.yaml    the engine's YAML/CSV config layer, verbatim
#
# GHAR_RE_BUNDLE_DIR overrides the location; the default sits beside the installed service package
# so it travels with the image.
BUNDLE_DIR_VAR = "GHAR_RE_BUNDLE_DIR"
_SERVICE_PKG_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_BUNDLE_DIR = os.path.join(os.path.dirname(_SERVICE_PKG_DIR), "data", "bundle")


def bundle_dir() -> str:
    """The configured bundle directory (may not exist — callers check)."""
    return os.environ.get(BUNDLE_DIR_VAR) or DEFAULT_BUNDLE_DIR


def bundle_manifest(directory: str | None = None) -> dict | None:
    """Read the bundle manifest, or None when no bundle is present."""
    path = os.path.join(directory or bundle_dir(), "manifest.json")
    if not os.path.isfile(path):
        return None
    with open(path) as fh:
        return json.load(fh)


class BundleCatalogueProvider:
    """Catalogue from the baked bundle's catalogue.json.

    The bundle stores the raw dish dicts, which is exactly what Catalogue's constructor takes — so
    this reconstructs an in-memory catalogue identical to the fixtures-backed one, with no bespoke
    deserialization that could drift from the fixture shape.
    """

    def __init__(self, directory: str | None = None):
        self._dir = directory or bundle_dir()

    def load(self) -> CatalogueSnapshot:
        with open(os.path.join(self._dir, "catalogue.json")) as fh:
            dish_dicts = json.load(fh)
        return Catalogue(dish_dicts)


class BundleConfigProvider:
    """Config from the baked bundle's config/ directory.

    Points ghar_re_core.config at the bundled config BEFORE constructing Config(), because that
    module resolves its source directory at import time from GHAR_RE_CONFIG_DIR. Without this the
    container would try to read <site-packages>/data/source and fail at startup — the exact break
    RE-DOC-10 §8 exists to prevent.
    """

    def __init__(self, directory: str | None = None):
        self._dir = directory or bundle_dir()

    def load(self) -> EngineConfig:
        config_dir = os.path.join(self._dir, "config")
        os.environ[core_config.CONFIG_DIR_VAR] = config_dir
        # config.SRC was bound at import time; repoint it so an already-imported module also
        # reads the bundle (import order must not decide where config comes from).
        core_config.SRC = config_dir
        core_config._CACHE.clear()  # noqa: SLF001 — drop anything parsed from the pre-override path
        cfg = Config()
        core_config.set_active_config(cfg)
        return cfg


def resolve_providers() -> tuple[CatalogueProvider, ConfigProvider, dict | None]:
    """Pick bundle providers when a bundle is present, repo providers otherwise.

    Deliberately automatic rather than an env flag someone must remember to set: in the image the
    bundle is always there (so deployment uses it), and in a checked-out repo without an exported
    bundle it isn't (so tests and local dev keep their current behaviour unchanged). Returns the
    manifest too, so startup can log and /v1/meta can report which snapshot is actually serving.
    """
    manifest = bundle_manifest()
    if manifest is not None:
        directory = bundle_dir()
        return BundleCatalogueProvider(directory), BundleConfigProvider(directory), manifest
    return LocalSnapshotCatalogueProvider(), YamlFileConfigProvider(), None


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


# ---------------------------------------------------------------------------
# Rate limiting (public-ingress hardening — see ratelimit.py's docstring)
# ---------------------------------------------------------------------------
# Read through a provider for the same reason the secret is: "where does this value come from" stays
# in one swappable place. Tunable by environment because the right ceiling depends on real traffic
# (Supabase's egress is NAT'd, so one address can legitimately carry many users) — an operator must
# be able to raise it with `fly secrets set` / a config change and a restart, not a code change.


@dataclass(frozen=True)
class RateLimitConfig:
    """Resolved rate-limit settings. max_requests == 0 disables the limiter entirely."""

    max_requests: int = DEFAULT_MAX_REQUESTS_PER_MINUTE
    window_seconds: int = DEFAULT_WINDOW_SECONDS
    max_tracked_clients: int = DEFAULT_MAX_TRACKED_CLIENTS

    def build(self) -> SlidingWindowRateLimiter:
        return SlidingWindowRateLimiter(
            max_requests=self.max_requests,
            window_seconds=self.window_seconds,
            max_tracked_clients=self.max_tracked_clients,
        )


@runtime_checkable
class RateLimitConfigProvider(Protocol):
    def load(self) -> RateLimitConfig: ...


class EnvRateLimitConfigProvider:
    """The one v1 adapter: reads the limit from the environment.

    A malformed value RAISES at startup rather than silently reverting to the default. A typo in a
    rate limit is the kind of thing that would otherwise be discovered during the incident it failed
    to prevent — the same reasoning as EnvAuthConfigProvider's int(skew) above.
    """

    MAX_VAR = "GHAR_RE_RATE_LIMIT_PER_MINUTE"
    WINDOW_VAR = "GHAR_RE_RATE_LIMIT_WINDOW_SECONDS"
    TRACKED_VAR = "GHAR_RE_RATE_LIMIT_MAX_CLIENTS"

    def __init__(self, environ: dict | None = None):
        self._environ = environ if environ is not None else os.environ

    def _int(self, var: str, default: int) -> int:
        raw = (self._environ.get(var) or "").strip()
        if not raw:
            return default
        try:
            return int(raw)
        except ValueError:
            raise RuntimeError(f"[ratelimit] {var} must be an integer, got {raw!r}") from None

    def load(self) -> RateLimitConfig:
        return RateLimitConfig(
            max_requests=self._int(self.MAX_VAR, DEFAULT_MAX_REQUESTS_PER_MINUTE),
            window_seconds=self._int(self.WINDOW_VAR, DEFAULT_WINDOW_SECONDS),
            max_tracked_clients=self._int(self.TRACKED_VAR, DEFAULT_MAX_TRACKED_CLIENTS),
        )
