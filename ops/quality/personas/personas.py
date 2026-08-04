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
    user_type: str = "synthetic"         # real inputs must use a pseudonymous test-user id
    source_persona_id: str | None = None  # P01-P41 when grounded in the canonical workbook


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


_PERSONA_MASTER_CSV = _REPO_ROOT / "data" / "source" / "class_first_v1" / "persona_master.csv"

# Real Indian states cycled deterministically across the CSV rows so the 41 ground-truth personas
# also exercise region coverage (the CSV itself carries no state/city column).
_STATE_CITY_CYCLE = [
    ("Delhi", "New Delhi"), ("Maharashtra", "Mumbai"), ("Karnataka", "Bengaluru"),
    ("Tamil Nadu", "Chennai"), ("West Bengal", "Kolkata"), ("Gujarat", "Ahmedabad"),
    ("Punjab", "Ludhiana"), ("Uttar Pradesh", "Lucknow"), ("Telangana", "Hyderabad"),
    ("Kerala", "Kochi"), ("Rajasthan", "Jaipur"), ("Bihar", "Patna"),
]

_LIFECYCLE_CONDITION = {
    "diabetes": ["diabetes"], "BP/heart": ["hypertension"], "diabetes/elderly": ["diabetes"],
    "child + diabetes/elderly": ["diabetes"], "recovery": ["recovery"],
}

_NONVEG_MODE_DIET = {
    "veg_only": ("veg", []), "jain": ("veg", []), "veg_default": ("veg", []),
    "health_veg_or_default": ("veg", []), "budget_default": ("veg", []),
    "outside_nonveg": ("veg", []),
    "protein_nonveg": ("non_veg", ["chicken", "egg"]),
    "regular_nonveg": ("non_veg", ["chicken", "mutton"]),
    "seafood": ("non_veg", ["fish", "prawn"]),
    "sunday_mutton": ("non_veg", ["mutton", "chicken"]),
    "egg_only": ("eggetarian", []),
    "default": ("veg", []),
}

_STAGE_HOUSEHOLD_TYPE = {
    "single/flatmate": "flatmates", "single": "single", "flatmates": "flatmates",
    "migrant": "single",
}


def _age_from_band(band: str) -> int:
    """Return the midpoint age of a 'NN-MM' or 'NN+' age_band string (e.g. '25-38' -> 31)."""
    band = band.strip()
    if band.endswith("+"):
        return int(band[:-1]) + 5
    lo, hi = band.split("-")
    return (int(lo) + int(hi)) // 2


def _member_ages(row: dict) -> list[dict]:
    """Build q12_member_ages from a persona_master row's age_band + household_stage/lifecycle."""
    self_age = _age_from_band(row["age_band"])
    members = [{"role": "self", "age": self_age}]
    stage = row["household_stage"]
    lifecycle = row["lifecycle_health"]
    if "couple" in stage or "family" in stage or "joint" in stage:
        members.append({"role": "adult", "age": max(self_age - 2, 18)})
    if "infant" in lifecycle:
        members.append({"role": "weaning", "age": 0})
    elif "baby" in lifecycle:
        members.append({"role": "weaning", "age": 1})
    elif "toddler" in lifecycle:
        members.append({"role": "toddler", "age": 2})
    elif "school kids" in lifecycle:
        members.append({"role": "child", "age": 9})
    elif "teen" in lifecycle:
        members.append({"role": "teen", "age": 15})
    if "elder" in stage or "elderly" in lifecycle or "elderly" in stage:
        members.append({"role": "senior", "age": 70})
    if "child" in lifecycle and "diabet" in lifecycle:
        members.append({"role": "child", "age": 8})
        members.append({"role": "senior", "age": 72})
    return members


def real_persona_derived() -> list[Persona]:
    """Translate the 41 ground-truth personas (P01-P41) from persona_master.csv into request-
    contract Personas (Q1-Q15 fields), so the roster is grounded in real cohort/persona design
    data rather than invented households. Region is cycled deterministically since the CSV itself
    carries no state/city column.
    """
    import csv

    out: list[Persona] = []
    with _PERSONA_MASTER_CSV.open(encoding="utf-8") as fh:
        for i, row in enumerate(csv.DictReader(fh)):
            state, city = _STATE_CITY_CYCLE[i % len(_STATE_CITY_CYCLE)]
            diet, nonveg_types = _NONVEG_MODE_DIET.get(row["nonveg_mode"], ("veg", []))
            is_jain = row["nonveg_mode"] == "jain" or "Jain" in row["lifecycle_health"]
            conditions = _LIFECYCLE_CONDITION.get(row["lifecycle_health"], [])
            household_type = _STAGE_HOUSEHOLD_TYPE.get(
                row["household_stage"],
                "couple_kids_parents" if "joint" in row["household_stage"]
                or "overlap" in row["household_stage"]
                else "couple_kids" if any(
                    tok in row["household_stage"] for tok in ("toddler", "kids", "teens", "infant", "baby")
                ) else "couple",
            )
            forbid: tuple[str, ...] = ("non_veg",) if diet in ("veg",) else ()
            household = {
                "q1_household_type": household_type, "q2_working_professionals": 1,
                "q3_home_state": state, "q4_current_city": city,
                "q5_diet": diet, "q6_nonveg_types": nonveg_types, "q7_veg_days": [],
                "q8_is_jain": is_jain, "q9_allergies": [], "q11_conditions": conditions,
                "q12_member_ages": _member_ages(row), "q13_who_cooks": "self",
                "q14_eat_out_per_week": 2, "q15_objective": "healthy_living",
            }
            out.append(Persona(
                key=f"real_{row['persona_id'].lower()}", label=row["persona_name"],
                household=household, context=_default_context(), forbid_diet=forbid,
                note=f"derived from persona_master {row['persona_id']} ({row['sub_cohort_label']})",
                source_persona_id=row["persona_id"],
            ))
    return out


# (household-declared allergen_type token, real ingredient-name token to verify exclusion against)
# — pass_allergen() (ghar_re_core/scoring.py) matches q9_allergies literally against each dish
# ingredient's `allergen_type` in data/source/ingredients_v5.csv (e.g. "peanut" -> allergen_type
# "peanuts", "egg" -> allergen_type "egg_allergen"), which is NOT the same string as the
# ingredient's own name; the black-box check below instead greps served ingredient NAMES. Both
# halves must be pulled from the real ingredient master, or the persona silently tests nothing.
_ALLERGY_TOKENS = (
    ("peanuts", "peanut"), ("dairy", "paneer"), ("gluten", "wheat_flour"),
    ("shellfish", "prawns"), ("egg_allergen", "egg"), ("soy", "soy_sauce"),
    ("sesame", "sesame_seeds"),
)
_UNCOVERED_STATES = [
    ("Rajasthan", "Jaipur"), ("Kerala", "Kochi"), ("Telangana", "Hyderabad"),
    ("Odisha", "Bhubaneswar"), ("Assam", "Guwahati"), ("Haryana", "Gurugram"),
    ("Madhya Pradesh", "Bhopal"), ("Jharkhand", "Ranchi"),
]


def adversarial_personas() -> list[Persona]:
    """Boundary/adversarial personas closing gaps the golden + persona_master sets don't cover:
    every allergen x diet combination, wider region coverage, extreme household shapes, multi-
    allergy households, additional malformed-payload variants, and additional impossible-combo
    resolutions. Behavioural expectations only (Phase 8 black-box rule) — no score assertions.
    """
    out: list[Persona] = []

    # 1) Allergen x diet matrix (14): every allergy token, once veg once non_veg.
    for declare_tok, check_tok in _ALLERGY_TOKENS:
        for diet, nonveg_types in (("veg", []), ("non_veg", ["chicken", "fish"])):
            out.append(Persona(
                key=f"allergy_{declare_tok}_{diet}", label=f"{diet} household allergic to {declare_tok}",
                household={
                    "q1_household_type": "couple", "q2_working_professionals": 2,
                    "q3_home_state": "Karnataka", "q4_current_city": "Bengaluru",
                    "q5_diet": diet, "q6_nonveg_types": nonveg_types, "q7_veg_days": [],
                    "q8_is_jain": False, "q9_allergies": [declare_tok], "q11_conditions": [],
                    "q12_member_ages": [{"role": "self", "age": 33}, {"role": "adult", "age": 31}],
                    "q13_who_cooks": "self", "q14_eat_out_per_week": 2, "q15_objective": "awesome_taste",
                },
                context=_default_context(),
                forbid_diet=("non_veg",) if diet == "veg" else (),
                forbid_ingredients=(check_tok,),
                note="allergen x diet matrix coverage",
            ))

    # 2) Wider region coverage (8): one household per otherwise-uncovered state, diet alternating.
    for i, (state, city) in enumerate(_UNCOVERED_STATES):
        diet = "veg" if i % 2 == 0 else "non_veg"
        out.append(Persona(
            key=f"region_{state.lower().replace(' ', '_')}", label=f"Household in {city}, {state}",
            household={
                "q1_household_type": "couple", "q2_working_professionals": 1,
                "q3_home_state": state, "q4_current_city": city,
                "q5_diet": diet, "q6_nonveg_types": ["chicken"] if diet == "non_veg" else [],
                "q7_veg_days": [], "q8_is_jain": False, "q9_allergies": [], "q11_conditions": [],
                "q12_member_ages": [{"role": "self", "age": 35}, {"role": "adult", "age": 33}],
                "q13_who_cooks": "self", "q14_eat_out_per_week": 1, "q15_objective": "healthy_living",
            },
            context=_default_context(), forbid_diet=("non_veg",) if diet == "veg" else (),
            note="region coverage gap-fill",
        ))

    # 3) Extreme household shapes (4): large joint family (veg/non_veg) + solo elder (veg/non_veg).
    for diet, nonveg_types in (("veg", []), ("non_veg", ["chicken", "mutton"])):
        out.append(Persona(
            key=f"large_joint_family_{diet}", label=f"Large 3-generation joint family ({diet})",
            household={
                "q1_household_type": "couple_kids_parents", "q2_working_professionals": 2,
                "q3_home_state": "Uttar Pradesh", "q4_current_city": "Lucknow",
                "q5_diet": diet, "q6_nonveg_types": nonveg_types, "q7_veg_days": [],
                "q8_is_jain": False, "q9_allergies": [], "q11_conditions": [],
                "q12_member_ages": [
                    {"role": "senior", "age": 74}, {"role": "senior", "age": 70},
                    {"role": "adult", "age": 45}, {"role": "adult", "age": 42},
                    {"role": "teen", "age": 16}, {"role": "child", "age": 10},
                ],
                "q13_who_cooks": "family", "q14_eat_out_per_week": 1, "q15_objective": "healthy_living",
            },
            context=_default_context(), forbid_diet=("non_veg",) if diet == "veg" else (),
            note="extreme household size (6 members, 3 generations)",
        ))
    for diet, nonveg_types in (("veg", []), ("non_veg", ["chicken"])):
        out.append(Persona(
            key=f"solo_elder_{diet}", label=f"Solo elder living alone ({diet})",
            household={
                "q1_household_type": "single", "q2_working_professionals": 0,
                "q3_home_state": "Tamil Nadu", "q4_current_city": "Chennai",
                "q5_diet": diet, "q6_nonveg_types": nonveg_types, "q7_veg_days": [],
                "q8_is_jain": False, "q9_allergies": [], "q11_conditions": ["hypertension"],
                "q12_member_ages": [{"role": "senior", "age": 78}],
                "q13_who_cooks": "self", "q14_eat_out_per_week": 0, "q15_objective": "healthy_living",
            },
            context=_default_context(), forbid_diet=("non_veg",) if diet == "veg" else (),
            note="single-elder boundary (age 78, solo)",
        ))

    # 4) Multi-allergy households (2): 3+ simultaneous allergens. declare/check pairs from the
    # same real ingredient master used by the matrix above.
    _multi = (
        ([("peanuts", "peanut"), ("dairy", "paneer"), ("gluten", "wheat_flour")]),
        ([("shellfish", "prawns"), ("egg_allergen", "egg"), ("soy", "soy_sauce"), ("sesame", "sesame_seeds")]),
    )
    for i, pairs in enumerate(_multi):
        diet, nonveg_types = ("veg", []) if i == 0 else ("non_veg", ["fish"])
        out.append(Persona(
            key=f"multi_allergy_{i}", label=f"Household with {len(pairs)} simultaneous allergies",
            household={
                "q1_household_type": "couple", "q2_working_professionals": 1,
                "q3_home_state": "Maharashtra", "q4_current_city": "Pune",
                "q5_diet": diet, "q6_nonveg_types": nonveg_types, "q7_veg_days": [],
                "q8_is_jain": False, "q9_allergies": [p[0] for p in pairs], "q11_conditions": [],
                "q12_member_ages": [{"role": "self", "age": 30}, {"role": "adult", "age": 28}],
                "q13_who_cooks": "self", "q14_eat_out_per_week": 2, "q15_objective": "awesome_taste",
            },
            context=_default_context(), forbid_diet=("non_veg",) if diet == "veg" else (),
            forbid_ingredients=tuple(p[1] for p in pairs),
            note="multi-allergen exclusion must hold simultaneously",
        ))

    # 5) Fasting/festival variants (2).
    out.append(Persona(
        key="fasting_ramzan_derived", label="Ramzan-observant non-veg household",
        household={
            "q1_household_type": "couple", "q2_working_professionals": 1,
            "q3_home_state": "Telangana", "q4_current_city": "Hyderabad",
            "q5_diet": "non_veg", "q6_nonveg_types": ["chicken", "mutton"], "q7_veg_days": [],
            "q8_is_jain": False, "q9_allergies": [], "q11_conditions": [],
            "q12_member_ages": [{"role": "self", "age": 36}, {"role": "adult", "age": 34}],
            "q13_who_cooks": "self", "q14_eat_out_per_week": 0, "q15_objective": "healthy_living",
        },
        context={**_default_context(), "fasting": True, "festival": "ramzan"}, expect_plates=None,
        note="fasting filter with non-veg household — must stay contract-valid",
    ))
    out.append(Persona(
        key="fasting_ekadashi_jain_derived", label="Ekadashi-observant Jain household",
        household={
            "q1_household_type": "couple", "q2_working_professionals": 1,
            "q3_home_state": "Gujarat", "q4_current_city": "Ahmedabad",
            "q5_diet": "veg", "q6_nonveg_types": [], "q7_veg_days": [],
            "q8_is_jain": True, "q9_allergies": [], "q11_conditions": [],
            "q12_member_ages": [{"role": "self", "age": 45}, {"role": "adult", "age": 42}],
            "q13_who_cooks": "self", "q14_eat_out_per_week": 0, "q15_objective": "healthy_living",
        },
        context={**_default_context(), "fasting": True, "festival": "ekadashi"},
        forbid_diet=("non_veg",), expect_plates=None,
        note="Jain + fasting compound constraint — must stay contract-valid",
    ))

    # 6) Impossible-combo resolutions (2): jain+dairy-allergy; egg-diet+egg-allergy.
    out.append(Persona(
        key="jain_dairy_allergy_derived", label="Jain household with dairy allergy",
        household={
            "q1_household_type": "couple", "q2_working_professionals": 2,
            "q3_home_state": "Rajasthan", "q4_current_city": "Jaipur",
            "q5_diet": "veg", "q6_nonveg_types": [], "q7_veg_days": [],
            "q8_is_jain": True, "q9_allergies": ["dairy"], "q11_conditions": [],
            "q12_member_ages": [{"role": "self", "age": 40}, {"role": "adult", "age": 38}],
            "q13_who_cooks": "self", "q14_eat_out_per_week": 1, "q15_objective": "healthy_living",
        },
        context=_default_context(), forbid_diet=("non_veg",), forbid_ingredients=("paneer",),
        expect_plates=None,
        note="jain (no root veg) + dairy allergy compound constraint must both hold; the double "
             "exclusion may legitimately shrink the pool below a full 7-plate plan",
    ))
    out.append(Persona(
        key="egg_diet_egg_allergy_derived", label="Egg-diet household with an egg allergy",
        household={
            "q1_household_type": "single", "q2_working_professionals": 1,
            "q3_home_state": "Kerala", "q4_current_city": "Kochi",
            "q5_diet": "eggetarian", "q6_nonveg_types": [], "q7_veg_days": [],
            "q8_is_jain": False, "q9_allergies": ["egg_allergen"], "q11_conditions": [],
            "q12_member_ages": [{"role": "self", "age": 27}],
            "q13_who_cooks": "self", "q14_eat_out_per_week": 3, "q15_objective": "awesome_taste",
        },
        context=_default_context(), forbid_ingredients=("egg",), expect_plates=None,
        note="contradictory q5_diet=eggetarian + egg allergy — allergen exclusion must win, may degrade",
    ))

    # 7) Additional malformed-payload variants (8): beyond the 3 already in derived_personas().
    out.append(Persona(key="negative_age_derived", label="Household with a negative member age",
        household={
            "q1_household_type": "single", "q2_working_professionals": 1,
            "q3_home_state": "Delhi", "q4_current_city": "New Delhi", "q5_diet": "veg",
            "q6_nonveg_types": [], "q7_veg_days": [], "q8_is_jain": False, "q9_allergies": [],
            "q11_conditions": [], "q12_member_ages": [{"role": "self", "age": -5}],
            "q13_who_cooks": "self", "q14_eat_out_per_week": 1, "q15_objective": "healthy_living",
        }, context=_default_context(), expect_status=422, expect_plates=None,
        note="negative age must be a clean 422"))
    out.append(Persona(key="unknown_diet_enum_derived", label="Household with an unrecognised diet value",
        household={
            "q1_household_type": "single", "q2_working_professionals": 1,
            "q3_home_state": "Delhi", "q4_current_city": "New Delhi", "q5_diet": "carnivore",
            "q6_nonveg_types": [], "q7_veg_days": [], "q8_is_jain": False, "q9_allergies": [],
            "q11_conditions": [], "q12_member_ages": [{"role": "self", "age": 30}],
            "q13_who_cooks": "self", "q14_eat_out_per_week": 1, "q15_objective": "healthy_living",
        }, context=_default_context(), expect_status=422, expect_plates=None,
        note="unrecognised enum value for q5_diet must be a clean 422"))
    out.append(Persona(key="huge_household_derived", label="Household with 20 members",
        household={
            "q1_household_type": "couple_kids_parents", "q2_working_professionals": 4,
            "q3_home_state": "Bihar", "q4_current_city": "Patna", "q5_diet": "veg",
            "q6_nonveg_types": [], "q7_veg_days": [], "q8_is_jain": False, "q9_allergies": [],
            "q11_conditions": [],
            "q12_member_ages": [{"role": "adult", "age": 30 + i} for i in range(20)],
            "q13_who_cooks": "family", "q14_eat_out_per_week": 1, "q15_objective": "healthy_living",
        }, context=_default_context(), forbid_diet=("non_veg",), expect_plates=None,
        note="extreme member count must not crash the pipeline"))
    out.append(Persona(key="zero_professionals_derived", label="Household with zero working professionals",
        household={
            "q1_household_type": "couple", "q2_working_professionals": 0,
            "q3_home_state": "Delhi", "q4_current_city": "New Delhi", "q5_diet": "veg",
            "q6_nonveg_types": [], "q7_veg_days": [], "q8_is_jain": False, "q9_allergies": [],
            "q11_conditions": [], "q12_member_ages": [{"role": "self", "age": 60}, {"role": "adult", "age": 58}],
            "q13_who_cooks": "self", "q14_eat_out_per_week": 0, "q15_objective": "healthy_living",
        }, context=_default_context(), forbid_diet=("non_veg",),
        note="zero working professionals must not crash the pipeline"))
    out.append(Persona(key="centenarian_derived", label="Household with a 100-year-old member",
        household={
            "q1_household_type": "couple_kids_parents", "q2_working_professionals": 1,
            "q3_home_state": "Punjab", "q4_current_city": "Ludhiana", "q5_diet": "veg",
            "q6_nonveg_types": [], "q7_veg_days": [], "q8_is_jain": False, "q9_allergies": [],
            "q11_conditions": [],
            "q12_member_ages": [{"role": "adult", "age": 45}, {"role": "senior", "age": 100}],
            "q13_who_cooks": "self", "q14_eat_out_per_week": 0, "q15_objective": "healthy_living",
        }, context=_default_context(), forbid_diet=("non_veg",),
        note="extreme age boundary (100) must not crash the pipeline"))
    out.append(Persona(key="daily_eat_out_derived", label="Household eating out every day of the week",
        household={
            "q1_household_type": "single", "q2_working_professionals": 1,
            "q3_home_state": "Maharashtra", "q4_current_city": "Mumbai", "q5_diet": "non_veg",
            "q6_nonveg_types": ["chicken"], "q7_veg_days": [], "q8_is_jain": False, "q9_allergies": [],
            "q11_conditions": [], "q12_member_ages": [{"role": "self", "age": 26}],
            "q13_who_cooks": "self", "q14_eat_out_per_week": 7, "q15_objective": "awesome_taste",
        }, context=_default_context(),
        note="max eat_out_per_week boundary must not crash the pipeline"))
    out.append(Persona(key="five_children_derived", label="Household with 5 children of different ages",
        household={
            "q1_household_type": "couple_kids", "q2_working_professionals": 2,
            "q3_home_state": "Uttar Pradesh", "q4_current_city": "Lucknow", "q5_diet": "veg",
            "q6_nonveg_types": [], "q7_veg_days": [], "q8_is_jain": False, "q9_allergies": [],
            "q11_conditions": [],
            "q12_member_ages": [{"role": "adult", "age": 38}, {"role": "adult", "age": 36},
                                 {"role": "weaning", "age": 1}, {"role": "toddler", "age": 3},
                                 {"role": "child", "age": 7}, {"role": "child", "age": 10},
                                 {"role": "teen", "age": 14}],
            "q13_who_cooks": "family", "q14_eat_out_per_week": 1, "q15_objective": "healthy_living",
        }, context=_default_context(), forbid_diet=("non_veg",),
        note="wide simultaneous age-safety-floor spread (weaning to teen) must not crash the pipeline"))
    out.append(Persona(key="duplicate_allergy_entries_derived", label="Household with duplicate allergy entries",
        household={
            "q1_household_type": "single", "q2_working_professionals": 1,
            "q3_home_state": "Karnataka", "q4_current_city": "Bengaluru", "q5_diet": "veg",
            "q6_nonveg_types": [], "q7_veg_days": [], "q8_is_jain": False,
            "q9_allergies": ["peanuts", "peanuts", "peanuts"], "q11_conditions": [],
            "q12_member_ages": [{"role": "self", "age": 29}],
            "q13_who_cooks": "self", "q14_eat_out_per_week": 2, "q15_objective": "awesome_taste",
        }, context=_default_context(), forbid_diet=("non_veg",), forbid_ingredients=("peanut",),
        note="duplicate allergy tokens must not break dedup/exclusion logic"))

    # 8) Objective coverage (4): one persona per Q15 objective not yet dominant in the roster,
    # each a clean veg household so only the objective varies.
    for obj in ("awesome_taste", "healthy_living", "into_fitness", "protein_calculator"):
        out.append(Persona(
            key=f"objective_{obj}_derived", label=f"Veg household with objective={obj}",
            household={
                "q1_household_type": "couple", "q2_working_professionals": 2,
                "q3_home_state": "Karnataka", "q4_current_city": "Bengaluru",
                "q5_diet": "veg", "q6_nonveg_types": [], "q7_veg_days": [],
                "q8_is_jain": False, "q9_allergies": [], "q11_conditions": [],
                "q12_member_ages": [{"role": "self", "age": 30}, {"role": "adult", "age": 28}],
                "q13_who_cooks": "self", "q14_eat_out_per_week": 2, "q15_objective": obj,
            },
            context=_default_context(), forbid_diet=("non_veg",),
            note="Q15 objective coverage gap-fill",
        ))

    return out


def all_personas() -> list[Persona]:
    """Return the full persona roster: golden (7) + derived edge cases (8) + real ground-truth
    personas translated from persona_master.csv (41) + adversarial gap-fill personas (44) = 100.
    """
    return golden_personas() + derived_personas() + real_persona_derived() + adversarial_personas()


if __name__ == "__main__":
    import json

    roster = all_personas()
    print(json.dumps(
        {"count": len(roster),
         "personas": [{"key": p.key, "label": p.label, "expect_status": p.expect_status,
                       "forbid_diet": p.forbid_diet, "note": p.note} for p in roster]},
        indent=2,
    ))
