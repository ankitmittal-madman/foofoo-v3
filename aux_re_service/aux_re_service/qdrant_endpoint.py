"""Strict Qdrant endpoint validation shared by runtime retrieval and publication upload."""

from __future__ import annotations

import re
import urllib.parse

LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "qdrant"}
FLY_PRIVATE_HOST = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.internal$")
GOVERNED_HTTPS_HOST = re.compile(
    r"^(?=.{1,253}$)(?=.*[a-z])(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"[a-z][a-z0-9-]{0,62}$"
)


def qdrant_base(url: str, allowed_host: str | None = None) -> str:
    """Allow local/private Qdrant or one exact governed HTTPS host."""
    parsed = urllib.parse.urlparse(url)
    hostname = parsed.hostname or ""
    is_local = hostname in LOCAL_HOSTS
    is_fly_private = bool(FLY_PRIVATE_HOST.fullmatch(hostname))
    is_governed_https = (
        bool(allowed_host)
        and bool(GOVERNED_HTTPS_HOST.fullmatch(allowed_host or ""))
        and hostname == allowed_host
        and parsed.scheme == "https"
    )
    if (
        parsed.scheme not in {"http", "https"}
        or not (is_local or is_fly_private or is_governed_https)
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
        or parsed.port not in {None, 443, 6333}
        or (is_fly_private and parsed.scheme != "http")
        or ((is_local or is_fly_private) and parsed.port not in {None, 6333})
    ):
        raise ValueError("Qdrant URL is not an approved local, private, or governed HTTPS endpoint")
    return url.rstrip("/")
