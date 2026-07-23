"""
ghar_re.knowledge — Knowledge-Base reference data, transcribed VERBATIM from
ghar_knowledge_base_v0_2.md.

This module is the editable source-of-truth the FROZEN spine reads (KB §0 interface).
Every row carries a `data_source` per the Task 1 mapping applied to the KB's own markers:
    KB ✓ (verified in catalogue)      -> 'real'
    KB ⚑ (KB's own "needs refinement") -> 'stub'
    anything computed/derived to fill   -> 'ai_generated'   (none here — this is transcription)

NOTE ON PROVENANCE: these are transcribed authored values, NOT invented golden-sample data,
so they legitimately carry 'real'/'stub'. The golden SAMPLE (ghar_re.fixtures) is separate and
is 'ai_generated'/'stub' only. The Task-4 data_source integrity test scopes to the sample.
"""

# ---------------------------------------------------------------------------
# KB §R1 — Zone map (cuisine_group -> zone). Grounded on the 810-dish catalogue.
# KB Evidence: High → 'real'.
# ---------------------------------------------------------------------------
ZONE_MAP = [
    # cuisine_group, zone, dish_count, data_source
    ("north_indian",     "North",     210, "real"),
    ("mughlai_nawabi",   "North",     210, "real"),   # KB groups mughlai under North
    ("south_indian",     "South",     141, "real"),
    ("west_indian",      "West",       96, "real"),
    ("east_indian",      "East",       68, "real"),
    ("central_indian",   "Central",    22, "real"),
    ("northeast_indian", "Northeast",  31, "real"),
    ("street_food",      "PanIndia",   55, "real"),
    ("chinese_asian",    "Global",    187, "real"),   # foreign/other -> Global
    ("continental",      "Global",    187, "real"),
    ("italian",          "Global",    187, "real"),
]

# State -> zone (KB §R1 "State→zone" line). Rajasthan flagged palette-North/diet-West (⚑).
STATE_ZONE = {
    "Delhi": "North", "Punjab": "North", "Haryana": "North", "Uttar Pradesh": "North",
    "Uttarakhand": "North", "Himachal Pradesh": "North", "J&K": "North",
    "Maharashtra": "West", "Gujarat": "West", "Goa": "West",
    "Tamil Nadu": "South", "Kerala": "South", "Karnataka": "South",
    "Andhra Pradesh": "South", "Telangana": "South",
    "West Bengal": "East", "Odisha": "East", "Bihar": "East", "Jharkhand": "East",
    "Madhya Pradesh": "Central", "Chhattisgarh": "Central",
    "Assam": "Northeast",
    # ⚑ Rajasthan = palette-North / diet-West. Palette zone (used for m_palette/comfort hero) = North.
    "Rajasthan": "North",
}

# ---------------------------------------------------------------------------
# KB §R3 — Comfort-hero maps (weather × zone). ✓ = verified in catalogue → 'real';
# ⚑ = KB "needs refinement" → 'stub'.  weather_type ∈ {rain, summer, winter}.
# Transcribed exactly from the three KB §R3 tables (heroes with their ✓/⚑ markers).
# ---------------------------------------------------------------------------
def _ch(zone, weather, name, verified):
    return (zone, weather, name, verified, "real" if verified else "stub")

COMFORT_HERO_MAP = [
    # RAIN / MONSOON
    _ch("North",    "rain", "Pakora",        True),
    _ch("North",    "rain", "Samosa",        True),
    _ch("North",    "rain", "Kadhi-Pakora",  True),
    _ch("North",    "rain", "Aloo Paratha",  True),
    _ch("West-MH",  "rain", "Kanda Bhaji",   True),
    _ch("West-MH",  "rain", "Vada Pav",      True),
    _ch("West-MH",  "rain", "Pithla-Bhakri", True),
    _ch("West-MH",  "rain", "Sol Kadhi",     True),
    _ch("West-GJ",  "rain", "Bhajiya",       False),
    _ch("West-GJ",  "rain", "Dal-Dhokli",    False),
    _ch("West-GJ",  "rain", "Methi Na Gota", False),
    _ch("South-TN", "rain", "Bajji/Bonda",   False),
    _ch("South-TN", "rain", "Medu Vada",     True),
    _ch("South-TN", "rain", "Rasam-Rice",    True),
    _ch("South-KL", "rain", "Parippu Vada",  False),
    _ch("South-KL", "rain", "Pazham Pori",   False),
    _ch("East-WB",  "rain", "Khichuri",      True),
    _ch("East-WB",  "rain", "Telebhaja",     False),
    _ch("Central",  "rain", "Poha",          True),
    _ch("Central",  "rain", "Pakora",        True),
    _ch("NE",       "rain", "Thukpa",        False),
    _ch("NE",       "rain", "Momos",         False),
    # SUMMER / HEATWAVE
    _ch("North",    "summer", "Sattu",        True),
    _ch("North",    "summer", "Chaas",        False),
    _ch("North",    "summer", "Aam Panna",    False),
    _ch("West",     "summer", "Sol Kadhi",    True),
    _ch("West",     "summer", "Aamras",       False),
    _ch("South",    "summer", "Curd Rice",    True),
    _ch("South",    "summer", "Neer Mor",     False),
    _ch("East",     "summer", "Panta Bhat",   False),
    # WINTER / COLD
    _ch("North",    "winter", "Sarson Ka Saag", True),
    _ch("North",    "winter", "Nihari",         True),
    _ch("North",    "winter", "Gajar Halwa",    False),
    _ch("West-GJ",  "winter", "Undhiyu",        True),
    _ch("West-MH",  "winter", "Pithla",         True),
    _ch("West-MH",  "winter", "Bajra Bhakri",   False),
    _ch("South",    "winter", "Ven Pongal",     True),
    _ch("South",    "winter", "Rasam",          True),
    _ch("East",     "winter", "Pithe",          False),
]

# KB §R3 hero NAME (as authored) -> the golden catalogue dish name that realises it.
# The KB names heroes generically ("Pakora", "Khichuri", "Rasam-Rice"); the golden sample names
# them concretely ("Onion Pakora", "Bhuna Khichuri", "Rasam"). Exact resolution avoids loose
# substring matches (e.g. "Pakora" must NOT also boost "Punjabi Kadhi Pakora").
COMFORT_HERO_TO_DISH = {
    "Pakora": "Onion Pakora",
    "Kanda Bhaji": "Kanda Bhaji",
    "Sarson Ka Saag": "Sarson Ka Saag",
    "Curd Rice": "Curd Rice",
    "Rasam": "Rasam", "Rasam-Rice": "Rasam",
    "Medu Vada": "Medu Vada",
    "Khichuri": "Bhuna Khichuri",
    "Undhiyu": "Undhiyu",
    "Pithla": "Pithla",
    "Ven Pongal": "Ven Pongal",
}

# Map an engine palette-zone (North/South/East/West/...) + weather tag to the KB §R3 zone key.
# KB splits West into West-MH / West-GJ and South into South-TN / South-KL; the engine resolves
# a household to a base zone, so we keep BOTH the base ("West") and sub keys and let the pipeline
# prefer the most specific available (via household home_state).
WEATHER_TAG_TO_KB = {"rainy": "rain", "hot_weather": "summer", "cold_weather": "winter"}

# ---------------------------------------------------------------------------
# KB §S1 — Signature calibration RULE (the 6 bands). Frozen doc → 'real'.
# ---------------------------------------------------------------------------
SIG_SCORE_BANDS = [
    # score, band_name, definition, data_source
    (1.00, "national_icon", "recognized/iconic across India (Butter Chicken, Hyderabadi Biryani, Masala Dosa)", "real"),
    (0.90, "state_icon",    "defining dish of a state (Dal Makhani, Undhiyu, Nihari, Litti Chokha)", "real"),
    (0.75, "regional_hero", "strong regional standard (Bisi Bele Bath, Macher Jhol, Puran Poli)", "real"),
    (0.60, "very_common",   "well-known everyday-plus (Rajma Chawal, Poha, Aloo Paratha)", "real"),
    (0.40, "common",        "ordinary named dish (standard dals, upma, sabzi-with-name)", "real"),
    (0.20, "utility",       "plain staple (steamed rice, plain dal, roti, papad)", "real"),
]
BAND_TO_SCORE = {b[1]: b[0] for b in SIG_SCORE_BANDS}

# ---------------------------------------------------------------------------
# KB §N1 — Negative priors (authored discouragements). Transcribed → 'real'.
# in_spine rows are ENFORCED by pairing_rules.yaml (S4) / weather; the two ⚑ v2 rows are stored
# as status='deferred_v2' and are NOT implemented (per Task 1 D).
# ---------------------------------------------------------------------------
NEGATIVE_PRIORS = [
    # discouragement, context, action, in_spine, enforced_via, status, data_source
    ("two rich/creamy gravies together", "any plate", "penalty (S4 hard-gate)", True,  "pairing_rules.yaml", "active", "real"),
    ("two same-base gravies (both tomato-onion / both coconut)", "any plate", "penalty", True, "pairing_rules.yaml", "active", "real"),
    ("two dry heroes as the pair", "any plate", "penalty", True, "pairing_rules.yaml", "active", "real"),
    ("cross-region pair (Bengali + Punjabi hero)", "any plate", "penalty (cuisine-dist gate)", True, "pairing_rules.yaml", "active", "real"),
    ("deep-fried / very-heavy", "heatwave day", "demote", True, "weather", "active", "real"),
    ("heavy lunch -> heavy dinner (same day)", "slot sequence", "demote (v2 needs history)", False, "not_yet_active", "deferred_v2", "real"),
    ("three of the same vegetable base (e.g. 3 potato dishes)", "across the 7", "demote (variety)", False, "not_yet_active", "deferred_v2", "real"),
    ("raw salads / street-style", "peak monsoon", "mild demote", True, "weather", "active", "real"),
]

# ---------------------------------------------------------------------------
# KB §E1 — Ingredient normalization map (starter). ✓/⚑: the 'expansion' row is ⚑ → 'stub'.
# Its own table (not aliases) precisely because 'expansion' rows fan out to a set.
# ---------------------------------------------------------------------------
INGREDIENT_NORMALIZATION = [
    # surface_token, canonical, norm_type, expansion(list|None), note, data_source
    ("coriander_seeds", "coriander", "alias",       None, None, "real"),
    ("cumin_powder",    "cumin",     "alias",       None, None, "real"),
    ("basmati_rice",    "rice",      "variety",     None, "basmati flag", "real"),
    ("mixed_vegetables", None,       "expansion",   ["potato","carrot","beans","peas","cauliflower"], "KB ⚑ needs refinement", "stub"),
    ("grated_coconut",  "coconut",   "form",        None, None, "real"),
    ("fish_fillet",     "fish",      "form",        None, None, "real"),
    ("dhaniya",         "coriander", "synonym",     None, None, "real"),
    ("palak",           "spinach",   "synonym",     None, None, "real"),
    ("mutton",          "goat",      "equivalence", None, None, "real"),
]

# ---------------------------------------------------------------------------
# KB §R2 — Region × Slot priors  PRIOR[zone][slot].  Additive BASE boosts.
# Transcribed authored numbers → 'real'; the one ⚑ cell (East breakfast) → 'stub'.
# Encoded as (zone, slot, match_kind, match_value, boost, usage_tags, data_source).
# match_value tokens are matched tolerantly by the pipeline (name substring / category / hero_role).
# Northeast + PanIndia/Global have NO §R2 table → intentionally absent (no invented numbers).
# ---------------------------------------------------------------------------
PRIOR_ZONE_SLOT = [
    # ---- Breakfast ----
    ("North",   "breakfast", "dish_name", "paratha", 0.4, ["Daily"], "real"),
    ("North",   "breakfast", "dish_name", "poha",    0.3, ["Daily"], "real"),
    ("North",   "breakfast", "dish_name", "chila",   0.3, ["Daily"], "real"),
    ("South",   "breakfast", "dish_name", "idli",    0.5, ["Daily"], "real"),
    ("South",   "breakfast", "dish_name", "dosa",    0.5, ["Daily"], "real"),
    ("South",   "breakfast", "dish_name", "upma",    0.3, ["Daily"], "real"),
    ("South",   "breakfast", "dish_name", "pongal",  0.3, ["Daily","Festival","Comfort"], "real"),
    ("West",    "breakfast", "dish_name", "poha",       0.5, ["Daily"], "real"),
    ("West",    "breakfast", "dish_name", "thalipeeth", 0.3, ["Daily"], "real"),
    ("West",    "breakfast", "dish_name", "upma",       0.3, ["Daily"], "real"),
    ("East",    "breakfast", "dish_name", "luchi",      0.4, ["Weekend","Daily"], "stub"),   # KB ⚑
    ("East",    "breakfast", "dish_name", "bread-omelette", 0.2, ["Daily"], "stub"),         # KB ⚑
    ("Central", "breakfast", "dish_name", "poha",    0.5, ["Daily"], "real"),
    # ---- Lunch ----
    ("North",   "lunch", "structure", "roti+sabzi+dal", 0.4, ["Daily"], "real"),
    ("North",   "lunch", "dish_name", "rajma",  0.3, ["Daily","Comfort"], "real"),
    ("North",   "lunch", "dish_name", "chole",  0.3, ["Daily"], "real"),
    ("South",   "lunch", "structure", "rice+sambar",  0.5, ["Daily"], "real"),
    ("South",   "lunch", "dish_name", "rasam",   0.5, ["Daily"], "real"),
    ("South",   "lunch", "dish_name", "poriyal", 0.3, ["Daily"], "real"),
    ("South",   "lunch", "dish_name", "curd rice", 0.3, ["Daily","Weather"], "real"),
    ("West",    "lunch", "structure", "roti+sabzi+dal", 0.4, ["Daily"], "real"),
    ("West",    "lunch", "dish_name", "varan",  0.3, ["Daily"], "real"),
    ("East",    "lunch", "dish_name", "macher jhol", 0.5, ["Daily"], "real"),
    ("East",    "lunch", "dish_name", "dal",    0.3, ["Daily"], "real"),
    ("Central", "lunch", "structure", "roti+dal+sabzi", 0.4, ["Daily"], "real"),
    ("Central", "lunch", "dish_name", "dal-bafla", 0.3, ["Daily"], "real"),
    # ---- Dinner ----
    ("North",   "dinner", "structure", "roti+sabzi+dal", 0.4, ["Daily"], "real"),
    ("North",   "dinner", "dish_name", "khichdi", 0.2, ["Comfort","Recovery","Weather"], "real"),
    ("South",   "dinner", "structure", "rice+rasam", 0.3, ["Daily"], "real"),
    ("South",   "dinner", "dish_name", "dosa",    0.3, ["Daily"], "real"),
    ("West",    "dinner", "structure", "roti+sabzi", 0.4, ["Daily"], "real"),
    ("West",    "dinner", "dish_name", "khichdi", 0.2, ["Comfort","Recovery"], "real"),
    ("East",    "dinner", "dish_name", "jhol",    0.4, ["Daily"], "real"),
]

# ---------------------------------------------------------------------------
# KB §C1 — State diet-default lean groupings (as authored in the KB doc text). Used ONLY to
# cross-check against data/source/community_priors.csv and surface conflicts (Task 3 D6 /
# Task 4 conflict report). community_priors.csv is the BASE the engine uses; this is the audit.
# lean label -> states, and the KB's cadence band for that lean.
# ---------------------------------------------------------------------------
KB_C1_LEAN = {
    # KB "Strongly veg" (Punjab noted "(veg-lean)")
    "Rajasthan": ("strongly_veg", "rare/weekend"),
    "Gujarat": ("strongly_veg", "rare/weekend"),
    "Haryana": ("strongly_veg", "rare/weekend"),
    "Punjab": ("strongly_veg", "rare/weekend"),   # KB: "Punjab(veg-lean)" under Strongly veg
    "Madhya Pradesh": ("strongly_veg", "rare/weekend"),
    # KB "Mixed"
    "Uttar Pradesh": ("mixed", "weekend/frequent"),
    "Maharashtra": ("mixed", "weekend/frequent"),
    "Karnataka": ("mixed", "weekend/frequent"),
    "Delhi": ("mixed", "weekend/frequent"),
    # KB "Strongly non-veg" (all NE)
    "West Bengal": ("strongly_non_veg", "frequent/daily"),
    "Kerala": ("strongly_non_veg", "frequent/daily"),
    "Telangana": ("strongly_non_veg", "frequent/daily"),
    "Andhra Pradesh": ("strongly_non_veg", "frequent/daily"),
    "Tamil Nadu": ("strongly_non_veg", "frequent/daily"),
    "Odisha": ("strongly_non_veg", "frequent/daily"),
    "Bihar": ("strongly_non_veg", "frequent/daily"),
    "Jharkhand": ("strongly_non_veg", "frequent/daily"),
    "Goa": ("strongly_non_veg", "frequent/daily"),
    "Assam": ("strongly_non_veg", "frequent/daily"),
}


def community_vs_kb_conflicts():
    """Cross-check community_priors.csv (BASE) against KB §C1. Returns a list of conflict dicts.
    Does NOT silently resolve — the founder resolves (Task 3 D6)."""
    import csv, os
    conflicts = []
    csv_states = {}
    path = os.path.join(os.path.dirname(__file__), "..", "data", "source", "community_priors.csv")
    with open(path) as f:
        for r in csv.DictReader(f):
            csv_states[r["state"]] = r["diet_lean"]
    # normalise KB veg_leaning vs strongly_veg: treat 'veg_leaning' as compatible with strongly_veg
    def _fam(lean):
        if lean in ("strongly_veg", "veg_leaning"):
            return "veg"
        if lean in ("strongly_non_veg", "non_veg_leaning"):
            return "nonveg"
        return "mixed"
    for state, (kb_lean, _band) in KB_C1_LEAN.items():
        if state not in csv_states:
            conflicts.append(dict(state=state, kind="missing_in_csv", kb=kb_lean, csv=None))
            continue
        csv_lean = csv_states[state]
        if _fam(csv_lean) != _fam(kb_lean):
            conflicts.append(dict(state=state, kind="lean_family_mismatch", kb=kb_lean, csv=csv_lean))
    for state, csv_lean in csv_states.items():
        if state not in KB_C1_LEAN:
            conflicts.append(dict(state=state, kind="missing_in_kb", kb=None, csv=csv_lean))
    return conflicts


# ---------------------------------------------------------------------------
# Sub-zone resolution for comfort heroes: a household's home_state → the KB §R3 sub-zone key.
# Lets the West Maharashtra household resolve to 'West-MH' (Kanda Bhaji) not generic West.
# ---------------------------------------------------------------------------
STATE_TO_KB_SUBZONE = {
    "Maharashtra": "West-MH", "Goa": "West-MH",
    "Gujarat": "West-GJ", "Rajasthan": "North",
    "Tamil Nadu": "South-TN", "Andhra Pradesh": "South-TN", "Telangana": "South-TN",
    "Karnataka": "South-TN", "Kerala": "South-KL",
    "West Bengal": "East-WB", "Odisha": "East-WB", "Bihar": "East-WB", "Jharkhand": "East-WB",
    "Assam": "NE",
}
