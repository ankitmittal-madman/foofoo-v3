from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol


class InvalidationRepository(Protocol):
    def cache_invalidation_events(self, after_id: int, limit: int) -> list[dict[str, Any]]: ...


@dataclass
class RedisRestClient:
    url: str
    token: str

    def command(self, *parts: Any) -> Any:
        request = urllib.request.Request(
            self.url,
            data=json.dumps(parts).encode(),
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=10) as response:  # noqa: S310
            if response.status != 200:
                raise RuntimeError(f"redis_rest_http_{response.status}")
            payload = json.loads(response.read(1_000_000))
        if payload.get("error"):
            raise RuntimeError("redis_rest_command_failed")
        return payload.get("result")


class CacheInvalidator:
    """Turn durable database events into Redis namespace-version bumps."""

    cursor_key = "foofoo:ontology:invalidation_cursor"

    def __init__(
        self,
        repository: InvalidationRepository,
        redis: RedisRestClient,
        batch_size: int = 500,
    ):
        self.repository = repository
        self.redis = redis
        self.batch_size = max(1, min(batch_size, 5000))

    def run_once(self) -> int:
        cursor = int(self.redis.command("GET", self.cursor_key) or 0)
        events = self.repository.cache_invalidation_events(cursor, self.batch_size)
        if not events:
            return 0
        for namespace in sorted({str(event["namespace"]) for event in events}):
            self.redis.command("INCR", f"foofoo:ontology:v:{namespace}")
        self.redis.command("SET", self.cursor_key, max(int(event["id"]) for event in events))
        return len(events)
