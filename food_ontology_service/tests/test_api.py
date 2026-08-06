from __future__ import annotations

from fastapi.testclient import TestClient
from food_ontology_service.main import create_app
from food_ontology_service.repository import MemoryRepository
from food_ontology_service.settings import Principal, Settings

TOKEN = "test-token"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}
EVIDENCE = [{"source_code": "foofoo_research", "extraction_method": "curated_import"}]


def client(scopes=frozenset({"ontology:read", "ontology:write", "ontology:admin"})):
    settings = Settings(
        environment="test", database_url=None, principals=(Principal("test", TOKEN, scopes),)
    )
    return TestClient(create_app(settings, MemoryRepository()))


def dish_payload(name="Masala Dosa", role="primary", class_code="BF_CRISP_SAVOURY"):
    return {
        "canonical_name": name,
        "aliases": [{"name": f"{name} alias", "confidence": 0.9, "evidence": EVIDENCE}],
        "class_memberships": [
            {
                "class_code": class_code,
                "slot": "breakfast",
                "role": role,
                "confidence": 0.95,
                "review_status": "accepted",
                "evidence": EVIDENCE,
            }
        ],
        "fields": {
            "cuisine": {
                "value": "south_indian",
                "confidence": 0.95,
                "review_status": "accepted",
                "evidence": EVIDENCE,
            }
        },
    }


def create_dish(api, payload=None, key="dish-1"):
    return api.post(
        "/v1/dishes", json=payload or dish_payload(), headers={**HEADERS, "Idempotency-Key": key}
    )


def test_auth_is_required_and_scoped():
    api = client(frozenset({"ontology:read"}))
    assert api.get("/v1/meal-classes").status_code == 401
    assert create_dish(api).status_code == 403


def test_create_resolve_and_idempotency_contract():
    api = client()
    first = create_dish(api)
    assert first.status_code == 201
    replay = create_dish(api)
    assert replay.status_code == 201
    assert replay.headers["Idempotency-Replayed"] == "true"
    assert replay.json()["id"] == first.json()["id"]

    conflict = create_dish(api, dish_payload("Idli"))
    assert conflict.status_code == 409
    resolved = api.get("/v1/dishes:resolve", params={"name": "Masala Dosa alias"}, headers=HEADERS)
    assert resolved.status_code == 200
    assert resolved.json()["id"] == first.json()["id"]
    assert resolved.headers["Cache-Control"].startswith("private")
    assert resolved.headers["ETag"]


def test_enrichment_is_async_and_deduplicated():
    api = client()
    dish_id = create_dish(api).json()["id"]
    result = api.post(
        f"/v1/dishes/{dish_id}/enrichment-jobs",
        json={"fields": ["texture"]},
        headers={**HEADERS, "Idempotency-Key": "enrich-1"},
    )
    assert result.status_code == 202
    assert result.json()["status"] == "queued"
    status = api.get(f"/v1/dishes/{dish_id}/enrichment-status", headers=HEADERS)
    assert status.status_code == 200
    assert len(status.json()["jobs"]) == 1


def test_primary_and_addon_candidate_pools_never_mix():
    api = client()
    create_dish(api, dish_payload(), "primary")
    create_dish(api, dish_payload("Coconut Chutney", "addon", "BF_CONDIMENT"), "addon")
    primary = api.get(
        "/v1/meal-classes/BF_CRISP_SAVOURY/dishes", params={"role": "primary"}, headers=HEADERS
    ).json()["items"]
    addon = api.get(
        "/v1/meal-classes/BF_CONDIMENT/dishes", params={"role": "addon"}, headers=HEADERS
    ).json()["items"]
    assert [x["canonical_name"] for x in primary] == ["Masala Dosa"]
    assert [x["canonical_name"] for x in addon] == ["Coconut Chutney"]


def test_relationship_and_cloudinary_reference_are_governed():
    api = client()
    source = create_dish(api, dish_payload(), "source").json()["id"]
    target = create_dish(api, dish_payload("Pesarattu"), "target").json()["id"]
    relation = api.post(
        f"/v1/dishes/{source}/relationships",
        headers=HEADERS,
        json={
            "target_dish_id": target,
            "relationship": "similar_to",
            "score": 0.86,
            "confidence": 0.8,
            "explanation_features": ["fermented_batter", "griddle"],
            "evidence": EVIDENCE,
        },
    )
    assert relation.status_code == 201
    similar = api.get(f"/v1/dishes/{source}/similar", headers=HEADERS).json()["items"]
    assert similar[0]["target_dish_id"] == target

    image = api.post(
        f"/v1/dishes/{source}/images",
        headers=HEADERS,
        json={
            "cloudinary_public_id": f"dishes/{source}/abc",
            "cloudinary_version": 1,
            "secure_url": "https://res.cloudinary.com/demo/image/upload/v1/abc",
            "checksum_sha256": "a" * 64,
            "source_type": "ai_generated",
            "review_status": "accepted",
            "is_primary": True,
        },
    )
    assert image.status_code == 201
    assert api.get(f"/v1/dishes/{source}/images", headers=HEADERS).json()["items"][0]["is_primary"]
