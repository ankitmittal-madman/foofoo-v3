"""
Service-to-service signature verification (RE-DOC-10 §9) — the RE side of the scheme that
supabase/functions/recommendations/re-client.ts already sends.

Scheme, verbatim from the edge function's implementation:
    timestamp     = floor(Date.now()/1000)              (unix seconds)
    signedPayload = f"{timestamp}.{rawBody}"            (rawBody = the exact JSON bytes sent)
    signature     = hex( HMAC-SHA256(sharedSecret, signedPayload) )
    header        = X-Ghar-Signature: t=<timestamp>,v1=<signature>

This module is PURE (no FastAPI import, no I/O) so it can be unit-tested directly; main.py wires
it in as middleware that runs before any body parsing or engine computation.

Two properties this deliberately guarantees:
  * The HMAC is verified over the RAW request bytes, never over a re-serialized parse of them —
    re-serializing would change key order/whitespace and break signatures that are actually valid.
  * Comparison is constant-time (hmac.compare_digest), so a timing side-channel can't be used to
    recover a valid signature byte by byte.
"""

from __future__ import annotations

import hashlib
import hmac

SIGNATURE_HEADER = "X-Ghar-Signature"
REQUEST_ID_HEADER = "X-Request-Id"

# Replay guard: reject a signature whose timestamp is further than this from our clock, in either
# direction (future-dated too — a skewed-forward caller is as suspect as a replayed old one).
DEFAULT_MAX_SKEW_SECONDS = 300


class AuthError(Exception):
    """Raised when a request's signature is missing, malformed, stale, or does not verify.

    `reason` is a short machine-readable token that is safe to log and safe to return to the
    caller — it never contains the secret, the expected signature, or any request content.
    """

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def parse_signature_header(raw: str | None) -> tuple[int, str]:
    """Parse `t=<unix>,v1=<hex>` into (timestamp, signature).

    Order-insensitive and tolerant of surrounding whitespace, but strict about the two parts being
    present and the timestamp being an integer — anything else is a malformed header, not a
    verification failure, and is rejected the same way.
    """
    if raw is None or not raw.strip():
        raise AuthError("missing_signature")

    parts: dict[str, str] = {}
    for chunk in raw.split(","):
        key, sep, value = chunk.strip().partition("=")
        if not sep:
            raise AuthError("malformed_signature")
        parts[key.strip()] = value.strip()

    if "t" not in parts or "v1" not in parts:
        raise AuthError("malformed_signature")

    try:
        timestamp = int(parts["t"])
    except ValueError:
        raise AuthError("malformed_signature") from None

    if not parts["v1"]:
        raise AuthError("malformed_signature")

    return timestamp, parts["v1"]


def expected_signature(secret: str, timestamp: int, raw_body: bytes) -> str:
    """hex( HMAC-SHA256(secret, f"{timestamp}.{raw_body}") ), computed over the raw bytes."""
    message = str(timestamp).encode("utf-8") + b"." + raw_body
    return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()


def verify_request(
    raw_body: bytes,
    signature_header: str | None,
    secret: str,
    now: float,
    max_skew_seconds: int = DEFAULT_MAX_SKEW_SECONDS,
) -> int:
    """Verify a signed request. Returns the signature's timestamp; raises AuthError otherwise.

    Checked in this order deliberately — the staleness check runs BEFORE the HMAC comparison so a
    replayed-but-otherwise-valid request is rejected on the cheap check, and the expensive HMAC is
    never computed for a request we already know we're refusing.
    """
    timestamp, provided = parse_signature_header(signature_header)

    if abs(now - timestamp) > max_skew_seconds:
        raise AuthError("stale_signature")

    if not hmac.compare_digest(expected_signature(secret, timestamp, raw_body), provided):
        raise AuthError("invalid_signature")

    return timestamp
