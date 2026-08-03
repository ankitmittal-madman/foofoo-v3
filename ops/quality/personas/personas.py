"""
Phase 3 — Personas.

Two tiers, both grounded in the REAL request contract (household q1..q15 fields) so every persona
can actually be POSTed to the running service:

  * GOLDEN personas — the 7 shipped golden-sample households (ghar_re_core.fixtures.HOUSEHOLDS),
    reused verbatim so persona tests exercise the same data the engine was built against.
  * DERIVED personas — edge / boundary / malformed households constructed here to probe behaviour
    the golden set does not cover (Jain exclusion, allergy exclusion, fasting, malformed input,
    empty household, impossible combinations).

Each persona carries EXPECTATIONS expressed as behaviour, not formulas (Phase 8 black-box rule):
what the response contract must hold, which dishes must be excluded, and whether the request is
expected to succeed (200), degrade with warnings, or be rejected (422). The recsys suite asserts
against these fields; nothing here asserts a score value.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Ensure the repo root (where ghar_re_core / ghar_re_service live as top-level packages) is
# importable whether this module is run standalone or collected by pytest.
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


@dataclass
class Persona:
    """One test persona: a request household + context, plus behavioural expectations."""

    key: str
    label: str
    household: dict[str, Any]
    context: dict[str, Any] = field(default_factory=dict)
    # Expectations (behavioural, not numeric):
    expect_status: int = 200            # 200 = accepted, 422 = contract-rejected
    expect_plates: int | None = 7        # exact plate count for /v1/recommendations, or None
    forbid_diet: tuple[str, ...] = ()    # dish diet values that must NEVER appear (e.g. "non_veg")
    forbid_ingredients: tuple[str, ...] = ()  # ingredient tokens that must never appear
    expect_warnings: bool | None = None  # True=must warn, False=must not, None=don't care
    note: str = ""


def _default_context() -> dict[str, Any]:
    """A neutral dinner/monsoon context reused by personas that don't override it."""
    return {"slot": "dinner", "season": "monsoon", "weather": {"is_raining": True, "temp_c": 27}}


def golden_personas() -> list[Persona]:
    """Return personas built directly from the shipped golden-sample households.

    Reads ghar_re_core.fixtures at call time (not import time) so a missing fixtures module fails
    loudly in the suite that uses it rather than at collection of unrelated suites.
    """
    from ghar_re_core import fixtures as fx

    out: list[Persona] = []
    for hh in fx.HOUSEHOLDS:
        key = hh["id_key"]
        household = {k: v for k, v in hh.items() if k != "id_key"}
        forbid: tuple[str, ...] = ()
        # A vegetarian/jain household must never be served a non-veg dish — a hard exclusion the
        # engine is contractually required to honour, checkable without knowing any score.
        if hh.get("q5_diet") == "veg":
            forbid = ("non_veg",)
        out.append(Persona(
            key=key, label=hh.get("label", key), household=household,
            context=_default_context(), forbid_diet=forbid,
            note="golden-sample household",
        ))
    return out


def derived_personas() -> list[Persona]:
    """Return derived edge / boundary / malformed personas the golden set does not cover."""
    return [
        # Jain — hard religious exclusion. Must succeed and never serve non-veg.
        Persona(
            key="jain_strict_derived", label="Strict Jain (no onion/garlic)",
            household={
                "q1_household_type": "couple", "q2_working_professionals": 2,
                "q3_home_state": "Gujarat", "q4_current_city": "Ahmedabad",
                "q5_diet": "veg", "q7_veg_days": [], "q8_is_jain": True,
                "q9_allergies": [], "q11_conditions": [], "q12_member_ages": [{"role": "self", "age": 34}, {"role": "adult", "age": 31}],
                "q13_who_cooks": "self", "q14_eat_out_per_week": 1, "q15_objective": "healthy_living",
            },
            context=_default_context(), forbid_diet=("non_veg",),
            note="jain exclusion must hold",
        ),
        # Allergy — nut allergy must exclude peanut-bearing dishes.
        Persona(
            key="nut_allergy_derived", label="Peanut-allergic vegetarian",
            household={
                "q1_household_type": "single", "q2_working_professionals": 1,
                "q3_home_state": "Karnataka", "q4_current_city": "Bengaluru",
                "q5_diet": "veg", "q7_veg_days": [], "q8_is_jain": False,
                "q9_allergies": ["peanut"], "q11_conditions": [], "q12_member_ages": [{"role": "self", "age": 29}],
                "q13_who_cooks": "self", "q14_eat_out_per_week": 3, "q15_objective": "awesome_taste",
            },
            context=_default_context(), forbid_diet=("non_veg",),
            forbid_ingredients=("peanut",),
            note="allergen exclusion must hold",
        ),
        # Fasting context — should still return a contract-valid response (may warn / be partial).
        Persona(
            key="fasting_navratri_derived", label="Navratri fasting household",
            household={
                "q1_household_type": "couple", "q2_working_professionals": 1,
                "q3_home_state": "Maharashtra", "q4_current_city": "Pune",
                "q5_diet": "veg", "q7_veg_days": [], "q8_is_jain": False,
                "q9_allergies": [], "q11_conditions": [], "q12_member_ages": [{"role": "self", "age": 40}, {"role": "adult", "age": 38}],
                "q13_who_cooks": "self", "q14_eat_out_per_week": 0, "q15_objective": "healthy_living",
            },
            context={**_default_context(), "fasting": True, "festival": "navratri"},
            forbid_diet=("non_veg",), expect_plates=None,
            note="fasting filter may reduce pool -> partial allowed, must stay contract-valid",
        ),
        # Health condition — diabetic + hypertensive senior. Behavioural: valid response.
        Persona(
            key="diabetic_senior_derived", label="Diabetic + hypertensive senior",
            household={
                "q1_household_type": "couple", "q2_working_professionals": 0,
                "q3_home_state": "Tamil Nadu", "q4_current_city": "Chennai",
                "q5_diet": "veg", "q7_veg_days": [], "q8_is_jain": False,
                "q9_allergies": [], "q11_conditions": ["diabetes", "hypertension"],
                "q12_member_ages": [{"role": "self", "age": 68}, {"role": "adult", "age": 65}], "q13_who_cooks": "self",
                "q14_eat_out_per_week": 1, "q15_objective": "healthy_living",
            },
            context=_default_context(), forbid_diet=("non_veg",),
            note="health conditions must not break the contract",
        ),
        # Infant present — extreme age boundary; response must remain valid.
        Persona(
            key="infant_household_derived", label="Household with a 1-year-old",
            household={
                "q1_household_type": "couple_kids", "q2_working_professionals": 2,
                "q3_home_state": "Delhi", "q4_current_city": "New Delhi",
                "q5_diet": "non_veg", "q6_nonveg_types": ["chicken", "egg"], "q7_veg_days": [],
                "q8_is_jain": False, "q9_allergies": [], "q11_conditions": [],
                "q12_member_ages": [{"role": "self", "age": 32}, {"role": "adult", "age": 30}, {"role": "toddler", "age": 1}], "q13_who_cooks": "family",
                "q14_eat_out_per_week": 2, "q15_objective": "awesome_taste",
            },
            context=_default_context(), expect_plates=7,
            note="age boundary (infant) must not crash the pipeline",
        ),
        # ---- MALFORMED / NEGATIVE personas: expect 422, never a 500 ----
        Persona(
            key="empty_household_derived", label="Empty household object",
            household={}, context=_default_context(),
            expect_status=422, expect_plates=None,
            note="missing all required q-fields must be a clean 422, not a 500",
        ),
        Persona(
            key="missing_diet_derived", label="Household missing q5_diet",
            household={
                "q1_household_type": "single", "q2_working_professionals": 1,
                "q3_home_state": "Delhi", "q4_current_city": "New Delhi",
                "q7_veg_days": [], "q8_is_jain": False, "q9_allergies": [],
                "q11_conditions": [], "q12_member_ages": [{"role": "self", "age": 30}], "q13_who_cooks": "self",
                "q14_eat_out_per_week": 5, "q15_objective": "awesome_taste",
            },
            context=_default_context(), expect_status=422, expect_plates=None,
            note="dropping a single required field must be a clean 422",
        ),
        Persona(
            key="impossible_combo_derived", label="Impossible: veg + non_veg types set",
            household={
                "q1_household_type": "single", "q2_working_professionals": 1,
                "q3_home_state": "Delhi", "q4_current_city": "New Delhi",
                "q5_diet": "veg", "q6_nonveg_types": ["chicken", "mutton"],
                "q7_veg_days": [], "q8_is_jain": True, "q9_allergies": [],
                "q11_conditions": [], "q12_member_ages": [{"role": "self", "age": 30}], "q13_who_cooks": "self",
                "q14_eat_out_per_week": 0, "q15_objective": "healthy_living",
            },
            context=_default_context(), expect_status=200, forbid_diet=("non_veg",),
            expect_plates=None,
            note="contradictory input (veg diet + nonveg types) must resolve safely to veg-only, "
                 "never serve non-veg",
        ),
    ]


def all_personas() -> list[Persona]:
    """Return the full persona roster (golden + derived) used by the recsys suite."""
    return golden_personas() + derived_personas()


if __name__ == "__main__":
    import json

    roster = all_personas()
    print(json.dumps(
        {"count": len(roster),
         "personas": [{"key": p.key, "label": p.label, "expect_status": p.expect_status,
                       "forbid_diet": p.forbid_diet, "note": p.note} for p in roster]},
        indent=2,
    ))
