from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row

from .models import (
    AliasInput,
    DishCreate,
    EvidenceRef,
    FieldValue,
    ReviewStatus,
)
from .postgres_repository import PostgresRepository

SOURCE_SYSTEM = "foofoo_supabase"
EVIDENCE = EvidenceRef(source_code="legacy_foofoo", extraction_method="watermarked_cutover_export")


def _json_default(value: Any) -> str:
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    return str(value)


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=_json_default).encode()


def bundle_checksum(bundle: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in bundle.items() if key != "checksum_sha256"}
    return hashlib.sha256(canonical_json(unsigned)).hexdigest()


def _role(value: str) -> str:
    return {
        "MAIN_PRIMARY": "primary",
        "ADDON_ONLY_NOT_PRIMARY": "addon",
        "COMBO_TEMPLATE_NOT_PRIMARY": "combo_component",
    }[value]


def export_legacy(source_dsn: str) -> dict[str, Any]:
    """Export one transactionally consistent, checksum-addressed legacy snapshot."""
    with psycopg.connect(source_dsn, row_factory=dict_row) as connection:
        connection.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        watermark_row = connection.execute("SELECT transaction_timestamp() AS value").fetchone()
        assert watermark_row is not None
        watermark = watermark_row["value"]
        classes = connection.execute(
            """SELECT class_code,display_name,
                      CASE WHEN 'snack'=ANY(slot) THEN 'snack' ELSE slot[1] END AS slot,
                      planning_role,parent_class_code,class_family_code AS family_code
               FROM public.meal_classes WHERE is_active ORDER BY class_code"""
        ).fetchall()
        dishes = connection.execute(
            """SELECT id,name,description,is_active,created_at,updated_at,diet_type,
                      meal_occasion,cook_time_minutes,difficulty,is_jain,allergen_flags
               FROM public.dishes ORDER BY id"""
        ).fetchall()
        aliases = connection.execute(
            """SELECT dish_id,synonym AS name,language,region AS region_code,alias_type,
                      confidence,review_status,source_url,extraction_method
               FROM public.dish_name_synonyms WHERE review_status<>'rejected'
               UNION ALL
               SELECT dish_id,alias_text,'und',NULL,alias_source,coalesce(confidence,0.7),
                      'provisional',NULL,'legacy_dish_alias'
               FROM public.dish_aliases ORDER BY dish_id,name"""
        ).fetchall()
        memberships = connection.execute(
            """SELECT dish_id,class_code,slot,item_role AS role,confidence,review_status,
                      source_name,classification_method
               FROM public.dish_meal_class_mappings WHERE review_status<>'rejected'
               ORDER BY dish_id,class_code,slot"""
        ).fetchall()
        taxonomy = connection.execute(
            """SELECT cur.dish_id,a.field_key,
                      coalesce(to_jsonb(t.code),to_jsonb(a.value_text),a.value_json) AS value,
                      a.confidence,a.review_status,a.source_name,a.extraction_method,
                      a.last_verified_at,f.provider_record_id,f.source_url
               FROM public.dish_taxonomy_current cur
               JOIN public.dish_taxonomy_assertions a ON a.id=cur.assertion_id
               LEFT JOIN public.taxonomy_terms t ON t.id=a.term_id
               LEFT JOIN public.food_source_records f ON f.id=a.source_record_id
               ORDER BY cur.dish_id,a.field_key"""
        ).fetchall()
        constraints = connection.execute(
            """SELECT dish_id,'constraints/'||constraint_code AS field_key,
                      jsonb_build_object('suitability',suitability) AS value,
                      confidence,review_status,source_name,extraction_method,last_verified_at,
                      NULL::text AS provider_record_id,
                      source_url FROM public.dish_constraints WHERE review_status<>'rejected'"""
        ).fetchall()
        regions = connection.execute(
            """SELECT dish_id,'regional_affinity/'||region_code AS field_key,
                      jsonb_build_object('score',affinity_score) AS value,
                      confidence,review_status,source_name,extraction_method,last_verified_at,
                      NULL::text AS provider_record_id,source_url
               FROM public.dish_regional_affinities WHERE review_status<>'rejected'"""
        ).fetchall()

    fields: dict[str, list[dict[str, Any]]] = {}
    for row in [*taxonomy, *constraints, *regions]:
        fields.setdefault(str(row["dish_id"]), []).append(dict(row))
    aliases_by_dish: dict[str, list[dict[str, Any]]] = {}
    for row in aliases:
        aliases_by_dish.setdefault(str(row["dish_id"]), []).append(dict(row))
    classes_by_dish: dict[str, list[dict[str, Any]]] = {}
    for row in memberships:
        classes_by_dish.setdefault(str(row["dish_id"]), []).append(dict(row))

    exported_dishes = []
    for row in dishes:
        item = dict(row)
        legacy_id = str(item.pop("id"))
        item["legacy_id"] = legacy_id
        item["aliases"] = aliases_by_dish.get(legacy_id, [])
        item["class_memberships"] = classes_by_dish.get(legacy_id, [])
        item["fields"] = fields.get(legacy_id, [])
        exported_dishes.append(item)
    bundle: dict[str, Any] = {
        "schema_version": "foofoo-ontology-cutover/v1",
        "source_system": SOURCE_SYSTEM,
        "watermark": watermark,
        "meal_classes": [dict(row) for row in classes],
        "dishes": exported_dishes,
    }
    bundle["checksum_sha256"] = bundle_checksum(bundle)
    return json.loads(canonical_json(bundle))


def validate_bundle(bundle: dict[str, Any]) -> None:
    if bundle.get("schema_version") != "foofoo-ontology-cutover/v1":
        raise RuntimeError("unsupported_cutover_bundle")
    if bundle.get("checksum_sha256") != bundle_checksum(bundle):
        raise RuntimeError("cutover_bundle_checksum_mismatch")
    ids = [str(row["legacy_id"]) for row in bundle.get("dishes", [])]
    if len(ids) != len(set(ids)):
        raise RuntimeError("duplicate_legacy_dish_id")
    normalized = [" ".join(str(row["name"]).casefold().split()) for row in bundle.get("dishes", [])]
    if len(normalized) != len(set(normalized)):
        raise RuntimeError("canonical_normalized_name_collision")


def _evidence(row: dict[str, Any]) -> list[EvidenceRef]:
    return [
        EvidenceRef(
            source_code=str(row.get("source_name") or EVIDENCE.source_code),
            source_record_id=row.get("provider_record_id"),
            source_url=row.get("source_url"),
            extraction_method=str(row.get("extraction_method") or EVIDENCE.extraction_method),
        )
    ]


def import_bundle(target_dsn: str, bundle: dict[str, Any]) -> dict[str, Any]:
    validate_bundle(bundle)
    repository = PostgresRepository(target_dsn)
    with psycopg.connect(target_dsn, row_factory=dict_row) as connection:
        run = connection.execute(
            """INSERT INTO ontology.cutover_runs
               (source_system,source_watermark,export_sha256,status)
               VALUES(%s,%s,%s,'importing')
               ON CONFLICT(source_system,export_sha256) DO UPDATE
               SET status=ontology.cutover_runs.status
               RETURNING id,status""",
            (bundle["source_system"], bundle["watermark"], bundle["checksum_sha256"]),
        ).fetchone()
        assert run is not None
        if run["status"] in {"imported", "reconciled"}:
            return {"run_id": str(run["id"]), "replayed": True, "imported_dishes": 0}
        for row in bundle["meal_classes"]:
            connection.execute(
                """INSERT INTO ontology.meal_classes
                   (class_code,display_name,slot,planning_role,parent_class_code,family_code)
                   VALUES(%s,%s,%s,%s,NULL,%s) ON CONFLICT(class_code) DO UPDATE SET
                   display_name=excluded.display_name,slot=excluded.slot,
                   planning_role=excluded.planning_role,
                   family_code=excluded.family_code""",
                (
                    row["class_code"],
                    row["display_name"],
                    row["slot"],
                    _role(row["planning_role"]),
                    row.get("family_code"),
                ),
            )
        for row in bundle["meal_classes"]:
            if row.get("parent_class_code"):
                connection.execute(
                    "UPDATE ontology.meal_classes SET parent_class_code=%s WHERE class_code=%s",
                    (row["parent_class_code"], row["class_code"]),
                )
        run_id = run["id"]

    imported = 0
    for row in bundle["dishes"]:
        with psycopg.connect(target_dsn, row_factory=dict_row) as connection:
            prior = connection.execute(
                """SELECT service_id FROM ontology.legacy_identity_map
                   WHERE source_system=%s AND entity_type='dish' AND legacy_id=%s""",
                (bundle["source_system"], row["legacy_id"]),
            ).fetchone()
        if prior:
            continue
        fields = {
            str(item["field_key"]): FieldValue(
                value=item["value"],
                confidence=float(item["confidence"]),
                review_status=ReviewStatus(item["review_status"]),
                evidence=_evidence(item),
                last_verified_at=item["last_verified_at"],
            )
            for item in row["fields"]
        }
        base_fields = {
            "diet_type": row.get("diet_type"),
            "meal_occasion": row.get("meal_occasion"),
            "cook_time_minutes": row.get("cook_time_minutes"),
            "difficulty": row.get("difficulty"),
            "is_jain": row.get("is_jain"),
            "allergen_flags": row.get("allergen_flags"),
        }
        for path, value in base_fields.items():
            if value is not None and path not in fields:
                fields[path] = FieldValue(
                    value=value,
                    confidence=1,
                    review_status=ReviewStatus.accepted,
                    evidence=[EVIDENCE],
                )
        description = None
        if row.get("description"):
            description = FieldValue(
                value=row["description"],
                confidence=1,
                review_status=ReviewStatus.accepted,
                evidence=[EVIDENCE],
            )
        created = repository.create_dish(
            DishCreate.model_validate(
                {
                    "canonical_name": row["name"],
                    "description": description,
                    "aliases": [
                        AliasInput(
                            name=item["name"],
                            language=item.get("language") or "und",
                            region_code=item.get("region_code"),
                            alias_type=item.get("alias_type") or "synonym",
                            confidence=float(item.get("confidence") or 0.7),
                            evidence=_evidence(item),
                        )
                        for item in row["aliases"]
                    ],
                    "class_memberships": [
                        {
                            "class_code": item["class_code"],
                            "slot": item["slot"],
                            "role": item["role"],
                            "confidence": float(item["confidence"]),
                            "review_status": item["review_status"],
                            "evidence": _evidence(item),
                        }
                        for item in row["class_memberships"]
                    ],
                    "fields": fields,
                }
            )
        )
        with psycopg.connect(target_dsn) as connection:
            connection.execute(
                "UPDATE ontology.dishes SET status=%s WHERE id=%s",
                ("active" if row["is_active"] else "retired", created.id),
            )
            connection.execute(
                """INSERT INTO ontology.legacy_identity_map
                   (source_system,entity_type,legacy_id,service_id,cutover_run_id)
                   VALUES(%s,'dish',%s,%s,%s)""",
                (bundle["source_system"], row["legacy_id"], created.id, run_id),
            )
        imported += 1
    with psycopg.connect(target_dsn) as connection:
        connection.execute(
            "UPDATE ontology.cutover_runs SET status='imported',completed_at=now() WHERE id=%s",
            (run_id,),
        )
    return {"run_id": str(run_id), "replayed": False, "imported_dishes": imported}


def reconcile(target_dsn: str, bundle: dict[str, Any]) -> dict[str, Any]:
    validate_bundle(bundle)
    expected_ids = {str(row["legacy_id"]) for row in bundle["dishes"]}
    expected_classes = {str(row["class_code"]) for row in bundle["meal_classes"]}
    with psycopg.connect(target_dsn, row_factory=dict_row) as connection:
        maps = connection.execute(
            """SELECT legacy_id,service_id FROM ontology.legacy_identity_map
               WHERE source_system=%s AND entity_type='dish'""",
            (bundle["source_system"],),
        ).fetchall()
        actual_classes = {
            row["class_code"]
            for row in connection.execute("SELECT class_code FROM ontology.meal_classes").fetchall()
        }
        role_row = connection.execute(
            """SELECT count(*) AS value FROM ontology.dish_class_memberships m
               JOIN ontology.meal_classes c USING(class_code) WHERE m.role<>c.planning_role"""
        ).fetchone()
        assert role_row is not None
        role_violations = role_row["value"]
        pointer_row = connection.execute(
            """SELECT count(*) AS value FROM ontology.current_field_values c
               JOIN ontology.assertions a ON a.id=c.assertion_id
               WHERE c.dish_id<>a.dish_id OR NOT EXISTS
                 (SELECT 1 FROM ontology.assertion_evidence e WHERE e.assertion_id=a.id)"""
        ).fetchone()
        assert pointer_row is not None
        pointer_violations = pointer_row["value"]
    actual_ids = {row["legacy_id"] for row in maps}
    report = {
        "schema_version": "foofoo-ontology-reconciliation/v1",
        "source_export_sha256": bundle["checksum_sha256"],
        "expected_dishes": len(expected_ids),
        "mapped_dishes": len(expected_ids & actual_ids),
        "missing_legacy_ids": sorted(expected_ids - actual_ids),
        "unexpected_legacy_ids": sorted(actual_ids - expected_ids),
        "missing_class_codes": sorted(expected_classes - actual_classes),
        "class_role_violations": role_violations,
        "field_pointer_evidence_violations": pointer_violations,
    }
    report["passed"] = not any(
        (
            report["missing_legacy_ids"],
            report["unexpected_legacy_ids"],
            report["missing_class_codes"],
            role_violations,
            pointer_violations,
        )
    )
    with psycopg.connect(target_dsn) as connection:
        connection.execute(
            """UPDATE ontology.cutover_runs SET status=%s,report=%s::jsonb,completed_at=now()
               WHERE source_system=%s AND export_sha256=%s""",
            (
                "reconciled" if report["passed"] else "failed",
                json.dumps(report),
                bundle["source_system"],
                bundle["checksum_sha256"],
            ),
        )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="One-way Foofoo ontology cutover tooling")
    sub = parser.add_subparsers(dest="command", required=True)
    export = sub.add_parser("export")
    export.add_argument("--source-dsn", required=True)
    export.add_argument("--output", type=Path, required=True)
    imp = sub.add_parser("import")
    imp.add_argument("--target-dsn", required=True)
    imp.add_argument("--input", type=Path, required=True)
    rec = sub.add_parser("reconcile")
    rec.add_argument("--target-dsn", required=True)
    rec.add_argument("--input", type=Path, required=True)
    rec.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "export":
        args.output.write_bytes(canonical_json(export_legacy(args.source_dsn)) + b"\n")
    else:
        bundle = json.loads(args.input.read_text(encoding="utf-8"))
        result = (
            import_bundle(args.target_dsn, bundle)
            if args.command == "import"
            else reconcile(args.target_dsn, bundle)
        )
        if args.command == "reconcile":
            args.report.write_bytes(canonical_json(result) + b"\n")
        print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
