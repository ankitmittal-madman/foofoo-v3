from __future__ import annotations

from uuid import uuid4

from food_ontology_service.handlers import (
    ClassificationRule,
    build_classify_handler,
    build_enrich_handler,
)
from food_ontology_service.models import DishCreate, FieldValue
from food_ontology_service.providers import (
    FoodOnProvider,
    ProviderFact,
    UsdaProvider,
    WikidataProvider,
)
from food_ontology_service.repository import MemoryRepository

EVIDENCE = [{"source_code": "fixture", "extraction_method": "test"}]


class Provider:
    def __init__(self, facts=None, error=None):
        self.facts = facts or []
        self.error = error

    def lookup(self, _name):
        if self.error:
            raise self.error
        return self.facts


def test_enrichment_retains_uncertain_evidence_and_protects_accepted_values():
    repository = MemoryRepository()
    dish = repository.create_dish(
        DishCreate(
            canonical_name="Poha",
            fields={
                "external_ids/wikidata": FieldValue(
                    value="Q-human", confidence=1, review_status="accepted", evidence=EVIDENCE
                )
            },
        )
    )
    handler = build_enrich_handler(
        repository,
        [
            Provider(
                [
                    ProviderFact(
                        "external_ids/wikidata",
                        "Q-provider",
                        0.9,
                        "wikidata",
                        "Q-provider",
                        "https://www.wikidata.org/wiki/Q-provider",
                        "exact",
                    ),
                    ProviderFact(
                        "nutrition/protein_g_per_100g",
                        {"value": 4, "unit": "G", "basis": "100g"},
                        0.9,
                        "usda_fdc",
                        "42",
                        "https://fdc.nal.usda.gov/fdc-app.html#/food-details/42",
                        "exact",
                    ),
                ]
            )
        ],
    )
    assert handler({"dish_id": dish.id, "requested_fields": []}) == "review"
    saved = repository.get_dish(dish.id)
    assert saved.fields["external_ids/wikidata"].value == "Q-human"
    assert "nutrition/protein_g_per_100g" not in saved.fields


def test_classification_rule_preserves_class_role_and_publishes_high_confidence():
    repository = MemoryRepository()
    dish = repository.create_dish(DishCreate(canonical_name="Kanda Poha"))
    # Memory classes are derived from memberships, so seed the canonical class on a fixture dish.
    repository.create_dish(
        DishCreate(
            canonical_name=f"Fixture {uuid4()}",
            class_memberships=[
                {
                    "class_code": "BF_POHA",
                    "slot": "breakfast",
                    "role": "primary",
                    "confidence": 1,
                    "review_status": "accepted",
                    "evidence": EVIDENCE,
                }
            ],
        )
    )
    handler = build_classify_handler(
        repository,
        [ClassificationRule(r"\bpoha\b", "BF_POHA", "breakfast", "primary", 0.95)],
    )
    assert handler({"dish_id": dish.id}) == "complete"
    assert repository.get_dish(dish.id).class_memberships[0].class_code == "BF_POHA"


def test_all_provider_failures_retry_instead_of_silently_reviewing():
    repository = MemoryRepository()
    dish = repository.create_dish(DishCreate(canonical_name="Poha"))
    handler = build_enrich_handler(repository, [Provider(error=TimeoutError())])
    try:
        handler({"dish_id": dish.id})
    except RuntimeError as exc:
        assert str(exc) == "all_enrichment_providers_failed"
    else:
        raise AssertionError("provider outage must be retryable")


def test_foodon_and_wikidata_adapters_preserve_external_identity():
    foodon = FoodOnProvider(
        lambda _url, _headers: {
            "response": {
                "docs": [
                    {
                        "label": "Poha",
                        "iri": "http://purl.obolibrary.org/obo/FOODON_123",
                        "synonym": ["Kanda Poha"],
                    }
                ]
            }
        }
    )
    wikidata = WikidataProvider(
        lambda _url, _headers: {
            "search": [
                {
                    "id": "Q123",
                    "label": "Poha",
                    "description": "Indian flattened rice dish",
                    "concepturi": "https://www.wikidata.org/wiki/Q123",
                }
            ]
        }
    )
    assert foodon.lookup("Poha")[0].value.endswith("FOODON_123")
    assert wikidata.lookup("Poha")[0].value == "Q123"


def test_usda_adapter_never_transfers_nutrition_from_a_similar_food():
    usda = UsdaProvider(
        "test-key",
        lambda _url, _headers: {
            "foods": [
                {
                    "fdcId": 42,
                    "description": "Rice flakes",
                    "foodNutrients": [{"nutrientName": "Protein", "unitName": "G", "value": 4.2}],
                }
            ]
        },
    )
    assert usda.lookup("Poha") == []
