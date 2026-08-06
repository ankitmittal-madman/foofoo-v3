"""Conservative dietary and allergy checks that always precede ranking."""

from __future__ import annotations

from .schemas import Candidate, ConstraintCheck, RecommendationRequest

ALIASES = {
    "groundnut": "peanut",
    "groundnuts": "peanut",
    "peanuts": "peanut",
    "arachis": "peanut",
    "cashews": "cashew",
    "milk products": "dairy",
    "milk solids": "dairy",
}


def _tokens(values: list[str]) -> set[str]:
    normalized = set()
    for value in values:
        token = value.strip().casefold()
        if token:
            normalized.add(ALIASES.get(token, token))
    return normalized


def check_candidate(candidate: Candidate, request: RecommendationRequest) -> ConstraintCheck:
    allergies = _tokens(request.allergies)
    restrictions = _tokens(request.restrictions)
    for member in request.household_members:
        allergies.update(_tokens(member.allergies))
        restrictions.update(_tokens(member.restrictions))

    ingredients = _tokens(candidate.ingredients)
    declared_allergens = _tokens(candidate.allergens)
    diets = _tokens(candidate.diet_types)
    unavailable = _tokens(request.unavailable_ingredients)
    reasons: list[str] = []

    allergy_hits = allergies & (ingredients | declared_allergens)
    if allergy_hits:
        reasons.append("allergy:" + ",".join(sorted(allergy_hits)))
    unavailable_hits = unavailable & ingredients
    if unavailable_hits:
        reasons.append("unavailable:" + ",".join(sorted(unavailable_hits)))

    diet_aliases = {
        "vegetarian": {"vegetarian", "vegan", "jain"},
        "veg": {"vegetarian", "vegan", "jain"},
        "vegan": {"vegan"},
        "jain": {"jain"},
        "no onion garlic": {"jain", "no onion garlic"},
    }
    for restriction in restrictions:
        allowed = diet_aliases.get(restriction)
        if allowed is not None and not (diets & allowed):
            reasons.append(f"diet:{restriction}")
        if (
            restriction.startswith("avoid:")
            and restriction.removeprefix("avoid:").strip() in ingredients
        ):
            reasons.append(f"restriction:{restriction}")

    if candidate.meal_slots and request.meal_slot.casefold() not in _tokens(candidate.meal_slots):
        reasons.append(f"meal_slot:{request.meal_slot.casefold()}")
    return ConstraintCheck(passed=not reasons, reasons=reasons)
