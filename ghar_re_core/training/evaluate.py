"""
ghar_re_core.training.evaluate — holdout eval report for an s_pref training run (Phase 3).

Produces a human-reviewable report with ranking, calibration, class-recall and prevalence-baseline
metrics. Accuracy alone is actively misleading for the production feedback distribution because
positive events heavily outnumber explicit negatives.
"""
from __future__ import annotations

from typing import Any


def evaluate(model, vectorizer, x_holdout, y_holdout) -> dict[str, Any]:
    """Evaluate discrimination and calibration against a prevalence-only baseline."""
    from sklearn.metrics import (
        accuracy_score,
        average_precision_score,
        balanced_accuracy_score,
        brier_score_loss,
        log_loss,
        recall_score,
        roc_auc_score,
    )

    y_pred = model.predict(x_holdout)
    y_proba = model.predict_proba(x_holdout)[:, 1]
    prevalence = sum(y_holdout) / len(y_holdout)
    baseline_proba = [prevalence] * len(y_holdout)
    report: dict[str, Any] = {
        "holdout_n": len(y_holdout),
        "holdout_accuracy": float(accuracy_score(y_holdout, y_pred)),
        "holdout_balanced_accuracy": float(balanced_accuracy_score(y_holdout, y_pred)),
        "holdout_positive_recall": float(recall_score(y_holdout, y_pred, pos_label=1)),
        "holdout_negative_recall": float(recall_score(y_holdout, y_pred, pos_label=0)),
        "holdout_prevalence": float(prevalence),
        "holdout_brier": float(brier_score_loss(y_holdout, y_proba)),
        "baseline_brier": float(brier_score_loss(y_holdout, baseline_proba)),
        "holdout_log_loss": float(log_loss(y_holdout, y_proba, labels=[0, 1])),
        "baseline_log_loss": float(log_loss(y_holdout, baseline_proba, labels=[0, 1])),
    }
    if len(set(y_holdout)) >= 2:
        report["holdout_auc"] = float(roc_auc_score(y_holdout, y_proba))
        report["holdout_average_precision"] = float(
            average_precision_score(y_holdout, y_proba)
        )
    else:
        report["holdout_auc"] = None
        report["holdout_auc_note"] = (
            "Holdout split has only one label class — AUC is undefined, not computed as a "
            "misleading placeholder value."
        )

    feature_names = vectorizer.get_feature_names_out()
    coefficients = model.coef_[0]
    report["coefficients"] = dict(sorted(
        zip(feature_names, (float(c) for c in coefficients), strict=True),
        key=lambda kv: abs(kv[1]),
        reverse=True,
    ))
    report["intercept"] = float(model.intercept_[0])
    return report


def assess_promotion_readiness(
    report: dict[str, Any],
    *,
    min_holdout_events: int,
    min_auc: float,
    min_class_recall: float,
) -> dict[str, Any]:
    """Fail-closed quality gate for a candidate artifact.

    Absolute thresholds are governed in pref_model.yaml. Calibration losses must also beat the
    holdout's prevalence-only predictor, making the gate adapt to the actual label imbalance.
    """
    checks = {
        "holdout_volume": report.get("holdout_n", 0) >= min_holdout_events,
        "auc": report.get("holdout_auc") is not None
        and report["holdout_auc"] >= min_auc,
        "positive_recall": report.get("holdout_positive_recall", 0.0) >= min_class_recall,
        "negative_recall": report.get("holdout_negative_recall", 0.0) >= min_class_recall,
        "brier_beats_prevalence": report.get("holdout_brier", float("inf"))
        < report.get("baseline_brier", float("-inf")),
        "log_loss_beats_prevalence": report.get("holdout_log_loss", float("inf"))
        < report.get("baseline_log_loss", float("-inf")),
    }
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "thresholds": {
            "min_holdout_events": min_holdout_events,
            "min_auc": min_auc,
            "min_class_recall": min_class_recall,
            "require_prevalence_baseline_improvement": True,
        },
    }
