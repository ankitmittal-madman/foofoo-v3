"""
schemas — request/response validation, framework-agnostic (RE-DOC-11 §4).

ZERO FastAPI imports. The Phase A JSON Schema (contracts/ghar-re-v1.schema.json) is the SINGLE
source of truth; this module validates payloads against it directly rather than hand-duplicating
the field rules in code. Route handlers (main.py) call validate_request / validate_response;
the RE validates its own responses before returning them (fail-closed, never silently
drift — RE-DOC-10 §15).
"""

from __future__ import annotations

import json
import os
from typing import Any

from jsonschema import Draft202012Validator

# Where the contract document is read from.
#
# Default: <repo>/contracts/ghar-re-v1.schema.json — correct from a checked-out repo.
#
# Override via GHAR_RE_CONTRACT_PATH: required in a CONTAINER, where this package is installed into
# site-packages and the relative walk above lands outside the image's copy of the repo. The
# Dockerfile copies the contract to an explicit path and sets this variable.
#
# The contract is deliberately NOT copied into the catalogue/config bundle: Phase E's contract-check
# CI gate asserts the repo contains exactly ONE ghar-re-v1.schema.json, so that both services
# provably read the same file. A second committed copy would defeat the very thing that check
# protects, hence a path override instead.
CONTRACT_PATH_VAR = "GHAR_RE_CONTRACT_PATH"
_HERE = os.path.dirname(os.path.abspath(__file__))
_CONTRACT_PATH = os.environ.get(CONTRACT_PATH_VAR) or os.path.normpath(
    os.path.join(_HERE, "..", "..", "contracts", "ghar-re-v1.schema.json")
)

with open(_CONTRACT_PATH) as _f:
    SCHEMA = json.load(_f)


def _validator_for(defname: str) -> Draft202012Validator:
    """A validator bound to one $def, resolving refs within the same contract document."""
    sub = {
        "$schema": SCHEMA["$schema"],
        "$id": SCHEMA["$id"],
        "$defs": SCHEMA["$defs"],
        "$ref": f"#/$defs/{defname}",
    }
    return Draft202012Validator(sub)


_REQUEST = _validator_for("RecommendationRequest")
_RESPONSE = _validator_for("RecommendationResponse")
_MEAL_EPISODE_REQUEST = _validator_for("MealEpisodeRequest")
_MEAL_EPISODE_RESPONSE = _validator_for("MealEpisodeSlateResponse")
_META = _validator_for("MetaResponse")


class ContractError(ValueError):
    """Raised when a payload violates the Phase A contract."""


def _validate(validator: Draft202012Validator, payload: Any, what: str):
    errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.path))
    if errors:
        msgs = "; ".join(
            f"{'/'.join(map(str, e.path)) or '<root>'}: {e.message}" for e in errors[:8]
        )
        raise ContractError(f"{what} does not conform to ghar-re-v1 contract: {msgs}")


def validate_request(payload: Any) -> None:
    """Validate an incoming recommendation request.

    Additive/open per RE-DOC-11 §5 — unknown fields
    are IGNORED (additionalProperties:true in the schema), never rejected."""
    _validate(_REQUEST, payload, "request")


def validate_response(payload: Any) -> None:
    """Validate an outgoing recommendation response against the Phase A contract before it is
    returned to the caller — the fail-closed check RE-DOC-10 §15 requires (the RE checks its own
    output shape, it never trusts that engine.run() got the wire format right by construction)."""
    _validate(_RESPONSE, payload, "response")


def validate_meal_episode_request(payload: Any) -> None:
    """Validate the canonical complete-meal episode request boundary."""
    _validate(_MEAL_EPISODE_REQUEST, payload, "meal episode request")


def validate_meal_episode_response(payload: Any) -> None:
    """Validate the canonical complete-meal episode response boundary."""
    _validate(_MEAL_EPISODE_RESPONSE, payload, "meal episode response")


def validate_meta(payload: Any) -> None:
    """Validate the GET /v1/meta response body against the Phase A MetaResponse contract."""
    _validate(_META, payload, "meta")


CONTRACT_PATH = _CONTRACT_PATH
