"""
schemas — request/response validation, framework-agnostic (RE-DOC-11 §4).

ZERO FastAPI imports. The Phase A JSON Schema (contracts/ghar-re-v1.schema.json) is the SINGLE
source of truth; this module validates payloads against it directly rather than hand-duplicating
the field rules in code. Route handlers (main.py) call validate_request / validate_response;
the RE validates its own responses before returning them (fail-closed, never silently drift — RE-DOC-10 §15).
"""
from __future__ import annotations

import json
import os
from typing import Any

from jsonschema import Draft202012Validator

# contracts/ghar-re-v1.schema.json lives at repo root /contracts.
_HERE = os.path.dirname(os.path.abspath(__file__))
_CONTRACT_PATH = os.path.normpath(os.path.join(_HERE, "..", "..", "contracts", "ghar-re-v1.schema.json"))

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
_META = _validator_for("MetaResponse")


class ContractError(ValueError):
    """Raised when a payload violates the Phase A contract."""


def _validate(validator: Draft202012Validator, payload: Any, what: str):
    errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.path))
    if errors:
        msgs = "; ".join(f"{'/'.join(map(str, e.path)) or '<root>'}: {e.message}" for e in errors[:8])
        raise ContractError(f"{what} does not conform to ghar-re-v1 contract: {msgs}")


def validate_request(payload: Any) -> None:
    """Validate an incoming recommendation request. Additive/open per RE-DOC-11 §5 — unknown fields
    are IGNORED (additionalProperties:true in the schema), never rejected."""
    _validate(_REQUEST, payload, "request")


def validate_response(payload: Any) -> None:
    _validate(_RESPONSE, payload, "response")


def validate_meta(payload: Any) -> None:
    _validate(_META, payload, "meta")


CONTRACT_PATH = _CONTRACT_PATH
