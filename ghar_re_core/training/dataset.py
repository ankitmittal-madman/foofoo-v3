"""
ghar_re_core.training.dataset — feedback-export loading + labeling for the s_pref training
pipeline (Phase 3, not fit, not shipped).

Export row shape (JSONL, one row per served/tapped dish, produced OFFLINE by a data owner — never
by this repo): each line is a JSON object with:
    {
      "household": {...},        # the raw household-answers dict derive_theta() already accepts
                                  # (same shape as ghar_re_core.fixtures.HOUSEHOLDS entries)
      "ctx": {...},               # the ctx dict ghar_re_core.pipeline.make_context() already
                                  # accepts (slot/season/weekday/weather/interaction_count/...)
      "dish_name": "...",         # must resolve via Catalogue().get(dish_name)
      "event_type": "accept" | "like" | "dislike" | "shown_not_tapped" | "edit" | "swap",
      "data_source": "real" | "ai_generated" | "stub"   # mirrors feedback_events.data_source
    }

This reuses the SAME real household/context/dish objects and the SAME
ghar_re_core.features.extract_features() every other module already goes through — training never
invents a parallel feature representation.

FD-11 (no fabricated/synthetic labels) discipline enforced here, not left to the caller:
  - Only `data_source == "real"` rows are ever used to build the training set — `ai_generated`/
    `stub` rows exist in the schema for test/demo fixtures elsewhere in the repo, and must never
    silently leak into a "trained" artifact.
  - Explicit positive intent/outcomes (`accept`, `like`, `make_this`, `cooked`, `completed`) -> 1.
  - Explicit negative intent/outcomes (`dislike`, `never`, `regretted`) -> 0.
  - `event_type == 'shown_not_tapped'` (and the unused `edit`/`swap`) are AMBIGUOUS — not a
    rejection, not a positive — and are EXCLUDED from training entirely, never labelled 0, per the
    plan's §3.3 spec and FD-11.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterator

from ghar_re_core.catalogue import Catalogue
from ghar_re_core.derivation import derive_theta
from ghar_re_core.features import extract_features
from ghar_re_core.pipeline import make_context

_POSITIVE_EVENT_TYPES = {"accept", "like", "make_this", "cooked", "completed"}
_NEGATIVE_EVENT_TYPES = {"dislike", "never", "regretted"}
# Ambiguous per FD-11 — deliberately never labelled, deliberately never trained on.
_AMBIGUOUS_EVENT_TYPES = {"shown_not_tapped", "edit", "swap"}

# The only data_source value this pipeline will ever build a training row from. `ai_generated`/
# `stub` rows are real, valid feedback_events rows for OTHER purposes (fixtures, demos) but must
# never be presented to this pipeline as if they were real user signal.
_REAL_DATA_SOURCE = "real"


@dataclass(frozen=True)
class LabeledRow:
    """One (features, label) training example, plus enough provenance to explain a
    refusal/report without re-reading the export file."""

    features: dict[str, Any]
    label: int
    dish_name: str
    event_type: str
    # The household this row came from. Older exports may omit it, but production readiness then
    # fails closed because diversity and household-isolated evaluation cannot be proven. It is
    # never fed into features/derive_theta (no household-identity leak into the model itself).
    household_id: str | None = None


class InsufficientDataError(Exception):
    """Raised (never silently swallowed) when the export, after real-data filtering and
    ambiguous-row exclusion, does not contain enough signal to responsibly fit anything — e.g.
    zero real rows, or only one label class present (logistic regression is undefined with a
    single class). This is the guard the plan leaves unspecified at a numeric-density level
    (WP-14's deliberate silence on a threshold number) but which this pipeline still must never
    skip: refusing to fit on structurally insufficient data is not a product density decision,
    it is a correctness requirement — a single-class fit would silently produce a meaningless,
    always-constant artifact rather than an honest refusal."""


def iter_export_rows(path: str) -> Iterator[dict[str, Any]]:
    """Yields each parsed JSON object from a feedback-export JSONL file, one per line. Blank
    lines are skipped; this never reaches into Postgres — `path` is always a local file the data
    owner produced offline."""
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def build_labeled_dataset(
    rows: Iterator[dict[str, Any]], catalogue: Catalogue | None = None
) -> list[LabeledRow]:
    """Turns raw export rows into `LabeledRow`s: filters to `data_source == "real"`, excludes
    ambiguous event types, resolves each dish via the real Catalogue, derives theta via the real
    derive_theta(), and extracts features via the real ghar_re_core.features.extract_features —
    the exact same function every other s_pref-consuming code path uses. Rows referencing an
    unknown dish name are skipped (never fabricated), with no error raised for that case alone
    (a stale/renamed dish in an old export is an expected, not exceptional, data-quality gap)."""
    cat = catalogue or Catalogue()
    labeled: list[LabeledRow] = []
    for row in rows:
        if row.get("data_source") != _REAL_DATA_SOURCE:
            continue
        event_type = row.get("event_type")
        if event_type in _AMBIGUOUS_EVENT_TYPES or event_type not in (
            _POSITIVE_EVENT_TYPES | _NEGATIVE_EVENT_TYPES
        ):
            continue

        dish = cat.get(row["dish_name"])
        if dish is None:
            continue

        theta = derive_theta(row["household"])
        ctx = make_context(**row.get("ctx", {}))
        features = extract_features(dish, theta, ctx)
        label = 1 if event_type in _POSITIVE_EVENT_TYPES else 0
        household_id = row.get("household_id")
        labeled.append(
            LabeledRow(
                features=features,
                label=label,
                dish_name=dish.name,
                event_type=event_type,
                household_id=household_id if isinstance(household_id, str) else None,
            )
        )
    return labeled


def guard_sufficient_data(labeled: list[LabeledRow]) -> None:
    """Refuses (raises InsufficientDataError, never returns a partial/fabricated "fit") if the
    labeled dataset cannot responsibly be fit: zero rows, or every row sharing the same label
    (no real accept/dislike contrast to learn from). Callers (train_pref_model.py) must let this
    propagate — never catch-and-fit-anyway."""
    if len(labeled) == 0:
        raise InsufficientDataError(
            "No real, non-ambiguous labeled rows found in the feedback export — refusing to fit. "
            "This is the expected state today (0 production feedback_events rows); this pipeline "
            "must never fabricate a training set to work around that."
        )
    labels = {row.label for row in labeled}
    if len(labels) < 2:
        raise InsufficientDataError(
            f"Only one label class ({labels}) present in {len(labeled)} real labeled row(s) — "
            "logistic regression needs both accept/like AND dislike examples to learn a real "
            "contrast; refusing to fit a single-class model rather than silently producing a "
            "constant, meaningless artifact."
        )


def check_training_readiness(
    labeled: list[LabeledRow], min_events: int, min_households: int
) -> None:
    """The density-level readiness gate WP-14 explicitly left unset ("flagged for the Founder, not
    guessed") — separate from guard_sufficient_data's CORRECTNESS-only checks above (zero rows /
    single label class), which this never replaces or loosens; both must pass. Raises
    InsufficientDataError (never returns a partial ok) when either count is below its
    `training_readiness` config threshold (pref_model.yaml, read via
    CONFIG.pref_training_min_events/pref_training_min_households).

    Every row must carry household_id when min_households is positive. Missing provenance cannot
    prove fleet diversity and would also prevent household-isolated holdout evaluation."""
    n_events = len(labeled)
    if n_events < min_events:
        raise InsufficientDataError(
            f"Only {n_events} real labeled row(s) available, below the configured "
            f"training_readiness.min_real_events={min_events} — refusing to train an artifact "
            "this thin. This is an engineering-readiness gate (is there enough signal to trust a "
            "fit at all), separate from guard_sufficient_data's structural checks."
        )
    rows_without_household = sum(row.household_id is None for row in labeled)
    if min_households > 0 and rows_without_household:
        raise InsufficientDataError(
            f"{rows_without_household} of {n_events} labeled row(s) have no household_id — "
            "refusing to bypass household-diversity and leakage checks with incomplete provenance."
        )
    household_ids = {row.household_id for row in labeled if row.household_id is not None}
    n_households = len(household_ids)
    if n_households < min_households:
        raise InsufficientDataError(
            f"Only {n_households} distinct household(s) contributed the {n_events} real labeled "
            f"row(s) available, below the configured training_readiness.min_households="
            f"{min_households} — refusing to train on signal this concentrated (a fit dominated "
            "by a handful of households' taste isn't a fleet-wide preference model)."
        )
