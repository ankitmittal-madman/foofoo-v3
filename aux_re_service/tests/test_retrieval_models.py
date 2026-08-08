from __future__ import annotations

import io
import json
from dataclasses import replace
from pathlib import Path

import pytest
from aux_re_service.config import Settings
from aux_re_service.qdrant_endpoint import qdrant_base
from aux_re_service.retrieval import CandidateRetriever, local_embedding
from aux_re_service.schemas import RecommendationRequest


def request(**overrides) -> RecommendationRequest:
    payload = {
        "user_id": "u",
        "household_id": "h",
        "meal_slot": "dinner",
        "region": "Maharashtra",
        "preferences": ["Maharashtrian"],
        "pantry_items": ["rice"],
        "existing_result": {"items": []},
        "candidates": [],
        "debug": True,
    }
    payload.update(overrides)
    return RecommendationRequest.model_validate(payload)


def config(**overrides) -> Settings:
    return replace(Settings.from_env(), enabled=True, **overrides)


def test_local_embedding_is_deterministic_normalized_and_context_sensitive():
    first = local_embedding("dinner Maharashtra rice")
    assert first == local_embedding("dinner Maharashtra rice")
    assert first != local_embedding("breakfast Kerala dosa")
    assert abs(sum(value * value for value in first) - 1.0) < 1e-9


def test_qdrant_endpoint_accepts_fly_private_dns_and_rejects_public_or_ambiguous_urls():
    assert (
        qdrant_base("http://foofoo-aux-qdrant.internal:6333")
        == "http://foofoo-aux-qdrant.internal:6333"
    )
    assert (
        qdrant_base("https://cluster.example.qdrant.io:6333", "cluster.example.qdrant.io")
        == "https://cluster.example.qdrant.io:6333"
    )
    for unsafe in (
        "https://qdrant.example.com:6333",
        "http://qdrant.internal.evil.example:6333",
        "http://user:qdrant@qdrant:6333",
        "http://qdrant:6333/collections",
        "http://qdrant:6334",
    ):
        with pytest.raises(ValueError):
            qdrant_base(unsafe)


def test_qdrant_query_and_structured_output(monkeypatch):
    captured = {}

    class Response(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            self.close()

    def fake_urlopen(req, timeout):
        captured["url"] = req.full_url
        captured["body"] = json.loads(req.data)
        captured["headers"] = dict(req.header_items())
        captured["timeout"] = timeout
        return Response(
            json.dumps(
                {
                    "result": {
                        "points": [
                            {
                                "id": "q-1",
                                "payload": {
                                    "name": "Varan Bhaat",
                                    "meal_slots": ["dinner"],
                                },
                            }
                        ]
                    }
                }
            ).encode()
        )

    monkeypatch.setattr("aux_re_service.retrieval.urllib.request.urlopen", fake_urlopen)
    result = CandidateRetriever(
        config(
            qdrant_url="http://localhost:6333",
            qdrant_api_key="protected",
            qdrant_enabled=True,
        )
    ).retrieve(request())
    assert captured["url"].endswith("/collections/foofoo_recipes/points/query")
    assert len(captured["body"]["query"]) == 64
    assert captured["body"]["filter"]["must"][0]["key"] == "meal_slots"
    assert captured["body"]["filter"]["must"][1] == {
        "key": "regions",
        "match": {"any": ["maharashtra", "west"]},
    }
    assert captured["headers"]["Api-key"] == "protected"
    assert result.candidates[0].id == "q-1"
    assert result.failures == {}


def test_qdrant_failure_isolated_when_request_candidates_exist(monkeypatch):
    def fail(*_args, **_kwargs):
        raise TimeoutError

    monkeypatch.setattr("aux_re_service.retrieval.urllib.request.urlopen", fail)
    candidate = {"id": "local", "name": "Local", "meal_slots": ["dinner"]}
    result = CandidateRetriever(
        config(qdrant_url="http://localhost:6333", qdrant_enabled=True)
    ).retrieve(request(candidates=[candidate]))
    assert [row.id for row in result.candidates] == ["local"]
    assert result.failures == {"qdrant": "TimeoutError"}


def test_qdrant_binds_retrieval_to_one_publication_and_canonical_ids(monkeypatch):
    captured = {}
    version = "sha256:catalogue-v1"
    dish_id = "00000000-0000-0000-0000-000000000001"

    class Response(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            self.close()

    def fake_urlopen(req, timeout):
        captured["body"] = json.loads(req.data)
        return Response(
            json.dumps(
                {
                    "result": {
                        "points": [
                            {
                                "id": dish_id,
                                "payload": {
                                    "id": dish_id,
                                    "name": "Published Poha",
                                    "meal_slots": ["dinner"],
                                    "publication_version": version,
                                },
                            }
                        ]
                    },
                }
            ).encode()
        )

    monkeypatch.setattr("aux_re_service.retrieval.urllib.request.urlopen", fake_urlopen)
    result = CandidateRetriever(
        config(
            qdrant_url="http://localhost:6333",
            qdrant_enabled=True,
            catalogue_publication_version=version,
        )
    ).retrieve(request())

    assert captured["body"]["filter"]["must"][1] == {
        "key": "publication_version",
        "match": {"value": version},
    }
    assert result.candidates[0].id == dish_id


def test_qdrant_prefilter_uses_strongest_diet_and_canonical_allergen(monkeypatch):
    captured = {}

    class Response(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            self.close()

    def fake_urlopen(req, timeout):
        captured["body"] = json.loads(req.data)
        return Response(json.dumps({"result": {"points": []}}).encode())

    monkeypatch.setattr("aux_re_service.retrieval.urllib.request.urlopen", fake_urlopen)
    CandidateRetriever(config(qdrant_url="http://localhost:6333", qdrant_enabled=True)).retrieve(
        request(
            restrictions=["vegetarian", "vegan"],
            allergies=["groundnut"],
        )
    )

    query_filter = captured["body"]["filter"]
    by_key = {item["key"]: item for item in query_filter["must"]}
    assert by_key["diet_types"] == {
        "key": "diet_types",
        "match": {"any": ["vegan"]},
    }
    assert query_filter["must_not"][0] == {
        "key": "allergens",
        "match": {"any": ["nuts"]},
    }


def test_knowledge_graph_expands_seed_and_cold_start():
    graph_path = Path(__file__).parents[1] / "examples" / "knowledge_graph.json"
    seed = {"id": "seed-dal", "name": "Dal seed", "meal_slots": ["dinner"]}
    seeded = CandidateRetriever(config(knowledge_graph_path=str(graph_path))).retrieve(
        request(candidates=[seed])
    )
    assert [candidate.id for candidate in seeded.candidates] == ["seed-dal", "varan-bhaat"]

    cold = CandidateRetriever(config(knowledge_graph_path=str(graph_path))).retrieve(request())
    assert [candidate.id for candidate in cold.candidates] == ["varan-bhaat"]
