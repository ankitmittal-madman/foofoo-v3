from __future__ import annotations

from copy import deepcopy

import pytest
from food_ontology_service.cutover import bundle_checksum, validate_bundle


def sample_bundle():
    bundle = {
        "schema_version": "foofoo-ontology-cutover/v1",
        "source_system": "foofoo_supabase",
        "watermark": "2026-08-06T00:00:00+00:00",
        "meal_classes": [],
        "dishes": [{"legacy_id": "1", "name": "Poha"}],
    }
    bundle["checksum_sha256"] = bundle_checksum(bundle)
    return bundle


def test_cutover_bundle_checksum_is_content_addressed():
    bundle = sample_bundle()
    validate_bundle(bundle)
    changed = deepcopy(bundle)
    changed["dishes"][0]["name"] = "Upma"
    with pytest.raises(RuntimeError, match="checksum"):
        validate_bundle(changed)


def test_cutover_rejects_normalized_name_collisions():
    bundle = sample_bundle()
    bundle["dishes"].append({"legacy_id": "2", "name": "  POHA "})
    bundle["checksum_sha256"] = bundle_checksum(bundle)
    with pytest.raises(RuntimeError, match="collision"):
        validate_bundle(bundle)
