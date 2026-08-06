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
    check_training_readiness,
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
        rows.append(
            {
                "household": HOUSEHOLD,
                "ctx": {"slot": "dinner", "season": "transitional"},
                "dish_name": _DISH_NAMES[i % len(_DISH_NAMES)],
                "event_type": event_type,
                "data_source": data_source,
            }
        )
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


def test_explicit_positive_and_negative_signals_have_consistent_labels():
    positives = ["accept", "like", "make_this", "cooked", "completed"]
    negatives = ["dislike", "never", "regretted"]
    rows = _rows(positives + negatives)
    labeled = build_labeled_dataset(iter(rows))
    by_event = {r.event_type: r.label for r in labeled}
    assert all(by_event[event] == 1 for event in positives)
    assert all(by_event[event] == 0 for event in negatives)


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


def test_readiness_gate_refuses_below_min_events():
    """check_training_readiness (item #4's density gate) is separate from and stricter than
    guard_sufficient_data — enough rows/both classes to structurally fit is not the same as
    enough rows to trust the fit."""
    rows = _rows((["accept", "like"] * 3) + (["dislike"] * 3))  # 12 rows, both classes present
    labeled = build_labeled_dataset(iter(rows))
    guard_sufficient_data(labeled)  # passes — both classes present
    with pytest.raises(InsufficientDataError, match="min_real_events"):
        check_training_readiness(labeled, min_events=10000, min_households=1)


def test_readiness_gate_refuses_below_min_households():
    rows = _rows((["accept", "like"] * 3) + (["dislike"] * 3))
    labeled_dicts = [dict(r, household_id="only-one-household") for r in rows]
    labeled = build_labeled_dataset(iter(labeled_dicts))
    with pytest.raises(InsufficientDataError, match="min_households"):
        check_training_readiness(labeled, min_events=1, min_households=500)


def test_readiness_gate_refuses_when_export_carries_no_household_id():
    """Missing provenance cannot prove household diversity or leakage-free evaluation."""
    rows = _rows((["accept", "like"] * 3) + (["dislike"] * 3))
    labeled = build_labeled_dataset(iter(rows))
    assert all(r.household_id is None for r in labeled)
    with pytest.raises(InsufficientDataError, match="no household_id"):
        check_training_readiness(labeled, min_events=1, min_households=500)


def test_readiness_gate_passes_when_both_thresholds_met():
    base_rows = _rows((["accept", "like"] * 3) + (["dislike"] * 3))  # 9 rows
    rows = [dict(r, household_id=f"hh-{i}") for i, r in enumerate(base_rows)]
    labeled = build_labeled_dataset(iter(rows))
    assert len(labeled) == 9
    check_training_readiness(labeled, min_events=9, min_households=9)  # does not raise


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

    # skip_readiness_gate=True: this is a deliberately small fixture proving the PIPELINE works,
    # not a real production-scale export — check_training_readiness's density gate (pref_model.yaml
    # training_readiness) is exactly what should (and does, see test below) block a fixture this
    # small in the default/production path.
    report = train(str(export_path), str(out_path), str(eval_out_path), skip_readiness_gate=True)

    assert out_path.exists()
    assert eval_out_path.exists()
    assert report["n_rows_total"] == len(rows)
    assert 0.0 <= report["holdout_accuracy"] <= 1.0

    import joblib

    artifact = joblib.load(out_path)
    assert "model" in artifact and "vectorizer" in artifact
    assert artifact["metadata"]["artifact_schema_version"] == "preference-artifact-v1"
    assert artifact["metadata"]["model_version"].startswith("sha256:")
    # The loaded model can score a fresh feature dict without raising.
    x = artifact["vectorizer"].transform([rows and _fixture_features()])
    proba = artifact["model"].predict_proba(x)
    assert proba.shape[1] == 2

    # The exact artifact written by training must also satisfy the live inference provider's
    # feature-dict contract; this catches writer/reader drift before an activation deploy.
    from ghar_re_core.model_provider import FileModelArtifactProvider

    provider = FileModelArtifactProvider(str(out_path))
    loaded = provider.load()
    assert loaded is not None
    assert 0.0 <= loaded.predict_proba(_fixture_features()) <= 1.0
    assert loaded.metadata["model_version"] == artifact["metadata"]["model_version"]


def test_training_holdout_is_household_isolated_when_provenance_exists(tmp_path):
    rows = []
    for index in range(20):
        pair = _rows(["accept", "dislike"])
        rows.extend(dict(row, household_id=f"hh-{index}") for row in pair)
    export_path = tmp_path / "grouped-export.jsonl"
    export_path.write_text("\n".join(json.dumps(row) for row in rows))
    out_path = tmp_path / "grouped-artifact.joblib"

    report = train(str(export_path), str(out_path), skip_readiness_gate=True)

    assert report["split_strategy"] == "household_group_holdout"
    assert report["train_households"] > 0
    assert report["holdout_households"] > 0
    assert report["household_overlap"] == 0


def test_train_default_path_blocks_the_same_fixture_on_density_not_just_structure(tmp_path):
    """Without skip_readiness_gate, the exact same small-but-structurally-valid fixture above
    (real pref_model.yaml training_readiness thresholds: min_real_events=10000,
    min_households=500) must still be refused — proving item #4's density gate is actually wired
    into the default train() path, not just callable in isolation."""
    event_types = (["accept", "like"] * 6) + (["dislike"] * 6)
    export_path = tmp_path / "export.jsonl"
    export_path.write_text("\n".join(json.dumps(r) for r in _rows(event_types)))
    out_path = tmp_path / "artifact.joblib"

    with pytest.raises(InsufficientDataError, match="min_real_events"):
        train(str(export_path), str(out_path))  # skip_readiness_gate defaults to False

    assert not out_path.exists(), "must never write an artifact when the readiness gate refuses"


def _fixture_features():
    from ghar_re_core.derivation import derive_theta
    from ghar_re_core.features import extract_features
    from ghar_re_core.pipeline import make_context

    dish = CAT.get(_DISH_NAMES[0])
    theta = derive_theta(HOUSEHOLD)
    ctx = make_context(slot="dinner", season="transitional")
    return extract_features(dish, theta, ctx)
