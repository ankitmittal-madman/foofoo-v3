"""
End-to-end tests: run the golden households through the full Ghar RE v1.0 pipeline and assert
the behaviours the Core Spine / D1-D7 / Final_RE / KB require (Task 4).
"""

from types import SimpleNamespace

from ghar_re_core import config as cfgmod
from ghar_re_core import fixtures as F
from ghar_re_core import knowledge as K
from ghar_re_core import scoring as S
from ghar_re_core import pairing as P
from ghar_re_core import catalogue as C
from ghar_re_core.catalogue import Catalogue, _CUISINE_STATE
from ghar_re_core.derivation import derive_theta
from ghar_re_core.pipeline import recommend, make_context

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
# 4b. A1 diet filter: a 'vegan' household (no golden-sample fixture sets q5_diet='vegan' today,
# so this is a direct unit test of pass_diet/vegan_compatible, not a full pipeline run) must
# reject dairy dishes and accept a known-vegan dish, using ingredients_v5.csv's existing
# is_vegan column (previously unread anywhere in ghar_re_core).
# ---------------------------------------------------------------------------
def test_vegan_diet_filter_rejects_dairy_accepts_known_vegan_dish():
    theta = {"diet": {"value": "vegan"}, "veg_days": {"value": []}}
    ctx = {}
    dal = CAT.get("Sambar")  # veg, no dairy ingredient among its listed ingredients
    assert dal is not None
    assert dal.vegan_compatible is True
    assert S.pass_diet(dal, theta, ctx) is True

    # any golden-sample dish containing a dairy ingredient must be rejected
    dairy_dish = next(
        d
        for d in CAT
        if any(C.ingredient_info(i).get("category") == "dairy" for i in d.ingredient_names)
    )
    assert dairy_dish.vegan_compatible is False
    assert S.pass_diet(dairy_dish, theta, ctx) is False


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
# 6. A3 allergen filter catches hidden-derivative gluten carriers (SP-F13), not just explicit
#    ingredient-level allergen flags — Sambar's own ingredients carry no explicit gluten flag,
#    but its sambar_powder ingredient is a known hing-containing (wheat-carrier) spice blend.
# ---------------------------------------------------------------------------
def test_allergen_filter_catches_hidden_derivative_gluten():
    sambar = CAT.get_dish("md5:Sambar")
    assert sambar is not None, "golden-master fixture 'Sambar' missing — test fixture drifted"
    assert "sambar_powder" in sambar.ingredient_names
    assert not any(
        C.ingredient_info(ing).get("allergen_type") == "gluten" for ing in sambar.ingredient_names
    ), "test assumption broken: an ingredient now carries an explicit gluten flag"
    assert "gluten" in C.dish_allergens(sambar), (
        "hidden-derivative gluten (via sambar_powder/hing) not detected"
    )

    gluten_free_hh = {
        "allergens": {
            "value": ["gluten"],
            "confidence": "explicit",
            "reason": "explicit",
            "band": "stable",
        }
    }
    assert not S.pass_allergen(sambar, gluten_free_hh, {}), (
        "gluten-allergic household must not pass Sambar"
    )


def test_allergen_filter_normalizes_household_and_ingredient_vocabularies():
    """Profile bitfield and ingredient-master aliases must converge before the A3 hard filter."""
    peanut_dish = SimpleNamespace(name="Peanut fixture", ingredient_names=["peanut"])
    egg_dish = SimpleNamespace(name="Egg fixture", ingredient_names=["egg"])

    assert "nuts" in C.dish_allergens(peanut_dish)
    assert "egg" in C.dish_allergens(egg_dish)
    for household_token, dish in (
        ("nuts", peanut_dish),
        ("peanut", peanut_dish),
        ("peanuts", peanut_dish),
        ("egg", egg_dish),
        ("egg_allergen", egg_dish),
    ):
        theta = {
            "allergens": {
                "value": [household_token],
                "confidence": "explicit",
                "reason": "explicit",
                "band": "stable",
            }
        }
        assert not S.pass_allergen(dish, theta, {}), f"{household_token} must exclude {dish.name}"


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
# 7. a non-standalone plate gets a support unless one of its heroes is already a staple
# ---------------------------------------------------------------------------
def test_non_standalone_gets_valid_support():
    for k, res in _all_default_runs().items():
        for p in res["plates"]:
            if p["form"] in ("pair", "single"):
                has_staple_hero = any(
                    set(dish.dish_category) & {"bread", "dosa_idli", "paratha_roti", "rice"}
                    for dish in P._plate_dishes(p)
                )
                if has_staple_hero:
                    assert p["support"] is None, f"{k}: redundant support {p['support']}"
                else:
                    assert p["support"] in CARB_SET, f"{k}: bad support {p['support']}"


def test_uttapam_pair_does_not_receive_redundant_roti():
    """A fermented-crepe hero is already the staple in its plate."""
    uttapam = SimpleNamespace(name="Uttapam", dish_category=["dosa_idli"])
    saagu = SimpleNamespace(name="Saagu", dish_category=["curry"])
    plate = {"form": "pair", "dry": uttapam, "liquid": saagu}

    assert P.default_carb(plate, {"region": {"value": "West"}}) is None


# ---------------------------------------------------------------------------
# 8. pairing guardrails: no chosen pair violates not_both_rich / not_same_base /
#    cuisine_coherence — and these gates ARE the KB §N1 in_spine rows.
# ---------------------------------------------------------------------------
def test_pairing_guardrails_hold_on_chosen_pairs():
    idf = P.SIM.build_idf(CAT)
    for k, res in _all_default_runs().items():
        for p in res["plates"]:
            if p["form"] == "pair":
                d, l = p["dry"], p["liquid"]
                assert not P.both_rich(d, l), f"{k}: both_rich {d.name}+{l.name}"
                assert not P.same_base(d, l, idf), f"{k}: same_base {d.name}+{l.name}"
                assert P.cuisine_dist(d, l) <= S.CONFIG.theta_region, (
                    f"{k}: cuisine incoherent {d.name}+{l.name}"
                )
                assert P.allowed(d, l, idf)


# ---------------------------------------------------------------------------
# 8b. Founder-directed RE compliance review (2026-08): _cuis() 0.70 same-parent-cuisine tier,
# m_season()'s monsoon "0 else" branch, theta_base config, and the new explain_dish/
# explain_pairing/explain_eligibility functions. Uses the real 810-dish catalogue (not the
# golden sample) since none of the golden sample's cuisines exercise the parent-cuisine tier.
# ---------------------------------------------------------------------------
def _real_catalogue():
    import json, os

    path = os.path.normpath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "ghar_re_service",
            "data",
            "bundle",
            "catalogue.json",
        )
    )
    with open(path) as f:
        return Catalogue(json.load(f))


def test_cuis_same_parent_cuisine_tier():
    real_cat = _real_catalogue()
    d = next(d for d in real_cat if d.cuisine == "malabar")
    assert d.state_origin != "Kerala"  # confirms this dish does NOT hit the 1.00 exact-match tier
    assert S._cuis(d, "Kerala") == 0.70, (
        "malabar (parent=kerala) vs state Kerala must hit the 0.70 tier"
    )


def test_cuis_exact_state_still_beats_parent_tier():
    real_cat = _real_catalogue()
    d = next(d for d in real_cat if d.cuisine == "punjabi")
    assert S._cuis(d, "Punjab") == 1.00


def test_cuis_no_relation_is_zero():
    real_cat = _real_catalogue()
    d = next(d for d in real_cat if d.cuisine == "japanese")
    assert S._cuis(d, "Punjab") == 0.0


def test_cuis_uses_confidence_weighted_governed_regional_affinity():
    real_cat = _real_catalogue()
    dish = next(d for d in real_cat if d.cuisine == "japanese")
    dish.regional_affinities = {"madhya_pradesh": 0.72, "maharashtra": 0.54}

    assert S._cuis(dish, "Madhya Pradesh") == 0.72
    assert S._cuis(dish, "Maharashtra") == 0.54


def test_cuis_governed_affinity_never_weakens_stronger_cuisine_origin():
    real_cat = _real_catalogue()
    dish = next(d for d in real_cat if d.cuisine == "punjabi")
    dish.regional_affinities = {"punjab": 0.3}

    assert S._cuis(dish, "Punjab") == 1.0


def test_theta_base_config_matches_frozen_spec():
    # Core Spine FROZEN §S4 line 641: theta_base default 0.6.
    assert S.CONFIG.theta_base == 0.6


def test_m_season_monsoon_non_rainy_dish_scores_zero_not_neutral():
    # Core Spine FROZEN §B3 line 318: "monsoon -> +1 rainy/comfort, 0 else" — unlike summer/
    # winter, monsoon has no neutral 0.5 default.
    non_rainy = next(d for d in CAT if "rainy" not in d.weather_affinity)
    assert S.m_season(non_rainy, {"season": "monsoon"}) == 0.0


def test_m_season_monsoon_rainy_dish_scores_one():
    rainy = next(d for d in CAT if "rainy" in d.weather_affinity)
    assert S.m_season(rainy, {"season": "monsoon"}) == 1.0


def test_explain_eligibility_reports_rejected_filters():
    hh = HH["jain_couple_ahmedabad"]
    theta = derive_theta(hh)
    ctx = make_context(slot="dinner", season="transitional")
    non_jain = next(d for d in CAT if d.jain_compatible == "N")
    result = S.explain_eligibility(non_jain, theta, ctx)
    assert result["eligible"] is False
    assert "jain" in result["rejected_filters"]


def test_explain_dish_matches_live_score_computation():
    hh = HH["single_professional_blr"]
    theta = derive_theta(hh)
    ctx = make_context(slot="dinner", season="transitional")
    dish = next(d for d in CAT if S.eligible(d, theta, ctx))
    explanation = S.explain_dish(dish, theta, ctx, "awesome_taste")
    assert explanation["eligibility"]["eligible"] is True
    assert explanation["base_total"] == round(S.base(dish, theta, ctx), 4)
    assert explanation["q15_contribution"] == round(S.gain_q15(dish, "awesome_taste"), 4)
    assert explanation["weather_contribution"] == round(S.m_weather(dish, theta, ctx), 4)
    # every named BASE module from the registry must appear as a contributor
    contributor_names = {c["module"] for c in explanation["base_contributors"]}
    assert {
        "m_palette",
        "m_slot",
        "m_season",
        "sig",
        "m_age",
        "m_household",
        "m_weather",
    } <= contributor_names


def test_explain_pairing_matches_live_compat_and_gates():
    idf = P.SIM.build_idf(CAT)
    dry = next(d for d in CAT if d.hero_role == "dry")
    liquid = next(d for d in CAT if d.hero_role == "liquid")
    explanation = P.explain_pairing(dry, liquid, idf)
    assert explanation["compat_total"] == round(P.compat(dry, liquid), 4)
    assert explanation["hard_gates"]["same_base"] == P.same_base(dry, liquid, idf)


def test_plate_label_uses_single_separator_space_before_support():
    plate = {
        "form": "single",
        "hero": SimpleNamespace(name="Paneer Bhurji"),
        "support": "Roti",
    }

    assert P.plate_label(plate) == "Paneer Bhurji (+ Roti)"


def test_decision_trace_winners_carry_structured_explanations_when_requested():
    hh = HH["single_professional_blr"]
    theta = derive_theta(hh)
    ctx = make_context(slot="dinner", season="transitional")
    chosen, trace = P.assemble_7(CAT, theta, ctx, "awesome_taste", with_trace=True)
    assert len(trace["winners"]) == len(chosen)
    for winner in trace["winners"]:
        assert "explanation" in winner
        assert "dishes" in winner["explanation"]
        for dish_explanation in winner["explanation"]["dishes"]:
            assert "base_contributors" in dish_explanation
            assert "q15_contribution" in dish_explanation
            assert "weather_contribution" in dish_explanation


def test_persisted_history_reranks_complete_landing_plates_without_changing_base_scores():
    hh = HH["single_professional_blr"]
    theta = derive_theta(hh)
    baseline_ctx = {
        **make_context(slot="dinner", season="transitional"),
        "diversity_policy": "home_v2",
    }
    baseline = P.assemble_7(CAT, theta, baseline_ctx, "awesome_taste")
    top = baseline[0]
    history_ctx = {
        **baseline_ctx,
        "novelty_budget": 0.6,
        "recent_class_counts": dict.fromkeys(P._plate_classes(top), 3),
        "recent_cuisine_counts": dict.fromkeys(P._plate_cuisines(top), 2),
    }
    reranked, trace = P.assemble_7(
        CAT,
        theta,
        history_ctx,
        "awesome_taste",
        with_trace=True,
    )

    assert reranked[0]["heroes"] != top["heroes"]
    assert reranked[0]["score"] in {plate["score"] for plate in baseline}
    assert reranked[0]["_historical_similarity"] < P._plate_history_similarity(top, history_ctx)
    assert "adaptive diversity reranking" in trace["reasoning"]
    assert "selection_score" in trace["winners"][0]


def test_guardrails_match_kb_negative_priors():
    # The KB §N1 in_spine=yes structural rows must be exactly the pairing hard gates we enforce.
    active_structural = {
        n[0]
        for n in K.NEGATIVE_PRIORS
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
    pool = [
        d
        for d in CAT
        if S.eligible(d, theta, ctx)
        and S.m_slot(d, ctx) > 0
        and d.hero_role in ("dry", "liquid", "single", "standalone")
    ]

    def rank(objective):
        return [
            d.name
            for d in sorted(pool, key=lambda d: S.score(d, theta, ctx, objective), reverse=True)
        ]

    at = rank("awesome_taste")
    hl = rank("healthy_living")
    assert at != hl, "Q15 produced no ranking change"

    # direction: an indulgent dish rises under Awesome Taste; a light dish rises under Healthy Living.
    indulgent = "Chettinad Chicken"  # oily, heavy, high gs_indulgence
    light = "Rasam"  # light, boiled, high gs_light
    assert at.index(indulgent) < hl.index(indulgent), (
        "indulgent dish should rank higher under Awesome Taste"
    )
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
        (
            (S.base(d, theta, ctx), d.name)
            for d in CAT
            if "rainy" in d.weather_affinity and S.eligible(d, theta, ctx)
        ),
        reverse=True,
    )
    return theta, [n for _, n in rows], recommend(hh, ctx, CAT)


def test_weather_north_surfaces_pakora():
    theta, ranked, res = _rain_ranked("couple_delhi_north")
    assert theta["region"]["value"] == "North"
    assert ranked[0] == "Onion Pakora", f"North rain top should be Onion Pakora, got {ranked[0]}"
    # and it actually appears in the served 7 plates
    served = {h for p in res["plates"] for h in p["heroes"]}
    assert "Onion Pakora" in served


def test_weather_west_mh_surfaces_pithla():
    # RE plumbing plan §0.3: COMFORT_HERO_MAP's West-MH rain row used to read "Pithla-Bhakri"
    # (hyphenated) — a pure spelling bug against the real catalogue's "Pithla" (no "Bhakri" at
    # all) — so the comfort-hero lift silently never fired against the REAL catalogue. This
    # ghar_re_core golden-sample fixture set happens to also contain a dish literally named
    # "Kanda Bhaji" (coincidental to this small 39-dish sample, not present in the real seeded
    # catalogue — see ghar_re_core/tests/test_comfort_hero.py), which is why this test previously
    # asserted "Kanda Bhaji" won here: COMFORT_HERO_TO_DISH's old identity mapping
    # ("Kanda Bhaji" -> "Kanda Bhaji") happened to resolve in THIS fixture world even though it
    # was a no-op against the real one. Once "Kanda Bhaji" was correctly remapped to the real
    # catalogue's "Pakora (Mixed Veg)" (absent from this small fixture set) and the
    # "Pithla-Bhakri" bug was fixed to "Pithla" (present in both), "Pithla" is now the hero that
    # actually resolves and wins here — which is the CORRECT behaviour post-fix, not a regression.
    theta, ranked, res = _rain_ranked("couple_mumbai_mh")
    assert theta["region"]["value"] == "West"
    assert ranked[0] == "Pithla", f"West-MH rain top should be Pithla, got {ranked[0]}"
    served = {h for p in res["plates"] for h in p["heroes"]}
    assert "Pithla" in served


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
    from ghar_re_core.seedgen import gen_golden
    import re

    sql = gen_golden()
    tags = re.findall(r"'(real|ai_generated|stub)'", sql)
    assert tags, "no data_source literals found in golden seed"
    assert "real" not in tags, "the golden SAMPLE must contain zero 'real' rows"
    assert set(tags) <= {"ai_generated", "stub"}


def test_kb_reference_verified_flag_maps_to_data_source():
    # ✓ (verified) -> real, ⚑ -> stub, for every comfort_hero_map row.
    for _zone, _weather, name, verified, ds in K.COMFORT_HERO_MAP:
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
        print(
            "  NONE — the two sources are consistent (Punjab 'veg_leaning' ~ KB 'strongly veg(veg-lean)')."
        )
    else:
        for c in conflicts:
            print(f"  {c['state']}: {c['kind']}  (KB={c['kb']} / CSV={c['csv']})")
    # This is a report, not an assertion on conflict count; it must simply run and surface state.
    assert isinstance(conflicts, list)


# ---------------------------------------------------------------------------
# 13. sig_band=None (dish not yet KB-scored — e.g. real-catalogue dishes with no sig_scores_v1.csv
# row) must be a legitimate "no signature contribution" state, never a KeyError and never a
# fabricated band/score (Phase G Task 3a).
# ---------------------------------------------------------------------------
def test_catalogue_handles_missing_sig_band():
    unscored = dict(F.DISHES[0])
    unscored["name"] = "Unscored Test Dish"
    unscored["sig_band"] = None

    cat = Catalogue([unscored])
    dish = cat.get("Unscored Test Dish")
    assert dish.sig_score == 0.0, "sig_band=None must yield sig_score 0.0, not a fabricated band"

    # sig(dish) — the BASE §B4 term scoring.py actually reads — must also be 0.0, and base() must
    # not raise for a dish with no signature score.
    theta = derive_theta(HH["single_professional_blr"])
    ctx = make_context(slot="dinner", season="transitional")
    assert S.sig(dish) == 0.0
    S.base(dish, theta, ctx)  # must not raise


# ---------------------------------------------------------------------------
# 14. Every real cuisine (data/source/cuisines_v4.csv) must resolve to a real zone via
# K.CUISINE_GROUP_MAP -> K.ZONE_MAP. The confirmed Phase G bug was exactly a coverage gap here:
# ghar_re_core.catalogue's cuisine->cuisine_group lookup only covered fixtures.py's 10-cuisine
# list, so 536 of 810 real-catalogue dishes (66%) silently got zone=None, which pushed
# pairing.cuisine_dist()'s cuisine_coherence hard gate into its harshest fallback for most
# cross-cuisine combinations (concretely: jain_couple_ahmedabad got only 3 of 7 plates instead of
# 7). This test catches a future cuisines_v4.csv update that reintroduces an unmapped cuisine
# before it's rediscovered by hand.
# ---------------------------------------------------------------------------
def test_cuisine_zone_coverage():
    import csv
    import os

    from ghar_re_core.config import SRC

    group_zone = {z[0]: z[1] for z in K.ZONE_MAP}
    unmapped = []
    with open(os.path.join(SRC, "cuisines_v4.csv"), newline="") as fh:
        for row in csv.DictReader(fh):
            name = row["name"]
            group = K.CUISINE_GROUP_MAP.get(name)
            zone = group_zone.get(group) if group else None
            if zone is None:
                unmapped.append((name, group))
    assert unmapped == [], f"cuisines with no resolvable zone (name, cuisine_group): {unmapped}"


# ---------------------------------------------------------------------------
# 14b. Dish.state_origin: (a) a dish dict that already carries a resolved state_origin (as the
# real-catalogue build_catalogue.py now does, sourced from cuisines_v4.csv's full 65-cuisine
# table) must not be clobbered by the legacy 10-cuisine-only fixtures lookup; (b) the golden
# sample (whose dicts never set this key) must still fall back to that legacy lookup unchanged,
# so this dimension's real-catalogue-coverage fix cannot silently alter a locked golden-master score.
# ---------------------------------------------------------------------------
def test_state_origin_prefers_dict_value_but_falls_back_for_golden_sample():
    from ghar_re_core.catalogue import Dish

    raw = dict(F.DISHES[0])
    assert "state_origin" not in raw, "golden-sample fixture dict unexpectedly carries state_origin"
    d = Dish(raw)
    assert d.state_origin == _CUISINE_STATE.get(raw["cuisine"]), (
        "golden sample must use the legacy lookup"
    )

    raw2 = dict(F.DISHES[0])
    raw2["state_origin"] = "Test State"
    d2 = Dish(raw2)
    assert d2.state_origin == "Test State", (
        "an already-resolved state_origin must not be overwritten"
    )


# ---------------------------------------------------------------------------
# 15. decision_trace / funnel — recommend(with_trace=True) exposes how the catalogue narrows
# down to the 7 served plates, per household+context (the funnel logging feature).
# ---------------------------------------------------------------------------
def test_recommend_without_trace_omits_decision_trace():
    hh = HH["pure_veg_family"] if "pure_veg_family" in HH else next(iter(HH.values()))
    res = recommend(hh, make_context(slot="dinner", season="transitional"), CAT)
    assert "decision_trace" not in res, "decision_trace must be opt-in via with_trace=True"


def test_decision_trace_funnel_is_monotonically_non_increasing_and_ends_at_eligible_count():
    for k, hh in HH.items():
        ctx = make_context(slot="dinner", season="transitional")
        res = recommend(hh, ctx, CAT, with_trace=True)
        funnel = res["decision_trace"]["funnel"]
        assert funnel[0]["stage"] == "catalogue_total"
        assert funnel[0]["count"] == len(list(CAT))
        counts = [stage["count"] for stage in funnel]
        assert counts == sorted(counts, reverse=True), (
            f"{k}: funnel counts must never increase stage-to-stage"
        )

        # The funnel's last stage must agree exactly with eligible()'s own count for this
        # household+context — eligibility_funnel() must never silently drift from eligible().
        theta = derive_theta(hh)
        eligible_count = sum(1 for d in CAT if S.eligible(d, theta, ctx, shared_hero=True))
        assert funnel[-1]["count"] == eligible_count


def test_decision_trace_winners_match_served_plates():
    hh = next(iter(HH.values()))
    res = recommend(hh, make_context(slot="dinner", season="transitional"), CAT, with_trace=True)
    trace = res["decision_trace"]
    assert len(trace["winners"]) == len(res["plates"])
    assert len(trace["alternatives_considered"]) <= 5
    for alt in trace["alternatives_considered"]:
        assert alt["why_it_lost"]  # every alternative carries a concrete reason, never blank


def test_decision_trace_never_changes_which_plates_are_served():
    # LOGGING-ONLY invariant (decision_log module docstring): asking for the trace must never
    # change the actual recommendation output. Pin Phase 2 exploration's epsilon to 0 for this
    # comparison: two independent, unseeded recommend() calls run under the real (nonzero)
    # bandit_weights.yaml epsilon can each roll their own independent explore/exploit decision,
    # which would make this comparison flaky for a reason that has nothing to do with with_trace.
    orig = cfgmod.active_config().bandit
    try:
        cfgmod.active_config().bandit = {"exploration": {"epsilon": 0.0, "exploration_boost": 0.0}}
        for k, hh in HH.items():
            ctx1 = make_context(slot="dinner", season="transitional")
            ctx2 = make_context(slot="dinner", season="transitional")
            plain = recommend(hh, ctx1, CAT)
            traced = recommend(hh, ctx2, CAT, with_trace=True)
            plain_ids = [
                p["dry"].name if p["form"] == "pair" else p["hero"].name for p in plain["plates"]
            ]
            traced_ids = [
                p["dry"].name if p["form"] == "pair" else p["hero"].name for p in traced["plates"]
            ]
            assert plain_ids == traced_ids, f"{k}: with_trace changed which plates were served"
    finally:
        cfgmod.active_config().bandit = orig
