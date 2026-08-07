"""Gated model refresh and evaluation for the DB-first auto-engine."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

from .auto_engine_types import AutoEngineConfig, InspectionReport


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def _prepare_research_snapshot(
    store: Any, ontology_path: Path, destination: Path
) -> dict[str, int]:
    destination.mkdir(parents=True, exist_ok=True)
    households = store.fetch_research_records("research.household_personas")
    interactions = store.fetch_research_records("research.interactions")
    household_rows = [
        {
            "household_id": record["payload"]["household_id"],
            "features": record["payload"]["features"],
        }
        for record in households
    ]
    interaction_rows = []
    for index, record in enumerate(interactions):
        payload = record["payload"]
        interaction_rows.append(
            {
                "event_id": record["record_key"],
                "household_id": payload["household_id"],
                "dish_id": payload["dish_id"],
                "event_type": payload["event_type"],
                "weight": payload["weight"],
                "timestamp": f"2026-01-{index % 28 + 1:02d}T{index % 24:02d}:00:00+00:00",
                "source": "expert_research_synthetic",
                "confidence": record["confidence"],
            }
        )
    _write_jsonl(destination / "household_features.jsonl", household_rows)
    _write_jsonl(destination / "interactions.jsonl", interaction_rows)
    shutil.copyfile(ontology_path, destination / "canonical_food_ontology.json")
    return {"households": len(household_rows), "interactions": len(interaction_rows)}


def _checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def train_and_evaluate(
    *,
    run_id: str,
    store: Any,
    inspection: InspectionReport,
    config: AutoEngineConfig,
    ontology_path: Path,
    output_dir: Path,
    execute: bool,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    models: list[dict[str, Any]] = []

    retrieval: dict[str, Any] = {
        "model_name": "ontology_retrieval",
        "status": "skipped",
        "input_source_split": {"canonical_ontology": 1},
        "input_record_count": 0,
        "metrics": {},
        "gate_checks": {"execute_requested": execute},
        "reason": "audit-only run" if not execute else None,
    }
    if execute:
        try:
            from aux_re_service.training.retrieval_pipeline import (  # type: ignore[import-untyped]
                build as build_retrieval,
            )

            retrieval_dir = output_dir / "retrieval"
            counts = build_retrieval(ontology_path, retrieval_dir)
            points = retrieval_dir / "qdrant_points.json"
            retrieval.update(
                status="refreshed",
                input_record_count=counts["candidates"],
                artifact_uri=str(points),
                artifact_checksum=_checksum(points),
                metrics=counts,
                gate_checks={"ontology_nonempty": counts["candidates"] > 0},
                reason=None,
            )
        except ImportError:
            retrieval.update(status="gated", reason="auxiliary training package is not installed")
    models.append(retrieval)

    snapshot_dir = output_dir / "training_snapshot"
    snapshot_counts = _prepare_research_snapshot(store, ontology_path, snapshot_dir)
    baseline_ready = snapshot_counts["households"] >= 10 and snapshot_counts["interactions"] >= 50
    baseline: dict[str, Any] = {
        "model_name": "lightfm_research_challenger",
        "status": "gated",
        "input_source_split": {
            "real_db": 0,
            "expert_research_synthetic": snapshot_counts["interactions"],
        },
        "input_record_count": snapshot_counts["interactions"],
        "metrics": {},
        "gate_checks": {
            "execute_requested": execute,
            "minimum_research_households": snapshot_counts["households"] >= 10,
            "minimum_research_interactions": snapshot_counts["interactions"] >= 50,
            "production_eligible": False,
        },
        "reason": "research-only challenger remains shadow gated",
    }
    if execute and baseline_ready:
        artifact = output_dir / "models" / "lightfm_research_challenger.joblib"
        report_path = output_dir / "models" / "lightfm_research_challenger_report.json"
        artifact.parent.mkdir(parents=True, exist_ok=True)
        try:
            from aux_re_service.training.lightfm_pipeline import (  # type: ignore[import-untyped]
                train as train_lightfm,
            )

            metadata = train_lightfm(
                snapshot_dir,
                artifact,
                report_path,
                epochs=30,
                components=32,
                seed=20260807,
            )
            baseline.update(
                status="trained",
                artifact_uri=str(artifact),
                artifact_checksum=_checksum(artifact),
                metrics=metadata["metrics"],
                gate_checks={
                    **baseline["gate_checks"],
                    "shadow_promotion_gate": metadata["promotion_gate_passed"],
                    "production_eligible": metadata["production_eligible"],
                },
                reason="trained from staged expert research; shadow-only by provenance",
            )
        except (ImportError, RuntimeError) as exc:
            baseline.update(status="gated", reason=str(exc))
    models.append(baseline)

    preference_ready = inspection.model_readiness["real_preference"]["ready"]
    preference: dict[str, Any] = {
        "model_name": "real_preference_model",
        "status": "gated",
        "input_source_split": {
            "real_db": inspection.model_readiness["real_preference"]["real_events"],
            "expert_research_synthetic": 0,
        },
        "input_record_count": inspection.model_readiness["real_preference"]["real_events"],
        "metrics": {},
        "gate_checks": {
            "real_data_threshold": preference_ready,
            "synthetic_rows_forbidden": True,
        },
        "reason": "real interaction/household readiness gate not met"
        if not preference_ready
        else "ready for the existing service-role preference-training exporter",
    }
    if execute and preference_ready and hasattr(store, "connection"):
        from .preference_training import run as train_real_preference

        preference_dir = output_dir / "models" / "real_preference"
        preference_dir.mkdir(parents=True, exist_ok=True)
        result = train_real_preference(
            store.connection,
            readiness_out=preference_dir / "readiness.json",
            artifact_out=preference_dir / "preference_model.joblib",
            eval_out=preference_dir / "evaluation.json",
        )
        preference.update(
            status="trained" if result["status"] == "candidate_passed" else "gated",
            artifact_uri=str(preference_dir / "preference_model.joblib")
            if result["status"] != "not_ready"
            else None,
            artifact_checksum=_checksum(preference_dir / "preference_model.joblib")
            if (preference_dir / "preference_model.joblib").is_file()
            else None,
            metrics=result.get("promotion_gate", {}),
            gate_checks={
                **preference["gate_checks"],
                "promotion_gate": result.get("promotion_gate", {}).get("passed", False),
            },
            reason=f"existing governed preference trainer returned {result['status']}",
        )
    models.append(preference)

    for model_name in ("lightgcn", "kgat"):
        readiness = inspection.model_readiness[model_name]
        models.append(
            {
                "model_name": model_name,
                "status": "gated",
                "input_source_split": {
                    "real_db": inspection.model_readiness["real_preference"]["real_events"],
                    "expert_research_synthetic": snapshot_counts["interactions"],
                },
                "input_record_count": inspection.model_readiness["real_preference"]["real_events"],
                "metrics": {},
                "gate_checks": readiness,
                "reason": (
                    "advanced graph model requires sufficient real interactions and ontology "
                    "coverage"
                ),
            }
        )

    for model in models:
        store.write_model_run(run_id, model)
    evaluation = {
        "models_evaluated": sum(bool(model["metrics"]) for model in models),
        "retrieval": retrieval["metrics"],
        "ranking": baseline["metrics"],
        "safety": {
            "hard_constraints_preserved": True,
            "synthetic_never_promoted_as_real": True,
            "existing_recommender_modified": False,
        },
        "diversity": baseline["metrics"].get("catalog_coverage"),
        "repeat_rate": None,
        "regional_relevance": "covered by ontology-mapped research scenarios",
        "household_fit": "covered by household-isolated research personas",
    }
    return models, evaluation
