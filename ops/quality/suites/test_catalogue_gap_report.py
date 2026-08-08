from ops.recommendation.catalogue_eligibility import REQUIRED_TAXONOMY_FIELDS, DishRecord
from ops.recommendation.catalogue_gap_report import BUCKET_ORDER, bucket_dish, build_gap_report

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


def test_publishable_dish_buckets_as_publishable():
    assert bucket_dish(make_dish()) == "publishable"


def test_inactive_dish_buckets_first_regardless_of_other_gaps():
    dish = make_dish(is_active=False, diet_type=None, has_ingredient_mapping=False)
    assert bucket_dish(dish) == "inactive_or_rejected"


def test_rejected_ontology_status_buckets_as_inactive_or_rejected():
    assert bucket_dish(make_dish(ontology_status="rejected")) == "inactive_or_rejected"


def test_missing_meal_class_before_missing_ingredients():
    dish = make_dish(has_meal_class_mapping=False, has_ingredient_mapping=False)
    assert bucket_dish(dish) == "missing_meal_class"


def test_missing_meal_slot_only():
    dish = make_dish(has_meal_slot_mapping=False)
    assert bucket_dish(dish) == "missing_meal_slot"


def test_missing_ingredients_only():
    dish = make_dish(has_ingredient_mapping=False)
    assert bucket_dish(dish) == "missing_ingredients"


def test_missing_diet_jain_allergen_only():
    assert bucket_dish(make_dish(diet_type=None)) == "missing_diet_jain_allergen"
    assert bucket_dish(make_dish(is_jain=None)) == "missing_diet_jain_allergen"
    assert bucket_dish(make_dish(allergen_flags=None)) == "missing_diet_jain_allergen"


def test_missing_cuisine_only():
    assert bucket_dish(make_dish(cuisine_id=None)) == "missing_cuisine"


def test_missing_taxonomy_only():
    partial = FULL_TAXONOMY - {"spice_level"}
    assert bucket_dish(make_dish(taxonomy_fields=partial)) == "missing_taxonomy"


def test_not_yet_enriched_but_otherwise_complete_buckets_as_missing_taxonomy():
    assert bucket_dish(make_dish(ontology_status="review")) == "missing_taxonomy"


def test_every_bucket_result_is_a_known_bucket_name():
    for dish in (
        make_dish(),
        make_dish(is_active=False),
        make_dish(has_meal_class_mapping=False),
        make_dish(has_meal_slot_mapping=False),
        make_dish(has_ingredient_mapping=False),
        make_dish(diet_type=None),
        make_dish(cuisine_id=None),
        make_dish(taxonomy_fields=frozenset()),
    ):
        assert bucket_dish(dish) in BUCKET_ORDER


def test_gap_report_counts_sum_to_total_dishes():
    dishes = [
        make_dish(dish_id="1"),
        make_dish(dish_id="2", is_active=False),
        make_dish(dish_id="3", has_meal_class_mapping=False),
        make_dish(dish_id="4", has_meal_slot_mapping=False),
        make_dish(dish_id="5", has_ingredient_mapping=False),
        make_dish(dish_id="6", diet_type=None),
        make_dish(dish_id="7", cuisine_id=None),
        make_dish(dish_id="8", taxonomy_fields=frozenset()),
    ]
    report = build_gap_report(dishes)
    assert report["total_dishes"] == len(dishes)
    assert sum(report["counts"].values()) == len(dishes)
    assert set(report["counts"]) == set(BUCKET_ORDER)


def test_gap_report_assigns_each_dish_exactly_one_bucket():
    dishes = [make_dish(dish_id=str(i)) for i in range(5)]
    report = build_gap_report(dishes)
    assignments = report["assignments"]
    assert len(assignments) == len(dishes)
    assert {a.dish_id for a in assignments} == {d.dish_id for d in dishes}


def test_empty_dish_list_produces_zeroed_report():
    report = build_gap_report([])
    assert report["total_dishes"] == 0
    assert sum(report["counts"].values()) == 0
