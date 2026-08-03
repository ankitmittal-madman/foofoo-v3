"""
generate_sig_scores_v1.py — builds sig_scores_v1.csv (KB0.2 Namespace D §S1/§S2), the file the
knowledge base itself says should exist but doesn't (confirmed absent by a repo-wide search during
the Phase G catalogue work).

WHAT THIS PRODUCES
  1. sig_scores_v1.csv         — one row per dish (all 810), written to ../sig_scores_v1.csv
                                  (i.e. data/sig_scores_v1.csv, resolving data/source/README.md's
                                  own `../sig_scores_v1.csv` config-table entry relative to this
                                  README's own directory — data/source/ — NOT the repo root).
  2. sig_scores_curation_template.csv — the 63 dishes flagged as plausible national_icon/
                                  state_icon candidates. RESOLVED (WP-21, 2026-08-03): all 63 rows
                                  in sig_scores_v1.csv have been assigned a real band (6
                                  national_icon, 23 state_icon, 34 confirmed regional_hero) via
                                  AI-researched Indian food-culture knowledge, per Founder direction
                                  that per-dish Founder review isn't feasible at this volume.
                                  status=AI_RESEARCHED (not FOUNDER_CURATED — no human has reviewed
                                  these individually; a spot-check is recommended, not a full
                                  re-review). See sig_scores_curation_template.csv's own filled-in
                                  columns for the resolved value + rationale per dish.

SCHEMA (KB0.2 §S2, exact column names, do not invent a different schema)
  dish_name, sig_score, band, evidence_confidence, coverage_confidence, owner, method, version
  (+ one extra column, status, not in the KB spec but necessary so build_catalogue.py — or
  whatever eventually reads this file — can distinguish a value a human has actually reviewed
  from a heuristic placeholder: AUTO_DRAFT vs PENDING_FOUNDER_REVIEW. Neither is FOUNDER_CURATED;
  that value doesn't appear anywhere in this file, because no row here has actually been reviewed
  by a human yet — this script only ever produces provisional data.)

CALIBRATION BANDS (KB0.2 §S1 — frozen, reproduced verbatim, never modified here)
  1.00 national_icon | 0.90 state_icon | 0.75 regional_hero
  0.60 very_common    | 0.40 common     | 0.20 utility

HEURISTIC (Task 1 — auto-draft rows). Signals inspected and what was actually usable:
  - cuisines_v4.csv `tier` (tier_1/2/3) and `is_user_facing` (Y/N): the primary signal. Every one
    of the 810 dishes' `Cuisines` value resolved against cuisines_v4.csv's `name` column (0
    unresolved — verified, unlike some other Phase G joins).
  - tags_v4.csv `tier` column, checked for a dish_category rollup: INSPECTED AND REJECTED. Every
    one of the 20 dish_category tag values (whole_meal, curry, dal_lentil, ...) is tier_1 — the
    column carries zero discriminating signal at the category level, so it contributes nothing
    and is not used.
  - dish_combo_items_v2_*.csv `role` == 'primary': a dish anchoring at least one combo as its
    named "primary" (e.g. Chole in "Chole Bhature", Rajma in "Rajma Chawal") is treated as a weak
    upward signal — only 24 of 810 catalogue dishes ever appear this way, so it's used as a
    one-band bump, never as the sole basis for a band.

  Mapping rule (cuisine tier x is_user_facing -> heuristic band, BEFORE the combo-primary bump):
    tier_1, facing=Y  -> regional_hero (0.75)   [heuristic ceiling — see cap rule below]
    tier_1, facing=N  -> very_common   (0.60)
    tier_2, facing=Y  -> very_common   (0.60)
    tier_2, facing=N  -> common        (0.40)
    tier_3, facing=Y  -> common        (0.40)
    tier_3, facing=N  -> utility       (0.20)
  Combo-primary bump: if the dish is a 'primary' role in >=1 combo, move up one band (utility ->
  common -> very_common -> regional_hero), capped at regional_hero.

  HARD CAP (per task instructions): no heuristic-assigned row may ever be national_icon (1.00) or
  state_icon (0.90) — those require real cultural/regional judgment no existing column proxies
  for. regional_hero (0.75) is the ceiling for every row this script assigns directly.

CURATION-CANDIDATE SELECTION (Task 2 — NOT a scoring rule, a "worth a Founder's look" filter)
  tier_1 AND is_user_facing='Y' AND (max region_food_affinity.csv affinity_score for that dish
  name >= 0.85, OR the dish is a 'primary' role in >=1 combo).
  This produced 63 dishes against a target of "roughly 58" (region_food_affinity's scores cluster
  at exactly 0.85 for many rows — tightening the threshold to 0.86 drops to 48, undershooting;
  0.85 was kept as the closer, more defensible match to "roughly 58"). Documented, not silently
  tuned to hit an exact number.

KNOWN LIMITATION (measured, not glossed over): 510 of 810 dishes (63%) belong to a tier_1 +
is_user_facing='Y' cuisine, and the mapping rule above sends every one of them to the same
regional_hero ceiling. This is a real property of the source data (tier_1 cuisines — Punjabi,
Tamil, Bengali, Gujarati, etc. — are simply the highest-dish-count cuisines in the catalogue), not
a rule bug, but it means the heuristic is coarse WITHIN that majority bucket: it distinguishes
cuisine-level prominence, not per-dish prominence inside a major cuisine. 514 of 810 auto-drafted
rows end up at exactly 0.75. Curating this bucket further (e.g. per-dish signals beyond what's in
today's source CSVs) is future work, not attempted here.
"""
from __future__ import annotations

import csv
import os

import openpyxl  # type: ignore[import-untyped]  # no stubs published; same as build_catalogue.py

_HERE = os.path.dirname(os.path.abspath(__file__))  # data/source
_DATA_DIR = os.path.dirname(_HERE)  # data/  (matches README.md's `../sig_scores_v1.csv`)

DISHES_XLSX = os.path.join(_HERE, "dishes.xlsx")
DISHES_SHEET = "dishes_810"
CUISINES_CSV = os.path.join(_HERE, "cuisines_v4.csv")
COMBO_ITEMS_CSV = os.path.join(_HERE, "dish_combo_items_v2_20260520.csv")
AFFINITY_CSV = os.path.join(_HERE, "region_food_affinity.csv")

OUT_SIG_SCORES = os.path.join(_DATA_DIR, "sig_scores_v1.csv")
OUT_CURATION_TEMPLATE = os.path.join(_HERE, "sig_scores_curation_template.csv")

VERSION = "KB0.2"

# KB0.2 §S1 — frozen calibration bands. Do not add, remove, or modify.
BAND_SCORE = {
    "national_icon": 1.00,
    "state_icon": 0.90,
    "regional_hero": 0.75,
    "very_common": 0.60,
    "common": 0.40,
    "utility": 0.20,
}
BAND_ORDER = ["utility", "common", "very_common", "regional_hero", "state_icon", "national_icon"]
HEURISTIC_CEILING = "regional_hero"  # hard cap — heuristic never assigns above this

AFFINITY_THRESHOLD = 0.85

SIG_SCORES_COLUMNS = [
    "dish_name", "sig_score", "band", "evidence_confidence", "coverage_confidence",
    "owner", "method", "version", "status",
]
CURATION_TEMPLATE_COLUMNS = [
    "dish_name", "suggested_band", "state_origin", "why_flagged",
    "sig_score", "evidence_confidence", "owner", "method",
]


def _read_dish_rows() -> list[dict]:
    wb = openpyxl.load_workbook(DISHES_XLSX, read_only=True, data_only=True)
    ws = wb[DISHES_SHEET]
    rows = list(ws.iter_rows(values_only=True))
    header = rows[1]  # row 1 (sheet row 2) — row 0 is blank, same quirk as build_catalogue.py
    return [dict(zip(header, r, strict=True)) for r in rows[2:] if r[1] is not None]


def _read_cuisines() -> dict[str, dict]:
    with open(CUISINES_CSV, newline="", encoding="utf-8") as fh:
        return {row["name"]: row for row in csv.DictReader(fh)}


def _read_primary_combo_dishes() -> set[str]:
    with open(COMBO_ITEMS_CSV, newline="", encoding="utf-8") as fh:
        return {row["dish_name"] for row in csv.DictReader(fh) if row["role"] == "primary"}


def _read_max_affinity() -> dict[str, float]:
    out: dict[str, float] = {}
    with open(AFFINITY_CSV, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            name = row["dish_name"]
            score = float(row["affinity_score"])
            if score > out.get(name, 0.0):
                out[name] = score
    return out


def _heuristic_band(tier: str | None, is_user_facing: str | None, is_combo_primary: bool) -> str:
    table: dict[tuple[str | None, str | None], str] = {
        ("tier_1", "Y"): "regional_hero",
        ("tier_1", "N"): "very_common",
        ("tier_2", "Y"): "very_common",
        ("tier_2", "N"): "common",
        ("tier_3", "Y"): "common",
        ("tier_3", "N"): "utility",
    }
    # unresolved cuisine (none observed in the 810-dish catalogue) -> conservative floor
    base = table.get((tier, is_user_facing), "utility")

    if is_combo_primary and base != HEURISTIC_CEILING:
        base = BAND_ORDER[min(BAND_ORDER.index(base) + 1, BAND_ORDER.index(HEURISTIC_CEILING))]
    return base


def build() -> tuple[list[dict], list[dict], list[str]]:
    """Returns (sig_scores_rows, curation_template_rows, dishes_with_no_band -- should be empty)."""
    dish_rows = _read_dish_rows()
    cuisines = _read_cuisines()
    combo_primary = _read_primary_combo_dishes()
    affinity = _read_max_affinity()

    unbandable: list[str] = []
    curation_names: set[str] = set()
    curation_rows: list[dict] = []

    for row in dish_rows:
        name = row["Dish Name"]
        cuisine = row["Cuisines"]
        cu = cuisines.get(cuisine)
        tier = cu["tier"] if cu else None
        facing = cu["is_user_facing"] if cu else None
        max_aff = affinity.get(name, 0.0)
        is_primary = name in combo_primary

        if tier == "tier_1" and facing == "Y" and (max_aff >= AFFINITY_THRESHOLD or is_primary):
            curation_names.add(name)
            why_bits = []
            if max_aff >= AFFINITY_THRESHOLD:
                why_bits.append(f"region_food_affinity={max_aff:.2f}")
            if is_primary:
                why_bits.append("combo primary role")
            suggested = _heuristic_band(tier, facing, is_primary)
            curation_rows.append({
                "dish_name": name,
                "suggested_band": f"SUGGESTION - NOT FINAL ({suggested})",
                "state_origin": cu.get("state_origin", "") if cu else "",
                "why_flagged": "tier_1 + user-facing + " + " + ".join(why_bits),
                "sig_score": "TBD",
                "evidence_confidence": "TBD",
                "owner": "TBD",
                "method": "TBD",
            })

    sig_rows: list[dict] = []
    for row in dish_rows:
        name = row["Dish Name"]
        cuisine = row["Cuisines"]
        cu = cuisines.get(cuisine)
        tier = cu["tier"] if cu else None
        facing = cu["is_user_facing"] if cu else None
        is_primary = name in combo_primary
        band = _heuristic_band(tier, facing, is_primary)
        if band not in BAND_SCORE:
            unbandable.append(name)
            continue

        is_pending_review = name in curation_names
        sig_rows.append({
            "dish_name": name,
            "sig_score": f"{BAND_SCORE[band]:.2f}",
            "band": band,
            "evidence_confidence": "Low",
            "coverage_confidence": "High",
            "owner": "Auto-derived",
            "method": (
                "catalogue heuristic (v1) - see generate_sig_scores_v1.py header for rule"
                if not is_pending_review
                else "catalogue heuristic (v1) - conservative placeholder, see "
                     "sig_scores_curation_template.csv for the founder-review candidate"
            ),
            "version": VERSION,
            "status": "PENDING_FOUNDER_REVIEW" if is_pending_review else "AUTO_DRAFT",
        })

    return sig_rows, curation_rows, unbandable


def _write_csv(path: str, columns: list[str], rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    sig_rows, curation_rows, unbandable = build()
    _write_csv(OUT_SIG_SCORES, SIG_SCORES_COLUMNS, sig_rows)
    _write_csv(OUT_CURATION_TEMPLATE, CURATION_TEMPLATE_COLUMNS, curation_rows)

    from collections import Counter
    band_counts = Counter(r["band"] for r in sig_rows)
    status_counts = Counter(r["status"] for r in sig_rows)

    print(f"Wrote {OUT_SIG_SCORES}: {len(sig_rows)} rows")
    print(f"Wrote {OUT_CURATION_TEMPLATE}: {len(curation_rows)} rows")
    print(f"Band distribution: {dict(band_counts)}")
    print(f"Status distribution: {dict(status_counts)}")
    if unbandable:
        print(f"UNBANDABLE (could not place in any band): {unbandable}")
    else:
        print("UNBANDABLE: none — every dish placed in a band.")


if __name__ == "__main__":
    main()
