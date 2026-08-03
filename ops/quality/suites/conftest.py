"""
Shared fixtures + helpers for the Ghar quality suites (Phases 4-8).

Responsibilities:
  * Put BOTH package roots on sys.path — ghar_re_core imports with the repo root on the path, but
    ghar_re_service is a nested package that needs `<repo>/ghar_re_service` on the path too.
  * Provide a session-scoped FastAPI TestClient whose context has run the real startup sequence
    (auth -> config -> catalogue(810 dishes) -> indices -> registry).
  * Provide `signed_post` — the HMAC signing the SIGNED_PATHS require, over the exact body bytes.
  * Provide a dish resolver (`dish_index`) so black-box exclusion checks (Phase 8) can map a served
    hero_dish_id back to the dish's diet / ingredients WITHOUT reaching into engine internals.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import sys
import time
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
for _p in (_REPO_ROOT, _REPO_ROOT / "ghar_re_service"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))


@pytest.fixture(scope="session")
def client():
    """Session-scoped TestClient with the full startup lifecycle executed once.

    Entering the TestClient context manager runs the FastAPI lifespan (startup), so `/readyz`
    returns 200 and the catalogue/config/registry are loaded before any test posts.
    """
    from fastapi.testclient import TestClient

    from ghar_re_service import main

    with TestClient(main.app) as c:
        yield c


@pytest.fixture(scope="session")
def secret():
    """The dev HMAC secret the local service loads at startup (test-only, never a prod secret)."""
    from ghar_re_service.providers import DEV_INSECURE_SECRET

    return DEV_INSECURE_SECRET


@pytest.fixture(scope="session")
def signed_post(client, secret):
    """Return a helper that POSTs a JSON payload to a SIGNED_PATH with a valid HMAC header.

    The signature covers `f"{ts}.".encode() + raw_body`, matching auth.verify_request. The helper
    serialises the payload ONCE and both signs and sends those exact bytes (the HMAC is over raw
    bytes, so re-serialising would invalidate it).
    """
    from ghar_re_service import auth

    def _post(path: str, payload: dict, *, ts: int | None = None, tamper: bool = False):
        raw = json.dumps(payload).encode()
        ts = int(time.time()) if ts is None else ts
        sig = hmac.new(secret.encode(), f"{ts}.".encode() + raw, hashlib.sha256).hexdigest()
        body = raw + b" " if tamper else raw  # tamper: sign clean bytes, send altered bytes
        return client.post(
            path, content=body,
            headers={"content-type": "application/json",
                     auth.SIGNATURE_HEADER: f"t={ts},v1={sig}"},
        )

    return _post


@pytest.fixture(scope="session")
def dish_index(client):
    """Return a dict mapping dish_id -> the loaded Dish object, for black-box exclusion checks."""
    from ghar_re_service import main

    return dict(main.state.catalogue.by_id)


@pytest.fixture(scope="session")
def contract_schema():
    """Load the v1 JSON-Schema contract once for independent response validation."""
    return json.loads((_REPO_ROOT / "contracts" / "ghar-re-v1.schema.json").read_text())
