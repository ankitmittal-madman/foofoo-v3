#!/usr/bin/env python3
"""CLI entry point: ingest database/seeds/IndianFoodDatasetCSV.csv into the dish catalogue.

Usage:
    python database/etl/ingest_dish_dataset.py --dry-run
    DATABASE_URL=postgres://... python database/etl/ingest_dish_dataset.py --apply
    python database/etl/ingest_dish_dataset.py --apply --csv path/to/other.csv --batch-size 500

See docs/architecture/[ACTIVE]_RUNBOOK_Dish_Ingestion_Pipeline_v1.1.md for the full operational
runbook, exact preconditions, and what --dry-run does and does not verify.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dish_ingestion.pipeline import run_pipeline  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CSV = ROOT / "database" / "seeds" / "IndianFoodDatasetCSV.csv"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="Parse/dedupe/map/enrich in memory; write nothing.")
    mode.add_argument("--apply", action="store_true", help="Write to the database at DATABASE_URL/SUPABASE_DB_URL.")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV, help=f"Source CSV path (default: {DEFAULT_CSV})")
    parser.add_argument("--batch-size", type=int, default=200, help="Rows per transaction batch (default: 200)")
    parser.add_argument("--limit", type=int, default=0, help="Process only the first N CSV rows (0 = all rows). For smoke-testing a real --apply run against a small slice first.")
    parser.add_argument("--report-out", type=Path, default=None, help="Optional path to also write the JSON summary report")
    image_mode = parser.add_mutually_exclusive_group()
    image_mode.add_argument("--generate-images", dest="generate_images", action="store_true", default=True,
                             help="Stage 5: generate + upload a dish image for any dish missing one (default: on).")
    image_mode.add_argument("--skip-images", dest="generate_images", action="store_false",
                             help="Disable Stage 5 entirely; every row gets a not_applicable image placeholder.")
    parser.add_argument("--image-delay", type=float, default=3.0,
                         help="Seconds to sleep between real Pollinations.ai calls (default: 3, rate-limit discipline).")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    log = logging.getLogger("dish_ingestion.cli")

    if not args.csv.exists():
        log.error("source CSV not found: %s", args.csv)
        return 2

    log.info("starting dish ingestion: mode=%s csv=%s batch_size=%s generate_images=%s limit=%s",
              "dry_run" if args.dry_run else "apply", args.csv, args.batch_size, args.generate_images,
              args.limit or "all")

    try:
        report = run_pipeline(csv_path=args.csv, dry_run=args.dry_run, batch_size=args.batch_size,
                               generate_images=args.generate_images, image_delay_seconds=args.image_delay,
                               row_limit=args.limit or None)
    except RuntimeError as exc:
        # e.g. DATABASE_URL missing in --apply mode — a clear, actionable error, not a stack trace.
        log.error(str(exc))
        return 3
    except Exception:
        log.exception("ingestion pipeline failed with an unhandled error")
        return 1

    print(json.dumps(report, indent=2, ensure_ascii=False))
    if args.report_out:
        args.report_out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        log.info("report written to %s", args.report_out)

    if not report.get("verified_against_live_db"):
        log.warning("DRY RUN: outcome counts above are illustrative only (empty reference tables) — "
                    "run --apply against a real database for a true report.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
