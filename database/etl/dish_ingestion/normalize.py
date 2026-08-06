"""Stage 1: load and normalize the source CSV.

Reads database/seeds/IndianFoodDatasetCSV.csv, trims/normalizes text fields, splits the
ingredient list, and computes a stable row fingerprint used for dedupe and idempotent reruns.
Never mutates the raw row — normalized fields are stored alongside raw_payload, not in place of it.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

EXPECTED_COLUMNS = [
    "Srno", "RecipeName", "TranslatedRecipeName", "Ingredients", "TranslatedIngredients",
    "PrepTimeInMins", "CookTimeInMins", "TotalTimeInMins", "Servings", "Cuisine", "Course",
    "Diet", "Instructions", "TranslatedInstructions", "URL",
]

_WS_RE = re.compile(r"\s+")


def _clean(value: str | None) -> str:
    """Collapse whitespace and trim; never raises on None."""
    if value is None:
        return ""
    return _WS_RE.sub(" ", value).strip()


def _split_ingredients(raw: str) -> list[str]:
    """Split a comma-separated ingredient blob into cleaned, non-empty ingredient phrases.

    The source format is a single free-text field, e.g.
    "6 Karela (Bitter Gourd) - deseeded,Salt - to taste,...". A plain comma split is used
    deliberately (matching the CSV's own delimiter convention) rather than attempting deeper
    quantity/unit parsing here — that belongs to a later, explicit ingredient-normalization pass,
    not this loader.
    """
    if not raw:
        return []
    parts = [p.strip() for p in raw.split(",")]
    return [p for p in parts if p]


def _to_int(value: str | None) -> int | None:
    if value is None or value.strip() == "":
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


@dataclass
class SourceRow:
    """One normalized CSV row, paired with its untouched raw form."""

    srno: int
    raw: dict = field(default_factory=dict)
    normalized: dict = field(default_factory=dict)
    fingerprint: str = ""


def compute_fingerprint(name: str, translated_name: str, ingredients: list[str], url: str) -> str:
    """Stable dedupe/idempotency key: same logical dish content -> same fingerprint, every run.

    Deliberately excludes Srno (not stable across CSV re-exports) and instruction text (long,
    frequently reformatted without changing the dish itself).
    """
    basis = json.dumps(
        {
            "name": name.strip().lower(),
            "translated_name": translated_name.strip().lower(),
            "ingredients": sorted(i.lower() for i in ingredients),
            "url": url.strip().lower(),
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()


def load_and_normalize(csv_path: Path) -> Iterator[SourceRow]:
    """Yield one SourceRow per CSV data row, in file order, deterministically.

    Raises FileNotFoundError if csv_path is missing rather than silently yielding nothing —
    an ETL that silently processes zero rows is a worse failure mode than a loud one.
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"source CSV not found: {csv_path}")

    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = [c for c in EXPECTED_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"source CSV missing expected columns: {missing}")

        for raw_row in reader:
            srno = _to_int(raw_row.get("Srno"))
            if srno is None:
                # A row with no parseable Srno cannot be tracked idempotently — skip loudly
                # at the caller via a sentinel rather than crash the whole load.
                srno = -1

            name = _clean(raw_row.get("RecipeName"))
            translated_name = _clean(raw_row.get("TranslatedRecipeName")) or name
            ingredients_raw = _clean(raw_row.get("TranslatedIngredients")) or _clean(raw_row.get("Ingredients"))
            ingredients = _split_ingredients(ingredients_raw)
            url = _clean(raw_row.get("URL"))

            normalized = {
                "name": name,
                "translated_name": translated_name,
                "ingredients": ingredients,
                "ingredients_raw_text": ingredients_raw,
                "prep_time_mins": _to_int(raw_row.get("PrepTimeInMins")),
                "cook_time_mins": _to_int(raw_row.get("CookTimeInMins")),
                "total_time_mins": _to_int(raw_row.get("TotalTimeInMins")),
                "servings": _to_int(raw_row.get("Servings")),
                "cuisine_raw": _clean(raw_row.get("Cuisine")),
                "course_raw": _clean(raw_row.get("Course")),
                "diet_raw": _clean(raw_row.get("Diet")),
                "url": url,
            }

            yield SourceRow(
                srno=srno,
                raw=dict(raw_row),
                normalized=normalized,
                fingerprint=compute_fingerprint(name, translated_name, ingredients, url),
            )
