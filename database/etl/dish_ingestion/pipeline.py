"""Orchestrates stages 1-6 of the ingestion pipeline over database/seeds/IndianFoodDatasetCSV.csv.

Batched, logged, resumable: rows are processed in batches (default 200), each batch is one DB
transaction (db.Database.transaction), and a failed batch only rolls back that batch — earlier
committed batches stay applied, so a rerun after a crash re-processes remaining/failed rows only
(every write is upsert/ON CONFLICT, so re-processing an already-applied row is a safe no-op).

--dry-run performs stages 1-5 fully (parse, dedupe, ontology-map, enrich, image-plumb) and prints
the same summary report as --apply, but never opens a DB connection and never writes anything.
"""

from __future__ import annotations

import hashlib
import logging
import time
from collections import Counter
from pathlib import Path

from .dedupe import DedupeDecision, DedupeIndex
from .groq_adapter import GroqAdapter
from .images import resolve_image_for_row
from .normalize import SourceRow, load_and_normalize
from .ontology_adapter import get_adapter

logger = logging.getLogger("dish_ingestion.pipeline")

BATCH_SIZE = 200
REGION_CODE_ALIASES = {"north", "south", "east", "west", "northeast", "pan_indian"}


def _file_checksum(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


class RowOutcome:
    __slots__ = ("row", "dedupe", "cuisine_match", "class_match", "diet_match", "region", "tags", "image", "errors")

    def __init__(self, row: SourceRow):
        self.row = row
        self.dedupe: DedupeDecision | None = None
        self.cuisine_match = None
        self.class_match = None
        self.diet_match = None
        self.region = None
        self.tags: list = []
        self.image = None
        self.errors: list[tuple[str, str, str]] = []  # (stage, code, detail)


def process_row(row: SourceRow, dedupe_index: DedupeIndex, ontology, groq: GroqAdapter) -> RowOutcome:
    """Runs stages 2-5 for a single row in memory. Never touches the DB — pure function of its
    inputs, which is what makes dry-run mode possible without a database at all."""
    outcome = RowOutcome(row)
    n = row.normalized

    try:
        outcome.dedupe = dedupe_index.decide(n["name"], row.fingerprint)
    except Exception as exc:  # defensive: dedupe must never crash the whole run
        outcome.errors.append(("dedupe", "dedupe_exception", str(exc)))
        outcome.dedupe = DedupeDecision("created_new", None, "error_fallback", 0.0)

    try:
        outcome.cuisine_match = ontology.match_cuisine(n["cuisine_raw"]) if n["cuisine_raw"] else None
        outcome.class_match = ontology.match_meal_class(n["course_raw"], []) if n["course_raw"] else None
        outcome.diet_match = ontology.match_diet(n["diet_raw"]) if n["diet_raw"] else None
    except Exception as exc:
        outcome.errors.append(("ontology_map", "ontology_exception", str(exc)))

    try:
        needs_region = True  # this dataset never supplies region directly
        if needs_region:
            outcome.region = groq.infer_regional_affinity(n["name"], n["cuisine_raw"])
        outcome.tags = groq.infer_tags(n["name"], n["ingredients"])
    except Exception as exc:
        outcome.errors.append(("enrich", "enrich_exception", str(exc)))

    try:
        outcome.image = resolve_image_for_row(n["name"], None)  # CSV has no image column
    except Exception as exc:
        outcome.errors.append(("image", "image_exception", str(exc)))

    return outcome


def run_pipeline(csv_path: Path, dry_run: bool, batch_size: int = BATCH_SIZE) -> dict:
    """Entry point used by the CLI. Returns the import summary report dict either way; only
    writes to the database when dry_run is False.
    """
    started = time.monotonic()
    checksum = _file_checksum(csv_path)
    logger.info("source checksum sha256=%s file=%s", checksum, csv_path)

    counters: Counter[str] = Counter()
    match_method_counts: Counter[str] = Counter()
    confidence_buckets: Counter[str] = Counter()
    review_reasons: Counter[str] = Counter()

    db = None
    run_id = None
    cuisines: dict[str, str] = {}
    meal_classes: list[dict] = []
    dedupe_index = DedupeIndex()

    if not dry_run:
        from .db import Database  # deferred import, see db.py docstring

        db = Database()
        with db.transaction() as cur:
            cuisines = db.load_cuisines(cur)
            meal_classes = db.load_meal_classes(cur)
            existing = db.load_existing_dishes(cur)
            dedupe_index.seed_existing(
                [{"name": e["name"], "fingerprint": e.get("fingerprint")} for e in existing]
            )
            run_id = db.start_import_run(cur, csv_path.name, checksum, "apply")
    else:
        # Dry-run: no DB, no reference-table reads. Ontology adapter runs against an empty
        # reference set so every match is reported as 'no_match' — this is expected and is
        # exactly why the report clearly labels dry-run output as "unverified against live DB".
        logger.warning("dry-run mode: no DB connection opened; ontology/meal-class matches are "
                        "reported against an EMPTY reference set and are illustrative only")

    ontology = get_adapter(cuisines, meal_classes)
    groq = GroqAdapter()

    batch: list[RowOutcome] = []
    total = 0

    def flush(batch: list[RowOutcome]) -> None:
        if not batch:
            return
        if dry_run:
            for o in batch:
                _tally(o, counters, match_method_counts, confidence_buckets, review_reasons)
            return
        with db.transaction() as cur:
            for o in batch:
                _persist_row(cur, db, run_id, o, counters, match_method_counts, confidence_buckets, review_reasons)

    for row in load_and_normalize(csv_path):
        total += 1
        outcome = process_row(row, dedupe_index, ontology, groq)
        batch.append(outcome)
        if len(batch) >= batch_size:
            flush(batch)
            batch = []
    flush(batch)

    elapsed = time.monotonic() - started
    report = {
        "source_file": str(csv_path),
        "source_checksum_sha256": checksum,
        "run_mode": "dry_run" if dry_run else "apply",
        "total_rows_processed": total,
        "elapsed_seconds": round(elapsed, 2),
        "outcome_counts": dict(counters),
        "match_method_counts": dict(match_method_counts),
        "ontology_confidence_distribution": dict(confidence_buckets),
        "review_reason_counts": dict(review_reasons),
        "verified_against_live_db": not dry_run,
    }

    if not dry_run:
        with db.transaction() as cur:
            db.complete_import_run(cur, run_id, counters, report)
        db.close()

    return report


def _confidence_bucket(score: float | None) -> str:
    if score is None:
        return "none"
    if score >= 0.9:
        return "0.9-1.0"
    if score >= 0.7:
        return "0.7-0.9"
    if score >= 0.5:
        return "0.5-0.7"
    return "0.0-0.5"


def _tally(o: RowOutcome, counters: Counter, match_method_counts: Counter, confidence_buckets: Counter, review_reasons: Counter) -> None:
    outcome_status = o.dedupe.outcome if o.dedupe else "errored"
    if o.errors:
        counters["errored"] += 1
    else:
        counters[outcome_status] += 1
    if o.dedupe:
        match_method_counts[o.dedupe.match_method] += 1
    if o.class_match:
        confidence_buckets[_confidence_bucket(o.class_match.confidence if o.class_match.matched else None)] += 1
    if o.class_match is None or not o.class_match.matched:
        review_reasons["no_meal_class_match"] += 1
    if o.dedupe and o.dedupe.outcome == "ambiguous_review":
        review_reasons["ambiguous_dedupe_candidate"] += 1


def _persist_row(cur, db, run_id: str, o: RowOutcome, counters: Counter, match_method_counts: Counter,
                  confidence_buckets: Counter, review_reasons: Counter) -> None:
    row = o.row
    n = row.normalized
    try:
        source_row_id = db.insert_source_row(cur, run_id, row.srno, row.fingerprint, row.raw, n)
    except Exception as exc:
        logger.error("failed to persist source row srno=%s: %s", row.srno, exc)
        counters["errored"] += 1
        return

    decision = o.dedupe
    match_method_counts[decision.match_method] += 1

    dish_id: str | None = None
    status = decision.outcome

    try:
        if decision.outcome == "matched_existing" and decision.target_key:
            dish_id = db.get_dish_id_by_name(cur, decision.target_key)
            if dish_id is None:
                # index said matched but DB disagrees (race with a concurrent run) — fall back to
                # creating, rather than silently dropping the row.
                status = "created_new"

        if status in ("created_new", "merged_duplicate", "ambiguous_review"):
            cuisine_id = o.cuisine_match.canonical_id if (o.cuisine_match and o.cuisine_match.matched) else None
            meal_occasion = [o.class_match.canonical_id] if (o.class_match and o.class_match.matched and o.class_match.canonical_id) else []
            cook_time = n.get("total_time_mins") or n.get("cook_time_mins") or 30
            create_name = n["name"] if status != "merged_duplicate" else n["name"]
            if status == "merged_duplicate" and decision.target_key:
                dish_id = db.get_dish_id_by_name(cur, decision.target_key)
                if n["translated_name"] and n["translated_name"].lower() != decision.target_key:
                    db.insert_alias(cur, dish_id, n["translated_name"], "dedupe_merge", run_id, decision.score)
                if n["name"].lower() != decision.target_key:
                    db.insert_alias(cur, dish_id, n["name"], "dedupe_merge", run_id, decision.score)
                status = "merged_duplicate"
            else:
                dish_id = db.upsert_dish(cur, create_name, row.raw.get("Instructions", "")[:2000], meal_occasion, cook_time, cuisine_id)
                status = "created_new" if status != "ambiguous_review" else "routed_review"
                if n["translated_name"] and n["translated_name"] != create_name:
                    db.insert_alias(cur, dish_id, n["translated_name"], "csv_translated_name", run_id, 1.0)

        # meal-class mapping (rule 4: only existing classes; low/no-confidence -> review queue)
        if o.class_match and o.class_match.matched and dish_id:
            # slot is embedded in canonical_id lookup via raw_response; recompute defensively
            slot = o.class_match.raw_response.get("matched_class", "").split("_")[0] if o.class_match.raw_response else None
            if o.class_match.confidence >= 0.6:
                db.insert_meal_class_mapping(
                    cur, dish_id, o.class_match.canonical_id, slot or "lunch",
                    o.class_match.confidence, "csv_import_ontology_fallback", o.class_match.match_method, "rules",
                )
                confidence_buckets[_confidence_bucket(o.class_match.confidence)] += 1
            else:
                review_reasons["low_confidence_ontology_match"] += 1
                db.insert_review_queue_entry(cur, source_row_id, dish_id, "low_confidence_ontology_match",
                                              {"course_raw": n["course_raw"], "confidence": o.class_match.confidence})
        else:
            review_reasons["no_meal_class_match"] += 1
            if dish_id:
                db.insert_review_queue_entry(cur, source_row_id, dish_id, "no_meal_class_match",
                                              {"course_raw": n["course_raw"]})

        if decision.outcome == "ambiguous_review" and dish_id:
            review_reasons["ambiguous_dedupe_candidate"] += 1
            db.insert_review_queue_entry(cur, source_row_id, dish_id, "ambiguous_dedupe_candidate",
                                          {"candidate": decision.target_key, "score": decision.score})

        # regional affinity (AI-generated enrichment, low confidence, provisional)
        if dish_id and o.region and o.region.value in REGION_CODE_ALIASES:
            db.insert_regional_affinity(cur, dish_id, o.region.value, 0.6, o.region.confidence,
                                         f"etl:{o.region.source}", "rules" if o.region.source == "heuristic" else "ml_model")

        # ingredients
        if dish_id:
            for ing in n["ingredients"][:40]:
                clean_name = ing[:200]
                try:
                    ing_id = db.upsert_ingredient(cur, clean_name, is_veg=True)
                    db.link_dish_ingredient(cur, dish_id, ing_id)
                except Exception as exc:
                    db.insert_row_error(cur, source_row_id, "persist", "ingredient_link_failed", str(exc))

        # image plumbing (mostly not_applicable for this dataset — see images.py)
        if dish_id and o.image:
            asset_id = db.insert_image_asset(cur, o.image.source_url, o.image.checksum_sha256, o.image.fetch_status)
            db.link_dish_image(cur, dish_id, asset_id, o.image.alt_text, o.image.is_primary, o.image.source_type, o.image.confidence)

        for stage, code, detail in o.errors:
            db.insert_row_error(cur, source_row_id, stage, code, detail)

        db.insert_row_result(cur, source_row_id, dish_id, status, decision.match_method, decision.score,
                              o.class_match.confidence if o.class_match else None,
                              o.class_match.canonical_id if (o.class_match and o.class_match.matched) else None)

        if o.errors:
            counters["errored"] += 1
        else:
            counters[status] += 1

    except Exception as exc:
        logger.exception("row srno=%s failed during persist", row.srno)
        db.insert_row_error(cur, source_row_id, "persist", "unhandled_exception", str(exc))
        counters["errored"] += 1
