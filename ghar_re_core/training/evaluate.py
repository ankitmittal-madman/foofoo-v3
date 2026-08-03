"""
ghar_re_core.training.evaluate — holdout eval report for an s_pref training run (Phase 3).

Produces a small, human-reviewable dict (never auto-applied anywhere) with holdout AUC/accuracy
and a per-feature coefficient dump, so a domain owner can sanity-check the learned coefficients
against actual domain intuition before ever considering flipping `pref_model.yaml.enabled`. This
module never writes pref_model.yaml, never calls set_active_model() — it only reports.
"""
from __future__ import annotations

from typing import Any


def evaluate(model, vectorizer, x_holdout, y_holdout) -> dict[str, Any]:
    """Computes holdout accuracy + AUC (AUC omitted, not fabricated as 0.5, if the holdout set
    itself has only one class) and a coefficient-per-feature-name dump for human review."""
    from sklearn.metrics import accuracy_score, roc_auc_score

    y_pred = model.predict(x_holdout)
    report: dict[str, Any] = {
        "holdout_n": len(y_holdout),
        "holdout_accuracy": float(accuracy_score(y_holdout, y_pred)),
    }
    if len(set(y_holdout)) >= 2:
        y_proba = model.predict_proba(x_holdout)[:, 1]
        report["holdout_auc"] = float(roc_auc_score(y_holdout, y_proba))
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
