"""PII-minimized structured logs and process-local metrics namespace."""

from __future__ import annotations

import json
import logging
import threading
from collections import Counter
from typing import Any

LOGGER = logging.getLogger("foofoo.aux_re")
LOGGER.setLevel(logging.INFO)
_LOCK = threading.Lock()
_COUNTERS: Counter[str] = Counter()


def record(decision: str) -> None:
    with _LOCK:
        _COUNTERS[f"decision.{decision}"] += 1


def metrics() -> dict[str, int]:
    with _LOCK:
        return dict(_COUNTERS)


def log_decision(**fields: Any) -> None:
    LOGGER.info(json.dumps({"namespace": "aux_rec", **fields}, sort_keys=True, default=str))
