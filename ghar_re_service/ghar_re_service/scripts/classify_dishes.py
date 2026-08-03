"""
classify_dishes — OFFLINE nutritionist/chef dish->meal-class classifier (WP-17 #5).

WHAT THIS SOLVES
The runtime cohort layer plans in MEAL CLASSES (Meal_Class_Master_v3, 131 behavioural classes), but
a dish only contributes to a household's cohort plan if it is mapped to a class. The prior coverage
was 202/810 (class_dish_options exact map + a precision-safe unanimous-token override pass); the
other 608 dishes carried S_cohort = 0.0 and could never be surfaced/suppressed by the plan. That
coverage gap was the ceiling on the whole class-first idea.

This module classifies EVERY catalogue dish into its best meal class by acting as an expert
nutritionist/chef would — reading each class's authored profile (slot, diet, heaviness, category,
cooking style, region) and each class's curated EXEMPLAR dishes (Class_Dish_Options_v3 +
Meal_Class_Master example_dishes) as ground truth, then scoring each dish against every
slot-and-diet-compatible class on:

  1. exemplar token overlap  (idf-weighted; the strongest signal — the exemplars ARE the expert's
                               own examples of the class, so a dish sharing their vocabulary belongs
                               to the class)
  2. dish_category -> class-family alignment
  3. heaviness match           (light/moderate/heavy)
  4. regional cuisine grounding (Maharashtrian -> Pitla-Bhakri, Bengali -> dal-bhaat/fish, ...)
  5. lifecycle/diet gating      (child/jain/fasting/infant/diabetic classes only match a dish whose
                                 own attributes support them; add-on-only classes are down-weighted
                                 so a general dish never lands in a member-specific add-on class)

Output: data/source/class_first_v1/dish_class_map.csv
  dish_name, meal_class_code, slot_group, method, confidence
  method = curated_exact  (dish is literally an exemplar of the class — reproduces the authored map)
         = chef_rubric    (derived here; confidence in [0,1] from the rubric score)

This is DERIVATION, not fabrication (FD-11): every chef_rubric row is a transparent, deterministic
consequence of the dish's own attributes matched against the authored class definitions, tagged with
its method + confidence so a reviewer can see exactly which mappings are curated vs derived and how
strong each derived one is. No dish is ever assigned a class it is diet/slot-incompatible with.

Run (invoked by prepare_cohort_intel.main, or standalone):
  cd ghar_re_service && PYTHONPATH=..:. python3 -m ghar_re_service.scripts.classify_dishes
"""

from __future__ import annotations

import csv
import json
import math
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
SRC = os.path.join(REPO, "data", "source", "class_first_v1")
CATALOGUE = os.path.join(REPO, "ghar_re_service", "data", "bundle", "catalogue.json")
OUT = os.path.join(SRC, "dish_class_map.csv")

# Tokens too generic to carry class signal on their own. idf down-weights most of these anyway; this
# set removes pure noise (conjunctions, plate/style words) before scoring.
STOP = {
    "and",
    "with",
    "or",
    "the",
    "a",
    "an",
    "of",
    "in",
    "on",
    "style",
    "home",
    "homestyle",
    "plate",
    "meal",
    "bowl",
    "special",
    "type",
    "mix",
    "mixed",
    "plain",
    "fresh",
}

# dish_category -> class-code substrings that category naturally belongs to. A moderate secondary
# signal (the exemplar overlap does most of the work); grounds ambiguous names in the right family.
CATEGORY_HINTS = {
    "dosa_idli": ("FERMENTED_CREPE", "STEAMED_FERMENTED", "SOUTH_TIFFIN", "MILLET_TRADITIONAL"),
    "paratha_roti": ("STUFFED_FLATBREAD", "PLAIN_FLATBREAD", "DAL_ROTI", "MILLET_ROTI", "PUNJAB"),
    "bread": ("PLAIN_FLATBREAD", "STUFFED_FLATBREAD", "DAL_ROTI", "MILLET_ROTI"),
    "dal_lentil": ("DAL_RICE", "DAL_ROTI", "RAJMA_CHOLE", "LIGHT_KHICHDI", "SOUTH_SAMBAR"),
    "dry_sabzi": (
        "SIMPLE_GREEN_VEG",
        "MIXED_VEG_DRY",
        "ROOT_TUBER",
        "LEAFY_GREENS",
        "GOURD_PUMPKIN",
    ),
    "curry": (
        "SEMI_GRAVY_VEG",
        "PANEER",
        "KADHI_CURD",
        "COCONUT_VEG_STEW",
        "CHICKEN_HOME",
        "FISH_CURRY",
        "EGG_CURRY",
        "MUTTON",
        "GOAN",
        "KERALA_MEAT",
    ),
    "rice": ("RICE_PULAO", "SOUTH_TAMARIND", "SOUTH_CURD", "DAL_RICE", "CURD_RICE"),
    "biryani_pulao": ("VEG_BIRYANI", "RICE_PULAO", "CHICKEN_BIRYANI", "MUSLIM_BIRYANI"),
    "snack_starter": (
        "FRIED_PAKORA",
        "STREET_CHAAT",
        "NAMKEEN",
        "STEAMED_SNACK",
        "SOUTH_TIFFIN",
        "NONVEG_SNACK",
        "EGG_SNACK",
        "BAKERY_CAFE",
    ),
    "chaat": ("STREET_CHAAT", "FRUIT_CHAAT"),
    "soup": ("KHICHDI_SOUP", "NONVEG_LIGHT_SOUP", "HIMALAYAN_THUKPA"),
    "kebab": ("TANDOORI_GRILL", "GRILLED_TIKKA", "NONVEG_SNACK", "HOME_STYLE_KEEMA"),
    "egg_dish": ("EGG_FAST", "EGG_CURRY", "EGG_RICE", "EGG_SNACK"),
    "noodle_pasta": ("INDO_CHINESE", "PASTA_PIZZA", "MOMO_NOODLES"),
    "whole_meal": (
        "THALI",
        "FESTIVE_THALI",
        "DAL_RICE",
        "GUJARATI",
        "RAJASTHANI",
        "PUNJABI",
        "MAHARASHTRIAN",
        "BENGALI",
        "ODIA",
        "BIHAR",
        "SOUTH_SAMBAR",
    ),
    "thali_combo": ("THALI", "FESTIVE_THALI"),
    "salad_raita": ("MODERN_SALAD", "FRUIT_CHAAT", "CURD_CHAAS"),
    "sweet_dessert": ("SWEET_REGIONAL", "BAKERY_CAFE"),
    "beverage": ("CURD_CHAAS", "TEA_BISCUIT", "BAKERY_CAFE"),
    "condiment_chutney": ("SIMPLE_GREEN_VEG", "SOUTH_TIFFIN"),
}

# cuisine -> the regional LD class-code substring(s) it grounds in (regional grounding: the
# "Maharashtra -> Pitla-Bhakri / Coconut-Stew" science). Foreign cuisines have no regional class and
# are intentionally absent (they fall through to modern/indo-chinese via CATEGORY_HINTS).
REGION_HINTS = {
    "maharashtrian": ("MAHARASHTRIAN",),
    "malvani": ("MAHARASHTRIAN", "COCONUT_VEG"),
    "kolhapuri": ("MAHARASHTRIAN",),
    "gujarati": ("GUJARATI",),
    "kutchi": ("GUJARATI",),
    "rajasthani": ("RAJASTHANI",),
    "sindhi": ("KADHI_CURD",),
    "punjabi": ("PUNJABI", "PANEER"),
    "delhi": ("PUNJABI", "PANEER"),
    "mughlai": ("MUSLIM_BIRYANI",),
    "awadhi": ("MUSLIM_BIRYANI",),
    "kashmiri": ("HIMALAYAN",),
    "bengali": ("BENGALI",),
    "odia": ("ODIA",),
    "bihari": ("BIHAR",),
    "up": ("DAL_ROTI", "PUNJABI"),
    "chhattisgarhi": ("DAL_ROTI",),
    "madhya_pradesh": ("DAL_ROTI",),
    "indori": ("POHA_CHIVDA", "STREET_CHAAT"),
    "tamil": ("SOUTH_SAMBAR", "SOUTH_CURD"),
    "chettinad": ("SOUTH_SAMBAR", "CHICKEN_HOME"),
    "andhra": ("SOUTH_SAMBAR", "SOUTH_TAMARIND"),
    "telangana": ("SOUTH_SAMBAR", "MUSLIM_BIRYANI"),
    "hyderabadi": ("MUSLIM_BIRYANI",),
    "karnataka": ("SOUTH_SAMBAR", "SOUTH_CURD"),
    "udupi": ("SOUTH_SAMBAR", "FERMENTED_CREPE"),
    "kerala": ("COCONUT_VEG", "KERALA_MEAT"),
    "malabar": ("COCONUT_VEG", "KERALA_MEAT"),
    "mangalorean": ("COCONUT_VEG", "SOUTH_SAMBAR"),
    "goan": ("GOAN", "FISH_CURRY"),
    "assamese": ("NORTHEAST",),
    "naga": ("NORTHEAST",),
    "mizo": ("NORTHEAST",),
    "manipuri": ("NORTHEAST",),
    "meghalayan": ("NORTHEAST",),
    "tripuri": ("NORTHEAST",),
    "arunachali": ("NORTHEAST",),
    "sikkimese": ("HIMALAYAN",),
    "himachali": ("HIMALAYAN",),
    "uttarakhandi": ("HIMALAYAN",),
    "indian_tibetan": ("HIMALAYAN",),
    "bhutanese": ("HIMALAYAN",),
    "burmese": ("HIMALAYAN",),
    "parsi": ("EGG_CURRY",),
    "indo_chinese": ("INDO_CHINESE",),
    "chinese_authentic": ("INDO_CHINESE",),
    "italian": ("PASTA_PIZZA",),
    "continental": ("PASTA_PIZZA",),
    "mexican": ("PASTA_PIZZA",),
    "thai": ("INDO_CHINESE",),
    "korean": ("INDO_CHINESE",),
    "japanese": ("INDO_CHINESE",),
    "vietnamese": ("INDO_CHINESE",),
    "lebanese": ("MODERN_SALAD",),
    "mediterranean": ("MODERN_SALAD",),
    "middle_eastern_generic": ("MODERN_SALAD",),
    "street_food_generic": ("STREET_CHAAT",),
}

# Hero-ingredient anchors: a dish's DEFINING ingredient dictates its class more than any regional or
# category hint (a chef classifies "Fish Curry" by the fish, not by it being a curry). Each anchor
# token, when present in the dish name/main ingredients, strongly boosts classes whose code carries
# the target marker — and for the mutually-exclusive nonveg proteins, penalises the WRONG-protein
# nonveg classes so a fish dish can never land in a chicken class.
PROTEIN_ANCHORS = {
    "fish": "FISH",
    "machli": "FISH",
    "prawn": "PRAWN",
    "crab": "PRAWN",
    "shrimp": "PRAWN",
    "chicken": "CHICKEN",
    "murgh": "CHICKEN",
    "mutton": "MUTTON",
    "lamb": "MUTTON",
    "keema": "KEEMA",
    "pork": "PORK",
    "egg": "EGG",
    "anda": "EGG",
    "bhurji": "EGG",
}
VEG_ANCHORS = {
    "paneer": "PANEER",
    "rajma": "RAJMA_CHOLE",
    "chole": "RAJMA_CHOLE",
    "chana": "RAJMA_CHOLE",
    "chhole": "RAJMA_CHOLE",
    "lobia": "RAJMA_CHOLE",
    "tofu": "SOY_TOFU",
    "soya": "SOY_TOFU",
    "soy": "SOY_TOFU",
    "khichdi": "KHICHDI",
    "biryani": "BIRYANI",
    "pulao": "RICE_PULAO",
    "sambar": "SOUTH_SAMBAR",
    "rasam": "SOUTH_SAMBAR",
    "kadhi": "KADHI_CURD",
    "dhokla": "STEAMED",
    "idli": "STEAMED_FERMENTED",
    "dosa": "FERMENTED_CREPE",
    "poha": "POHA",
    "upma": "UPMA_DALIA",
}
_NONVEG_MARKERS = ("FISH", "PRAWN", "CHICKEN", "MUTTON", "KEEMA", "PORK")

# dish meal_type slot -> the class slot_group(s) it can be served from.
SLOT_TO_GROUP = {
    "breakfast": {"Breakfast"},
    "lunch": {"Lunch/Dinner"},
    "dinner": {"Lunch/Dinner", "Dinner"},
    "snacks": {"Snack"},
}

# lifecycle/diet-specific class categories that must be GATED by dish attributes (a dish only lands
# here if it genuinely fits) — otherwise a plain sabzi could wrongly become the "infant 6m+" class.
GATED_CATEGORIES = {
    "child",
    "infant",
    "pregnancy_postpartum",
    "jain",
    "fasting",
    "medical_health",
}


def _toks(*strings):
    """Lowercased, punctuation-stripped, stopword-filtered token set from one or more strings.
    Parenthetical qualifiers ('Lassi (Sweet)') are dropped so they don't fragment the match."""
    out: set[str] = set()
    for s in strings:
        if not s:
            continue
        s = re.sub(r"\([^)]*\)", "", str(s))
        for t in re.sub(r"[^a-z0-9 ]", " ", s.lower()).split():
            if t not in STOP and len(t) > 1:
                out.add(t)
    return out


def _heaviness_band(n):
    """dish heaviness 1/2/3 -> the master's light/moderate/heavy vocabulary."""
    return {1: "light", 2: "moderate", 3: "heavy"}.get(n, "moderate")


def load_classes():
    """Build the per-class profile the rubric scores against: slot/diet/heaviness/category/family,
    an add-on flag, and the class's EXEMPLAR token set (Meal_Class_Master example_dishes + every
    Class_Dish_Options dish name for that class + the class name itself)."""
    classes = {}
    with open(os.path.join(SRC, "meal_class_master.csv"), newline="") as f:
        for r in csv.DictReader(f):
            code = r["meal_class_code"]
            classes[code] = {
                "code": code,
                "slot_group": r["slot_group"],
                "diet_type": r["diet_type"],
                "heaviness": r["heaviness"],
                "category": r["class_category"],
                "family": r["class_family_code"],
                "is_addon": "ADDON_ONLY" in (r.get("planning_role_v3") or ""),
                "tokens": _toks(r["class_name"], r["example_dishes"]),
            }
    # fold every curated exemplar dish name into its class's token set (and remember the exact map)
    exact = {}
    with open(os.path.join(SRC, "class_dish_options.csv"), newline="") as f:
        for r in csv.DictReader(f):
            code = r["meal_class_code"]
            if code in classes:
                classes[code]["tokens"] |= _toks(r["dish_name"])
                exact.setdefault(" ".join(sorted(_toks(r["dish_name"]))), code)
    return classes, exact


def _idf(classes):
    """Inverse class-frequency for every exemplar token, so a token shared by many classes
    ('rice', 'masala') counts far less than a distinctive one ('pitla', 'dhokla', 'litti')."""
    df: dict[str, int] = {}
    for c in classes.values():
        for t in c["tokens"]:
            df[t] = df.get(t, 0) + 1
    n = len(classes)
    return {t: math.log((n + 1) / (v + 1)) + 1.0 for t, v in df.items()}


def _diet_ok(dish_diet, cls):
    """Diet compatibility (a hard gate — never assign a diet-incompatible class):
    veg dish  -> veg/jain/mixed classes, never egg/nonveg;
    egg dish  -> egg/mixed classes (+ veg is fine, an egg household eats veg);
    non_veg   -> the nonveg classes (code carries a meat marker) or mixed."""
    dt = cls["diet_type"]
    code = cls["code"]
    meat = any(
        m in code
        for m in (
            "CHICKEN",
            "FISH",
            "MUTTON",
            "PRAWN",
            "CRAB",
            "KEEMA",
            "PORK",
            "RED_MEAT",
            "SEAFOOD",
            "NONVEG",
            "TANDOORI",
            "MUSLIM_BIRYANI",
            "SMOKED_PORK",
            "MEAT_STEW",
            "XACUTI",
        )
    )
    if dish_diet == "veg":
        return dt in ("veg", "jain", "mixed") and not meat and "EGG" not in code
    if dish_diet == "egg":
        return dt in ("veg", "egg", "mixed") and not meat
    # non_veg
    return meat or dt in ("mixed", "nonveg")


def classify(dish, classes, idf, exact):
    """Return (meal_class_code, slot_group, method, confidence) for one dish dict."""
    dtoks = _toks(dish["name"], *dish.get("synonyms", []), *dish.get("alternate_names", []))
    main_ing = _toks(*[i[0] for i in dish.get("ingredients", []) if i[1]])
    # curated exact: the dish IS an exemplar of a class -> authored truth, reproduce it.
    key = " ".join(sorted(dtoks))
    if key in exact:
        code = exact[key]
        return code, classes[code]["slot_group"], "curated_exact", 1.0

    groups = set()
    for slot in dish.get("meal_type", []):
        groups |= SLOT_TO_GROUP.get(slot, set())
    if not groups:
        groups = {"Lunch/Dinner"}  # slotless dish: default to the main-meal group

    cats = set(dish.get("dish_category", []))
    hb = _heaviness_band(dish.get("heaviness"))
    cuisine = dish.get("cuisine", "")
    region_sub = REGION_HINTS.get(cuisine, ())
    cat_subs = set()
    for c in cats:
        cat_subs.update(CATEGORY_HINTS.get(c, ()))
    # hero-ingredient anchors present in this dish (name tokens + main ingredients)
    anchor_toks = dtoks | main_ing
    anchors = {m for t, m in PROTEIN_ANCHORS.items() if t in anchor_toks}
    anchors |= {m for t, m in VEG_ANCHORS.items() if t in anchor_toks}
    wrong_protein = (
        {m for m in _NONVEG_MARKERS if m not in anchors}
        if (anchors & set(_NONVEG_MARKERS))
        else set()
    )

    best, best_score = None, 0.0
    for cls in classes.values():
        if cls["slot_group"] not in groups:
            continue
        if not _diet_ok(dish["diet"], cls):
            continue
        # 1. idf-weighted exemplar token overlap (name tokens count full, ingredient tokens half)
        overlap = sum(idf.get(t, 1.0) for t in (dtoks & cls["tokens"]))
        overlap += 0.5 * sum(idf.get(t, 1.0) for t in (main_ing & cls["tokens"]) - dtoks)
        score = overlap
        # 1b. hero-ingredient anchor: the dish's defining ingredient dominates the classification
        if any(m in cls["code"] for m in anchors):
            score += 3.5
        if any(m in cls["code"] for m in wrong_protein):
            score -= 4.0  # a fish dish must never fall into a chicken/mutton class
        # 2. category-family alignment (secondary; tokens/anchors lead)
        if any(sub in cls["code"] for sub in cat_subs):
            score += 1.5
        # 3. heaviness match
        if cls["heaviness"] == hb:
            score += 0.6
        # 4. regional grounding (tie-breaker for ambiguous names, not an override)
        if any(sub in cls["code"] for sub in region_sub):
            score += 1.5
        # 5. gating: member-specific / add-on classes need positive support, else strongly demoted
        if cls["is_addon"] or cls["category"] in GATED_CATEGORIES:
            supported = _gate_supported(dish, cls, dtoks)
            if not supported:
                score -= 5.0
            else:
                score += 0.5
        if score > best_score:
            best, best_score = cls, score

    if best is None:
        return None, None, "unmapped", 0.0
    # confidence: squash the rubric score into [0,1] (a score of ~6 -> ~0.75; tune gentle).
    conf = round(1.0 - math.exp(-best_score / 4.0), 3) if best_score > 0 else 0.0
    return best["code"], best["slot_group"], "chef_rubric", conf


def _gate_supported(dish, cls, dtoks):
    """Does the dish genuinely fit a gated (child/jain/fasting/infant/diabetic/add-on) class?"""
    cat = cls["category"]
    spice = dish.get("spice_level")
    if cat == "jain":
        return dish.get("jain_compatible") == "Y"
    if cat == "fasting":
        return bool(dish.get("farali_compatible")) or "vrat" in dtoks or "sabudana" in dtoks
    if (
        cat in ("child", "infant")
        or "CHILD" in cls["code"]
        or "KID" in cls["code"]
        or "INFANT" in cls["code"]
    ):
        # child/infant food is mild and not heavy/fried
        return (spice is not None and spice <= 1) and dish.get("heaviness", 2) <= 2
    if cat in ("medical_health", "pregnancy_postpartum"):
        return spice is not None and spice <= 2
    # generic add-on (e.g. leftover/office): allow only if exemplar tokens actually overlap
    return bool(dtoks & cls["tokens"])


def build_map():
    """Classify every catalogue dish; return list of (name, code, slot_group, method, conf) rows."""
    classes, exact = load_classes()
    idf = _idf(classes)
    with open(CATALOGUE) as f:
        dishes = json.load(f)
    rows = []
    for d in dishes:
        code, sg, method, conf = classify(d, classes, idf, exact)
        rows.append((d["name"], code or "", sg or "", method, conf))
    rows.sort()
    return rows


def main():
    rows = build_map()
    with open(OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["dish_name", "meal_class_code", "slot_group", "method", "confidence"])
        w.writerows(rows)
    total = len(rows)
    mapped = sum(1 for r in rows if r[1])
    curated = sum(1 for r in rows if r[3] == "curated_exact")
    chef = sum(1 for r in rows if r[3] == "chef_rubric")
    lowconf = sum(1 for r in rows if r[3] == "chef_rubric" and r[4] < 0.4)
    print(
        f"  wrote dish_class_map.csv: {mapped}/{total} mapped "
        f"({curated} curated_exact, {chef} chef_rubric, {lowconf} chef low-confidence <0.4)"
    )


if __name__ == "__main__":
    main()
