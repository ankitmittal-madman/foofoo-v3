"""Validate and normalize captured real feedback for the next governed data refresh."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from ..schemas import FeedbackEvent
from .data_pipeline import NEGATIVE_EVENTS, POSITIVE_EVENTS

FEEDBACK_WEIGHTS: dict[str, float] = {
    **POSITIVE_EVENTS,
    **NEGATIVE_EVENTS,
    "repeat": 0.9,
    "rejected": -1.0,
    "household_vote": 0.0,
    "substituted": -0.4,
}


def normalize(source: Path, output: Path, report_path: Path) -> dict[str, Any]:
    seen: set[str] = set()
    normalized: list[dict[str, Any]] = []
    invalid = duplicates = 0
    for line in source.read_text().splitlines() if source.is_file() else []:
        if not line.strip():
            continue
        try:
            event = FeedbackEvent.model_validate_json(line)
        except (ValidationError, ValueError):
            invalid += 1
            continue
        if event.event_id in seen:
            duplicates += 1
            continue
        seen.add(event.event_id)
        weight = FEEDBACK_WEIGHTS[event.event_type]
        if event.event_type in {"rated", "household_vote"}:
            weight = (float(event.feedback_score or 3) - 3.0) / 2.0
        base = {
            "event_id": f"real:{event.event_id}",
            "household_id": event.household_id,
            "dish_id": event.dish_id,
            "timestamp": event.event_at.isoformat(),
            "meal_slot": (event.meal_slot or "").casefold(),
            "weight": weight,
            "event_type": event.event_type,
            "member_id": event.member_id,
            "day_type": str(event.context.get("day_type") or "unknown").casefold(),
            "context": event.context,
            "source_dataset": "real_feedback",
        }
        normalized.append(base)
        if event.event_type == "substituted" and event.substitute_dish_id:
            normalized.append(
                {
                    **base,
                    "event_id": f"real:{event.event_id}:substitute",
                    "dish_id": event.substitute_dish_id,
                    "weight": 0.8,
                    "event_type": "substitute_selected",
                }
            )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in normalized))
    report: dict[str, Any] = {
        "source": str(source),
        "valid_unique_events": len(seen),
        "normalized_interactions": len(normalized),
        "invalid_events": invalid,
        "duplicate_events": duplicates,
        "positive_interactions": sum(float(row["weight"]) > 0 for row in normalized),
        "negative_interactions": sum(float(row["weight"]) < 0 for row in normalized),
        "household_votes": sum(row["event_type"] == "household_vote" for row in normalized),
        "production_merge_allowed": invalid == 0 and duplicates == 0 and bool(normalized),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize captured FooFoo feedback")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(normalize(args.source, args.output, args.report), indent=2))


if __name__ == "__main__":
    main()
