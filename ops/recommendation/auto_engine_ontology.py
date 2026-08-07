"""Canonical ontology gate and confidence scoring for generated research records."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .auto_engine_research import provenance_tags
from .auto_engine_types import AutoEngineConfig, ResearchRecord


def load_ontology(path: Path) -> dict[str, Any]:
    ontology = json.loads(path.read_text(encoding="utf-8"))
    if not ontology.get("dishes") or not ontology.get("relations"):
        raise RuntimeError("ontology must contain canonical dishes and relations")
    return ontology


def confidence_band(value: float) -> str:
    if value >= 0.85:
        return "high"
    if value >= 0.65:
        return "medium"
    return "low"


def _dish_references(payload: dict[str, Any]) -> set[str]:
    references: set[str] = set()
    for key in ("dish_id", "substitute_dish_id"):
        if payload.get(key):
            references.add(str(payload[key]))
    references.update(str(value) for value in payload.get("dish_ids", []))
    references.update(
        str(meal["dish_id"])
        for meal in payload.get("meals", [])
        if isinstance(meal, dict) and meal.get("dish_id")
    )
    return references


def map_and_score_records(
    proposed: list[dict[str, Any]],
    ontology: dict[str, Any],
    config: AutoEngineConfig,
) -> tuple[list[ResearchRecord], dict[str, Any]]:
    dishes = {dish["id"]: dish for dish in ontology["dishes"]}
    mapped: list[ResearchRecord] = []
    rejected = 0
    canonicalized = 0
    for item in proposed:
        payload = dict(item["payload"])
        references = _dish_references(payload)
        missing = sorted(references - dishes.keys())
        applicable = bool(references)
        mapping_status = "mapped" if applicable and not missing else "not_applicable"
        if missing:
            mapping_status = "rejected"
            rejected += 1
        else:
            canonicalized += len(references)

        # Equal-weight, explainable components. Synthetic research is deliberately capped below 1.
        regional_match = payload.get("regional_match")
        if regional_match is None and "regional_match_ratio" in payload:
            regional_match = float(payload["regional_match_ratio"]) >= 0.5
        components = {
            "source_quality": 0.84,
            "ontology_mapping": 0.98 if mapping_status == "mapped" else 0.88,
            "food_realism": 0.93 if references else 0.88,
            "regional_plausibility": 0.92
            if regional_match is True
            else 0.82
            if regional_match is False
            else 0.86,
            "household_plausibility": 0.92 if payload.get("household_id") else 0.84,
            "known_behavior_consistency": 0.88,
            "dedupe_uniqueness": 0.96,
        }
        confidence = round(sum(components.values()) / len(components), 4)
        if mapping_status == "rejected":
            confidence = 0.0
        payload["ontology_mapping"] = {
            "status": mapping_status,
            "ontology_version": config.ontology_version,
            "canonical_dish_ids": sorted(references),
            "missing_dish_ids": missing,
        }
        payload["confidence_components"] = components
        mapped.append(
            ResearchRecord(
                target_table=item["target_table"],
                record_key=item["record_key"],
                payload=payload,
                source_type="expert_research_synthetic",
                generation_method=config.generator_version,
                confidence=confidence,
                confidence_band=confidence_band(confidence),
                ontology_mapping_status=mapping_status,
                ontology_version=config.ontology_version,
                provenance_tags=provenance_tags(),
                explanation=item["explanation"],
            )
        )
    summary = {
        "proposed": len(proposed),
        "accepted": len(proposed) - rejected,
        "rejected": rejected,
        "canonical_references_mapped": canonicalized,
        "aliases_merged": 0,
        "regional_variants_mapped": sum(
            1 for record in mapped if record.payload.get("region") and record.confidence > 0
        ),
        "ontology_version": config.ontology_version,
    }
    return mapped, summary
