from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID

from .models import (
    ClassMembershipInput,
    EvidenceRef,
    FieldValue,
    PlanningRole,
    ReviewStatus,
)
from .providers import FoodOnProvider, ProviderFact, UsdaProvider, WikidataProvider
from .repository import Repository, normalize_name

LOW_RISK_AUTO_PUBLISH = {
    "external_ids/foodon",
    "external_ids/wikidata",
    "source_aliases/foodon",
}


class EnrichmentProvider(Protocol):
    def lookup(self, name: str) -> list[ProviderFact]: ...


@dataclass(frozen=True)
class ClassificationRule:
    pattern: str
    class_code: str
    slot: str
    role: str
    confidence: float = 0.9


def _field(fact: ProviderFact) -> FieldValue:
    accepted = (
        fact.field_path in LOW_RISK_AUTO_PUBLISH
        and fact.confidence >= 0.85
        and not fact.safety_critical
    )
    return FieldValue(
        value=fact.value,
        confidence=fact.confidence,
        review_status=ReviewStatus.accepted if accepted else ReviewStatus.provisional,
        evidence=[
            EvidenceRef(
                source_code=fact.source_code,
                source_record_id=fact.source_record_id,
                source_url=fact.source_url,
                extraction_method=fact.extraction_method,
            )
        ],
    )


def build_enrich_handler(repository: Repository, providers: list[EnrichmentProvider]):
    def handle(job: dict[str, Any]) -> str:
        dish = repository.get_dish(UUID(str(job["dish_id"])))
        requested = set(job.get("requested_fields") or [])
        candidates: dict[str, FieldValue] = {}
        failures: list[Exception] = []
        for provider in providers:
            try:
                for fact in provider.lookup(dish.canonical_name):
                    if (
                        requested
                        and fact.field_path not in requested
                        and fact.field_path.split("/", 1)[0] not in requested
                    ):
                        continue
                    candidate = _field(fact)
                    prior = candidates.get(fact.field_path)
                    if prior is None or candidate.confidence > prior.confidence:
                        candidates[fact.field_path] = candidate
            except Exception as exc:
                failures.append(exc)
        if not candidates:
            if failures and len(failures) == len(providers):
                raise RuntimeError("all_enrichment_providers_failed") from failures[0]
            return "review"
        _published, review = repository.publish_worker_fields(dish.id, candidates)
        return "review" if review else "complete"

    return handle


def build_classify_handler(repository: Repository, rules: list[ClassificationRule]):
    def handle(job: dict[str, Any]) -> str:
        dish = repository.get_dish(UUID(str(job["dish_id"])))
        searchable = " ".join(
            [dish.canonical_name]
            + [alias.name for alias in dish.aliases]
            + [str(field.value) for field in dish.fields.values()]
        )
        matches: list[ClassMembershipInput] = []
        classes = {row["class_code"]: row for row in repository.list_classes()}
        evidence = [
            EvidenceRef(source_code="foofoo_class_rules", extraction_method="reviewed_regex_rule")
        ]
        for rule in rules:
            canonical = classes.get(rule.class_code)
            if canonical is None or re.search(rule.pattern, searchable, re.IGNORECASE) is None:
                continue
            if canonical["slot"] != rule.slot or str(canonical["planning_role"]) != rule.role:
                raise ValueError("classification_rule_role_mismatch")
            matches.append(
                ClassMembershipInput(
                    class_code=rule.class_code,
                    slot=rule.slot,
                    role=PlanningRole(rule.role),
                    confidence=rule.confidence,
                    review_status=(
                        ReviewStatus.accepted
                        if rule.confidence >= 0.9
                        else ReviewStatus.provisional
                    ),
                    evidence=evidence,
                )
            )
        if not matches:
            # Conservative exact-name fallback can nominate a class but never auto-publishes it.
            name = normalize_name(dish.canonical_name)
            for class_code, row in classes.items():
                if name == normalize_name(str(row.get("display_name", ""))):
                    matches.append(
                        ClassMembershipInput(
                            class_code=class_code,
                            slot=row["slot"],
                            role=PlanningRole(row["planning_role"]),
                            confidence=0.8,
                            review_status=ReviewStatus.provisional,
                            evidence=[
                                EvidenceRef(
                                    source_code="foofoo_class_catalogue",
                                    extraction_method="exact_display_name",
                                )
                            ],
                        )
                    )
                    break
        if not matches:
            return "review"
        _published, review = repository.publish_worker_classes(dish.id, matches)
        return "review" if review else "complete"

    return handle


def _rules_from_env() -> list[ClassificationRule]:
    raw = os.getenv("ONTOLOGY_CLASSIFICATION_RULES_JSON", "[]")
    parsed = json.loads(raw)
    if not isinstance(parsed, list):
        raise RuntimeError("ONTOLOGY_CLASSIFICATION_RULES_JSON must be an array")
    return [ClassificationRule(**item) for item in parsed]


def build_handlers() -> dict[str, Any]:
    from .postgres_repository import PostgresRepository

    dsn = os.getenv("ONTOLOGY_DATABASE_URL")
    if not dsn:
        raise RuntimeError("ONTOLOGY_DATABASE_URL is required")
    repository = PostgresRepository(dsn)
    providers: list[EnrichmentProvider] = [FoodOnProvider(), WikidataProvider()]
    usda_key = os.getenv("ONTOLOGY_USDA_API_KEY")
    if usda_key:
        providers.append(UsdaProvider(usda_key))
    return {
        "enrich": build_enrich_handler(repository, providers),
        "classify": build_classify_handler(repository, _rules_from_env()),
    }
