"""
ghar_re_core.model_provider — the s_pref artifact injection seam (Phase 3, not fit, not shipped).

Mirrors ghar_re_core/config.py's ConfigProvider injection-seam pattern exactly
(active_config()/set_active_config()/_ConfigProxy): `active_model()` / `set_active_model()` /
`PREF_MODEL` (a thin proxy every core module can safely import at module-load time, before any
provider has been chosen).

Default active provider is `NullModelArtifactProvider` — no artifact, ever. This is the ONLY
provider actually exercised in this phase: there is no trained artifact anywhere in this repo,
and this module does not fabricate one. `FileModelArtifactProvider` is the seam a future WP
wires up once a real artifact exists (RE-DOC-11 §8: "retraining and redeploying becomes a
deploy, not a code change") — the loader is built now so that future WP is a config change, not
a code change, but nothing in Phase 3 invokes it against a real file in production.
"""
from __future__ import annotations

import os
from typing import Any, Optional, Protocol


class ModelArtifactProvider(Protocol):
    """Uniform shape for anything that can hand ghar_re_core.preference.s_pref a loaded model
    artifact (or the absence of one). `load()` is called once at provider-selection time (not per
    scoring call) — ghar_re_core.preference reads the already-loaded `.artifact` via
    `active_model()` on every s_pref() call, never re-loading from disk mid-request."""

    artifact: Optional[Any]

    def load(self) -> Optional[Any]: ...


class NullModelArtifactProvider:
    """The default, and — as of this phase — the ONLY provider actually in use anywhere: no
    trained artifact exists yet, so `load()` always returns None and `artifact` is always None.
    ghar_re_core.preference.s_pref checks this and returns the neutral/unfit value (0.0) whenever
    `active_model().artifact is None`, which today is unconditionally true."""

    def __init__(self):
        self.artifact = None

    def load(self) -> Optional[Any]:
        """No artifact to load — returns None. Never raises, never fabricates a placeholder
        object; `None` is the correct, honest representation of "no trained model exists"."""
        return None


class FileModelArtifactProvider:
    """Loads a versioned, immutable joblib artifact from `path` at construction time. This is the
    loader half of the seam RE-DOC-11 §8 describes — built now so activating s_pref later is a
    config change (point `pref_model.yaml.model_artifact_path` at a real file + set
    `enabled: true`), not a code change. NOT wired into the live default provider in this phase;
    nothing in this repo constructs one against a real path yet, because no real artifact exists
    (Phase 3's training pipeline is explicitly never run against real production feedback_events
    in this plan — see ghar_re_core/training/train_pref_model.py)."""

    def __init__(self, path: str):
        self._path = path
        self.artifact: Optional[Any] = None

    def load(self) -> Optional[Any]:
        """Loads the joblib artifact at `self._path` if the file exists, else returns None
        (never raises for a missing file — a missing/not-yet-trained artifact is an expected,
        honest state this phase must degrade gracefully from, not an error)."""
        if not self._path or not os.path.exists(self._path):
            self.artifact = None
            return None
        import joblib  # imported lazily — joblib is a training/inference-only dependency, never
        # required for the (currently universal) Null-provider path.
        self.artifact = joblib.load(self._path)
        return self.artifact


# ---------------------------------------------------------------------------
# Active-model injection seam (mirrors config.py's active_config()/set_active_config() exactly).
# ---------------------------------------------------------------------------
_active_provider: Optional[ModelArtifactProvider] = None


def active_model() -> ModelArtifactProvider:
    """Return the ModelArtifactProvider currently in effect, creating the default
    NullModelArtifactProvider the first time it's needed. This is what PREF_MODEL (the proxy
    every core module imports) delegates to on every attribute access."""
    global _active_provider
    if _active_provider is None:
        _active_provider = NullModelArtifactProvider()
        _active_provider.load()
    return _active_provider


def set_active_model(provider: ModelArtifactProvider) -> None:
    """Inject the ModelArtifactProvider the engine should use (called by the service at startup,
    mirroring set_active_config()). The caller is responsible for calling `provider.load()`
    first (or accepting that `.artifact` may still be None if it hasn't been loaded)."""
    global _active_provider
    _active_provider = provider


class _ModelProxy:
    """Delegates every attribute access to the current active ModelArtifactProvider, so callers
    (ghar_re_core.preference.s_pref) never hold a stale reference."""

    def __getattr__(self, name):
        return getattr(active_model(), name)


# What ghar_re_core.preference imports; resolves to the active provider on each access.
PREF_MODEL = _ModelProxy()
