"""
Startup lifecycle (RE-DOC-10 §7): load config → load catalogue → build indices → mark ready.
Each step is logged (structured). /readyz flips to 200 only after this completes successfully.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from uuid import UUID

from ghar_re_core import config as core_config
from ghar_re_core import model_provider as core_model
from ghar_re_service.modules import build_registry
from ghar_re_service.providers import (
    AuthConfig,
    AuthConfigProvider,
    CatalogueProvider,
    ConfigProvider,
    EnvAuthConfigProvider,
    EnvRateLimitConfigProvider,
    RateLimitConfigProvider,
    resolve_providers,
)
from ghar_re_service.published_catalogue import (
    PublishedCatalogueStore,
    load_from_environment,
    reconcile_fallback_identities,
)
from ghar_re_service.ratelimit import SlidingWindowRateLimiter

SERVICE_NAME = "ghar_re_service"
PREFERENCE_MODEL_PATH_VAR = "GHAR_RE_PREF_MODEL_PATH"


def validate_preference_artifact_for_activation(artifact: object) -> str:
    """Return the governed model version or reject an artifact that cannot support a trustworthy
    production evaluation claim."""
    metadata = getattr(artifact, "metadata", None)
    if not isinstance(metadata, dict):
        raise RuntimeError("Preference artifact is missing governed metadata")
    model_version = metadata.get("model_version")
    if not isinstance(model_version, str) or not model_version.startswith("sha256:"):
        raise RuntimeError("Preference artifact is missing a content-derived model_version")
    if metadata.get("readiness_gate_bypassed") is not False:
        raise RuntimeError("Preference artifact bypassed the production readiness gate")
    if metadata.get("split_strategy") != "household_group_holdout":
        raise RuntimeError("Preference artifact was not evaluated on household-isolated holdout")
    if metadata.get("household_overlap") != 0:
        raise RuntimeError("Preference artifact evaluation leaks households across the split")
    if metadata.get("promotion_gate_passed") is not True:
        raise RuntimeError("Preference artifact did not pass governed promotion quality gates")
    return model_version


# --- structured JSON logging (RE-DOC-10 §10 — logs span two languages, so no plain text) ---
def _make_logger() -> logging.Logger:
    """Build (once) the module-wide structured logger that every `log_event()` call writes to.

    Idempotent by checking `logger.handlers` first, so re-importing this module (tests, reloads)
    never attaches a second stdout handler and doubles every log line.
    """
    logger = logging.getLogger("ghar_re_service")
    if not logger.handlers:
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(h)
        logger.setLevel(logging.INFO)
    return logger


LOG = _make_logger()


def log_event(event: str, **fields):
    """Every line is JSON and carries `service` (Phase D, RE-DOC-10 observability)."""
    LOG.info(json.dumps({"event": event, "service": SERVICE_NAME, **fields}))


def catalogue_identity_summary(catalogue: object | None) -> dict[str, int]:
    """Return public, count-only diagnostics for the loaded catalogue identity index.

    Alias strings are intentionally excluded: operators need to know whether ambiguity changed,
    while the unauthenticated metadata endpoint should disclose no catalogue content.
    """
    if catalogue is None:
        return {
            "canonical_dishes": 0,
            "canonical_uuid_dishes": 0,
            "legacy_id_dishes": 0,
            "resolvable_names": 0,
            "ambiguous_aliases": 0,
            "shadowed_aliases": 0,
        }
    dishes = list(getattr(catalogue, "dishes", ()) or ())

    def has_canonical_uuid(dish: object) -> bool:
        """Return whether one loaded dish exposes an RFC UUID without revealing the value."""
        try:
            UUID(str(getattr(dish, "id", "")))
            return True
        except ValueError:
            return False

    canonical_uuid_dishes = sum(has_canonical_uuid(dish) for dish in dishes)
    return {
        "canonical_dishes": len(dishes),
        "canonical_uuid_dishes": canonical_uuid_dishes,
        "legacy_id_dishes": len(dishes) - canonical_uuid_dishes,
        "resolvable_names": len(getattr(catalogue, "by_normalized_name", {}) or {}),
        "ambiguous_aliases": len(getattr(catalogue, "ambiguous_aliases", {}) or {}),
        "shadowed_aliases": len(getattr(catalogue, "shadowed_aliases", {}) or {}),
    }


@dataclass
class Counters:
    """Lightweight in-process counters (Phase D Task 3) — cheap, removable, no metrics backend.
    Reset on process restart; exposed read-only via GET /v1/meta."""

    requests_total: int = 0
    success_total: int = 0
    partial_total: int = 0  # warnings[] non-empty but request otherwise succeeded (Task 4)
    errors_total: int = 0  # invalid request or unhandled exception
    # Requests shed by the rate limiter before reaching signature verification. Tracked separately
    # from errors_total on purpose: a 429 is the service working as designed, and folding it into
    # the error count would make "is the engine unhealthy?" unanswerable from /v1/meta during
    # exactly the traffic spike you would want to read that number.
    rate_limited_total: int = 0

    def record(self, outcome: str) -> None:
        """Tally one completed /v1/recommendations request under its outcome bucket.

        `outcome` is one of "success" / "partial" / anything else (treated as an error) — called
        once per request by the route handler in main.py, never for requests shed by the rate
        limiter (those go through `record_rate_limited()` instead).
        """
        self.requests_total += 1
        if outcome == "success":
            self.success_total += 1
        elif outcome == "partial":
            self.partial_total += 1
        else:
            self.errors_total += 1

    def record_rate_limited(self) -> None:
        """Counted outside record() — a shed request never reached the engine, so it is not one of
        requests_total's success/partial/error outcomes."""
        self.rate_limited_total += 1

    def as_dict(self) -> dict:
        """Snapshot the current counters as a plain dict — this is exactly the `metrics` field
        GET /v1/meta returns to callers, read-only and reset only on process restart."""
        return {
            "requests_total": self.requests_total,
            "success_total": self.success_total,
            "partial_total": self.partial_total,
            "errors_total": self.errors_total,
            "rate_limited_total": self.rate_limited_total,
        }


@dataclass
class AppState:
    """Process-wide state built at startup and read by the routes."""

    # Left None so startup() can resolve bundle-vs-repo providers together (they must agree —
    # a bundled catalogue with repo config, or vice versa, would be an incoherent snapshot).
    # Tests still inject an explicit pair, which bypasses resolution entirely.
    config_provider: ConfigProvider | None = None
    catalogue_provider: CatalogueProvider | None = None
    auth_provider: AuthConfigProvider = field(default_factory=EnvAuthConfigProvider)
    rate_limit_provider: RateLimitConfigProvider = field(default_factory=EnvRateLimitConfigProvider)
    config: object | None = None
    catalogue: object | None = None
    published_catalogue: PublishedCatalogueStore | None = None
    registry: list | None = None
    auth: AuthConfig | None = None
    rate_limiter: SlidingWindowRateLimiter | None = None
    bundle: dict | None = None  # baked-bundle manifest when serving from an image (RE-DOC-10 §8)
    preference_model_status: str = "unloaded"
    preference_model_version: str | None = None
    ready: bool = False
    counters: Counters = field(default_factory=Counters)


def configure_preference_model(config: object) -> core_model.ModelArtifactProvider:
    """Install the configured learned-preference provider, failing closed when activation is
    requested but incomplete. Disabled deployments explicitly reset to the null provider so test
    reloads and rolling workers cannot retain a stale model from an earlier configuration."""
    mode = getattr(config, "pref_model_mode", None)
    if mode not in {"disabled", "shadow", "active"}:
        mode = "active" if bool(getattr(config, "pref_model_enabled", False)) else "disabled"
    provider: core_model.ModelArtifactProvider
    if mode == "disabled":
        provider = core_model.NullModelArtifactProvider()
        provider.load()
        core_model.set_active_model(provider)
        return provider

    weight = float(getattr(config, "w_pref", 0.0))
    if mode == "active" and not 0 < weight <= 1:
        raise RuntimeError(
            "Preference model is active but w_pref is not in (0, 1]; refusing a silent no-op"
        )
    if mode == "shadow" and weight != 0:
        raise RuntimeError(
            "Preference model shadow mode requires w_pref=0 to guarantee no rank impact"
        )
    configured_path = (
        os.environ.get(PREFERENCE_MODEL_PATH_VAR)
        or getattr(config, "pref_model_artifact_path", None)
        or ""
    )
    if not configured_path:
        raise RuntimeError("Preference model is enabled but no artifact path is configured")
    path = (
        configured_path
        if os.path.isabs(configured_path)
        else os.path.join(
            core_config.SRC,
            configured_path,
        )
    )
    provider = core_model.FileModelArtifactProvider(path)
    artifact = provider.load()
    if artifact is None:
        raise RuntimeError(f"Preference model artifact does not exist: {path}")
    validate_preference_artifact_for_activation(artifact)
    core_model.set_active_model(provider)
    return provider


def startup(state: AppState) -> AppState:
    """Runs the load sequence. Sets state.ready=True only if every step succeeds."""
    t0 = time.time()
    log_event("startup.begin")

    # 0. auth (RE-DOC-10 §9). Loaded FIRST and deliberately: in production a missing shared secret
    # raises here, so the process dies before loading a catalogue it would then serve unauthed.
    # Only the skew is logged — the secret's value is never logged, not even truncated.
    state.auth = state.auth_provider.load()
    log_event("startup.auth_loaded", max_skew_seconds=state.auth.max_skew_seconds)

    # 0a. rate limiter. Built here (not lazily on first request) so a malformed limit is a startup
    # failure an operator sees in `fly logs`, not a surprise during the first burst of traffic.
    rl_cfg = state.rate_limit_provider.load()
    state.rate_limiter = rl_cfg.build()
    log_event(
        "startup.rate_limit_loaded",
        enabled=state.rate_limiter.enabled,
        max_requests=rl_cfg.max_requests,
        window_seconds=rl_cfg.window_seconds,
    )

    # 0b. data source. Bundle when one is baked into the image, repo files otherwise. Resolved as a
    # PAIR so catalogue and config always come from the same snapshot. Explicitly-injected
    # providers (tests) win and skip resolution.
    if state.catalogue_provider is None or state.config_provider is None:
        cat_p, cfg_p, manifest = resolve_providers()
        state.catalogue_provider = state.catalogue_provider or cat_p
        state.config_provider = state.config_provider or cfg_p
        state.bundle = manifest
    log_event(
        "startup.source_resolved",
        source="bundle" if state.bundle else "repo_files",
        bundle_version=(state.bundle or {}).get("bundle_version"),
    )

    # 1. config
    state.config = state.config_provider.load()
    log_event("startup.config_loaded", config_version=state.config.versions["config"])

    # 1a. learned preference artifact. This used to have a training writer and a file provider but
    # no startup wiring, so flipping pref_model.yaml could never activate the trained model.
    preference_provider = configure_preference_model(state.config)
    preference_artifact = preference_provider.artifact
    state.preference_model_status = (
        getattr(state.config, "pref_model_mode", "active")
        if preference_artifact is not None
        else "disabled"
    )
    metadata = getattr(preference_artifact, "metadata", {}) if preference_artifact else {}
    state.preference_model_version = (
        metadata.get("model_version") if isinstance(metadata, dict) else None
    )
    log_event(
        "startup.preference_model_loaded",
        status=state.preference_model_status,
        model_version=state.preference_model_version,
        weight=state.config.w_pref,
    )

    # 2. catalogue
    state.catalogue = state.catalogue_provider.load()

    # Optional scalable publication: verified once at startup, hydrated only for bounded IDs on a
    # request. Absence leaves the immutable bundle path exactly unchanged; a configured but corrupt
    # artifact fails startup rather than silently serving unverified database candidates.
    state.published_catalogue = load_from_environment()
    fallback_identity = reconcile_fallback_identities(state.catalogue, state.published_catalogue)
    log_event(
        "startup.catalogue_loaded",
        **catalogue_identity_summary(state.catalogue),
        identity_resolution=fallback_identity,
    )
    log_event(
        "startup.published_catalogue_loaded",
        configured=state.published_catalogue is not None,
        publication_version=(
            state.published_catalogue.version if state.published_catalogue else None
        ),
        published_rows=(state.published_catalogue.row_count if state.published_catalogue else 0),
    )

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
