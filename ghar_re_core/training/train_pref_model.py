"""
ghar_re_core.training.train_pref_model — s_pref training CLI (Phase 3, not fit, not shipped).

    python -m ghar_re_core.training.train_pref_model \\
        --feedback-export <path-to-jsonl> --out <artifact-path> [--eval-out <report-json-path>]

Reads a feedback export (produced OFFLINE by a data owner — a SELECT against feedback_events
joined to recommendation_events, run manually, never automatically by this script; this script
never opens a DB connection itself, keeping RE-DOC-10 §1's "Edge Functions own 100% of DB access"
boundary intact even for training), extracts features via ghar_re_core.features.extract_features,
fits a small sklearn.linear_model.LogisticRegression, and writes a versioned joblib artifact plus
a small eval report for human review.

**This script is built and unit-tested against a fixture-based export in this phase, but is never
invoked against real production feedback_events anywhere in this plan** — there is no real data
yet (0 production rows), and the guard below (ghar_re_core.training.dataset.guard_sufficient_data)
refuses to fit rather than fabricate a result if that's still true when someone does run it.
"""
from __future__ import annotations

import argparse
import json
import sys

from ghar_re_core.training.dataset import (
    InsufficientDataError,
    build_labeled_dataset,
    guard_sufficient_data,
    iter_export_rows,
)
from ghar_re_core.training.evaluate import evaluate


def _vectorize(labeled_rows):
    """DictVectorizer handles the mixed categorical (diet/region/slot/...) + numeric
    (module__* raw values, interaction_count) feature dict ghar_re_core.features.extract_features
    produces, without this script hand-rolling its own one-hot encoding."""
    from sklearn.feature_extraction import DictVectorizer

    vectorizer = DictVectorizer(sparse=False)
    x = vectorizer.fit_transform([row.features for row in labeled_rows])
    y = [row.label for row in labeled_rows]
    return vectorizer, x, y


def train(feedback_export_path: str, out_path: str, eval_out_path: str | None = None, test_size: float = 0.25, random_state: int = 0) -> dict:
    """Runs the full pipeline end-to-end: load export -> filter/label -> guard -> vectorize ->
    fit -> holdout-eval -> write artifact + report. Raises InsufficientDataError (propagated to
    the CLI as a non-zero exit, message printed, NOTHING written) rather than ever producing a
    "trained" artifact from insufficient or non-real data."""
    import joblib
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split

    rows = build_labeled_dataset(iter_export_rows(feedback_export_path))
    guard_sufficient_data(rows)  # raises InsufficientDataError; caller must not catch-and-fit-anyway

    vectorizer, x, y = _vectorize(rows)

    # Stratify only when both classes have enough rows for the requested split; guard above
    # already proved at least 2 classes exist, but a tiny dataset can still make stratification
    # infeasible for a given test_size — fall back to a plain split rather than crashing.
    try:
        x_train, x_holdout, y_train, y_holdout = train_test_split(
            x, y, test_size=test_size, random_state=random_state, stratify=y,
        )
    except ValueError:
        x_train, x_holdout, y_train, y_holdout = train_test_split(
            x, y, test_size=test_size, random_state=random_state,
        )

    model = LogisticRegression(max_iter=1000)
    model.fit(x_train, y_train)

    report = evaluate(model, vectorizer, x_holdout, y_holdout)
    report["n_rows_total"] = len(rows)
    report["n_rows_train"] = len(y_train)

    joblib.dump({"model": model, "vectorizer": vectorizer}, out_path)
    if eval_out_path:
        with open(eval_out_path, "w") as f:
            json.dump(report, f, indent=2)
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Train the s_pref preference model from a feedback export JSONL. Fixture-"
                     "tested only in this phase — never run against real production data yet.",
    )
    parser.add_argument("--feedback-export", required=True, help="Path to the feedback export JSONL.")
    parser.add_argument("--out", required=True, help="Path to write the trained joblib artifact.")
    parser.add_argument("--eval-out", default=None, help="Optional path to write the eval report JSON.")
    parser.add_argument("--test-size", type=float, default=0.25)
    parser.add_argument("--random-state", type=int, default=0)
    args = parser.parse_args(argv)

    try:
        report = train(
            args.feedback_export, args.out, args.eval_out, args.test_size, args.random_state,
        )
    except InsufficientDataError as e:
        print(f"REFUSING TO TRAIN: {e}", file=sys.stderr)
        return 1

    print(json.dumps(
        {k: v for k, v in report.items() if k != "coefficients"}, indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
