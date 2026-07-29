"""
Per-client request rate limiting (Phase F follow-up — public-ingress hardening).

WHY THIS EXISTS. The founder decision recorded in README §"Public ingress" settles the networking
question: Supabase Edge Functions cannot present a fixed egress IP range, so the RE accepts public
ingress and the HMAC signature check (auth.py) is the sole trust boundary. That check is
cryptographically sound, but it is now internet-reachable — so anything that can send bytes can make
the service compute an HMAC. This module caps how often any single client may do that.

It is deliberately NOT a WAF. It is a volume damper: it stops one noisy or hostile source from
burning the machine's CPU on signature verification, and nothing more. Distributed floods, botnets,
and L7 attack patterns are out of scope (see README for the Cloudflare note if that day comes).

Like auth.py this module is PURE — no FastAPI import, no I/O, no clock of its own (callers pass
`now`) — so its behaviour is unit-testable without HTTP or sleeps.

Two properties worth stating explicitly, because both are deliberate trade-offs:

  * BOUNDED MEMORY, IMPERFECT ACCOUNTING. Tracking one entry per source address is itself a memory
    exhaustion vector when the addresses are attacker-controlled. The tracking table is therefore
    capped and evicts least-recently-seen clients, which means a rotating-IP flood can evict a
    legitimate client's tally and hand it a fresh allowance. That is the correct trade: a bounded
    table that occasionally forgives beats an unbounded one that can OOM the machine it protects.

  * PER PROCESS, PER MACHINE. The window lives in this process's memory. The Dockerfile pins
    `--workers 1`, so today one machine == one window, and `min_machines_running = 1` means there is
    normally one machine — the configured limit is the real limit. Scale to N machines and the
    effective ceiling becomes N x the limit, because Fly's proxy may route the same client to any of
    them. Shared enforcement needs shared state (Redis et al) and is not worth it at this size.
"""

from __future__ import annotations

import math
from collections import OrderedDict, deque
from dataclasses import dataclass

# Generous on purpose. Legitimate traffic arrives from Supabase's Edge Function egress, which is
# NAT'd — many end users can share one source address, so a tight per-IP cap would throttle real
# users, not attackers. Tune with GHAR_RE_RATE_LIMIT_PER_MINUTE (see providers.py) rather than
# editing this; the point of a default is to be safe when nobody has thought about it yet.
DEFAULT_MAX_REQUESTS_PER_MINUTE = 300
DEFAULT_WINDOW_SECONDS = 60
DEFAULT_MAX_TRACKED_CLIENTS = 4096


@dataclass(frozen=True)
class RateLimitDecision:
    """Outcome of one check. `retry_after` is seconds, and is 0 whenever `allowed` is True."""

    allowed: bool
    remaining: int
    retry_after: int


class SlidingWindowRateLimiter:
    """Sliding-window counter: at most `max_requests` per `window_seconds` per client key.

    Sliding rather than fixed-bucket deliberately. A fixed 60s bucket lets a caller send the full
    allowance at 11:59:59 and the full allowance again at 12:00:00 — double the intended rate across
    the boundary, which is exactly the burst this is meant to damp.
    """

    def __init__(
        self,
        max_requests: int = DEFAULT_MAX_REQUESTS_PER_MINUTE,
        window_seconds: int = DEFAULT_WINDOW_SECONDS,
        max_tracked_clients: int = DEFAULT_MAX_TRACKED_CLIENTS,
    ):
        if max_requests < 0:
            raise ValueError("max_requests must be >= 0 (0 disables the limiter)")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be > 0")
        if max_tracked_clients <= 0:
            raise ValueError("max_tracked_clients must be > 0")

        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.max_tracked_clients = max_tracked_clients
        # client key -> timestamps of its hits inside the window, oldest first. OrderedDict gives
        # O(1) least-recently-seen eviction; deque gives O(1) expiry from the front.
        self._hits: OrderedDict[str, deque[float]] = OrderedDict()

    @property
    def enabled(self) -> bool:
        """0 requests/window means "turned off", not "block everything" — an operator setting the
        limit to zero is disabling a damper, and must never be able to accidentally black-hole all
        traffic by doing so."""
        return self.max_requests > 0

    @property
    def tracked_clients(self) -> int:
        return len(self._hits)

    def check(self, client_key: str, now: float) -> RateLimitDecision:
        """Record a request from `client_key` and say whether it is allowed.

        Non-idempotent by design: an allowed request consumes allowance. A REJECTED one does not —
        a client that is already over the limit cannot push its own reset further away by continuing
        to hammer, which would turn a brief burst into an unbounded lockout.
        """
        if not self.enabled:
            return RateLimitDecision(allowed=True, remaining=-1, retry_after=0)

        hits = self._hits.get(client_key)
        if hits is None:
            hits = deque()
            self._hits[client_key] = hits
        self._hits.move_to_end(client_key)  # mark most-recently-seen for the eviction policy

        # Drop everything that has aged out of the window.
        cutoff = now - self.window_seconds
        while hits and hits[0] <= cutoff:
            hits.popleft()

        if len(hits) >= self.max_requests:
            # The window frees a slot when its oldest hit ages out. Always >= 1 so a caller that
            # honours Retry-After actually waits rather than spinning on a 0.
            retry_after = max(1, math.ceil(hits[0] + self.window_seconds - now))
            return RateLimitDecision(allowed=False, remaining=0, retry_after=retry_after)

        hits.append(now)
        self._evict_stale()
        return RateLimitDecision(
            allowed=True, remaining=self.max_requests - len(hits), retry_after=0
        )

    def _evict_stale(self) -> None:
        """Hold the tracking table at its cap, dropping least-recently-seen clients first.

        The client just touched was moved to the end above, so it is never the one evicted.
        """
        while len(self._hits) > self.max_tracked_clients:
            self._hits.popitem(last=False)


# Header set by Fly's proxy to the real client address (fly-proxy overwrites any value the client
# sent, so it cannot be forged from the internet).
#
# X-Forwarded-For is deliberately NOT consulted: any client can put anything in it, so keying a rate
# limiter on it would let an attacker mint a fresh allowance per request by varying the header —
# strictly worse than no limiter, because it costs memory while enforcing nothing.
#
# Residual gap, stated rather than glossed: a peer already inside the same Fly organisation reaches
# the app over 6PN without traversing fly-proxy, and could set this header itself. Such a caller is
# already inside the network trust boundary and still needs a valid HMAC signature to get past
# auth.py, so this does not widen the boundary that actually matters.
CLIENT_IP_HEADER = "Fly-Client-IP"


def client_key(fly_client_ip: str | None, peer_host: str | None) -> str:
    """Pick the key to rate-limit on: the proxy-supplied client IP, else the socket peer.

    Falls back to a constant when neither is available (some ASGI test transports set no client).
    That collapses those callers into one shared bucket, which is the conservative direction — it
    can over-limit, never under-limit.
    """
    ip = (fly_client_ip or "").strip()
    if ip:
        return ip
    peer = (peer_host or "").strip()
    return peer or "unknown"
