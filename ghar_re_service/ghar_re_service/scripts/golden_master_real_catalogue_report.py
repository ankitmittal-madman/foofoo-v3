"""
Phase G Task 3b — golden-master regression report: 39-dish fixtures vs the real 810-dish
catalogue, for the same fixed household+context cases test_golden_master.py locks.

NOT a pass/fail gate (there is no golden file to compare the real-catalogue run against — the
39-dish golden JSONs are, by design, locked to the 39-dish pool). This is a reporting script:
run the same GOLDEN_CASES through both catalogues and print exactly what differs and why,
so a pool-size change (39 -> 810 dishes) is distinguishable from an actual scoring bug.

Lives in ghar_re_service (not ghar_re_core/tests) because it needs build_catalogue.py — putting
it under ghar_re_core would have ghar_re_core import from ghar_re_service, inverting the repo's
own dependency direction (ghar_re_service depends on ghar_re_core, never the reverse).

Usage: python -m ghar_re_service.scripts.golden_master_real_catalogue_report
"""

from __future__ import annotations

from typing import cast

from ghar_re_core import fixtures as F
from ghar_re_core.catalogue import Catalogue
from ghar_re_core.pipeline import make_context, recommend
from ghar_re_core.tests.test_golden_master import GOLDEN_CASES, _canonicalize, _load_golden
from ghar_re_service.scripts.build_catalogue import build_catalogue

HH = {h["id_key"]: h for h in F.HOUSEHOLDS}


def _plate_summary(p: dict) -> dict:
    hero = p.get("hero")
    dry = p.get("dry")
    liquid = p.get("liquid")
    return {
        "form": p["form"],
        "hero_dish": hero.name if hero else None,
        "dry": dry.name if dry else None,
        "liquid": liquid.name if liquid else None,
        "score": round(p["score"], 4),
    }


def main() -> None:
    fixture_cat = Catalogue()  # 39-dish golden sample (default)
    real_dishes, build_report = build_catalogue()
    real_cat = Catalogue(real_dishes)
    sig_none_names = {d["name"] for d in real_dishes if d["sig_band"] is None}

    print(f"Fixture catalogue: {len(fixture_cat.dishes)} dishes")
    print(
        f"Real catalogue:    {len(real_cat.dishes)} dishes "
        f"({len(sig_none_names)} with sig_band=None, "
        f"{len(real_cat.dishes) - len(sig_none_names)} KB-matched)"
    )
    print()

    print("=== Baseline: 39-dish fixture run vs committed golden JSON ===")
    baseline_pass = 0
    baseline_fail = 0
    for id_key, ctx_kw in GOLDEN_CASES.items():
        ctx = make_context(**cast(dict, ctx_kw))
        actual = _canonicalize(recommend(HH[id_key], ctx, fixture_cat))
        expected = _load_golden(id_key)
        if actual == expected:
            baseline_pass += 1
            print(f"  [PASS] {id_key}: exact match, no drift")
        else:
            baseline_fail += 1
            print(
                f"  [FAIL] {id_key}: MISMATCH vs committed golden — this would be a real "
                f"scoring regression, independent of the Phase G catalogue swap"
            )
    print(
        f"  -> {baseline_pass} passed, {baseline_fail} failed "
        f"(out of {len(GOLDEN_CASES)} household+context cases)"
    )
    print()

    print("=== Real 810-dish catalogue run: same household+context cases ===")
    exercised_sig_none: set[tuple[str, int, str, str]] = set()
    total_dish_slots = 0
    for id_key, ctx_kw in GOLDEN_CASES.items():
        ctx = make_context(**cast(dict, ctx_kw))
        res_fixture = recommend(HH[id_key], ctx, fixture_cat)
        res_real = recommend(HH[id_key], ctx, real_cat)

        print(f"\n--- {id_key} ({ctx_kw}) ---")
        fixture_plates = [_plate_summary(p) for p in res_fixture["plates"]]
        real_plates = [_plate_summary(p) for p in res_real["plates"]]
        if len(fixture_plates) != len(real_plates):
            print(
                f"  *** PLATE COUNT DIFFERS: fixture={len(fixture_plates)} "
                f"real={len(real_plates)} -- flagged below, not silently ignored ***"
            )
        for i, (fp, rp) in enumerate(zip(fixture_plates, real_plates, strict=False)):
            same_form = fp["form"] == rp["form"]
            same_hero = fp["hero_dish"] == rp["hero_dish"]
            print(
                f"  plate {i}: fixture form={fp['form']!r} hero={fp['hero_dish']!r} "
                f"score={fp['score']}  |  real form={rp['form']!r} hero={rp['hero_dish']!r} "
                f"score={rp['score']}" + ("" if (same_form and same_hero) else "  <-- DIFFERS")
            )
            for slot_name in ("hero_dish", "dry", "liquid"):
                name = rp[slot_name]
                total_dish_slots += 1 if name else 0
                if name in sig_none_names:
                    exercised_sig_none.add((id_key, i, slot_name, name))

    print()
    print("=== sig_band=None fix: how often was it actually exercised ===")
    print(
        f"  {len(exercised_sig_none)} of {total_dish_slots} served dish-slots (hero/dry/liquid, "
        f"across all {len(GOLDEN_CASES)} households' plates) were filled by a dish with "
        f"sig_band=None -- i.e. a dish that would have raised KeyError without the Task 3a fix."
    )
    for id_key, plate_idx, slot_name, name in sorted(exercised_sig_none):
        print(f"    {id_key} plate {plate_idx} [{slot_name}]: {name!r}")


if __name__ == "__main__":
    main()
