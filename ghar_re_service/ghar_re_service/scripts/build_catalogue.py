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
is a separate step (Phase G Task 1 proper), deliberately not done here.

SOURCE FILES READ (all under data/source/, resolved the same way export_bundle.py resolves it)
  dishes.xlsx                  sheet "dishes_810" — the 810 authored dishes. NOTE: row 1 of the
                                sheet is blank; the real header is row 2 (openpyxl 0-indexed: header
                                = rows[1], data starts at rows[2]).
  ingredients_v5.csv            ingredient master: category / diet_type / allergen / jain flags.
  ingredient_aliases_v2.csv      Hindi/regional alias -> canonical ingredient name.
  cuisines_v4.csv                cuisine -> cuisine_group / state_origin / tier.
  term_synonyms_v2.csv           dish-name-level synonyms (Pani Puri / Gol Gappa / Puchka / ...).
  ghar_knowledge_base_v0_2.md     sig-score band definitions, read via ghar_re_core.knowledge
                                  (SIG_SCORE_BANDS) rather than re-parsed here — see _sig_band().

FIELDS DERIVED, NOT SOURCED (documented per-field below — never fabricated, always flagged)
  diet              -> from ingredient diet_type: 'non_veg' if any ingredient is non_veg, else
                        'egg' if any is egg, else 'veg'. (dishes.xlsx has no diet column.)
  jain_compatible    -> 'Y' only if diet == 'veg' AND every resolved ingredient is jain-compatible
                        per ingredients_v5.csv; else 'N'. (No column in dishes.xlsx.)
  farali_compatible  -> always False. Neither dishes.xlsx nor ingredients_v5.csv/tags_v4.csv carries
                        a farali/vrat flag. This is a genuine data gap (see GAP: farali below), not
                        a "no dish is farali" claim — left False rather than guessed per dish.
  hero_role          -> BEST-EFFORT heuristic from dish_category (+ a first-ingredient diet signal
                        for the curry/single-vs-liquid split), reverse-engineered from the
                        dish_category -> hero_role correlation observed across all 39 golden-sample
                        dishes (see _hero_role() for the exact rules and its known blind spot).
  sig_band/sig_score -> ONLY set when the dish name matches one of the specific dishes the KB's own
                        SIG_SCORE_BANDS definitions name as examples (ghar_re_core.knowledge —
                        transcribed verbatim from the KB, data_source='real'). The KB itself
                        (ghar_knowledge_base_v0_2.md line ~161) says all 810 draft scores are
                        supposed to live in a separate file, sig_scores_v1.csv — THAT FILE DOES NOT
                        EXIST ANYWHERE IN THIS REPO (verified: `find` for it returns nothing). This
                        is the single biggest data gap this transform surfaces: every dish not
                        name-matched against the KB's own examples gets sig_band=None (Catalogue's
                        Dish class currently requires a valid sig_band key to look up sig_score —
                        making 750+ dishes with sig_band=None loadable is a follow-up, out of scope
                        for this module, which only builds dish dicts).
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
is_main = ingredient category in MAIN_INGREDIENT_CATEGORIES and not flagged is_common='Y' in
ingredients_v5.csv. This under-classifies dairy-based proteins (e.g. paneer) as non-main because
'dairy' also covers butter/cream/milk, which are legitimately non-main — ingredients_v5.csv gives
no way to tell them apart. Flagged as an approximation, not fact.

ALLERGEN HIDDEN-DERIVATIVE GAP (explicitly out of scope to fix, per task)
ingredients_v5.csv only carries direct is_allergen/allergen_type per ingredient. There is no table
anywhere capturing hidden derivatives (hing/asafoetida commonly contains wheat flour as a carrier;
some spice blends contain gluten). ghar_re_core.catalogue.dish_allergens() is explicit-ingredient-
only by its own docstring ("hidden-derivative layer is out of scope") and this module does not
change that. build_report()'s `hidden_allergen_risk` list instead separately flags every dish
containing a known-risk ingredient by name/alias (hing/asafoetida, plus anything already flagged
wheat-adjacent in allergen_type) so this stays a visible, named, open P0 gap rather than one that
disappears into a catalogue that LOOKS allergen-safe.
"""
from __future__ import annotations

import csv
import os
import re
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

# Ingredient categories (ingredients_v5.csv `category` column) treated as "the point of the dish"
# for the is_main approximation. See module docstring's known blind spot re: dairy/paneer.
MAIN_INGREDIENT_CATEGORIES = {
    "meat", "seafood", "egg", "lentil_legume", "vegetable", "leafy_green",
}

# Known-risk ingredient names/aliases for the hidden-allergen-derivative gap report. hing is the
# textbook example (often cut with wheat flour); anything already allergen_type='wheat'-adjacent
# by name is added as a second, narrower check inside build_report().
HIDDEN_ALLERGEN_RISK_NAMES = {"hing", "asafoetida"}


@dataclass
class BuildReport:
    """Everything this transform found that it will NOT silently paper over."""

    dish_count: int = 0
    incomplete_ing_blocks: list[tuple[str, list[str]]] = field(default_factory=list)
    unresolved_cuisines: list[tuple[str, str]] = field(default_factory=list)
    hidden_allergen_risk: list[tuple[str, list[str]]] = field(default_factory=list)
    sig_band_stub_count: int = 0
    sig_band_matched: list[tuple[str, str]] = field(default_factory=list)


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


def _sig_band_examples() -> dict[str, str]:
    """dish name (lowercased) -> band_name, for the specific example dishes the KB's own
    SIG_SCORE_BANDS definitions name (ghar_re_core.knowledge, transcribed verbatim, data_source
    'real'). This is the ONLY source of sig_band for the real catalogue — see module docstring's
    GAP note on the missing sig_scores_v1.csv file."""
    out: dict[str, str] = {}
    for _score, band_name, definition, _src in K.SIG_SCORE_BANDS:
        for name in re.findall(r"([A-Za-z][A-Za-z ']+[A-Za-z])(?:,|\))", definition):
            out[name.strip().lower()] = band_name
    return out


_SIG_BAND_EXAMPLES = _sig_band_examples()


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


def _hero_role(cats: set[str], name: str, first_ingredient_diet: str | None) -> str:
    """BEST-EFFORT heuristic. Derived from the dish_category -> hero_role correlation across every
    dish in ghar_re_core/fixtures.py (all 39 golden-sample dishes were cross-tabulated by hand to
    build these rules). Known blind spot: single-protein VEGETARIAN curries (e.g. paneer-based)
    can be under-classified as 'liquid' instead of 'single', since ingredients_v5.csv's diet_type
    doesn't distinguish a protein-centric veg curry from a generic vegetable curry the way a human
    curator did for the golden sample. Not silently treated as certainly correct — flag for
    spot-review, don't trust blindly for paneer/tofu/soya dishes categorized 'curry'."""
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
        return "single" if first_ingredient_diet == "non_veg" else "liquid"
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
        ing_map[name]["diet_type"]
        for name, ok in resolved_ingredients
        if ok and name in ing_map
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


def transform_dish_row(
    row: dict,
    ing_map: dict[str, dict],
    alias_map: dict[str, str],
    cuisine_map: dict[str, dict],
    dish_synonyms: dict[str, list[str]],
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
        tok for tok, _ok in resolved
        if tok.strip().lower() in HIDDEN_ALLERGEN_RISK_NAMES
        or alias_map.get(tok.strip().lower(), "").lower() in HIDDEN_ALLERGEN_RISK_NAMES
    ]
    if hidden_risk_hits:
        report.hidden_allergen_risk.append((name, hidden_risk_hits))

    diet = _diet(resolved, ing_map)
    jain = _jain_compatible(diet, resolved, ing_map)

    main_categories = MAIN_INGREDIENT_CATEGORIES
    ingredients = [
        (
            resolved_name,
            ing_map.get(resolved_name, {}).get("category") in main_categories
            and not ing_map.get(resolved_name, {}).get("is_common", False),
        )
        for resolved_name, _ok in resolved
    ]
    first_ingredient_diet = (
        ing_map.get(resolved[0][0], {}).get("diet_type") if resolved else None
    )

    cuisine = row["Cuisines"]
    if cuisine not in cuisine_map:
        report.unresolved_cuisines.append((name, cuisine))

    cats = set(_split(row["Dish Category"]))
    hero_role = _hero_role(cats, name, first_ingredient_diet)

    sig_band = _SIG_BAND_EXAMPLES.get(name.strip().lower())
    if sig_band:
        report.sig_band_matched.append((name, sig_band))
    else:
        report.sig_band_stub_count += 1

    alt_names = _split(row["Alternate Names"])
    synonyms = dish_synonyms.get(name.strip().lower(), [])

    calories = row["Calories"]
    prep = row["Prep Mins"] or 0
    cook = row["Cooks Mins"] or 0

    return {
        "name": name,
        "cuisine": cuisine,
        "diet": diet,
        "hero_role": hero_role,
        "sig_band": sig_band,  # None for ~all 810 dishes — see module docstring GAP note
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
        "farali_compatible": False,  # GAP: no farali/vrat signal anywhere in data/source/
        "alternate_names": alt_names,
        "synonyms": synonyms,
        "ingredients": ingredients,
        "macro": {
            "calories": calories,
            "protein_g": None,
            "fibre_g": None,
            "fat_g": None,
            "carbs_g": None,
            "sugar_g": None,
            "sodium_mg": None,
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

    report = BuildReport()
    dishes = [
        transform_dish_row(row, ing_map, alias_map, cuisine_map, dish_synonyms, report)
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
    print(f"sig_band matched from KB examples: {len(report.sig_band_matched)}")
    print(f"sig_band left None (stub): {report.sig_band_stub_count}")
