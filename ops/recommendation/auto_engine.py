"""FooFoo DB-first recommendation auto-training engine.

The pipeline is deliberately operational rather than autonomous in the unsafe sense: it inspects
the DB first, writes generated records only to governed research staging, keeps synthetic and real
signals separate, and never activates a model or changes the existing recommender.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from .auto_engine_inspector import inspect_database
from .auto_engine_ontology import load_ontology, map_and_score_records
from .auto_engine_research import generate_research_records
from .auto_engine_store import DryRunTrainingStore, MemoryTrainingStore, PostgresTrainingStore
from .auto_engine_training import train_and_evaluate
from .auto_engine_types import AutoEngineConfig

ROOT = Path(__file__).parents[2]
DEFAULT_ONTOLOGY = ROOT / "aux_re_service/data/training/v1/canonical_food_ontology.json"


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
    ) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = handle.name
    os.replace(temporary, path)


def _batch_id(
    inspection: dict[str, Any], ontology: dict[str, Any], config: AutoEngineConfig
) -> str:
    semantic_ontology = {key: value for key, value in ontology.items() if key != "generated_at"}
    payload = json.dumps(
        {"inspection": inspection, "ontology": semantic_ontology, "config": config.as_dict()},
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()[:24]


def _seed_report(counts: dict[str, Any]) -> dict[str, Any]:
    tables = {table: value.as_report() for table, value in sorted(counts.items())}
    return {
        "tables": tables,
        "total_inserted": sum(value.inserted for value in counts.values()),
        "total_updated": sum(value.updated for value in counts.values()),
        "total_skipped": sum(value.skipped for value in counts.values()),
        "total_rejected": sum(value.rejected for value in counts.values()),
    }


def _next_actions(inspection: Any, models: list[dict[str, Any]]) -> list[str]:
    actions = [
        f"Enrich {entity} until its configured coverage threshold passes."
        for entity in inspection.enrichment_targets
    ]
    if not inspection.model_readiness["real_preference"]["ready"]:
        actions.append("Collect consented, exactly attributed real positive and negative feedback.")
    if not inspection.model_readiness["lightgcn"]["ready"]:
        actions.append("Keep LightGCN disabled until the real interaction/household gate passes.")
    if not inspection.model_readiness["kgat"]["ready"]:
        actions.append("Keep KGAT disabled until both graph volume and ontology coverage pass.")
    if any(model["status"] == "gated" for model in models):
        actions.append("Review gated model evidence before any shadow or production promotion.")
    return list(dict.fromkeys(actions))


def run_auto_engine(
    connection: Any,
    *,
    store: Any,
    mode: str,
    ontology_path: Path,
    output_dir: Path,
    config: AutoEngineConfig | None = None,
) -> dict[str, Any]:
    if mode not in {"audit", "dry_run", "execute"}:
        raise ValueError("mode must be audit, dry_run, or execute")
    selected = config or AutoEngineConfig()
    ontology = load_ontology(ontology_path)
    inspection = inspect_database(connection, selected)
    inspection_report = inspection.as_report()
    batch_id = _batch_id(inspection_report, ontology, selected)
    run_id, _ = store.begin_run(batch_id, selected.engine_version, mode, selected.as_dict())
    store.write_inspection(run_id, inspection)

    proposed = [] if mode == "audit" else generate_research_records(inspection, ontology, selected)
    mapped, ontology_summary = map_and_score_records(proposed, ontology, selected)
    counts = store.seed_records(run_id, batch_id, mapped, selected.minimum_confidence)
    seed_summary = _seed_report(counts)
    research_summary: dict[str, Any] = {
        "triggered": bool(proposed),
        "reason": list(inspection.enrichment_targets)
        if proposed
        else ["audit_only_or_required_research_coverage_already_staged"],
        "generated_records": len(proposed),
        "source_type": "expert_research_synthetic",
        "generation_method": selected.generator_version,
        "paid_ai_used": False,
        "batch_confidence": round(
            sum(
                record.confidence
                for record in mapped
                if record.confidence >= selected.minimum_confidence
            )
            / max(
                1,
                sum(record.confidence >= selected.minimum_confidence for record in mapped),
            ),
            4,
        ),
        "confidence_bands": {
            band: sum(value.confidence_bands[band] for value in counts.values())
            for band in ("high", "medium", "low")
        },
    }
    research_summary["batch_confidence_band"] = (
        "high"
        if research_summary["batch_confidence"] >= 0.85
        else "medium"
        if research_summary["batch_confidence"] >= 0.65
        else "low"
    )

    models, evaluation = train_and_evaluate(
        run_id=run_id,
        store=store,
        inspection=inspection,
        config=selected,
        ontology_path=ontology_path,
        output_dir=output_dir / batch_id.replace(":", "-"),
        execute=mode == "execute",
    )
    readiness = {
        "production_ready": False,
        "existing_recommender_untouched": True,
        "fallback_required": True,
        "models": {
            model["model_name"]: {
                "status": model["status"],
                "reason": model.get("reason"),
                "gate_checks": model.get("gate_checks", {}),
            }
            for model in models
        },
    }
    report = {
        "run_id": run_id,
        "batch_id": batch_id,
        "engine_version": selected.engine_version,
        "mode": mode,
        "db_audit": inspection_report,
        "research_generation": research_summary,
        "seeding": seed_summary,
        "ontology": ontology_summary,
        "training": {"models": models},
        "evaluation": evaluation,
        "readiness": readiness,
        "next_actions": _next_actions(inspection, models),
    }
    status = (
        "completed_with_gates"
        if any(model["status"] == "gated" for model in models)
        else "completed"
    )
    store.finish_run(run_id, report, status)
    report["status"] = status
    return report


def connect(dsn: str) -> Any:
    import psycopg2  # type: ignore[import-untyped]

    return psycopg2.connect(
        dsn,
        connect_timeout=15,
        application_name="foofoo-recommendation-auto-engine",
    )


def main(argv: list[str] | None = None) -> int:
    from .preference_training import database_url

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("audit", "dry_run", "execute"), default="audit")
    parser.add_argument("--ontology", type=Path, default=DEFAULT_ONTOLOGY)
    parser.add_argument("--output-dir", type=Path, default=Path("auto-engine-runs"))
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)

    connection = connect(database_url())
    store: Any
    if args.mode == "execute":
        store = PostgresTrainingStore(connection)
    elif args.mode == "dry_run":
        store = DryRunTrainingStore(connection)
    else:
        store = MemoryTrainingStore()
    try:
        report = run_auto_engine(
            connection,
            store=store,
            mode=args.mode,
            ontology_path=args.ontology,
            output_dir=args.output_dir,
        )
        if args.mode == "execute":
            connection.commit()
        else:
            connection.rollback()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    _atomic_json(args.report, report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
