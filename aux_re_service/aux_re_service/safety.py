"""Conservative dietary and allergy checks that always precede ranking."""

from __future__ import annotations

from .schemas import Candidate, ConstraintCheck, RecommendationRequest

ALIASES = {
    "nut": "nuts",
    "groundnut": "nuts",
    "groundnuts": "nuts",
    "peanut": "nuts",
    "peanuts": "nuts",
    "arachis": "nuts",
    "cashew": "nuts",
    "cashews": "nuts",
    "tree_nut": "nuts",
    "tree_nuts": "nuts",
    "milk products": "dairy",
    "milk solids": "dairy",
}


def canonical_tokens(values: list[str]) -> set[str]:
    """Normalize shared household/catalogue vocabulary before hard-safety comparisons."""
    normalized = set()
    for value in values:
        token = value.strip().casefold()
        if token:
            normalized.add(ALIASES.get(token, token))
    return normalized


def check_candidate(candidate: Candidate, request: RecommendationRequest) -> ConstraintCheck:
    allergies = canonical_tokens(request.allergies)
    restrictions = canonical_tokens(request.restrictions)
    for member in request.household_members:
        allergies.update(canonical_tokens(member.allergies))
        restrictions.update(canonical_tokens(member.restrictions))

    ingredients = canonical_tokens(candidate.ingredients)
    declared_allergens = canonical_tokens(candidate.allergens)
    diets = canonical_tokens(candidate.diet_types)
    unavailable = canonical_tokens(request.unavailable_ingredients)
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

    if candidate.meal_slots and request.meal_slot.casefold() not in canonical_tokens(
        candidate.meal_slots
    ):
        reasons.append(f"meal_slot:{request.meal_slot.casefold()}")
    return ConstraintCheck(passed=not reasons, reasons=reasons)
