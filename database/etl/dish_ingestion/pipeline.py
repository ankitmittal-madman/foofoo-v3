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
import os
import time
from collections import Counter
from pathlib import Path

from . import images
from .dedupe import DedupeDecision, DedupeIndex
from .groq_adapter import GroqAdapter
from .image_prompt import ImagePromptGenerator, assemble_prompt, clean_dish_name_for_prompt
from .images import CloudinaryUploader, HFImageClient, PollinationsClient
from .normalize import SourceRow, load_and_normalize
from .ontology_adapter import get_adapter

logger = logging.getLogger("dish_ingestion.pipeline")

BATCH_SIZE = 200
REGION_CODE_ALIASES = {"north", "south", "east", "west", "northeast", "pan_indian"}
DEFAULT_IMAGE_DELAY_SECONDS = 3  # ported from the reference Pollinations script's own default
# dish_meal_class_mappings.slot CHECK constraint (migration 056) — the only values Postgres accepts.
VALID_MEAL_SLOTS = {"breakfast", "lunch", "dinner", "snack"}


class ImageContext:
    """Threads Stage-5 config + mutable idempotency state through the batch loop.

    `existing_dish_ids_with_image` starts seeded from a real DB query (load_dish_ids_with_image)
    in apply mode, and this run adds to it as it generates — so two dishes created in the SAME run
    (e.g. two rows that dedupe-merge onto one dish) never generate/upload twice either, not just
    across reruns.
    """

    __slots__ = ("generate_images", "dry_run", "image_delay_seconds", "prompt_gen", "pollinations",
                 "hf_image", "uploader", "existing_dish_ids_with_image")

    def __init__(self, generate_images: bool, dry_run: bool, image_delay_seconds: float = DEFAULT_IMAGE_DELAY_SECONDS):
        self.generate_images = generate_images
        self.dry_run = dry_run
        self.image_delay_seconds = image_delay_seconds
        self.prompt_gen = ImagePromptGenerator()
        self.pollinations = PollinationsClient()
        self.hf_image = HFImageClient()
        self.uploader = CloudinaryUploader()
        self.existing_dish_ids_with_image: set[str] = set()


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


def process_row(row: SourceRow, dedupe_index: DedupeIndex, ontology, groq: GroqAdapter,
                 image_ctx: ImageContext) -> RowOutcome:
    """Runs stages 2-5 for a single row in memory. Never touches the DB — pure function of its
    inputs, which is what makes dry-run mode possible without a database at all.

    Real image generation/upload cannot happen here: it needs a resolved dish_id (to check the
    idempotency guard) which only exists once the dish is persisted. So in apply mode this stage
    only PLANS (leaves outcome.image = None; the real work happens in `_persist_row`). In dry-run
    mode it produces an illustrative `planned_dry_run` result — heuristic fields only, by design,
    so a dry run never makes a network call to Groq/HF either, matching the same "dry-run touches
    no external paid/rate-limited service" discipline as Pollinations/Cloudinary.
    """
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

    # Groq enrichment is a real network call and the dominant cost of a full-dataset run --
    # skip it entirely for a row dedupe already resolved to a pre-existing dish (from this run's
    # in-memory index OR a prior run's persisted data, since dedupe_index is seeded from
    # load_existing_dishes at startup). Its regional-affinity/tags rows were already written the
    # first time this dish was created; re-deriving them on every resume wastes the majority of a
    # rerun's wall time re-processing rows that need no new enrichment at all.
    if outcome.dedupe.outcome != "matched_existing":
        try:
            outcome.region = groq.infer_regional_affinity(n["name"], n["cuisine_raw"])
            outcome.tags = groq.infer_tags(n["name"], n["ingredients"])
        except Exception as exc:
            outcome.errors.append(("enrich", "enrich_exception", str(exc)))

    try:
        if not image_ctx.generate_images:
            outcome.image = images.not_applicable(n["name"])
        elif image_ctx.dry_run:
            clean_name = clean_dish_name_for_prompt(n["name"])
            fields = image_ctx.prompt_gen.resolve_fields(
                clean_name, n["cuisine_raw"], n["course_raw"], n["ingredients"], force_heuristic=True
            )
            prompt_text = assemble_prompt(clean_name, fields)
            outcome.image = images.planned_dry_run(n["name"], prompt_text, fields.source, fields.model_name)
        else:
            outcome.image = None  # resolved for real in _persist_row once dish_id is known
    except Exception as exc:
        outcome.errors.append(("image", "image_exception", str(exc)))

    return outcome


def run_pipeline(csv_path: Path, dry_run: bool, batch_size: int = BATCH_SIZE,
                  generate_images: bool = True, image_delay_seconds: float = DEFAULT_IMAGE_DELAY_SECONDS,
                  row_limit: int | None = None, only_srno: set[int] | None = None) -> dict:
    """Entry point used by the CLI. Returns the import summary report dict either way; only
    writes to the database when dry_run is False.

    generate_images: Stage 5 real generation trigger (--generate-images / --skip-images). When
    False, every dish gets the not_applicable placeholder regardless of run mode. When True and
    dry_run is True, Stage 5 is only planned/reported (heuristic fields, no network) — see
    process_row's docstring. When True and dry_run is False, real Pollinations+Cloudinary calls
    happen in _persist_row for any dish that does not already have an image.

    row_limit: process only the first N CSV rows (None/0 = all rows). For smoke-testing a real
    --apply run (e.g. a first live Cloudinary/Groq test) against a small slice before committing
    to the full dataset. Does not change dedupe/report semantics beyond operating on fewer rows.

    only_srno: process only these specific, possibly non-contiguous, source_srno values (None =
    no filter). For re-testing a small named set of dishes (e.g. after a prompt-quality fix)
    without row_limit's "first N rows" constraint. Combines with row_limit if both are set.
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
    image_ctx = ImageContext(generate_images=generate_images, dry_run=dry_run, image_delay_seconds=image_delay_seconds)

    if not dry_run:
        from .db import Database  # deferred import, see db.py docstring

        db = Database()
        try:
            with db.transaction() as cur:
                cuisines = db.load_cuisines(cur)
                meal_classes = db.load_meal_classes(cur)
                existing = db.load_existing_dishes(cur)
                dedupe_index.seed_existing(
                    [{"name": e["name"], "fingerprint": e.get("fingerprint")} for e in existing]
                )
                image_ctx.existing_dish_ids_with_image = db.load_dish_ids_with_image(cur)
                actor = os.environ.get("FOOFOO_IMPORT_ACTOR", "etl_script")
                run_id = db.start_import_run(
                    cur, csv_path.name, checksum, "apply", actor
                )
        except BaseException:
            db.close()
            raise
    else:
        # Dry-run: no DB, no reference-table reads. Ontology adapter runs against an empty
        # reference set so every match is reported as 'no_match' — this is expected and is
        # exactly why the report clearly labels dry-run output as "unverified against live DB".
        logger.warning("dry-run mode: no DB connection opened; ontology/meal-class matches are "
                        "reported against an EMPTY reference set and are illustrative only")

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
                _persist_row(cur, db, run_id, o, counters, match_method_counts, confidence_buckets,
                             review_reasons, image_ctx)

    try:
        ontology = get_adapter(cuisines, meal_classes)
        groq = GroqAdapter()

        for row in load_and_normalize(csv_path):
            if row_limit and total >= row_limit:
                logger.info("row_limit=%s reached, stopping read early", row_limit)
                break
            if only_srno is not None and row.srno not in only_srno:
                continue
            total += 1
            outcome = process_row(row, dedupe_index, ontology, groq, image_ctx)
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
            completion_counters = dict(counters)
            completion_counters["total_rows"] = total
            with db.transaction() as cur:
                db.complete_import_run(cur, run_id, completion_counters, report)

        return report
    except BaseException as exc:
        if not dry_run and db is not None and run_id is not None:
            failure_report = {
                "schema_version": "dish-ingestion-failure-v1",
                "status": "failed",
                "source_file": str(csv_path),
                "source_checksum_sha256": checksum,
                "run_mode": "apply",
                "total_rows_processed": total,
                "outcome_counts": dict(counters),
                "failure_type": type(exc).__name__,
                "verified_against_live_db": False,
            }
            try:
                with db.transaction() as cur:
                    changed = db.fail_import_run(cur, run_id, failure_report)
                if not changed:
                    logger.error("failed import could not close its running lineage row")
            except Exception:
                logger.exception("failed to close import lineage after pipeline error")
        raise
    finally:
        if db is not None:
            db.close()


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


def _persist_image_result(cur, db, dish_id: str, img: images.ImageResult) -> None:
    asset_id = db.insert_image_asset(
        cur, img.source_url, img.checksum_sha256, img.fetch_status,
        storage_path=img.storage_path, prompt_text=img.prompt_text, prompt_backend=img.prompt_backend,
        prompt_model_name=img.prompt_model_name, image_gen_backend=img.image_gen_backend,
        image_gen_seed=img.image_gen_seed,
    )
    db.link_dish_image(cur, dish_id, asset_id, img.alt_text, img.is_primary, img.source_type, img.confidence)


def _persist_row(cur, db, run_id: str, o: RowOutcome, counters: Counter, match_method_counts: Counter,
                  confidence_buckets: Counter, review_reasons: Counter, image_ctx: ImageContext) -> None:
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

    # A savepoint per row, not just the whole-batch transaction: without it, a CheckViolation (or
    # any other DB error) partway through this row leaves the connection in
    # InFailedSqlTransaction, and the insert_row_error() call in the except block below would
    # itself fail with the same error — silently swallowing the real failure and killing the rest
    # of the batch. Rolling back to the savepoint on error restores a usable transaction so the
    # error can actually be recorded and the batch can continue.
    savepoint = f"row_{row.srno}"
    cur.execute(f"SAVEPOINT {savepoint}")

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
            # dish_meal_class_mappings_slot_check only accepts breakfast/lunch/dinner/snack —
            # take the real slot the ontology adapter resolved from meal_classes.slot, never a
            # substring of the class_code (that produced invalid values like 'BF').
            slot = o.class_match.raw_response.get("matched_slot") if o.class_match.raw_response else None
            if slot not in VALID_MEAL_SLOTS:
                slot = "lunch"
            if o.class_match.confidence >= 0.6:
                db.insert_meal_class_mapping(
                    cur, dish_id, o.class_match.canonical_id, slot,
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
            region_source_type = "rules" if o.region.source == "heuristic" else "ml_model"
            db.insert_regional_affinity(cur, dish_id, o.region.value, 0.6, o.region.confidence,
                                         f"etl:{o.region.source}", region_source_type,
                                         model_name=o.region.model_name if region_source_type == "ml_model" else None)

        # ingredients
        if dish_id:
            for ing in n["ingredients"][:40]:
                clean_name = ing[:200]
                try:
                    ing_id = db.upsert_ingredient(cur, clean_name, is_veg=True)
                    db.link_dish_ingredient(cur, dish_id, ing_id)
                except Exception as exc:
                    db.insert_row_error(cur, source_row_id, "persist", "ingredient_link_failed", str(exc))

        # image handling (Stage 5 — see images.py). o.image is already set (not_applicable) if
        # generation is disabled; it is None here whenever real generation is enabled in apply
        # mode, because process_row could not resolve a dish_id to check idempotency against.
        logger.info("image branch check: dish_id=%s o.image=%r generate_images=%s dry_run=%s",
                    dish_id, o.image, image_ctx.generate_images, image_ctx.dry_run)
        if dish_id and o.image is not None:
            logger.info("dish %s: persisting pre-set image result (source_type=%s)", dish_id, o.image.source_type)
            _persist_image_result(cur, db, dish_id, o.image)
        elif dish_id and image_ctx.generate_images and not image_ctx.dry_run:
            if dish_id in image_ctx.existing_dish_ids_with_image:
                logger.info("dish %s already has an image; skipping generation (idempotent)", dish_id)
            else:
                clean_name = clean_dish_name_for_prompt(n["name"])
                logger.info("dish %s (%s -> %s): attempting real image generation", dish_id, n["name"], clean_name)
                fields = image_ctx.prompt_gen.resolve_fields(
                    clean_name, n["cuisine_raw"], n["course_raw"], n["ingredients"],
                    instructions=row.raw.get("Instructions", ""),
                )
                prompt_text = assemble_prompt(clean_name, fields)
                # HF fallback intentionally not passed here (Founder directive): chaining
                # Pollinations' full retry cycle + an HF attempt inside one open DB transaction
                # was long enough to trip Supabase's idle-in-transaction/statement timeout,
                # aborting every row in the run (see import_row_errors: "current transaction is
                # aborted"). HFImageClient stays available on image_ctx for a future fix that
                # moves generation outside the transaction, but is not invoked for now.
                image_result = images.generate_and_upload(
                    clean_name, prompt_text, fields.source, fields.model_name,
                    image_ctx.pollinations, image_ctx.uploader,
                )
                logger.info("dish %s: image_result fetch_status=%s storage_path=%s",
                            dish_id, image_result.fetch_status, image_result.storage_path)
                _persist_image_result(cur, db, dish_id, image_result)
                if image_result.fetch_status == "fetched":
                    image_ctx.existing_dish_ids_with_image.add(dish_id)
                else:
                    db.insert_row_error(cur, source_row_id, "image", "image_generation_failed",
                                         image_result.alt_text or "unknown image failure")
                # rate limiting: small delay between real Pollinations calls, ported from the
                # reference script's DELAY_BETWEEN_REQUESTS default (task brief rule 4).
                time.sleep(image_ctx.image_delay_seconds)

        for stage, code, detail in o.errors:
            db.insert_row_error(cur, source_row_id, stage, code, detail)

        db.insert_row_result(cur, source_row_id, dish_id, status, decision.match_method, decision.score,
                              o.class_match.confidence if o.class_match else None,
                              o.class_match.canonical_id if (o.class_match and o.class_match.matched) else None)

        if o.errors:
            counters["errored"] += 1
        else:
            counters[status] += 1

        cur.execute(f"RELEASE SAVEPOINT {savepoint}")

    except Exception as exc:
        logger.exception("row srno=%s failed during persist", row.srno)
        # Restores the transaction to a usable state (see the SAVEPOINT comment above) so this
        # error can actually be written, instead of raising InFailedSqlTransaction on top of the
        # original error and losing both.
        cur.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
        db.insert_row_error(cur, source_row_id, "persist", "unhandled_exception", str(exc))
        cur.execute(f"RELEASE SAVEPOINT {savepoint}")
        counters["errored"] += 1
