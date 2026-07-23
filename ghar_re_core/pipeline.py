"""
ghar_re.pipeline — end-to-end orchestration of the Ghar RE v1.0 rebuild.

    raw Q1-Q15  ->  D1-D7 derivation (θ)  ->  hard filters (§S2A)  ->  BASE (§S2B) × GAIN_Q15 (§S3)
                ->  pairing guardrails + plate_score (§S4)  ->  assemble-7 + carb attach  ->  7 plates

Weather is a MOCKED injected input (no live API in v1): ctx carries weather_condition / temp_c /
is_raining, per Task 3 point 3.
"""
from ghar_re_core.config import CONFIG
from ghar_re_core.catalogue import Catalogue
from ghar_re_core.derivation import derive_theta
from ghar_re_core import pairing


def recommend(household, ctx, catalogue=None):
    """Run the full pipeline for one (household, context). Returns dict with theta + 7 plates."""
    cat = catalogue or Catalogue()
    theta = derive_theta(household)
    objective = household.get("q15_objective") or CONFIG.default_objective
    plates = pairing.assemble_7(cat, theta, ctx, objective, n=7)
    return dict(
        household=household["label"],
        theta=theta,
        objective=objective,
        plates=plates,
        versions=CONFIG.versions,
    )


def make_context(slot="dinner", season="transitional", weekday="Monday",
                 weather_condition=None, temp_c=None, is_raining=False,
                 active_modes=None, calorie_target=None):
    return dict(slot=slot, season=season, weekday=weekday,
                weather_condition=weather_condition, temp_c=temp_c, is_raining=is_raining,
                active_modes=active_modes or [], calorie_target=calorie_target)


def format_result(res):
    lines = [f"Household: {res['household']}  |  objective={res['objective']}  |  "
             f"{res['versions']['spine']} · {res['versions']['kb']} · {res['versions']['config']}",
             f"  region={res['theta']['region']['value']} blend={res['theta']['blend']['value']} "
             f"income={res['theta']['income_band']['value']} spice_ceiling={res['theta']['spice_ceiling']['value']} "
             f"jain={res['theta']['is_jain']['value']} weaning={res['theta']['weaning_present']['value']}"]
    for i, p in enumerate(res["plates"], 1):
        lines.append(f"   {i}. [{p['score']:.3f}] {pairing.plate_label(p)}")
    return "\n".join(lines)


if __name__ == "__main__":
    from ghar_re_core import fixtures as F
    cat = Catalogue()
    for hh in F.HOUSEHOLDS:
        ctx = make_context(slot="dinner", season="transitional")
        print(format_result(recommend(hh, ctx, cat)))
        print()
