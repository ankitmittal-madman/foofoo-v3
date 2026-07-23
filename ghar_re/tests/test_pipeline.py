"""
End-to-end tests: run the golden households through the full Ghar RE v1.0 pipeline and assert
the behaviours the Core Spine / D1-D7 / Final_RE / KB require (Task 4).
"""
import pytest

from ghar_re import fixtures as F
from ghar_re import knowledge as K
from ghar_re import scoring as S
from ghar_re import pairing as P
from ghar_re.catalogue import Catalogue
from ghar_re.derivation import derive_theta
from ghar_re.pipeline import recommend, make_context

CAT = Catalogue()
HH = {h["id_key"]: h for h in F.HOUSEHOLDS}
CARB_SET = {"Roti", "Paratha", "Poori", "Rice"}


def _run(id_key, **ctx_kw):
    hh = HH[id_key]
    ctx = make_context(**ctx_kw)
    return recommend(hh, ctx, CAT)


def _all_default_runs():
    return {k: _run(k, slot="dinner", season="transitional") for k in HH}


# ---------------------------------------------------------------------------
# 1. each household gets exactly 7 ranked plates, sorted by plate_score desc
# ---------------------------------------------------------------------------
def test_each_household_gets_exactly_7_plates():
    for k, res in _all_default_runs().items():
        assert len(res["plates"]) == 7, f"{k} got {len(res['plates'])} plates"
        scores = [p["score"] for p in res["plates"]]
        assert scores == sorted(scores, reverse=True), f"{k} plates not rank-sorted"


# ---------------------------------------------------------------------------
# 2. no duplicate hero dish within one household's 7 plates
# ---------------------------------------------------------------------------
def test_no_duplicate_hero_within_seven():
    for k, res in _all_default_runs().items():
        heroes = [h for p in res["plates"] for h in p["heroes"]]
        assert len(heroes) == len(set(heroes)), f"{k} has a duplicate hero: {heroes}"


# ---------------------------------------------------------------------------
# 3. a Jain household never receives a jain_compatible=N dish
# ---------------------------------------------------------------------------
def test_jain_household_never_gets_non_jain():
    res = _run("jain_couple_ahmedabad", slot="dinner", season="transitional")
    assert res["theta"]["is_jain"]["value"] is True
    for p in res["plates"]:
        for d in P._plate_dishes(p):
            assert d.jain_compatible == "Y", f"Jain household got non-Jain dish {d.name}"
        # support is an abstract editable carb from {Roti,Paratha,Poori,Rice} (§S4.4) — all plain
        # and inherently Jain-safe (no onion/garlic/root).
        if p.get("support"):
            assert p["support"] in CARB_SET


# ---------------------------------------------------------------------------
# 4. a pure-veg household never receives a non_veg (or egg) dish
# ---------------------------------------------------------------------------
def test_pure_veg_never_gets_non_veg():
    for k in ("joint_family_elders_delhi", "couple_delhi_north", "couple_mumbai_mh"):
        res = _run(k, slot="dinner", season="transitional")
        assert res["theta"]["diet"]["value"] == "veg"
        for p in res["plates"]:
            for d in P._plate_dishes(p):
                assert d.diet == "veg", f"{k} veg household got {d.diet} dish {d.name}"


# ---------------------------------------------------------------------------
# 5. the weaning-present household's plates respect the spice/texture floor (A4)
# ---------------------------------------------------------------------------
def test_weaning_household_respects_a4_floor():
    hh = HH["couple_toddler_pune"]
    theta = derive_theta(hh)
    assert theta["weaning_present"]["value"] is True
    ctx = make_context(slot="dinner", season="transitional")
    res = recommend(hh, ctx, CAT)
    for p in res["plates"]:
        for d in P._plate_dishes(p):
            assert S.pass_weaning(d, theta, ctx), f"weaning floor violated by {d.name}"
            assert d.spice_level <= 1
            assert set(d.texture) & {"soft", "smooth", "fluffy", "sticky"}
            assert not (set(d.texture) & {"crunchy", "crispy", "dense", "chewy"})


# ---------------------------------------------------------------------------
# 6. a standalone dish, if selected, appears alone with NO support attached
# ---------------------------------------------------------------------------
def test_standalone_appears_alone_no_support():
    seen_standalone = False
    for k, res in _all_default_runs().items():
        for p in res["plates"]:
            if p["form"] == "standalone":
                seen_standalone = True
                assert len(p["heroes"]) == 1
                assert p.get("support") is None, f"{k}: standalone {p['hero'].name} got support"
    assert seen_standalone, "no standalone plate ever selected — sample too weak to test"


# ---------------------------------------------------------------------------
# 7. a non-standalone plate has a support/carb from the fixed set {Roti,Paratha,Poori,Rice}
# ---------------------------------------------------------------------------
def test_non_standalone_gets_valid_support():
    for k, res in _all_default_runs().items():
        for p in res["plates"]:
            if p["form"] in ("pair", "single"):
                assert p["support"] in CARB_SET, f"{k}: bad support {p['support']}"


# ---------------------------------------------------------------------------
# 8. pairing guardrails: no chosen pair violates not_both_rich / not_same_base /
#    cuisine_coherence — and these gates ARE the KB §N1 in_spine rows.
# ---------------------------------------------------------------------------
def test_pairing_guardrails_hold_on_chosen_pairs():
    for k, res in _all_default_runs().items():
        for p in res["plates"]:
            if p["form"] == "pair":
                d, l = p["dry"], p["liquid"]
                assert not P.both_rich(d, l), f"{k}: both_rich {d.name}+{l.name}"
                assert not P.same_base(d, l), f"{k}: same_base {d.name}+{l.name}"
                assert P.cuisine_dist(d, l) <= S.CONFIG.theta_region, \
                    f"{k}: cuisine incoherent {d.name}+{l.name}"
                assert P.allowed(d, l)


def test_guardrails_match_kb_negative_priors():
    # The KB §N1 in_spine=yes structural rows must be exactly the pairing hard gates we enforce.
    active_structural = {
        n[0] for n in K.NEGATIVE_PRIORS
        if n[3] and n[5] == "active" and n[4] == "pairing_rules.yaml"
    }
    assert active_structural == {
        "two rich/creamy gravies together",
        "two same-base gravies (both tomato-onion / both coconut)",
        "two dry heroes as the pair",
        "cross-region pair (Bengali + Punjabi hero)",
    }
    # the two ⚑ v2 rows must be stored but marked deferred (NOT implemented)
    deferred = {n[0] for n in K.NEGATIVE_PRIORS if n[5] == "deferred_v2"}
    assert len(deferred) == 2


# ---------------------------------------------------------------------------
# 9. Q15 gain measurably shifts ranking between Awesome Taste and Healthy Living
#    on the same eligible pool, in the expected direction.
# ---------------------------------------------------------------------------
def test_q15_shifts_ranking_expected_direction():
    hh = HH["single_professional_blr"]
    theta = derive_theta(hh)
    ctx = make_context(slot="dinner", season="transitional")
    pool = [d for d in CAT if S.eligible(d, theta, ctx) and S.m_slot(d, ctx) > 0
            and d.hero_role in ("dry", "liquid", "single", "standalone")]

    def rank(objective):
        return [d.name for d in sorted(pool, key=lambda d: S.score(d, theta, ctx, objective), reverse=True)]

    at = rank("awesome_taste")
    hl = rank("healthy_living")
    assert at != hl, "Q15 produced no ranking change"

    # direction: an indulgent dish rises under Awesome Taste; a light dish rises under Healthy Living.
    indulgent = "Chettinad Chicken"   # oily, heavy, high gs_indulgence
    light = "Rasam"                    # light, boiled, high gs_light
    assert at.index(indulgent) < hl.index(indulgent), "indulgent dish should rank higher under Awesome Taste"
    assert hl.index(light) < at.index(light), "light dish should rank higher under Healthy Living"

    # and the per-dish gain moves the right way
    pbm = CAT.get("Paneer Butter Masala")
    assert S.gain_q15(pbm, "awesome_taste") > S.gain_q15(pbm, "healthy_living")


# ---------------------------------------------------------------------------
# 10. WEATHER + KB §R3 (the most important test): inject rain for two DIFFERENT zones and assert
#     each surfaces the SPECIFIC KB-named comfort hero for THEIR zone — not a generic boosted dish.
# ---------------------------------------------------------------------------
def _rain_ranked(id_key):
    hh = HH[id_key]
    theta = derive_theta(hh)
    ctx = make_context(slot="dinner", season="monsoon", is_raining=True)
    rows = sorted(
        ((S.base(d, theta, ctx), d.name) for d in CAT
         if "rainy" in d.weather_affinity and S.eligible(d, theta, ctx)),
        reverse=True)
    return theta, [n for _, n in rows], recommend(hh, ctx, CAT)


def test_weather_north_surfaces_pakora():
    theta, ranked, res = _rain_ranked("couple_delhi_north")
    assert theta["region"]["value"] == "North"
    assert ranked[0] == "Onion Pakora", f"North rain top should be Onion Pakora, got {ranked[0]}"
    # and it actually appears in the served 7 plates
    served = {h for p in res["plates"] for h in p["heroes"]}
    assert "Onion Pakora" in served


def test_weather_west_mh_surfaces_kanda_bhaji():
    theta, ranked, res = _rain_ranked("couple_mumbai_mh")
    assert theta["region"]["value"] == "West"
    assert ranked[0] == "Kanda Bhaji", f"West-MH rain top should be Kanda Bhaji, got {ranked[0]}"
    served = {h for p in res["plates"] for h in p["heroes"]}
    assert "Kanda Bhaji" in served


def test_weather_is_zone_specific_not_generic():
    # The SAME weather must trigger DIFFERENT heroes by zone (the Strand-1 core rule).
    _, north, _ = _rain_ranked("couple_delhi_north")
    _, west, _ = _rain_ranked("couple_mumbai_mh")
    assert north[0] != west[0]
    # North's hero must beat West's hero for the North household and vice-versa
    assert north.index("Onion Pakora") < north.index("Kanda Bhaji")
    assert west.index("Kanda Bhaji") < west.index("Onion Pakora")


# ---------------------------------------------------------------------------
# 11. data_source integrity: every row in the SAMPLE dataset is 'ai_generated' or 'stub',
#     and ZERO sample rows are 'real'. (KB reference rows are a separate dataset and may be real.)
# ---------------------------------------------------------------------------
def test_sample_dataset_data_source_integrity():
    from ghar_re.seedgen import gen_golden
    import re
    sql = gen_golden()
    tags = re.findall(r"'(real|ai_generated|stub)'", sql)
    assert tags, "no data_source literals found in golden seed"
    assert "real" not in tags, "the golden SAMPLE must contain zero 'real' rows"
    assert set(tags) <= {"ai_generated", "stub"}


def test_kb_reference_verified_flag_maps_to_data_source():
    # ✓ (verified) -> real, ⚑ -> stub, for every comfort_hero_map row.
    for zone, weather, name, verified, ds in K.COMFORT_HERO_MAP:
        assert ds == ("real" if verified else "stub"), f"{name}: verified={verified} ds={ds}"
    # sig bands + zone map are transcribed authored/catalogue values -> real
    assert all(b[3] == "real" for b in K.SIG_SCORE_BANDS)
    assert all(z[3] == "real" for z in K.ZONE_MAP)


# ---------------------------------------------------------------------------
# 12. conflict-surfacing report (not pass/fail): print community_priors vs KB §C1 disagreements.
# ---------------------------------------------------------------------------
def test_community_prior_vs_kb_c1_conflict_report(capsys):
    conflicts = K.community_vs_kb_conflicts()
    print("\n=== community_priors.csv vs KB §C1 conflict report ===")
    if not conflicts:
        print("  NONE — the two sources are consistent (Punjab 'veg_leaning' ~ KB 'strongly veg(veg-lean)').")
    else:
        for c in conflicts:
            print(f"  {c['state']}: {c['kind']}  (KB={c['kb']} / CSV={c['csv']})")
    # This is a report, not an assertion on conflict count; it must simply run and surface state.
    assert isinstance(conflicts, list)
