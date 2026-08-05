"""Versioned, bundle-backed meal-episode grammar registry.

The recommendation runtime consumes the same governed grammar concepts that are represented by
``food.plate_grammars``. Keeping the published snapshot in the immutable bundle makes generation
deterministic and avoids a database dependency inside the recommendation engine.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Any

from ghar_re_core import config

GRAMMAR_SNAPSHOT = "episode_grammars_v1.json"


@lru_cache(maxsize=1)
def published_grammars() -> dict[str, dict[str, Any]]:
    """Load and validate the published grammar snapshot once for the process lifetime."""
    path = os.path.join(config.SRC, GRAMMAR_SNAPSHOT)
    with open(path, encoding="utf-8") as handle:
        payload = json.load(handle)
    if payload.get("schema_version") != 1 or not isinstance(payload.get("grammars"), list):
        raise ValueError(f"unsupported episode grammar snapshot: {path}")
    grammars: dict[str, dict[str, Any]] = {}
    for grammar in payload["grammars"]:
        code = grammar.get("grammar_code")
        version = grammar.get("version")
        if grammar.get("status") != "published" or not isinstance(code, str):
            continue
        if not isinstance(version, int) or version < 1 or code in grammars:
            raise ValueError(f"invalid or duplicate published episode grammar: {code!r}")
        grammars[code] = grammar
    if not grammars:
        raise ValueError(f"no published episode grammars in {path}")
    return grammars


def grammar_for_plate(plate: dict[str, Any], slot: str) -> dict[str, Any]:
    """Resolve the governed grammar for a generated plate and assert its slot is supported."""
    code = (
        "SINGLE_PRIMARY"
        if plate["form"] != "pair" and not plate.get("support")
        else "BASE_WITH_SIDES"
    )
    grammar = published_grammars().get(code)
    if grammar is None:
        raise ValueError(f"published episode grammar missing: {code}")
    if slot not in grammar["meal_slots"]:
        raise ValueError(f"episode grammar {code} does not support slot {slot}")
    return grammar


def validate_component_roles(grammar: dict[str, Any], roles: list[str]) -> None:
    """Fail closed when generated component roles violate the selected grammar cardinalities."""
    counts = {role: roles.count(role) for role in set(roles)}
    for role, required_count in grammar.get("required_roles", {}).items():
        if counts.get(role, 0) < int(required_count):
            raise ValueError(
                f"episode grammar {grammar['grammar_code']} requires {required_count} {role}"
            )
    allowed = set(grammar.get("required_roles", {})) | set(grammar.get("optional_roles", {}))
    unknown = set(counts) - allowed
    if unknown:
        raise ValueError(
            f"episode grammar {grammar['grammar_code']} has unknown roles: {sorted(unknown)}"
        )
    for role, bounds in grammar.get("optional_roles", {}).items():
        count = counts.get(role, 0)
        if count < int(bounds.get("min", 0)) or count > int(bounds.get("max", count)):
            raise ValueError(
                f"episode grammar {grammar['grammar_code']} rejects {count} {role} components"
            )
