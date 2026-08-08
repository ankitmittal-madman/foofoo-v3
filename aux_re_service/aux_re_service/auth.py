"""Raw-body HMAC verification for Edge-to-Aux compute calls."""

from __future__ import annotations

import hashlib
import hmac

SIGNATURE_HEADER = "X-Aux-Signature"
REQUEST_ID_HEADER = "X-Request-Id"
MAX_SKEW_SECONDS = 300


class AuthError(ValueError):
    """Safe machine-readable authentication failure."""


def signature(secret: str, timestamp: int, body: bytes) -> str:
    message = str(timestamp).encode() + b"." + body
    return hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()


def verify(body: bytes, header: str | None, secret: str, now: float) -> None:
    if not header:
        raise AuthError("missing_signature")
    fields = dict(part.strip().split("=", 1) for part in header.split(",") if "=" in part)
    try:
        timestamp = int(fields["t"])
        provided = fields["v1"]
    except (KeyError, ValueError) as exc:
        raise AuthError("malformed_signature") from exc
    if abs(now - timestamp) > MAX_SKEW_SECONDS:
        raise AuthError("stale_signature")
    if not hmac.compare_digest(signature(secret, timestamp, body), provided):
        raise AuthError("invalid_signature")
