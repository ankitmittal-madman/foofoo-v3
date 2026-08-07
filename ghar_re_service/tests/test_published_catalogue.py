import hashlib
import json
import sqlite3

import pytest
from ghar_re_service.published_catalogue import (
    PublishedCatalogueError,
    PublishedCatalogueStore,
    select_for_request,
)

from ghar_re_core.catalogue import Catalogue, dish_allergens


def publication_row(dish_id: str, name: str = "Published Poha") -> dict:
    return {
        "schema_version": "recommendation-catalogue-row-v1",
        "id": dish_id,
        "name": name,
        "diet_type": "veg",
        "is_jain": True,
        "allergen_flags": 160,
        "cook_time_minutes": 20,
        "difficulty": "beginner",
        "calories": 250,
        "serving_size": "1 plate",
        "food_dna_tier_1": "tier_1",
        "cuisine": {"name": "maharashtrian", "state_origin": "Maharashtra"},
        "ingredients": [
            {"name": "rice", "is_main_ingredient": True},
            {"name": "salt", "is_main_ingredient": False},
        ],
        "aliases": ["Kanda Poha"],
        "taxonomy": {
            "hero_role": "standalone",
            "spice_level": 1,
            "heaviness": 1,
            "cooking_method": ["sauteed"],
            "texture": ["soft"],
            "richness": ["light"],
            "weather_affinity": ["all_weather"],
            "meal_type": ["breakfast"],
            "farali_compatible": False,
        },
    }


def build_publication(tmp_path, rows):
    directory = tmp_path / "publication"
    directory.mkdir()
    index_path = directory / "catalogue.sqlite3"
    with sqlite3.connect(index_path) as database:
        database.execute(
            "CREATE TABLE catalogue (dish_id TEXT PRIMARY KEY, name TEXT, payload TEXT) WITHOUT ROWID"
        )
        database.executemany(
            "INSERT INTO catalogue VALUES (?, ?, ?)",
            [
                (row["id"], row["name"], json.dumps(row, sort_keys=True, separators=(",", ":")))
                for row in rows
            ],
        )
    index_hash = hashlib.sha256(index_path.read_bytes()).hexdigest()
    (directory / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "recommendation-catalogue-publication-v1",
                "publication_version": "sha256:test-publication",
                "row_count": len(rows),
                "catalogue_sqlite_sha256": index_hash,
            }
        )
    )
    return directory


def test_store_hydrates_only_requested_ids_with_canonical_identity(tmp_path):
    first_id = "00000000-0000-0000-0000-000000000001"
    second_id = "00000000-0000-0000-0000-000000000002"
    store = PublishedCatalogueStore(
        build_publication(
            tmp_path,
            [publication_row(first_id), publication_row(second_id, "Published Idli")],
        )
    )

    catalogue = store.hydrate([second_id])

    assert [dish.id for dish in catalogue] == [second_id]
    assert catalogue.get("Published Idli").main_ingredients == ["rice"]
    assert catalogue.get("Published Idli").jain_compatible == "Y"
    assert dish_allergens(catalogue.get("Published Idli")) >= {"fish", "soy"}


def test_store_fails_closed_for_missing_ids_or_incomplete_taxonomy(tmp_path):
    dish_id = "00000000-0000-0000-0000-000000000001"
    row = publication_row(dish_id)
    row["taxonomy"].pop("hero_role")
    store = PublishedCatalogueStore(build_publication(tmp_path, [row]))

    with pytest.raises(PublishedCatalogueError, match="taxonomy"):
        store.hydrate([dish_id])
    with pytest.raises(PublishedCatalogueError, match="absent"):
        store.hydrate(["00000000-0000-0000-0000-000000000099"])


def test_store_rejects_tampered_index(tmp_path):
    dish_id = "00000000-0000-0000-0000-000000000001"
    directory = build_publication(tmp_path, [publication_row(dish_id)])
    with (directory / "catalogue.sqlite3").open("ab") as handle:
        handle.write(b"tampered")
    with pytest.raises(PublishedCatalogueError, match="checksum"):
        PublishedCatalogueStore(directory)


def test_request_selection_preserves_fallback_and_reports_hydration_failure(tmp_path):
    fallback = Catalogue()
    selected, metadata = select_for_request({}, fallback, None)
    assert selected is fallback
    assert metadata["reason"] == "bounded_candidates_not_requested"

    dish_id = "00000000-0000-0000-0000-000000000001"
    store = PublishedCatalogueStore(build_publication(tmp_path, [publication_row(dish_id)]))
    selected, metadata = select_for_request(
        {"candidate_dish_ids": ["00000000-0000-0000-0000-000000000099"]}, fallback, store
    )
    assert selected is fallback
    assert metadata["reason"] == "candidate_hydration_failed"


def test_request_selection_uses_bounded_publication_when_all_ids_resolve(tmp_path):
    fallback = Catalogue()
    dish_id = "00000000-0000-0000-0000-000000000001"
    store = PublishedCatalogueStore(build_publication(tmp_path, [publication_row(dish_id)]))

    selected, metadata = select_for_request({"candidate_dish_ids": [dish_id]}, fallback, store)

    assert selected is not fallback
    assert metadata == {
        "source": "published_candidates",
        "reason": "bounded_candidates_hydrated",
        "publication_version": "sha256:test-publication",
        "candidate_count": 1,
    }
