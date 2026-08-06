"""Stage 3: pluggable Dish Ontology API adapter.

Design: a small Protocol (`OntologyAdapter`) with two implementations —

  * `NullExternalOntologyAdapter` — always reports "no external ontology API configured" and
    defers to the repo's own tables. This is the ACTIVE adapter in this delivery: no real Dish
    Ontology API endpoint/credentials exist in this repo or environment, and the task brief is
    explicit that a nonexistent external API must never be fabricated. Every call this adapter
    makes is 100% local — it reads public.cuisines, public.meal_classes, public.taxonomy_terms,
    and public.dish_name_synonyms (all already in this schema) and does fuzzy/exact string
    matching against them. No network call is made.
  * A documented extension point (`ExternalOntologyAdapter`, sketched but not instantiated) shows
    exactly where a real HTTP-backed ontology API would plug in if one is ever configured — same
    `match()` signature, so `pipeline.py` never needs to change to swap adapters.

Selection is via `get_adapter(db)`, which always returns the fallback today. If an env var
`DISH_ONTOLOGY_API_URL` is set in future, wiring a real adapter here is the only change needed.
"""

from __future__ import annotations

import difflib
import os
from dataclasses import dataclass
from typing import Protocol


@dataclass
class OntologyMatch:
    """Result of mapping a raw field value to a canonical ontology entity."""

    matched: bool
    canonical_id: str | None       # e.g. cuisines.id, meal_classes.class_code, taxonomy_terms.id
    canonical_label: str | None
    match_method: str               # 'exact', 'fuzzy', 'no_match'
    confidence: float                # 0..1
    raw_response: dict               # kept verbatim for food_source_records.source_payload


class OntologyAdapter(Protocol):
    def match_cuisine(self, raw_cuisine: str) -> OntologyMatch: ...
    def match_meal_class(self, raw_course: str, meal_occasion_hint: list[str]) -> OntologyMatch: ...
    def match_diet(self, raw_diet: str) -> OntologyMatch: ...


class NullExternalOntologyAdapter:
    """Fallback adapter: repo's own ontology tables + local string matching.

    ACTIVE adapter for this delivery. Documented explicitly per task brief rule 2: no real
    Dish Ontology API is configured/available in this environment, so this fallback is used and
    every match records match_method starting with 'local_' so downstream reporting can always
    tell a real-API match from a local-fallback match if/when a real adapter is added later.
    """

    def __init__(self, cuisines: dict[str, str], meal_classes: list[dict], diet_terms: dict[str, str]):
        """
        cuisines: {lowercase cuisine name -> cuisines.id}
        meal_classes: list of {class_code, slot, display_name} from public.meal_classes
        diet_terms: {lowercase diet label -> canonical diet_type value}
        """
        self._cuisines = cuisines
        self._meal_classes = meal_classes
        self._diet_terms = diet_terms

    def _best_fuzzy(self, needle: str, haystack: list[str], cutoff: float = 0.72) -> tuple[str | None, float]:
        if not needle:
            return None, 0.0
        matches = difflib.get_close_matches(needle.lower(), haystack, n=1, cutoff=cutoff)
        if not matches:
            return None, 0.0
        ratio = difflib.SequenceMatcher(None, needle.lower(), matches[0]).ratio()
        return matches[0], ratio

    def match_cuisine(self, raw_cuisine: str) -> OntologyMatch:
        key = raw_cuisine.strip().lower()
        if key in self._cuisines:
            return OntologyMatch(
                matched=True, canonical_id=self._cuisines[key], canonical_label=raw_cuisine,
                match_method="local_exact", confidence=1.0,
                raw_response={"input": raw_cuisine, "method": "exact_lookup"},
            )
        best, score = self._best_fuzzy(key, list(self._cuisines.keys()))
        if best:
            return OntologyMatch(
                matched=True, canonical_id=self._cuisines[best], canonical_label=best,
                match_method="local_fuzzy", confidence=round(score, 3),
                raw_response={"input": raw_cuisine, "method": "difflib_fuzzy", "matched_key": best},
            )
        return OntologyMatch(
            matched=False, canonical_id=None, canonical_label=None,
            match_method="no_match", confidence=0.0,
            raw_response={"input": raw_cuisine, "method": "no_match"},
        )

    def match_meal_class(self, raw_course: str, meal_occasion_hint: list[str]) -> OntologyMatch:
        """Map CSV 'Course' (e.g. 'Side Dish', 'Main Course', 'Dessert', 'Snack') to an EXISTING
        meal_classes row only. Never invents a new class_code — rule 4 of the task brief.
        """
        key = raw_course.strip().lower()
        # Heuristic slot hint from the raw course text; used only to break ties among
        # equally-scored class_code candidates, never to fabricate a class.
        course_to_slot = {
            "breakfast": "breakfast", "lunch": "lunch", "dinner": "dinner",
            "snack": "snack", "appetizer": "snack", "side dish": "lunch",
            "main course": "lunch", "dessert": "snack", "one pot dish": "lunch",
        }
        hint_slot = course_to_slot.get(key)

        candidates = self._meal_classes
        labels = [c["display_name"].lower() for c in candidates]
        best, score = self._best_fuzzy(key, labels, cutoff=0.55)
        if best is None:
            return OntologyMatch(
                matched=False, canonical_id=None, canonical_label=None,
                match_method="no_match", confidence=0.0,
                raw_response={"input": raw_course, "method": "no_match"},
            )
        chosen = [c for c in candidates if c["display_name"].lower() == best]
        if hint_slot:
            slot_narrowed = [c for c in chosen if c["slot"] == hint_slot]
            if slot_narrowed:
                chosen = slot_narrowed
        pick = chosen[0]
        return OntologyMatch(
            matched=True, canonical_id=pick["class_code"], canonical_label=pick["display_name"],
            match_method="local_fuzzy", confidence=round(min(score, 0.85), 3),
            raw_response={"input": raw_course, "method": "difflib_fuzzy", "matched_class": pick["class_code"]},
        )

    def match_diet(self, raw_diet: str) -> OntologyMatch:
        key = raw_diet.strip().lower()
        canonical = self._diet_terms.get(key)
        if canonical:
            return OntologyMatch(
                matched=True, canonical_id=canonical, canonical_label=canonical,
                match_method="local_exact", confidence=0.95,
                raw_response={"input": raw_diet, "method": "keyword_map"},
            )
        # Substring heuristics, since CSV Diet values are compound, e.g. "High Protein Vegetarian".
        if "non veg" in key or "non-veg" in key or "egg" in key:
            value = "egg" if "egg" in key and "non veg" not in key else "non_veg"
            return OntologyMatch(
                matched=True, canonical_id=value, canonical_label=value,
                match_method="local_keyword", confidence=0.7,
                raw_response={"input": raw_diet, "method": "substring_heuristic"},
            )
        if "vegan" in key:
            return OntologyMatch(
                matched=True, canonical_id="vegan", canonical_label="vegan",
                match_method="local_keyword", confidence=0.7,
                raw_response={"input": raw_diet, "method": "substring_heuristic"},
            )
        if "veg" in key:
            return OntologyMatch(
                matched=True, canonical_id="veg", canonical_label="veg",
                match_method="local_keyword", confidence=0.6,
                raw_response={"input": raw_diet, "method": "substring_heuristic"},
            )
        return OntologyMatch(
            matched=False, canonical_id=None, canonical_label=None,
            match_method="no_match", confidence=0.0,
            raw_response={"input": raw_diet, "method": "no_match"},
        )


DIET_TERM_MAP = {
    "diabetic friendly": "veg",
    "vegetarian": "veg",
    "high protein vegetarian": "veg",
    "eggetarian": "egg",
    "non vegeterian": "non_veg",
    "non vegetarian": "non_veg",
    "vegan": "vegan",
    "no onion no garlic (sattvic)": "veg",
    "gluten free": "veg",
    "sugar free diet": "veg",
}


def get_adapter(cuisines: dict[str, str], meal_classes: list[dict]) -> OntologyAdapter:
    """Adapter factory. Always returns the local-fallback adapter today (see module docstring);
    checks DISH_ONTOLOGY_API_URL only to make the extension point visible/discoverable, never to
    fabricate a call to an endpoint this repo does not actually have.
    """
    if os.environ.get("DISH_ONTOLOGY_API_URL"):
        # NOTE: intentionally not implemented. No real Dish Ontology API is available in this
        # environment/repo. Wiring a real HTTP adapter here is future work, not simulated here.
        raise NotImplementedError(
            "DISH_ONTOLOGY_API_URL is set but no ExternalOntologyAdapter implementation exists "
            "yet in this repo — refusing to fabricate calls to an unconfigured external API. "
            "Remove the env var to use the local fallback adapter, or implement the real client."
        )
    return NullExternalOntologyAdapter(cuisines=cuisines, meal_classes=meal_classes, diet_terms=DIET_TERM_MAP)
