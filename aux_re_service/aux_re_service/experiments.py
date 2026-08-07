"""Stable household-level control/treatment assignment for governed A/B rollout."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .config import Settings


@dataclass(frozen=True)
class ExperimentAssignment:
    enabled: bool
    variant: str
    bucket: float


def assign(household_id: str, settings: Settings) -> ExperimentAssignment:
    digest = hashlib.sha256(f"{settings.experiment_salt}:{household_id}".encode()).digest()
    bucket = int.from_bytes(digest[:8], "big") / (2**64 - 1)
    if not settings.experiment_enabled:
        return ExperimentAssignment(False, "not_enrolled", bucket)
    variant = "treatment" if bucket < settings.experiment_percent else "control"
    return ExperimentAssignment(True, variant, bucket)
