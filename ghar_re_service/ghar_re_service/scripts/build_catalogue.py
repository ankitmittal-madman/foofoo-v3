"""
ghar_re_service.scripts.build_catalogue — real 810-dish catalogue transform (Phase G Task 2).

WHAT THIS SOLVES
export_bundle.py currently bakes ghar_re_core.fixtures.DISHES (a 39-dish invented "golden sample")
into the deployable image. Phase G swaps that source for the real catalogue authored in
data/source/dishes.xlsx (sheet "dishes_810", 810 rows) while producing dish dicts in EXACTLY the
shape ghar_re_core.catalogue.Catalogue's constructor already expects (see ghar_re_core/fixtures.py
_dish() for the canonical shape). Nothing downstream (Catalogue, Dish, the scoring/pairing/
derivation modules, CatalogueProvider/ConfigProvider) changes because of this module.

THIS MODULE ONLY BUILDS THE LIST OF DISH DICTS (+ a gap report). Wiring it into export_bundle.py
was Phase G Task 1 proper — DONE (see export_bundle.py's CATALOGUE_SOURCE and
ghar_re_service/data/bundle/manifest.json, dish_count=810, catalogue_source cites this module).
This module's own docstring above ("Phase G Task 2") predates that wiring landing; kept accurate
retroactively rather than left to imply the swap is still pending.

SOURCE FILES READ (under data/source/ unless noted, resolved the same way export_bundle.py does)
  dishes.xlsx                  sheet "dishes_810" — the 810 authored dishes. NOTE: row 1 of the
                                sheet is blank; the real header is row 2 (openpyxl 0-indexed: header
                                = rows[1], data starts at rows[2]).
  ingredients_v5.csv            ingredient master: category / diet_type / allergen / jain flags.
  ingredient_aliases_v2.csv      Hindi/regional alias -> canonical ingredient name.
  cuisines_v4.csv                cuisine -> cuisine_group / state_origin / tier.
  term_synonyms_v2.csv           dish-name-level synonyms (Pani Puri / Gol Gappa / Puchka / ...).
  ../sig_scores_v1.csv           i.e. data/sig_scores_v1.csv (one level ABOVE data/source/, per
                                  data/source/README.md's own config table) — dish_name -> band,
                                  authored separately (KB0.2 §S1/§S2). See load_sig_scores().

FIELDS DERIVED, NOT SOURCED (documented per-field below — never fabricated, always flagged)
  diet              -> from ingredient diet_type: 'non_veg' if any ingredient is non_veg, else
                        'egg' if any is egg, else 'veg'. (dishes.xlsx has no diet column.)
  jain_compatible    -> 'Y' only if diet == 'veg' AND every resolved ingredient is jain-compatible
                        per ingredients_v5.csv; else 'N'. (No column in dishes.xlsx.)
  farali_compatible  -> 'Y' only if diet == 'veg' AND every resolved ingredient is farali-compatible
                        per ingredients_v5.csv's `is_farali_compatible` column (added for this fix —
                        see FARALI COMPATIBILITY below), mirroring how jain_compatible is derived.
                        Any unresolved ingredient token makes the dish False (can't verify -> not
                        claimed compatible), the same conservative stance jain_compatible already
                        takes.
  hero_role          -> BEST-EFFORT heuristic from dish_category (+ a has-protein-centre signal —
                        ANY resolved ingredient in a main-protein category OR a paneer/khoya name,
                        not just the first ingredient — for the curry/single-vs-liquid split),
                        reverse-engineered from the dish_category -> hero_role correlation observed
                        across all 39 golden-sample dishes (see _hero_role() for the exact rules).
  sig_band/sig_score -> read from ../sig_scores_v1.csv (i.e. data/sig_scores_v1.csv — one level
                        above source_dir, exactly where data/source/README.md's own config table
                        entry `../sig_scores_v1.csv` resolves), keyed on dish_name. That file was
                        authored separately (see its own generator, data/source/
                        generate_sig_scores_v1.py, on a different branch) with 747 AUTO_DRAFT rows
                        (heuristic-assigned, capped at regional_hero) and 63 PENDING_FOUNDER_REVIEW
                        rows (same heuristic band, flagged for founder attention — still a real,
                        usable value, not a placeholder to null out). Both kinds are used as-is
                        here; this module doesn't distinguish them further. A dish whose name has
                        no row in sig_scores_v1.csv even after normalization (case/whitespace)
                        gets sig_band=None and is added to report.sig_band_unmatched — see
                        _normalize_name() and load_sig_scores().
  macro              -> only 'calories' is populated (dishes.xlsx has a Calories column); every
                        other macro field (protein_g/fibre_g/fat_g/carbs_g/sugar_g/sodium_mg) is
                        left as None. No macro breakdown exists anywhere in data/source/. Nothing
                        in ghar_re_core currently reads these fields besides fixtures.py itself, so
                        None values do not break existing scoring/derivation/pairing code.

INGREDIENT RESOLUTION AND THE "INCOMPLETE ING-BLOCK" GAP
Each dish's Ingredients cell is a flat comma-separated token list. Every token is resolved against
ingredients_v5.csv's `name` column directly, then against ingredient_aliases_v2.csv's `alias`
column (case-insensitive) if the direct match fails. Tokens that resolve neither way are KEPT in
the dish's ingredient list verbatim (never dropped, never guessed at) but the dish is added to
build_report()'s `incomplete_ing_blocks` list with the exact unresolved token(s) — per the task's
explicit instruction not to silently drop the ingredient or the dish.

is_main (protein-centric vs seasoning) is NOT present anywhere in the source data either — the
golden sample hand-curated this distinction. Approximated here as:
is_main = ingredient category in MAIN_INGREDIENT_CATEGORIES, OR the ingredient is paneer/khoya (the
two protein-centric dairy items ingredients_v5.csv's plain 'dairy' category otherwise lumps in with
butter/cream/milk) — and not flagged is_common='Y'. The paneer/khoya override closes the previously
documented blind spot (a paneer curry no longer silently loses its protein classification just
because 'dairy' isn't in MAIN_INGREDIENT_CATEGORIES); milk/cream/butter/ghee/cheese still correctly
score as non-main. Still an approximation, not fact — flagged as such.

ALLERGEN HIDDEN-DERIVATIVE GAP (now covers the one known instance; see catalogue.dish_allergens())
ingredients_v5.csv only carries direct is_allergen/allergen_type per ingredient — asafoetida's own
row is correctly blank (pure hing has no gluten), so nothing in that CSV can flag its commercial
wheat-flour-carrier risk. ghar_re_core.catalogue.py now carries a small authored
HIDDEN_DERIVATIVE_ALLERGENS table (currently just {"asafoetida": "gluten"} — the one instance this
catalogue's 810 dishes actually surfaced, via the 20-dish hidden_allergen_risk report below) that
dish_allergens() unions into its result, so a gluten-allergic household's A3 hard filter now
actually excludes those dishes instead of only reporting them. Any OTHER hidden-derivative pairing
discovered later should be added to that same table, not silently left as a report-only footnote.
build_report()'s `hidden_allergen_risk` list still separately flags every dish containing a
known-risk ingredient by name/alias, so the underlying data gap (no ingredient-level "commercial
form may contain X" column) stays visible even though this one instance is now actively enforced.

FARALI COMPATIBILITY (previously always False — now derived, heuristic, and clearly imperfect)
ingredients_v5.csv gained an `is_farali_compatible` column (conservative allow-list: whole spices,
fruit/dry-fruit/dairy/coconut/seed/oil categories, and named fasting staples default Y; meat/
seafood/egg/lentil_legume/most grain_flour/vegetable default N) plus 4 previously-absent fasting
staples (kuttu_atta, singhara_atta, rajgira_flour, sendha_namak) that had ZERO rows before this fix
— meaning no dish naming them could resolve at all, let alone be marked fasting-compatible. This is
a best-effort religious-observance heuristic, not an authoritative ruling: regional/community vrat
rules vary (e.g. some traditions permit black salt or certain rice forms this table denies), so it
is intentionally conservative — ambiguous ingredients are marked N (not verified) rather than a
guessed Y, exactly as jain_compatible already does for onion/garlic-adjacent cases.
"""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass, field

import openpyxl

from ghar_re_core import knowledge as K

_HERE = os.path.dirname(os.path.abspath(__file__))  # .../ghar_re_service/scripts
_PKG_DIR = os.path.dirname(_HERE)  # .../ghar_re_service (the package)
_SERVICE_ROOT = os.path.dirname(_PKG_DIR)  # ghar_re_service/ (project dir)
_REPO_ROOT = os.path.dirname(_SERVICE_ROOT)  # repo root

DEFAULT_SOURCE_DIR = os.path.join(_REPO_ROOT, "data", "source")

DISHES_XLSX = "dishes.xlsx"
DISHES_SHEET = "dishes_810"
INGREDIENTS_CSV = "ingredients_v5.csv"
INGREDIENT_ALIASES_CSV = "ingredient_aliases_v2.csv"
CUISINES_CSV = "cuisines_v4.csv"
TERM_SYNONYMS_CSV = "term_synonyms_v2.csv"
# Lives at data/sig_scores_v1.csv — ONE LEVEL ABOVE source_dir (data/source/), matching
# data/source/README.md's own config table entry `../sig_scores_v1.csv` resolved relative to
# that README's own directory. NOT inside data/source/ like every other file this module reads.
SIG_SCORES_CSV = "sig_scores_v1.csv"
# Lives at data/dish_macro_v1.csv — same "one level above source_dir" placement as
# SIG_SCORES_CSV above, for the same reason (authored separately from dishes.xlsx, keyed by
# dish_name). Added 2026-08-04 (Founder-directed backlog closeout, item 4): 50 dishes' real
# nutrition macros (protein_g/fibre_g/fat_g/carbs_g/sugar_g/sodium_mg), AI-researched from
# established Indian food-composition knowledge — same AI_RESEARCHED provenance standard as
# the sig-score curation batches, not a lab-measured or live-cited source. Covers 50/810 dishes;
# every other dish's macro fields remain None (an honest "not yet researched" state, never a
# fabricated 0 or guessed average).
DISH_MACRO_CSV = "dish_macro_v1.csv"

# Ingredient categories (ingredients_v5.csv `category` column) treated as "the point of the dish"
# for the is_main approximation. See module docstring's known blind spot re: dairy/paneer.
MAIN_INGREDIENT_CATEGORIES = {
    "meat",
    "seafood",
    "egg",
    "lentil_legume",
    "vegetable",
    "leafy_green",
}

# Known-risk ingredient names/aliases for the hidden-allergen-derivative gap report. Kept in sync
# with ghar_re_core.catalogue.HIDDEN_DERIVATIVE_ALLERGENS (the table that actually ENFORCES these at
# scoring time) so the report and the real filter never drift apart — see that table's own comments
# for the researched basis of each entry (hing's wheat-flour carrier, soy sauce's traditional wheat
# brewing, sambar powder/chaat masala's hing content).
HIDDEN_ALLERGEN_RISK_NAMES = {"hing", "asafoetida", "soy_sauce", "sambar_powder", "chaat_masala"}


@dataclass
class BuildReport:
    """Everything this transform found that it will NOT silently paper over."""

    dish_count: int = 0
    incomplete_ing_blocks: list[tuple[str, list[str]]] = field(default_factory=list)
    unresolved_cuisines: list[tuple[str, str]] = field(default_factory=list)
    hidden_allergen_risk: list[tuple[str, list[str]]] = field(default_factory=list)
    # sig_scores_v1.csv join (dish_name -> band). matched = (dish_name, band); unmatched = dish
    # names with no resolvable row even after normalization — target is an empty list.
    sig_band_matched: list[tuple[str, str]] = field(default_factory=list)
    sig_band_unmatched: list[str] = field(default_factory=list)


def _split(cell: str | None) -> list[str]:
    """Comma-separated cell -> stripped, non-empty token list."""
    if not cell:
        return []
    return [t.strip() for t in str(cell).split(",") if t.strip()]


def load_ingredients(source_dir: str) -> dict[str, dict]:
    path = os.path.join(source_dir, INGREDIENTS_CSV)
    out: dict[str, dict] = {}
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            out[row["name"]] = {
                "category": row["category"],
                "diet_type": row["diet_type"],
                "is_allergen": row["is_allergen"] == "Y",
                "allergen_type": row["allergen_type"] or None,
                "is_jain_compatible": row["is_jain_compatible"] == "Y",
                "is_common": row["is_common"] == "Y",
                "is_farali_compatible": row.get("is_farali_compatible") == "Y",
            }
    return out


def load_ingredient_aliases(source_dir: str) -> dict[str, str]:
    """alias (lowercased) -> canonical ingredient_name. Later rows win on collision (rare;
    aliases are per-language and collisions were not observed in ingredient_aliases_v2.csv)."""
    path = os.path.join(source_dir, INGREDIENT_ALIASES_CSV)
    out: dict[str, str] = {}
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["is_active"] == "Y":
                out[row["alias"].strip().lower()] = row["ingredient_name"]
    return out


def load_cuisines(source_dir: str) -> dict[str, dict]:
    path = os.path.join(source_dir, CUISINES_CSV)
    out: dict[str, dict] = {}
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            out[row["name"]] = {
                "cuisine_group": row["cuisine_group"],
                "state_origin": row["state_origin"],
                "tier": row["tier"],
            }
    return out


def load_dish_synonyms(source_dir: str) -> dict[str, list[str]]:
    """canonical dish name (lowercased) -> [synonym, ...], from term_synonyms_v2.csv."""
    path = os.path.join(source_dir, TERM_SYNONYMS_CSV)
    out: dict[str, list[str]] = {}
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["is_active"] == "Y":
                out.setdefault(row["canonical_name"].strip().lower(), []).append(row["synonym"])
    return out


def _normalize_name(name: str) -> str:
    """Case/whitespace-insensitive join key, so incidental casing or whitespace differences
    between dishes.xlsx and sig_scores_v1.csv (two files authored independently, on separate
    branches) don't silently drop a dish to sig_band=None. Collapses internal whitespace runs
    too, not just leading/trailing."""
    return " ".join(name.strip().split()).casefold()


def load_sig_scores(source_dir: str) -> dict[str, str]:
    """normalized dish_name -> band, from ../sig_scores_v1.csv (data/sig_scores_v1.csv — one
    level above source_dir). Every row (both AUTO_DRAFT and PENDING_FOUNDER_REVIEW status) is
    used as-is: PENDING_FOUNDER_REVIEW rows already carry a real, conservative heuristic band,
    not a placeholder to be treated as absent. A row whose band isn't one of the 6 known KB0.2
    §S1 bands (data corruption, not a naming issue) is skipped and NOT counted as a join match —
    it would fail exactly the same way a missing row does downstream (Catalogue.Dish's
    K.BAND_TO_SCORE lookup), so treating it as unmatched is honest, not silent.
    """
    path = os.path.join(os.path.dirname(source_dir), SIG_SCORES_CSV)
    out: dict[str, str] = {}
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            band = row["band"]
            if band in K.BAND_TO_SCORE:
                out[_normalize_name(row["dish_name"])] = band
    return out


def load_dish_macro(source_dir: str) -> dict[str, dict]:
    """normalized dish_name -> {protein_g, fibre_g, fat_g, carbs_g, sugar_g, sodium_mg}, from
    ../dish_macro_v1.csv (data/dish_macro_v1.csv — one level above source_dir, same placement
    convention as SIG_SCORES_CSV/load_sig_scores() above). Returns {} entries are simply absent
    from the dict — callers must treat a missing key as "not yet researched", never fabricate a
    default. All values are ints in the source CSV; cast to int here so build_report()/JSON
    serialization gets a plain number, not a string."""
    path = os.path.join(os.path.dirname(source_dir), DISH_MACRO_CSV)
    out: dict[str, dict] = {}
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            out[_normalize_name(row["dish_name"])] = {
                "protein_g": int(row["protein_g"]),
                "fibre_g": int(row["fibre_g"]),
                "fat_g": int(row["fat_g"]),
                "carbs_g": int(row["carbs_g"]),
                "sugar_g": int(row["sugar_g"]),
                "sodium_mg": int(row["sodium_mg"]),
            }
    return out


def resolve_ingredient(
    token: str, ing_map: dict[str, dict], alias_map: dict[str, str]
) -> tuple[str, bool]:
    """Returns (resolved_name_or_original_token, resolved: bool)."""
    if token in ing_map:
        return token, True
    canonical = alias_map.get(token.strip().lower())
    if canonical and canonical in ing_map:
        return canonical, True
    return token, False


def _hero_role(cats: set[str], name: str, has_protein_centre: bool) -> str:
    """BEST-EFFORT heuristic. Derived from the dish_category -> hero_role correlation across every
    dish in ghar_re_core/fixtures.py (all 39 golden-sample dishes were cross-tabulated by hand to
    build these rules). `has_protein_centre` (see _has_protein_centre()) checks EVERY resolved
    ingredient, not just the first, and treats paneer/khoya as protein-centric alongside meat/
    seafood/egg/lentil_legume — closing the previously documented blind spot where a paneer curry
    with paneer listed second/third (not the dish's first ingredient token) was silently
    under-classified as 'liquid' instead of 'single'."""
    STAPLE_ONLY = {"paratha_roti", "bread", "rice"}
    if cats and cats <= STAPLE_ONLY:
        return "support"
    if cats & {"snack_starter", "egg_dish"}:
        return "dry"
    if "biryani_pulao" in cats:
        return "standalone"
    if "whole_meal" in cats:
        return "single" if "rice" in cats else "standalone"
    if "dosa_idli" in cats:
        FILLED_KEYWORDS = ("masala", "paneer", "cheese", "mysore", "podi", "set")
        return "standalone" if any(k in name.lower() for k in FILLED_KEYWORDS) else "dry"
    if "curry" in cats:
        if "dal_lentil" in cats:
            return "liquid"
        return "single" if has_protein_centre else "liquid"
    if "dal_lentil" in cats:
        return "liquid"
    if "dry_sabzi" in cats:
        return "dry"
    if "soup" in cats:
        return "liquid"
    # Anything else (sweets/desserts/chutneys/beverages — none appear in the 39-dish golden
    # sample, so there's no precedent to reverse-engineer from) defaults to 'support' rather than
    # a guessed poolable role, so it's excluded from B/L/D plate pools (ghar_re_core/pairing.py)
    # instead of silently entering scoring with a fabricated hero_role.
    return "support"


def _diet(resolved_ingredients: list[tuple[str, bool]], ing_map: dict[str, dict]) -> str:
    diet_types = {
        ing_map[name]["diet_type"] for name, ok in resolved_ingredients if ok and name in ing_map
    }
    if "non_veg" in diet_types:
        return "non_veg"
    if "egg" in diet_types:
        return "egg"
    return "veg"


def _jain_compatible(
    diet: str, resolved_ingredients: list[tuple[str, bool]], ing_map: dict[str, dict]
) -> str:
    if diet != "veg":
        return "N"
    for name, ok in resolved_ingredients:
        if ok and name in ing_map and not ing_map[name]["is_jain_compatible"]:
            return "N"
    return "Y"


# Ingredients whose OWN category is generic (paneer/khoya both sit under ingredients_v5.csv's plain
# 'dairy' category, alongside butter/cream/milk) but that are, in practice, the protein centre of a
# dish exactly like a meat/lentil main would be. Named override, not a category, since the CSV has
# no way to distinguish them from non-main dairy — see module docstring's is_main section.
_PROTEIN_CENTRIC_DAIRY_NAMES = {"paneer", "khoya"}


def _has_protein_centre(
    resolved_ingredients: list[tuple[str, bool]], ing_map: dict[str, dict]
) -> bool:
    """Whether ANY resolved ingredient in this dish is a main-protein-category item (meat/seafood/
    egg/lentil_legume — the last covers tofu already) or a protein-centric dairy name (paneer/khoya)
    — used by _hero_role's curry branch instead of only checking the FIRST ingredient's diet_type,
    which silently misclassified a paneer curry as 'liquid' whenever paneer wasn't listed first."""
    for name, ok in resolved_ingredients:
        if not ok:
            continue
        if name in _PROTEIN_CENTRIC_DAIRY_NAMES:
            return True
        info = ing_map.get(name)
        if info and info["category"] in ("meat", "seafood", "egg", "lentil_legume"):
            return True
    return False


def _farali_compatible(
    diet: str, resolved_ingredients: list[tuple[str, bool]], ing_map: dict[str, dict]
) -> str:
    """See module docstring's FARALI COMPATIBILITY section: 'Y' only if diet == 'veg' AND every
    resolved ingredient is fasting-compatible per ingredients_v5.csv's is_farali_compatible column.
    An unresolved token (can't verify) or diet != veg makes the whole dish 'N', the same
    conservative stance _jain_compatible already takes — never guess a Y."""
    if diet != "veg":
        return "N"
    for name, ok in resolved_ingredients:
        if not ok or name not in ing_map or not ing_map[name]["is_farali_compatible"]:
            return "N"
    return "Y"


def transform_dish_row(
    row: dict,
    ing_map: dict[str, dict],
    alias_map: dict[str, str],
    cuisine_map: dict[str, dict],
    dish_synonyms: dict[str, list[str]],
    sig_scores_map: dict[str, str],
    dish_macro_map: dict[str, dict],
    report: BuildReport,
) -> dict:
    name = row["Dish Name"]

    raw_tokens = _split(row["Ingredients"])
    resolved: list[tuple[str, bool]] = [
        resolve_ingredient(tok, ing_map, alias_map) for tok in raw_tokens
    ]
    unresolved = [tok for tok, ok in resolved if not ok]
    if unresolved:
        report.incomplete_ing_blocks.append((name, unresolved))

    hidden_risk_hits = [
        tok
        for tok, _ok in resolved
        if tok.strip().lower() in HIDDEN_ALLERGEN_RISK_NAMES
        or alias_map.get(tok.strip().lower(), "").lower() in HIDDEN_ALLERGEN_RISK_NAMES
    ]
    if hidden_risk_hits:
        report.hidden_allergen_risk.append((name, hidden_risk_hits))

    diet = _diet(resolved, ing_map)
    jain = _jain_compatible(diet, resolved, ing_map)
    farali = _farali_compatible(diet, resolved, ing_map)

    main_categories = MAIN_INGREDIENT_CATEGORIES
    ingredients = [
        (
            resolved_name,
            (
                ing_map.get(resolved_name, {}).get("category") in main_categories
                or resolved_name in _PROTEIN_CENTRIC_DAIRY_NAMES
            )
            and not ing_map.get(resolved_name, {}).get("is_common", False),
        )
        for resolved_name, _ok in resolved
    ]
    has_protein_centre = _has_protein_centre(resolved, ing_map)

    cuisine = row["Cuisines"]
    if cuisine not in cuisine_map:
        report.unresolved_cuisines.append((name, cuisine))

    cats = set(_split(row["Dish Category"]))
    hero_role = _hero_role(cats, name, has_protein_centre)

    sig_band = sig_scores_map.get(_normalize_name(name))
    if sig_band:
        report.sig_band_matched.append((name, sig_band))
    else:
        report.sig_band_unmatched.append(name)

    alt_names = _split(row["Alternate Names"])
    synonyms = dish_synonyms.get(name.strip().lower(), [])

    calories = row["Calories"]
    prep = row["Prep Mins"] or 0
    cook = row["Cooks Mins"] or 0

    # Researched macro fields (2026-08-04, 50/810 dishes) — see load_dish_macro(). Absent for
    # the other 760 dishes; those keep the None defaults below, an honest "not yet researched"
    # state rather than a fabricated average.
    macro_extra = dish_macro_map.get(_normalize_name(name), {})

    return {
        "name": name,
        "cuisine": cuisine,
        # cuisines_v4.csv's 65-cuisine state_origin, resolved here (was loaded into cuisine_map but
        # never written into this dict — ghar_re_core.catalogue.Dish previously also unconditionally
        # overwrote any state_origin with its own 10-cuisine-only fixtures lookup regardless, so
        # this key was silently discarded twice; both are now fixed together). None if the cuisine
        # failed to resolve (already flagged above via report.unresolved_cuisines).
        "state_origin": cuisine_map.get(cuisine, {}).get("state_origin") or None,
        "diet": diet,
        "hero_role": hero_role,
        "sig_band": sig_band,  # from sig_scores_v1.csv; None only if the join failed — see report
        "spice_level": row["Spice Level"],
        "sweetness": row["Sweetness"],
        "heaviness": row["Heaviness"],
        "difficulty": row["Difficulty"],
        "prep_mins": prep,
        "cook_mins": cook,
        "total_mins": row["Total Mins"] or (prep + cook),
        "calories": calories,
        "serving_size": row["Serving Size"],
        "meal_type": _split(row["Meal Types"]),
        "dish_category": sorted(cats),
        "cooking_method": _split(row["Cooking Method"]),
        "primary_taste": _split(row["Primary Taste"]),
        "texture": _split(row["Texture"]),
        "richness": _split(row["Richness"]),
        "mouthfeel": _split(row["Mouthfeel"]),
        "aroma_profile": _split(row["Aroma Profile"]),
        "fermentation": row["Fermentation"] or "none",
        "serving_temp": row["Serving Temp"] or "hot",
        "weather_affinity": _split(row["Weather Affinity"]),
        "jain_compatible": jain,
        "scope_tier": row["tier_1"],
        # bool, not "Y"/"N" — ghar_re_core.catalogue.Dish/scoring.pass_mode_fasting reads this as a
        # Python bool (mirrors fixtures.py's golden-sample shape); see FARALI COMPATIBILITY above.
        "farali_compatible": farali == "Y",
        "alternate_names": alt_names,
        "synonyms": synonyms,
        "ingredients": ingredients,
        "macro": {
            "calories": calories,
            "protein_g": macro_extra.get("protein_g"),
            "fibre_g": macro_extra.get("fibre_g"),
            "fat_g": macro_extra.get("fat_g"),
            "carbs_g": macro_extra.get("carbs_g"),
            "sugar_g": macro_extra.get("sugar_g"),
            "sodium_mg": macro_extra.get("sodium_mg"),
        },
    }


def _read_dish_rows(source_dir: str) -> list[dict]:
    path = os.path.join(source_dir, DISHES_XLSX)
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb[DISHES_SHEET]
    rows = list(ws.iter_rows(values_only=True))
    # Row 0 (sheet row 1) is blank; row 1 (sheet row 2) is the real header.
    header = rows[1]
    out = []
    for r in rows[2:]:
        if r[1] is None:  # no dish name -> not a real data row
            continue
        out.append(dict(zip(header, r, strict=True)))
    return out


def build_catalogue(source_dir: str = DEFAULT_SOURCE_DIR) -> tuple[list[dict], BuildReport]:
    """Returns (dish_dicts, report). dish_dicts match ghar_re_core/fixtures.py's _dish() shape."""
    ing_map = load_ingredients(source_dir)
    alias_map = load_ingredient_aliases(source_dir)
    cuisine_map = load_cuisines(source_dir)
    dish_synonyms = load_dish_synonyms(source_dir)
    sig_scores_map = load_sig_scores(source_dir)
    dish_macro_map = load_dish_macro(source_dir)

    report = BuildReport()
    dishes = [
        transform_dish_row(
            row, ing_map, alias_map, cuisine_map, dish_synonyms, sig_scores_map,
            dish_macro_map, report,
        )
        for row in _read_dish_rows(source_dir)
    ]
    report.dish_count = len(dishes)
    return dishes, report


if __name__ == "__main__":
    dishes, report = build_catalogue()
    print(f"Built {report.dish_count} dish dicts.")
    print(f"Incomplete ING-blocks: {len(report.incomplete_ing_blocks)}")
    print(f"Unresolved cuisines: {len(report.unresolved_cuisines)}")
    print(f"Hidden-allergen-risk dishes: {len(report.hidden_allergen_risk)}")
    print(f"sig_band matched from sig_scores_v1.csv: {len(report.sig_band_matched)}")
    print(f"sig_band unmatched (join failed): {len(report.sig_band_unmatched)}")
    if report.sig_band_unmatched:
        print(f"  unmatched dishes: {report.sig_band_unmatched}")
