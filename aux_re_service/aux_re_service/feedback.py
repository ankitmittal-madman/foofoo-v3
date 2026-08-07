"""Idempotent local feedback capture for consented auxiliary-learning events."""

from __future__ import annotations

import json
import threading
from pathlib import Path

from .schemas import FeedbackEvent

_LOCK = threading.Lock()


class FeedbackStoreError(RuntimeError):
    """Feedback is disabled, misconfigured, or unavailable."""


class LocalFeedbackStore:
    def __init__(self, path: Path):
        if not path.is_absolute():
            raise FeedbackStoreError("feedback path must be absolute")
        self.path = path

    def append(self, event: FeedbackEvent) -> bool:
        """Append once and return False when the event ID was already recorded."""
        with _LOCK:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if self.path.is_file():
                for line in self.path.read_text().splitlines():
                    try:
                        if json.loads(line).get("event_id") == event.event_id:
                            return False
                    except json.JSONDecodeError:
                        continue
            payload = event.model_dump(mode="json")
            with self.path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")
                stream.flush()
            return True
