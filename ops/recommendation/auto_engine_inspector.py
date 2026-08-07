"""DB-first inventory and quality analysis for the recommendation auto-engine."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .auto_engine_types import AuditRow, AutoEngineConfig, InspectionReport

# Fixed, reviewed SQL avoids accepting identifiers from configuration or command-line input.
AUDIT_QUERIES: dict[str, tuple[str, str]] = {
    "dishes": (
        "public.dishes",
        """/* auto_engine:dishes */ SELECT count(*) total_records,
        count(*) FILTER (WHERE is_active AND name<>'' AND cardinality(meal_occasion)>0) usable_records,
        count(*) FILTER (WHERE name='' OR cardinality(meal_occasion)=0) missing_fields,
        count(*)-(SELECT count(DISTINCT lower(btrim(name))) FROM public.dishes) duplicate_records,
        0 orphan_records, 0 low_confidence_records FROM public.dishes""",
    ),
    "ontology_nodes": (
        "food.ontology_nodes",
        """/* auto_engine:ontology_nodes */ SELECT count(*) total_records,
        count(*) FILTER (WHERE status='active' AND review_status<>'rejected') usable_records,
        count(*) FILTER (WHERE label='' OR source_name='') missing_fields, 0 duplicate_records,
        0 orphan_records, count(*) FILTER (WHERE confidence<0.65) low_confidence_records
        FROM food.ontology_nodes""",
    ),
    "ontology_relations": (
        "food.ontology_edges",
        """/* auto_engine:ontology_relations */ SELECT count(*) total_records,
        count(*) FILTER (WHERE review_status<>'rejected' AND effective_to IS NULL) usable_records,
        0 missing_fields, 0 duplicate_records, 0 orphan_records,
        count(*) FILTER (WHERE confidence<0.65) low_confidence_records FROM food.ontology_edges""",
    ),
    "users": (
        "public.profiles",
        """/* auto_engine:users */ SELECT count(*) total_records, count(*) usable_records,
        0 missing_fields, 0 duplicate_records, 0 orphan_records, 0 low_confidence_records
        FROM public.profiles""",
    ),
    "households": (
        "public.households",
        """/* auto_engine:households */ SELECT count(*) total_records,
        count(*) FILTER (WHERE status='active') usable_records, 0 missing_fields, 0 duplicate_records,
        0 orphan_records, 0 low_confidence_records FROM public.households""",
    ),
    "interactions": (
        "public.outcome_events",
        """/* auto_engine:interactions */ SELECT count(*) total_records,
        count(*) FILTER (WHERE outcome_type IN ('chosen','locked','cooked','ordered','completed',
          'liked','disliked','enjoyed','regretted','replaced')) usable_records,
        count(*) FILTER (WHERE episode_hash IS NULL) missing_fields, 0 duplicate_records,
        count(*) FILTER (WHERE slate_id IS NULL) orphan_records, 0 low_confidence_records
        FROM public.outcome_events""",
    ),
    "meal_plans": (
        "public.slates",
        """/* auto_engine:meal_plans */ SELECT count(*) total_records,
        count(*) FILTER (WHERE household_id IS NOT NULL AND request_id<>'' AND model_version<>'') usable_records,
        count(*) FILTER (WHERE request_id='' OR model_version='') missing_fields, 0 duplicate_records,
        0 orphan_records, 0 low_confidence_records FROM public.slates""",
    ),
    "feedback_events": (
        "public.feedback_events",
        """/* auto_engine:feedback_events */ SELECT count(*) total_records,
        count(*) FILTER (WHERE data_source='real' AND dish_id IS NOT NULL
          AND event_type IN ('accept','like','make_this','cooked','completed','dislike','never','regretted')) usable_records,
        count(*) FILTER (WHERE dish_id IS NULL) missing_fields, 0 duplicate_records,
        count(*) FILTER (WHERE recommendation_event_id IS NULL) orphan_records, 0 low_confidence_records
        FROM public.feedback_events""",
    ),
    "regions": (
        "public.re_states",
        """/* auto_engine:regions */ SELECT count(*) total_records,
        count(*) FILTER (WHERE state_code<>'' AND region<>'') usable_records,
        count(*) FILTER (WHERE state_name='' OR region='') missing_fields, 0 duplicate_records,
        0 orphan_records, 0 low_confidence_records FROM public.re_states""",
    ),
    "ingredients": (
        "public.ingredients",
        """/* auto_engine:ingredients */ SELECT count(*) total_records,
        count(*) FILTER (WHERE is_active AND name<>'') usable_records,
        count(*) FILTER (WHERE name='') missing_fields,
        count(*)-(SELECT count(DISTINCT lower(btrim(name))) FROM public.ingredients) duplicate_records,
        0 orphan_records, 0 low_confidence_records FROM public.ingredients""",
    ),
    "substitutions": (
        "public.ingredients",
        """/* auto_engine:substitutions */ SELECT count(*) FILTER (WHERE can_substitute_id IS NOT NULL) total_records,
        count(*) FILTER (WHERE can_substitute_id IS NOT NULL AND can_substitute_id<>id) usable_records,
        0 missing_fields, 0 duplicate_records,
        count(*) FILTER (WHERE can_substitute_id=id) orphan_records, 0 low_confidence_records
        FROM public.ingredients""",
    ),
    "diet_allergy_constraints": (
        "public.household_members",
        """/* auto_engine:diet_allergy_constraints */ SELECT count(*) total_records,
        count(*) FILTER (WHERE is_active AND (diet_type IS NOT NULL OR allergen_flags<>0)) usable_records,
        count(*) FILTER (WHERE diet_type IS NULL AND allergen_flags=0) missing_fields,
        0 duplicate_records, 0 orphan_records, 0 low_confidence_records
        FROM public.household_members""",
    ),
    "candidate_vectors": (
        "public.dishes",
        """/* auto_engine:candidate_vectors */ SELECT count(*) total_records,
        count(*) FILTER (WHERE genome_vector IS NOT NULL AND cardinality(genome_vector)>0) usable_records,
        count(*) FILTER (WHERE genome_vector IS NULL OR cardinality(genome_vector)=0) missing_fields,
        0 duplicate_records, 0 orphan_records, 0 low_confidence_records FROM public.dishes""",
    ),
    "labeled_training_rows": (
        "public.feedback_events",
        """/* auto_engine:labeled_training_rows */ SELECT count(*) FILTER (WHERE data_source='real'
          AND event_type IN ('accept','like','make_this','cooked','completed','dislike','never','regretted')) total_records,
        count(*) FILTER (WHERE data_source='real' AND dish_id IS NOT NULL AND recommendation_event_id IS NOT NULL
          AND event_type IN ('accept','like','make_this','cooked','completed','dislike','never','regretted')) usable_records,
        count(*) FILTER (WHERE data_source='real' AND (dish_id IS NULL OR recommendation_event_id IS NULL)) missing_fields,
        0 duplicate_records, 0 orphan_records, 0 low_confidence_records FROM public.feedback_events""",
    ),
    "evaluation_rows": (
        "public.outcome_events",
        """/* auto_engine:evaluation_rows */ SELECT count(*) total_records,
        count(*) FILTER (WHERE slate_id IS NOT NULL AND episode_hash IS NOT NULL) usable_records,
        count(*) FILTER (WHERE slate_id IS NULL OR episode_hash IS NULL) missing_fields,
        0 duplicate_records, 0 orphan_records, 0 low_confidence_records FROM public.outcome_events""",
    ),
    "research_household_personas": (
        "research.auto_training_records",
        """/* auto_engine:research_household_personas */ SELECT count(*) total_records,
        count(*) FILTER (WHERE ontology_mapping_status<>'rejected' AND confidence>=0.65) usable_records,
        count(*) FILTER (WHERE payload='{}'::jsonb) missing_fields, 0 duplicate_records,
        0 orphan_records, count(*) FILTER (WHERE confidence<0.65) low_confidence_records
        FROM research.auto_training_records WHERE target_table='research.household_personas'""",
    ),
    "research_interactions": (
        "research.auto_training_records",
        """/* auto_engine:research_interactions */ SELECT count(*) total_records,
        count(*) FILTER (WHERE ontology_mapping_status='mapped' AND confidence>=0.65) usable_records,
        count(*) FILTER (WHERE NOT (payload ? 'household_id' AND payload ? 'dish_id')) missing_fields,
        0 duplicate_records, 0 orphan_records,
        count(*) FILTER (WHERE confidence<0.65) low_confidence_records
        FROM research.auto_training_records WHERE target_table='research.interactions'""",
    ),
    "research_weekly_plans": (
        "research.auto_training_records",
        """/* auto_engine:research_weekly_plans */ SELECT count(*) total_records,
        count(*) FILTER (WHERE ontology_mapping_status='mapped' AND confidence>=0.65) usable_records,
        count(*) FILTER (WHERE NOT payload ? 'meals') missing_fields, 0 duplicate_records,
        0 orphan_records, count(*) FILTER (WHERE confidence<0.65) low_confidence_records
        FROM research.auto_training_records WHERE target_table='research.weekly_plans'""",
    ),
    "research_substitutions": (
        "research.auto_training_records",
        """/* auto_engine:research_substitutions */ SELECT count(*) total_records,
        count(*) FILTER (WHERE ontology_mapping_status='mapped' AND confidence>=0.65) usable_records,
        count(*) FILTER (WHERE NOT (payload ? 'dish_id' AND payload ? 'substitute_dish_id')) missing_fields,
        0 duplicate_records, 0 orphan_records,
        count(*) FILTER (WHERE confidence<0.65) low_confidence_records
        FROM research.auto_training_records WHERE target_table='research.substitution_examples'""",
    ),
}

RESEARCH_ENTITY_NAMES = tuple(
    name for name in AUDIT_QUERIES if name.startswith("research_")
)
PRODUCTION_ENTITY_NAMES = tuple(
    name for name in AUDIT_QUERIES if name not in RESEARCH_ENTITY_NAMES
)


def _mapping(cursor: Any, row: Any) -> Mapping[str, Any]:
    if isinstance(row, Mapping):
        return row
    return dict(zip((column[0] for column in cursor.description), row, strict=True))


def inspect_entities(connection: Any, entity_names: tuple[str, ...]) -> tuple[AuditRow, ...]:
    """Read a reviewed subset of audit queries from one database connection."""
    rows: list[AuditRow] = []
    with connection.cursor() as cursor:
        for entity_type in entity_names:
            source_table, query = AUDIT_QUERIES[entity_type]
            cursor.execute(query)
            result = cursor.fetchone()
            if result is None:
                raise RuntimeError(f"audit returned no row for {source_table}")
            item = _mapping(cursor, result)
            rows.append(
                AuditRow(
                    entity_type=entity_type,
                    source_table=source_table,
                    total_records=int(item.get("total_records") or 0),
                    usable_records=int(item.get("usable_records") or 0),
                    missing_fields=int(item.get("missing_fields") or 0),
                    duplicate_records=int(item.get("duplicate_records") or 0),
                    orphan_records=int(item.get("orphan_records") or 0),
                    low_confidence_records=int(item.get("low_confidence_records") or 0),
                )
            )
    return tuple(rows)


def build_inspection(
    rows: tuple[AuditRow, ...], config: AutoEngineConfig
) -> InspectionReport:
    """Derive readiness from one complete, uniquely keyed audit snapshot."""
    names = [row.entity_type for row in rows]
    missing = sorted(set(AUDIT_QUERIES) - set(names))
    duplicates = sorted(name for name in set(names) if names.count(name) > 1)
    unknown = sorted(set(names) - set(AUDIT_QUERIES))
    if missing or duplicates or unknown:
        raise RuntimeError(
            "audit snapshot must contain each governed entity exactly once; "
            f"missing={missing}, duplicates={duplicates}, unknown={unknown}"
        )

    by_entity = {row.entity_type: row for row in rows}
    thresholds = {
        "dishes": config.minimum_dishes,
        "ontology_relations": config.minimum_ontology_relations,
        "households": config.minimum_households,
        "feedback_events": config.minimum_real_interactions,
        "ingredients": config.minimum_ingredients,
        "substitutions": config.minimum_substitutions,
        "regions": config.minimum_regions,
        "candidate_vectors": config.minimum_dishes,
    }
    enrichment_targets = tuple(
        entity
        for entity, minimum in thresholds.items()
        if by_entity[entity].usable_records < minimum
    )
    quality = round(sum(row.coverage_score for row in rows) / len(rows), 4)
    ontology_rows = [by_entity[name] for name in ("dishes", "ontology_nodes", "ontology_relations")]
    ontology_coverage = round(
        sum(row.coverage_score for row in ontology_rows) / len(ontology_rows), 4
    )
    real_events = by_entity["labeled_training_rows"].usable_records
    households = by_entity["households"].usable_records
    baseline_ready = (
        by_entity["dishes"].usable_records >= config.minimum_dishes
        and by_entity["candidate_vectors"].usable_records >= config.minimum_dishes
        and ontology_coverage >= 0.70
    )
    model_readiness: dict[str, dict[str, Any]] = {
        "retrieval": {"ready": baseline_ready, "requires": "ontology and candidate vectors"},
        "baseline_local": {
            "ready": baseline_ready,
            "requires": "canonical dishes and ontology-backed features",
        },
        "real_preference": {
            "ready": real_events >= config.minimum_real_interactions
            and households >= config.minimum_households,
            "real_events": real_events,
            "households": households,
        },
        "lightgcn": {
            "ready": real_events >= config.minimum_real_interactions
            and households >= config.minimum_graph_households,
            "real_events": real_events,
            "households": households,
        },
        "kgat": {
            "ready": real_events >= config.minimum_real_interactions
            and households >= config.minimum_graph_households
            and ontology_coverage >= 0.90,
            "ontology_coverage": ontology_coverage,
        },
    }
    return InspectionReport(
        rows=tuple(rows),
        data_quality_score=quality,
        ontology_coverage_score=ontology_coverage,
        strong_enough_for_baseline=baseline_ready,
        enrichment_targets=enrichment_targets,
        model_readiness=model_readiness,
    )


def inspect_database(
    connection: Any,
    config: AutoEngineConfig,
    research_connection: Any | None = None,
) -> InspectionReport:
    """Inspect production facts and private research state without mixing write targets."""
    research_source = research_connection or connection
    rows = inspect_entities(connection, PRODUCTION_ENTITY_NAMES) + inspect_entities(
        research_source, RESEARCH_ENTITY_NAMES
    )
    return build_inspection(rows, config)
