"""
ghar_re_core.decision_log — plain-English decision logging for the Assemble-7 selection.

Wired into pairing.assemble_7() (Core Spine §S4.6), the single point in the engine where a
final 7-plate dish pool is picked from every scored candidate plate for one household+context.
This is the concrete "class plan -> dish pool" decision referred to by the repository's
household -> cohort -> class plan -> dish pool philosophy (CLAUDE.md, Repository Philosophy):
logs which plates were served, the closest alternatives that were passed over and why, and a
short plain-English reasoning string — the non-technical reader's window into "why did the app
recommend these seven plates" without reading scoring.py or pairing.py.

Uses Python's stdlib `logging` module only (no new dependency), one JSON object per line — the
same structured-JSON convention ghar_re_service/lifecycle.py already uses for log_event(). This
module has NO service/handler configuration of its own: ghar_re_core stays a pure domain package
with zero I/O opinions. Whatever process hosts it (ghar_re_service today, in-process test runs,
a future CLI) attaches handlers to the "ghar_re_core.decision" logger name if it wants to see
output; with no handler attached, calls here are inert (Python's standard "logging is a no-op
until configured" behaviour) and never raise.

LOGGING-ONLY, non-negotiable: this module must never influence scoring, ranking, filtering, or
the plates returned by assemble_7 — it only ever *reads* the already-decided result. See the
call site in pairing.assemble_7 for the one-line wiring and its own comment confirming this.
"""

from __future__ import annotations

import json
import logging

LOG = logging.getLogger("ghar_re_core.decision")

# How many passed-over alternatives to include per decision — enough for a human to sanity-check
# "why not the next best plate" without dumping every rejected candidate (there can be dozens).
_MAX_ALTERNATIVES = 5


def _plate_label(p) -> str:
    # Imported lazily (not at module top) to avoid a circular import: pairing.py imports this
    # module at top level to make the one-line call at the end of assemble_7.
    from ghar_re_core.pairing import plate_label

    return plate_label(p)


def build_decision_trace(
    household_label, ctx, objective, all_plates, chosen, funnel=None, theta=None, idf=None
) -> dict:
    """Build the decision-trace dict for one Assemble-7 decision — the same payload
    log_assemble7_decision below writes to the logger, but returned directly so a caller (e.g.
    pipeline.recommend()) can include it in an API response regardless of whether any logging
    handler is attached. Pure function: reads `all_plates`/`chosen`/`funnel`, never mutates them
    and never influences what was already decided.

    household_label: household["label"] from the fixtures/request, or None if unavailable.
    ctx: the context dict (slot/season/weekday/... ) passed into assemble_7.
    objective: the resolved q15_objective string driving GAIN_Q15 weighting.
    all_plates: every candidate plate build_plates() scored, each already carrying 'score',
        'heroes', and 'experimental' — NOT yet filtered by the no-duplicate/discovery rules.
    chosen: the final list of plates actually served, already sorted best-first.
    funnel: optional pre-computed scoring.eligibility_funnel() result (stage-by-stage dish
        counts); included as-is under "funnel" when supplied, omitted entirely if None.
    """
    chosen_heroes: set = set()
    for p in chosen:
        chosen_heroes |= p["heroes"]

    winners = []
    for i, plate in enumerate(chosen, 1):
        winner = {"rank": i, "plate": _plate_label(plate), "score": round(plate["score"], 4)}
        if "_selection_score" in plate:
            winner["selection_score"] = round(plate["_selection_score"], 6)
            winner["historical_similarity"] = round(plate.get("_historical_similarity", 0.0), 6)
        winners.append(winner)
    # Additive-only, per-winner structured explanation (eligibility/rejected-filters, BASE
    # contributors, Q15 contribution, weather contribution, pairing contribution) — the six
    # categories the Founder-directed RE compliance review (2026-08) requires be explainable.
    # Only computed when the caller supplies theta+idf (assemble_7 does, whenever with_trace=True);
    # omitted from `winners[i]` entirely otherwise, so this never changes trace shape for a caller
    # that doesn't opt in.
    if theta is not None and idf is not None:
        from ghar_re_core import scoring as _S
        from ghar_re_core.pairing import _plate_dishes, explain_pairing

        for i, p in enumerate(chosen):
            dishes = _plate_dishes(p)
            explanation = {"dishes": [_S.explain_dish(d, theta, ctx, objective) for d in dishes]}
            if p["form"] == "pair":
                explanation["pairing"] = explain_pairing(p["dry"], p["liquid"], idf)
            winners[i]["explanation"] = explanation

    # Alternatives: the highest-scoring candidates that did NOT make it into the served set,
    # each with the concrete reason it lost (mirrors the actual guards in pairing.assemble_7).
    chosen_ids = {id(p) for p in chosen}
    passed_over = [p for p in all_plates if id(p) not in chosen_ids]
    passed_over.sort(key=lambda p: p["score"], reverse=True)

    alternatives = []
    for p in passed_over[:_MAX_ALTERNATIVES]:
        if p["heroes"] & chosen_heroes:
            reason = "hero dish already used in a served plate (no-duplicate guard, §S4.6)"
        elif p.get("experimental"):
            reason = "discovery-dial cap reached for experimental/exploratory plates (§S4.6)"
        else:
            reason = "scored lower than the plates that were served"
        alternatives.append(
            {
                "plate": _plate_label(p),
                "score": round(p["score"], 4),
                "why_it_lost": reason,
            }
        )

    if winners:
        ranking_basis = (
            "post-eligibility adaptive diversity reranking over plate_score"
            if any("_selection_score" in plate for plate in chosen)
            else "plate_score (BASE x GAIN_Q15, pairing-adjusted)"
        )
        reasoning = (
            f"Served {len(chosen)} plate(s) for "
            f"{household_label or 'household'} ({ctx.get('slot', 'unknown slot')}, "
            f"objective={objective}), ranked by {ranking_basis}. Top choice: {winners[0]['plate']} "
            f"(score {winners[0]['score']})."
        )
    else:
        reasoning = (
            f"No plates could be served for {household_label or 'household'} — no eligible "
            f"candidates passed the hard filters/pairing gates for this context."
        )

    trace = {
        "event": "re.assemble7_decision",
        "household": household_label,
        "slot": ctx.get("slot"),
        "objective": objective,
        "winners": winners,
        "alternatives_considered": alternatives,
        "reasoning": reasoning,
    }
    if funnel is not None:
        trace["funnel"] = funnel
    return trace


def log_assemble7_decision(
    household_label, ctx, objective, all_plates, chosen, funnel=None
) -> None:
    """Log one Assemble-7 decision via build_decision_trace() above. Call AFTER assemble_7 has
    already picked `chosen` from `all_plates`. A no-op unless a handler is attached to the
    "ghar_re_core.decision" logger (Python's standard "logging is a no-op until configured"
    behaviour) — see the module docstring. Arguments match build_decision_trace()."""
    if not LOG.isEnabledFor(logging.INFO):
        return  # skip building the payload entirely when nobody is listening
    trace = build_decision_trace(household_label, ctx, objective, all_plates, chosen, funnel)
    LOG.info(json.dumps(trace, default=str))
