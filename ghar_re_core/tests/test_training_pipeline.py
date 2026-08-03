"""
Phase 3 tests — ghar_re_core.training (dataset labeling + train_pref_model.py CLI pipeline).

Fixture-based ONLY, per the plan's explicit framing: these prove the PIPELINE runs end-to-end and
produces a loadable artifact, never that any particular model is good, and never against real
production feedback_events (0 rows exist). Also covers the insufficient-data / non-real-data
refusal guard, which must never silently "fit anyway".
"""
import json

import pytest

from ghar_re_core import fixtures as F
from ghar_re_core.catalogue import Catalogue
from ghar_re_core.training.dataset import (
    InsufficientDataError,
    build_labeled_dataset,
    guard_sufficient_data,
)
from ghar_re_core.training.train_pref_model import train

CAT = Catalogue()
HOUSEHOLD = next(h for h in F.HOUSEHOLDS if h["id_key"] == "single_professional_blr")
_DISH_NAMES = [d.name for d in CAT][:6]


def _rows(event_types, data_source="real"):
    """Builds fixture-shaped export rows (clearly synthetic FIXTURE data for testing the pipeline
    mechanics, never presented as real signal outside a test) pairing each requested event_type
    with a distinct real catalogue dish so build_labeled_dataset has real Dish objects to resolve."""
    rows = []
    for i, event_type in enumerate(event_types):
        rows.append({
            "household": HOUSEHOLD,
            "ctx": {"slot": "dinner", "season": "transitional"},
            "dish_name": _DISH_NAMES[i % len(_DISH_NAMES)],
            "event_type": event_type,
            "data_source": data_source,
        })
    return rows


# ---------------------------------------------------------------------------
# dataset labeling
# ---------------------------------------------------------------------------
def test_ambiguous_event_types_excluded_not_labelled_zero():
    rows = _rows(["shown_not_tapped", "edit", "swap", "accept", "dislike"])
    labeled = build_labeled_dataset(iter(rows))
    assert len(labeled) == 2
    assert {r.event_type for r in labeled} == {"accept", "dislike"}


def test_non_real_data_source_excluded():
    rows = _rows(["accept", "dislike"], data_source="ai_generated")
    labeled = build_labeled_dataset(iter(rows))
    assert labeled == []


def test_accept_and_like_label_one_dislike_labels_zero():
    rows = _rows(["accept", "like", "dislike"])
    labeled = build_labeled_dataset(iter(rows))
    by_event = {r.event_type: r.label for r in labeled}
    assert by_event["accept"] == 1
    assert by_event["like"] == 1
    assert by_event["dislike"] == 0


def test_unknown_dish_name_skipped_not_fabricated():
    rows = _rows(["accept"])
    rows[0]["dish_name"] = "Definitely Not A Real Catalogue Dish"
    labeled = build_labeled_dataset(iter(rows))
    assert labeled == []


# ---------------------------------------------------------------------------
# (d) the training pipeline's guard against insufficient data actually refuses.
# ---------------------------------------------------------------------------
def test_guard_refuses_on_zero_rows():
    with pytest.raises(InsufficientDataError):
        guard_sufficient_data([])


def test_guard_refuses_on_single_class():
    rows = _rows(["accept", "like"])
    labeled = build_labeled_dataset(iter(rows))
    assert labeled and {r.label for r in labeled} == {1}
    with pytest.raises(InsufficientDataError):
        guard_sufficient_data(labeled)


def test_train_refuses_and_writes_nothing_on_insufficient_data(tmp_path):
    export_path = tmp_path / "export.jsonl"
    export_path.write_text("\n".join(json.dumps(r) for r in _rows(["accept", "like"])))
    out_path = tmp_path / "artifact.joblib"

    with pytest.raises(InsufficientDataError):
        train(str(export_path), str(out_path))

    assert not out_path.exists(), "must never write an artifact when the data guard refuses"


def test_train_refuses_on_all_non_real_data_source(tmp_path):
    export_path = tmp_path / "export.jsonl"
    export_path.write_text(
        "\n".join(json.dumps(r) for r in _rows(["accept", "dislike"], data_source="stub"))
    )
    out_path = tmp_path / "artifact.joblib"

    with pytest.raises(InsufficientDataError):
        train(str(export_path), str(out_path))

    assert not out_path.exists()


# ---------------------------------------------------------------------------
# end-to-end pipeline run on a small, clearly-labeled fixture dataset.
# ---------------------------------------------------------------------------
def test_train_end_to_end_on_fixture_dataset_produces_loadable_artifact(tmp_path):
    """Proves the PIPELINE works (loads export, extracts real features, fits, writes a loadable
    artifact + eval report) — not that this particular fixture-fit model is good. Uses a slightly
    larger fixture set so the holdout split has both classes to compute AUC on."""
    event_types = (["accept", "like"] * 6) + (["dislike"] * 6)
    rows = _rows(event_types)
    export_path = tmp_path / "export.jsonl"
    export_path.write_text("\n".join(json.dumps(r) for r in rows))
    out_path = tmp_path / "artifact.joblib"
    eval_out_path = tmp_path / "eval.json"

    report = train(str(export_path), str(out_path), str(eval_out_path))

    assert out_path.exists()
    assert eval_out_path.exists()
    assert report["n_rows_total"] == len(rows)
    assert 0.0 <= report["holdout_accuracy"] <= 1.0

    import joblib
    artifact = joblib.load(out_path)
    assert "model" in artifact and "vectorizer" in artifact
    # The loaded model can score a fresh feature dict without raising.
    x = artifact["vectorizer"].transform([rows and _fixture_features()])
    proba = artifact["model"].predict_proba(x)
    assert proba.shape[1] == 2


def _fixture_features():
    from ghar_re_core.derivation import derive_theta
    from ghar_re_core.features import extract_features
    from ghar_re_core.pipeline import make_context

    dish = CAT.get(_DISH_NAMES[0])
    theta = derive_theta(HOUSEHOLD)
    ctx = make_context(slot="dinner", season="transitional")
    return extract_features(dish, theta, ctx)
