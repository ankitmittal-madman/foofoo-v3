"""Bounded, disk-backed hydration of published database candidates for authoritative Ghar safety.

The store never scans or loads the full publication. Aux/Edge supplies at most 500 canonical dish
IDs; this module fetches only those JSON payloads from SQLite, validates the Ghar-critical fields,
and constructs the ordinary in-memory Catalogue shape consumed by unchanged core mathematics.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Protocol
from uuid import UUID

from ghar_re_core.catalogue import Catalogue, allergens_from_flags, regional_affinity_scores

PUBLICATION_DIR_VAR = "GHAR_RE_PUBLISHED_CATALOGUE_DIR"
MAX_CANDIDATE_IDS = 500
MANIFEST_SCHEMA_VERSION = "recommendation-catalogue-publication-v1"
REQUIRED_TAXONOMY_FIELDS = {
    "hero_role",
    "spice_level",
    "heaviness",
    "cooking_method",
    "texture",
    "richness",
    "weather_affinity",
    "meal_type",
}


class PublishedCatalogueError(RuntimeError):
    """Raised when a publication cannot prove complete, canonical candidate hydration."""


class IdentityCatalogue(Protocol):
    """Minimal mutable catalogue surface required for startup identity reconciliation."""

    dishes: list[Any]
    by_id: dict[str, Any]


def _sha256_file(path: Path) -> str:
    """Hash a publication artifact in bounded chunks before trusting its contents."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _as_list(value: Any) -> list[Any]:
    """Normalize a scalar or array taxonomy assertion without inventing missing values."""
    if isinstance(value, list):
        return value
    return [] if value is None else [value]


def _number(value: Any, field: str) -> int:
    """Require one bounded integer-like ranking field from the governed taxonomy payload."""
    if isinstance(value, bool):
        raise PublishedCatalogueError(f"{field} must be numeric")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise PublishedCatalogueError(f"{field} must be numeric") from exc


def to_ghar_dish(row: Mapping[str, Any]) -> dict[str, Any]:
    """Translate one complete publication row into Ghar's existing catalogue constructor shape."""
    taxonomy = row.get("taxonomy")
    cuisine = row.get("cuisine")
    ingredients = row.get("ingredients")
    if not isinstance(taxonomy, Mapping) or not taxonomy.keys() >= REQUIRED_TAXONOMY_FIELDS:
        raise PublishedCatalogueError("candidate is missing Ghar-critical taxonomy fields")
    if not isinstance(cuisine, Mapping) or not cuisine.get("name"):
        raise PublishedCatalogueError("candidate is missing canonical cuisine")
    if not isinstance(ingredients, list) or not ingredients:
        raise PublishedCatalogueError("candidate is missing governed ingredients")

    ingredient_pairs: list[tuple[str, bool]] = []
    explicit_allergens = set(allergens_from_flags(row.get("allergen_flags")))
    for ingredient in ingredients:
        if not isinstance(ingredient, Mapping) or not ingredient.get("name"):
            raise PublishedCatalogueError("candidate contains an invalid ingredient")
        ingredient_pairs.append(
            (str(ingredient["name"]), bool(ingredient.get("is_main_ingredient", False)))
        )
        explicit_allergens.update(allergens_from_flags(ingredient.get("allergen_flags")))

    raw_diet = str(row.get("diet_type") or "")
    if raw_diet not in {"veg", "vegan", "egg", "non_veg"}:
        raise PublishedCatalogueError("candidate has unsupported diet_type")
    total_mins = _number(row.get("cook_time_minutes"), "cook_time_minutes")
    hero_values = _as_list(taxonomy["hero_role"])
    if len(hero_values) != 1 or str(hero_values[0]) not in {
        "dry",
        "liquid",
        "single",
        "standalone",
        "support",
    }:
        raise PublishedCatalogueError("candidate has invalid hero_role")
    aliases = [str(value) for value in row.get("aliases", []) if str(value).strip()]
    is_jain = bool(row.get("is_jain"))
    farali_value = taxonomy.get("farali_compatible", False)
    farali = farali_value is True or str(farali_value).upper() == "Y"
    return {
        "id": str(row["id"]),
        "name": str(row["name"]),
        "cuisine": str(cuisine["name"]),
        "state_origin": cuisine.get("state_origin") or taxonomy.get("state_origin"),
        "diet": "veg" if raw_diet == "vegan" else raw_diet,
        "hero_role": str(hero_values[0]),
        "sig_band": None,
        "spice_level": _number(taxonomy["spice_level"], "spice_level"),
        "sweetness": _number(taxonomy.get("sweetness", 0), "sweetness"),
        "heaviness": _number(taxonomy["heaviness"], "heaviness"),
        "difficulty": str(row.get("difficulty") or "intermediate"),
        "prep_mins": 0,
        "cook_mins": total_mins,
        "total_mins": total_mins,
        "calories": row.get("calories"),
        "serving_size": row.get("serving_size"),
        "meal_type": [str(value) for value in _as_list(taxonomy["meal_type"])],
        "dish_category": [str(value) for value in _as_list(taxonomy.get("dish_category"))],
        "cooking_method": [str(value) for value in _as_list(taxonomy["cooking_method"])],
        "primary_taste": [str(value) for value in _as_list(taxonomy.get("primary_taste"))],
        "texture": [str(value) for value in _as_list(taxonomy["texture"])],
        "richness": [str(value) for value in _as_list(taxonomy["richness"])],
        "mouthfeel": [str(value) for value in _as_list(taxonomy.get("mouthfeel"))],
        "aroma_profile": [str(value) for value in _as_list(taxonomy.get("aroma_profile"))],
        "fermentation": str(taxonomy.get("fermentation") or "none"),
        "serving_temp": str(taxonomy.get("serving_temp") or "hot"),
        "weather_affinity": [str(value) for value in _as_list(taxonomy["weather_affinity"])],
        "jain_compatible": "Y" if is_jain else "N",
        "vegan_compatible": raw_diet == "vegan",
        "scope_tier": str(row.get("food_dna_tier_1") or "experimental"),
        "farali_compatible": farali,
        "alternate_names": aliases,
        "synonyms": aliases,
        "ingredients": ingredient_pairs,
        "allergens": sorted(explicit_allergens),
        "regional_affinities": list(row.get("regional_affinities") or []),
        "macro": {"calories": row.get("calories")},
    }


class PublishedCatalogueStore:
    """Verified publication metadata plus per-request canonical-ID hydration from SQLite."""

    def __init__(self, directory: str | Path):
        self.directory = Path(directory)
        manifest_path = self.directory / "manifest.json"
        index_path = self.directory / "catalogue.sqlite3"
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise PublishedCatalogueError("published catalogue manifest is unreadable") from exc
        if manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION:
            raise PublishedCatalogueError("published catalogue manifest schema is unsupported")
        expected_hash = manifest.get("catalogue_sqlite_sha256")
        if not isinstance(expected_hash, str) or _sha256_file(index_path) != expected_hash:
            raise PublishedCatalogueError("published catalogue index checksum mismatch")
        self.index_path = index_path
        self.version = str(manifest.get("publication_version"))
        self.row_count = int(manifest.get("row_count", 0))
        if self.row_count <= 0:
            raise PublishedCatalogueError("published catalogue contains no rows")
        self.identity_row_count = int(manifest.get("identity_row_count", self.row_count))
        if self.identity_row_count < self.row_count:
            raise PublishedCatalogueError("published catalogue identity coverage is incomplete")

    def hydrate(self, candidate_ids: list[str]) -> Catalogue:
        """Load exactly the requested canonical candidates and preserve caller retrieval order."""
        unique_ids = list(dict.fromkeys(value for value in candidate_ids if isinstance(value, str)))
        if not unique_ids or len(unique_ids) > MAX_CANDIDATE_IDS:
            raise PublishedCatalogueError("candidate_dish_ids must contain 1 to 500 unique ids")
        placeholders = ",".join("?" for _ in unique_ids)
        uri = f"file:{self.index_path}?mode=ro"
        with sqlite3.connect(uri, uri=True) as database:
            rows = database.execute(
                f"SELECT dish_id, payload FROM catalogue WHERE dish_id IN ({placeholders})",  # noqa: S608 -- placeholders are generated, not user input
                unique_ids,
            ).fetchall()
        payload_by_id = {dish_id: json.loads(payload) for dish_id, payload in rows}
        missing = [dish_id for dish_id in unique_ids if dish_id not in payload_by_id]
        if missing:
            raise PublishedCatalogueError(
                f"{len(missing)} candidate ids are absent from publication"
            )
        return Catalogue([to_ghar_dish(payload_by_id[dish_id]) for dish_id in unique_ids])

    def canonical_identities_by_name(self) -> dict[str, dict[str, Any]]:
        """Return verified UUID and regional metadata keyed by normalized canonical name.

        This startup-only identity index reads no user data and does not hydrate safety taxonomy or
        alter the serving candidate pool. It exists so the immutable fallback can emit canonical
        dish identity and consume confidence-weighted regional soft-ranking evidence.
        """
        uri = f"file:{self.index_path}?mode=ro"
        with sqlite3.connect(uri, uri=True) as database:
            has_identity_index = database.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='catalogue_identity'"
            ).fetchone()
            source = "catalogue_identity" if has_identity_index else "catalogue"
            columns = {
                str(row[1])
                for row in database.execute(f"PRAGMA table_info({source})").fetchall()  # noqa: S608
            }
            regional_sql = "regional_affinities" if "regional_affinities" in columns else "'[]'"
            rows = database.execute(  # noqa: S608
                f"SELECT dish_id, name, {regional_sql} FROM {source}"
            ).fetchall()
        if len(rows) != self.identity_row_count:
            raise PublishedCatalogueError(
                "published catalogue identity count does not match manifest"
            )

        identities: dict[str, dict[str, Any]] = {}
        for raw_id, raw_name, raw_regional_affinities in rows:
            dish_id = str(raw_id)
            try:
                canonical_id = str(UUID(dish_id))
            except ValueError as exc:
                raise PublishedCatalogueError(
                    "published catalogue contains an invalid dish id"
                ) from exc
            if canonical_id != dish_id.casefold():
                raise PublishedCatalogueError(
                    "published catalogue contains a non-canonical dish id"
                )
            name_key = " ".join(str(raw_name).casefold().split())
            if not name_key:
                raise PublishedCatalogueError("published catalogue contains an empty dish name")
            try:
                regional_affinities = json.loads(str(raw_regional_affinities))
            except json.JSONDecodeError as exc:
                raise PublishedCatalogueError(
                    "published catalogue contains invalid regional affinity metadata"
                ) from exc
            prior = identities.get(name_key)
            if prior is not None and prior["dish_id"] != canonical_id:
                raise PublishedCatalogueError("published catalogue contains a dish-name collision")
            identities[name_key] = {
                "dish_id": canonical_id,
                "regional_affinities": regional_affinities,
            }
        return identities

    def canonical_ids_by_name(self) -> dict[str, str]:
        """Return only canonical UUIDs for callers that do not need regional metadata."""
        return {
            name: str(identity["dish_id"])
            for name, identity in self.canonical_identities_by_name().items()
        }


def reconcile_fallback_identities(
    catalogue: IdentityCatalogue, store: PublishedCatalogueStore | None
) -> dict[str, int]:
    """Attach exact canonical UUIDs to matching fallback dishes without changing candidates.

    Only normalized canonical-name equality is accepted; aliases and fuzzy matching are excluded
    because either could silently attach feedback to the wrong dish. Exact matches receive the UUID
    and confidence-weighted regional soft evidence. Unmatched dishes keep legacy identifiers and
    remain measurable in the returned aggregate coverage counts.
    """
    dishes = list(catalogue.dishes)
    if store is None:
        return {"total": len(dishes), "resolved": 0, "unresolved": len(dishes)}

    identities = store.canonical_identities_by_name()
    resolved = 0
    for dish in dishes:
        identity = identities.get(" ".join(str(dish.name).casefold().split()))
        if identity is None:
            continue
        dish.id = identity["dish_id"]
        dish.regional_affinities = regional_affinity_scores(identity["regional_affinities"])
        resolved += 1

    # Catalogue constructed this index before publication loading. Rebuild it atomically after all
    # exact matches are attached so get_dish() and response serialization observe the same IDs.
    catalogue.by_id = {dish.id: dish for dish in dishes}
    if len(catalogue.by_id) != len(dishes):
        raise PublishedCatalogueError("canonical identity reconciliation produced a collision")
    return {"total": len(dishes), "resolved": resolved, "unresolved": len(dishes) - resolved}


def load_from_environment(
    environ: Mapping[str, str] | None = None,
) -> PublishedCatalogueStore | None:
    """Load the optional published index configured for shadow/bounded serving at startup."""
    values = environ or os.environ
    directory = values.get(PUBLICATION_DIR_VAR)
    return PublishedCatalogueStore(directory) if directory else None


def select_for_request(
    request: Mapping[str, Any], fallback: Any, store: PublishedCatalogueStore | None
) -> tuple[Any, dict[str, Any]]:
    """Choose bounded published candidates or preserve the deterministic fallback catalogue."""
    candidate_ids = request.get("candidate_dish_ids")
    if not isinstance(candidate_ids, list) or not candidate_ids:
        return fallback, {"source": "fallback_bundle", "reason": "bounded_candidates_not_requested"}
    if store is None:
        return fallback, {"source": "fallback_bundle", "reason": "publication_not_configured"}
    try:
        catalogue = store.hydrate(candidate_ids)
    except PublishedCatalogueError:
        return fallback, {"source": "fallback_bundle", "reason": "candidate_hydration_failed"}
    return catalogue, {
        "source": "published_candidates",
        "reason": "bounded_candidates_hydrated",
        "publication_version": store.version,
        "candidate_count": len(catalogue.dishes),
    }
