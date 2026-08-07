"""Value objects shared by the recommendation auto-training roles."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class AuditRow:
    entity_type: str
    source_table: str
    total_records: int
    usable_records: int
    missing_fields: int = 0
    duplicate_records: int = 0
    orphan_records: int = 0
    low_confidence_records: int = 0
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def coverage_score(self) -> float:
        if self.total_records == 0:
            return 0.0
        return round(max(0.0, min(1.0, self.usable_records / self.total_records)), 4)

    def as_report(self) -> dict[str, Any]:
        return {**asdict(self), "coverage_score": self.coverage_score}


@dataclass(frozen=True)
class InspectionReport:
    rows: tuple[AuditRow, ...]
    data_quality_score: float
    ontology_coverage_score: float
    strong_enough_for_baseline: bool
    enrichment_targets: tuple[str, ...]
    model_readiness: dict[str, dict[str, Any]]

    def as_report(self) -> dict[str, Any]:
        return {
            "tables_inspected": len(self.rows),
            "entities": [row.as_report() for row in self.rows],
            "data_quality_score": self.data_quality_score,
            "ontology_coverage_score": self.ontology_coverage_score,
            "strong_enough_for_baseline": self.strong_enough_for_baseline,
            "enrichment_targets": list(self.enrichment_targets),
            "model_readiness": self.model_readiness,
        }


@dataclass(frozen=True)
class ResearchRecord:
    target_table: str
    record_key: str
    payload: dict[str, Any]
    source_type: str
    generation_method: str
    confidence: float
    confidence_band: str
    ontology_mapping_status: str
    ontology_version: str
    provenance_tags: tuple[str, ...]
    explanation: str


@dataclass
class TableSeedCount:
    inserted: int = 0
    updated: int = 0
    skipped: int = 0
    rejected: int = 0
    confidences: list[float] = field(default_factory=list)
    confidence_bands: dict[str, int] = field(
        default_factory=lambda: {"high": 0, "medium": 0, "low": 0}
    )

    def as_report(self) -> dict[str, Any]:
        return {
            "inserted": self.inserted,
            "updated": self.updated,
            "skipped": self.skipped,
            "rejected": self.rejected,
            "average_confidence": round(sum(self.confidences) / len(self.confidences), 4)
            if self.confidences
            else None,
            "confidence_bands": dict(self.confidence_bands),
        }


@dataclass(frozen=True)
class AutoEngineConfig:
    engine_version: str = "foofoo-auto-engine-v1"
    ontology_version: str = "indian-food-ontology-v2"
    generator_version: str = "expert-household-research-v1"
    minimum_confidence: float = 0.65
    minimum_dishes: int = 100
    minimum_ontology_relations: int = 500
    minimum_households: int = 500
    minimum_real_interactions: int = 10_000
    minimum_graph_households: int = 5_000
    minimum_ingredients: int = 100
    minimum_substitutions: int = 50
    minimum_regions: int = 10
    research_household_limit: int = 24
    research_interaction_limit: int = 240

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
