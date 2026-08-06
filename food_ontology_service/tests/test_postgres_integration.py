from __future__ import annotations

import hashlib
import os
from uuid import uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient

from food_ontology_service.main import create_app
from food_ontology_service.postgres_repository import PostgresRepository
from food_ontology_service.settings import Principal, Settings
from food_ontology_service.worker import OntologyWorker


DSN = os.getenv("ONTOLOGY_TEST_DSN")
pytestmark = pytest.mark.skipif(not DSN, reason="ONTOLOGY_TEST_DSN not configured")
TOKEN = "postgres-test-token"
AUTH = {"Authorization": f"Bearer {TOKEN}"}
EVIDENCE = [{"source_code": "integration_test", "extraction_method": "test_fixture"}]


@pytest.fixture(scope="module")
def repository():
    assert DSN
    repo = PostgresRepository(DSN)
    with psycopg.connect(DSN) as connection:
        connection.execute(
            """INSERT INTO ontology.meal_classes(class_code,display_name,slot,planning_role)
               VALUES('TEST_PRIMARY','Test primary','breakfast','primary'),
                     ('TEST_ADDON','Test add-on','breakfast','addon')
               ON CONFLICT(class_code) DO NOTHING"""
        )
    return repo


@pytest.fixture()
def api(repository):
    settings = Settings(
        "test", DSN,
        (Principal("postgres-integration", TOKEN,
                   frozenset({"ontology:read", "ontology:write", "ontology:admin"})),),
    )
    return TestClient(create_app(settings, repository))


def payload(name: str, class_code: str, role: str):
    return {
        "canonical_name": name,
        "aliases": [{"name": f"{name} Alias", "confidence": 0.9, "evidence": EVIDENCE}],
        "class_memberships": [{
            "class_code": class_code, "slot": "breakfast", "role": role,
            "confidence": 0.95, "review_status": "accepted", "evidence": EVIDENCE,
        }],
        "fields": {"cuisine": {"value": "test_cuisine", "confidence": 0.9,
                                 "review_status": "accepted", "evidence": EVIDENCE}},
    }


def create(api: TestClient, body: dict, key: str):
    return api.post("/v1/dishes", json=body, headers={**AUTH, "Idempotency-Key": key})


def test_real_postgres_api_idempotency_resolution_and_role_separation(api):
    suffix = uuid4().hex[:10]
    primary_name = f"Primary {suffix}"
    addon_name = f"Addon {suffix}"
    primary_body = payload(primary_name, "TEST_PRIMARY", "primary")
    first = create(api, primary_body, f"create-primary-{suffix}")
    assert first.status_code == 201, first.text
    replay = create(api, primary_body, f"create-primary-{suffix}")
    assert replay.status_code == 201
    assert replay.headers["Idempotency-Replayed"] == "true"
    assert replay.json()["id"] == first.json()["id"]
    assert create(api, payload(addon_name, "TEST_ADDON", "addon"),
                  f"create-addon-{suffix}").status_code == 201

    resolved = api.get("/v1/dishes:resolve", params={"name": f"{primary_name} Alias"}, headers=AUTH)
    assert resolved.status_code == 200
    assert resolved.json()["id"] == first.json()["id"]

    primary = api.get("/v1/meal-classes/TEST_PRIMARY/dishes",
                      params={"role": "primary"}, headers=AUTH).json()["items"]
    addon = api.get("/v1/meal-classes/TEST_ADDON/dishes",
                    params={"role": "addon"}, headers=AUTH).json()["items"]
    assert primary_name in {item["canonical_name"] for item in primary}
    assert addon_name in {item["canonical_name"] for item in addon}
    assert addon_name not in {item["canonical_name"] for item in primary}


def test_real_postgres_job_claim_completion_and_retry(api, repository):
    suffix = uuid4().hex[:10]
    dish = create(api, payload(f"Queued {suffix}", "TEST_PRIMARY", "primary"),
                  f"create-queued-{suffix}").json()
    for key, fields in (("complete", ["texture"]), ("retry", ["region"])):
        result = api.post(f"/v1/dishes/{dish['id']}/enrichment-jobs",
                          json={"fields": fields},
                          headers={**AUTH, "Idempotency-Key": f"{key}-{suffix}"})
        assert result.status_code == 202, result.text

    def handler(job):
        if "region" in job["requested_fields"]:
            raise TimeoutError("simulated provider outage")
        return "complete"

    report = OntologyWorker(repository, f"integration-{suffix}", {"enrich": handler}, 10).run_once()
    assert report.completed >= 1
    assert report.retried >= 1
    with psycopg.connect(DSN, row_factory=psycopg.rows.dict_row) as connection:
        rows = connection.execute(
            "SELECT status FROM ontology.jobs WHERE dish_id=%s ORDER BY created_at", (dish["id"],)
        ).fetchall()
    assert {row["status"] for row in rows} >= {"complete", "retry"}


def test_real_postgres_relationship_image_and_update_are_read_after_write(api):
    suffix = uuid4().hex[:10]
    source = create(api, payload(f"Source {suffix}", "TEST_PRIMARY", "primary"),
                    f"source-{suffix}").json()
    target = create(api, payload(f"Target {suffix}", "TEST_PRIMARY", "primary"),
                    f"target-{suffix}").json()
    updated = api.patch(f"/v1/dishes/{source['id']}", headers=AUTH,
                        json={"canonical_name": f"Updated {suffix}"})
    assert updated.status_code == 200
    assert updated.json()["canonical_name"] == f"Updated {suffix}"

    relation = api.post(f"/v1/dishes/{source['id']}/relationships", headers=AUTH, json={
        "target_dish_id": target["id"], "relationship": "similar_to", "score": 0.8,
        "confidence": 0.85, "explanation_features": ["class"], "evidence": EVIDENCE,
    })
    assert relation.status_code == 201
    assert relation.json()["relationships"][0]["target_dish_id"] == target["id"]

    image = api.post(f"/v1/dishes/{source['id']}/images", headers=AUTH, json={
        "cloudinary_public_id": f"dishes/{source['id']}/{suffix}",
        "cloudinary_version": 1,
        "secure_url": f"https://res.cloudinary.com/test/image/upload/v1/{suffix}",
        "checksum_sha256": hashlib.sha256(suffix.encode()).hexdigest(),
        "source_type": "ai_generated", "review_status": "accepted", "is_primary": True,
    })
    assert image.status_code == 201
    assert image.json()["images"][0]["is_primary"] is True
