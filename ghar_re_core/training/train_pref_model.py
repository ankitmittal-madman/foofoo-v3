"""
ghar_re_core.training.train_pref_model — s_pref training CLI (Phase 3, not fit, not shipped).

    python -m ghar_re_core.training.train_pref_model \\
        --feedback-export <path-to-jsonl> --out <artifact-path> [--eval-out <report-json-path>]

Reads a feedback export produced OFFLINE by a data owner through the service-role-only
`ml.preference_training_export_rows()` database function. This script never opens a DB connection,
keeping RE-DOC-10 §1's "Edge Functions own 100% of DB access" boundary intact even for training.
It extracts features via ghar_re_core.features.extract_features,
fits a small sklearn.linear_model.LogisticRegression, and writes a versioned joblib artifact plus
a small eval report for human review.

**This script is built and unit-tested against a fixture-based export in this phase, but is never
invoked against real production feedback_events anywhere in this plan** — there is no real data
yet (0 production rows), and the guard below (ghar_re_core.training.dataset.guard_sufficient_data)
refuses to fit rather than fabricate a result if that's still true when someone does run it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone

from ghar_re_core.config import CONFIG
from ghar_re_core.training.dataset import (
    InsufficientDataError,
    build_labeled_dataset,
    check_training_readiness,
    guard_sufficient_data,
    iter_export_rows,
)
from ghar_re_core.training.evaluate import assess_promotion_readiness, evaluate
from ghar_re_core.model_provider import PREFERENCE_ARTIFACT_SCHEMA_VERSION


def _vectorize(labeled_rows):
    """DictVectorizer handles the mixed categorical (diet/region/slot/...) + numeric
    (module__* raw values, interaction_count) feature dict ghar_re_core.features.extract_features
    produces, without this script hand-rolling its own one-hot encoding."""
    from sklearn.feature_extraction import DictVectorizer

    vectorizer = DictVectorizer(sparse=False)
    x = vectorizer.fit_transform([row.features for row in labeled_rows])
    y = [row.label for row in labeled_rows]
    return vectorizer, x, y


def train(
    feedback_export_path: str,
    out_path: str,
    eval_out_path: str | None = None,
    test_size: float = 0.25,
    random_state: int = 0,
    skip_readiness_gate: bool = False,
) -> dict:
    """Runs the full pipeline end-to-end: load export -> filter/label -> guard -> readiness gate
    -> vectorize -> fit -> holdout-eval -> write artifact + report. Raises InsufficientDataError
    (propagated to the CLI as a non-zero exit, message printed, NOTHING written) rather than ever
    producing a "trained" artifact from insufficient, non-real, or too-thin data.

    `skip_readiness_gate`: bypasses ONLY check_training_readiness's density check (CLI --force) —
    never guard_sufficient_data's structural correctness checks just above it, which always run
    regardless. For a deliberate human test run against a small real export, not a default."""
    import joblib
    import sklearn
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import GroupShuffleSplit, train_test_split

    rows = build_labeled_dataset(iter_export_rows(feedback_export_path))
    guard_sufficient_data(
        rows
    )  # raises InsufficientDataError; caller must not catch-and-fit-anyway
    if not skip_readiness_gate:
        check_training_readiness(
            rows,
            CONFIG.pref_training_min_events,
            CONFIG.pref_training_min_households,
        )

    vectorizer, x, y = _vectorize(rows)

    household_ids = [row.household_id for row in rows]
    grouped_split = all(household_ids) and len(set(household_ids)) >= 2
    train_households: set[str | None] = set()
    holdout_households: set[str | None] = set()
    if grouped_split:
        # Never let the same household appear in training and evaluation. Try several deterministic
        # group splits because sparse household labels can make an individual split single-class.
        chosen = None
        splitter = GroupShuffleSplit(
            n_splits=32,
            test_size=test_size,
            random_state=random_state,
        )
        for train_indices, holdout_indices in splitter.split(x, y, groups=household_ids):
            candidate_train = [y[index] for index in train_indices]
            candidate_holdout = [y[index] for index in holdout_indices]
            if len(set(candidate_train)) >= 2 and len(set(candidate_holdout)) >= 2:
                chosen = (train_indices, holdout_indices, candidate_train, candidate_holdout)
                break
        if chosen is None:
            raise InsufficientDataError(
                "Could not form a household-isolated holdout containing both label classes; "
                "refusing a leaky or non-evaluable fit."
            )
        train_indices, holdout_indices, y_train, y_holdout = chosen
        x_train, x_holdout = x[train_indices], x[holdout_indices]
        train_households = {household_ids[index] for index in train_indices}
        holdout_households = {household_ids[index] for index in holdout_indices}
        split_strategy = "household_group_holdout"
    else:
        # Only reachable for an explicit --force/dev run: the production readiness gate requires
        # household provenance. Preserve fixture usability without pretending this is deployable.
        try:
            x_train, x_holdout, y_train, y_holdout = train_test_split(
                x,
                y,
                test_size=test_size,
                random_state=random_state,
                stratify=y,
            )
        except ValueError:
            x_train, x_holdout, y_train, y_holdout = train_test_split(
                x,
                y,
                test_size=test_size,
                random_state=random_state,
            )
        train_households = set()
        holdout_households = set()
        split_strategy = "row_holdout_forced"

    model = LogisticRegression(max_iter=1000)
    model.fit(x_train, y_train)

    report = evaluate(model, vectorizer, x_holdout, y_holdout)
    report["n_rows_total"] = len(rows)
    report["n_rows_train"] = len(y_train)
    report["split_strategy"] = split_strategy
    report["train_households"] = len(train_households)
    report["holdout_households"] = len(holdout_households)
    report["household_overlap"] = len(train_households & holdout_households)
    promotion_gate = assess_promotion_readiness(
        report,
        min_holdout_events=CONFIG.pref_evaluation_min_holdout_events,
        min_auc=CONFIG.pref_evaluation_min_auc,
        min_class_recall=CONFIG.pref_evaluation_min_class_recall,
    )
    # A forced fixture/dev fit is useful for pipeline testing but can never be promotable.
    if skip_readiness_gate:
        promotion_gate["passed"] = False
        promotion_gate["checks"]["production_readiness_not_bypassed"] = False
    else:
        promotion_gate["checks"]["production_readiness_not_bypassed"] = True
    report["promotion_gate"] = promotion_gate

    fingerprint_payload = {
        "features": vectorizer.get_feature_names_out().tolist(),
        "coefficients": model.coef_.tolist(),
        "intercept": model.intercept_.tolist(),
        "classes": model.classes_.tolist(),
    }
    model_version = (
        "sha256:"
        + hashlib.sha256(
            json.dumps(fingerprint_payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:16]
    )
    metadata = {
        "artifact_schema_version": PREFERENCE_ARTIFACT_SCHEMA_VERSION,
        "model_version": model_version,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "feature_count": len(vectorizer.get_feature_names_out()),
        "n_rows_total": len(rows),
        "n_rows_train": len(y_train),
        "label_counts": {str(label): y.count(label) for label in sorted(set(y))},
        "random_state": random_state,
        "test_size": test_size,
        "readiness_gate_bypassed": skip_readiness_gate,
        "split_strategy": split_strategy,
        "household_overlap": len(train_households & holdout_households),
        "promotion_gate_passed": promotion_gate["passed"],
        "promotion_gate": promotion_gate,
        "libraries": {
            "scikit_learn": sklearn.__version__,
            "joblib": joblib.__version__,
        },
    }
    report["artifact_metadata"] = metadata

    # Atomic replacement prevents a service restart from observing a half-written joblib file.
    out_dir = os.path.dirname(os.path.abspath(out_path))
    fd, temp_path = tempfile.mkstemp(prefix=".pref-model-", suffix=".joblib", dir=out_dir)
    os.close(fd)
    try:
        joblib.dump({"model": model, "vectorizer": vectorizer, "metadata": metadata}, temp_path)
        os.replace(temp_path, out_path)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    if eval_out_path:
        with open(eval_out_path, "w") as f:
            json.dump(report, f, indent=2)
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Train the s_pref preference model from a feedback export JSONL. Fixture-"
        "tested only in this phase — never run against real production data yet.",
    )
    parser.add_argument(
        "--feedback-export", required=True, help="Path to the feedback export JSONL."
    )
    parser.add_argument("--out", required=True, help="Path to write the trained joblib artifact.")
    parser.add_argument(
        "--eval-out", default=None, help="Optional path to write the eval report JSON."
    )
    parser.add_argument("--test-size", type=float, default=0.25)
    parser.add_argument("--random-state", type=int, default=0)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Bypass the training_readiness density gate (pref_model.yaml) for a deliberate test "
        "run against a small real export. Never bypasses guard_sufficient_data's structural "
        "correctness checks (zero rows / single label class) — those always run.",
    )
    args = parser.parse_args(argv)

    try:
        report = train(
            args.feedback_export,
            args.out,
            args.eval_out,
            args.test_size,
            args.random_state,
            skip_readiness_gate=args.force,
        )
    except InsufficientDataError as e:
        print(f"REFUSING TO TRAIN: {e}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {k: v for k, v in report.items() if k != "coefficients"},
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
