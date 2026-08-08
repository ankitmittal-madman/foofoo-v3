from ops.recommendation.catalogue_eligibility import (
    REQUIRED_TAXONOMY_FIELDS,
    DishRecord,
    evaluate_dish,
    evaluate_dishes,
)

FULL_TAXONOMY = frozenset(REQUIRED_TAXONOMY_FIELDS)


def make_dish(**overrides) -> DishRecord:
    base = dict(
        dish_id="d1",
        is_active=True,
        ontology_status="enriched",
        diet_type="veg",
        is_jain=True,
        allergen_flags=0,
        cuisine_id="c1",
        has_ingredient_mapping=True,
        has_meal_class_mapping=True,
        has_meal_slot_mapping=True,
        taxonomy_fields=FULL_TAXONOMY,
    )
    base.update(overrides)
    return DishRecord(**base)


def test_fully_valid_dish_passes_with_no_reasons():
    result = evaluate_dish(make_dish())
    assert result.passed is True
    assert result.reasons == ()


def test_inactive_dish_fails_with_inactive_reason():
    result = evaluate_dish(make_dish(is_active=False))
    assert result.passed is False
    assert "inactive" in result.reasons


def test_ontology_status_not_enriched_fails():
    result = evaluate_dish(make_dish(ontology_status="pending"))
    assert result.passed is False
    assert "ontology_status_not_enriched:pending" in result.reasons


def test_missing_diet_type_fails():
    result = evaluate_dish(make_dish(diet_type=None))
    assert "diet_type_missing" in result.reasons


def test_invalid_diet_type_fails():
    result = evaluate_dish(make_dish(diet_type="carnivore"))
    assert "diet_type_invalid:carnivore" in result.reasons


def test_missing_jain_compatibility_fails():
    result = evaluate_dish(make_dish(is_jain=None))
    assert "jain_compatibility_missing" in result.reasons


def test_missing_allergen_flags_fails():
    result = evaluate_dish(make_dish(allergen_flags=None))
    assert "allergen_flags_missing" in result.reasons


def test_missing_cuisine_fails():
    result = evaluate_dish(make_dish(cuisine_id=None))
    assert "cuisine_mapping_missing" in result.reasons


def test_missing_ingredient_mapping_fails():
    result = evaluate_dish(make_dish(has_ingredient_mapping=False))
    assert "ingredient_mapping_missing" in result.reasons


def test_missing_meal_class_mapping_fails():
    result = evaluate_dish(make_dish(has_meal_class_mapping=False))
    assert "meal_class_mapping_missing" in result.reasons


def test_missing_meal_slot_mapping_fails():
    result = evaluate_dish(make_dish(has_meal_slot_mapping=False))
    assert "meal_slot_mapping_missing" in result.reasons


def test_incomplete_taxonomy_lists_exact_missing_fields():
    partial = FULL_TAXONOMY - {"spice_level", "texture"}
    result = evaluate_dish(make_dish(taxonomy_fields=partial))
    assert result.passed is False
    taxonomy_reason = next(r for r in result.reasons if r.startswith("taxonomy_incomplete:"))
    assert "spice_level" in taxonomy_reason
    assert "texture" in taxonomy_reason
    assert "hero_role" not in taxonomy_reason


def test_multiple_failures_all_reported_never_short_circuited():
    result = evaluate_dish(
        make_dish(is_active=False, diet_type=None, has_ingredient_mapping=False)
    )
    assert "inactive" in result.reasons
    assert "diet_type_missing" in result.reasons
    assert "ingredient_mapping_missing" in result.reasons


def test_evaluate_dishes_preserves_order():
    dishes = [make_dish(dish_id="a"), make_dish(dish_id="b", is_active=False)]
    results = evaluate_dishes(dishes)
    assert [r.dish_id for r in results] == ["a", "b"]
    assert results[0].passed is True
    assert results[1].passed is False
