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
    # The remaining cuisine_group values from cuisines_v4.csv (real 810-dish catalogue) that
    # weren't yet enumerated above — all genuinely foreign, so the KB §R1 "foreign/other -> Global"
    # rule (already the comment on chinese_asian above) now covers ALL of them explicitly instead
    # of only 3 of ~14. dish_count=187 matches the existing Global rows: it's the ZONE's total
    # (chinese_asian 50 + continental 33 + italian 30 + japanese 15 + thai 12 + korean 10 +
    # middle_eastern 10 + mexican 9 + vietnamese 8 + burmese 5 + bhutanese 4 + mediterranean 1 +
    # anglo_indian 0 + american 0 = 187 in the real catalogue), repeated per row exactly like the
    # three existing Global rows already do — not a per-cuisine_group count.
    ("japanese",         "Global",    187, "real"),
    ("korean",           "Global",    187, "real"),
    ("thai",             "Global",    187, "real"),
    ("vietnamese",       "Global",    187, "real"),
    ("middle_eastern",   "Global",    187, "real"),
    ("mexican",          "Global",    187, "real"),
    ("american",         "Global",    187, "real"),
    ("burmese",          "Global",    187, "real"),
    ("bhutanese",        "Global",    187, "real"),
    ("mediterranean",    "Global",    187, "real"),
    # anglo_indian: genuinely a boundary case (colonial-era Indian/British fusion, cuisines_v4.csv
    # gives it state_origin='Pan-India' rather than any single region or foreign country) — not a
    # core North/South/West/East/Central/Northeast/PanIndia regional palette, so it falls under the
    # KB's own "...or OTHER" half of "foreign/other -> Global", not a silent guess.
    ("anglo_indian",     "Global",    187, "real"),
]

# ---------------------------------------------------------------------------
# cuisine (data/source/cuisines_v4.csv `name`) -> cuisine_group, transcribed verbatim from that
# file (all 65 rows — real 810-dish catalogue's actual cuisine list, not the 10-cuisine fixture
# subset). This is the fix for the confirmed Phase G bug: ghar_re_core.catalogue previously built
# its cuisine->cuisine_group lookup from ghar_re_core.fixtures.CUISINES (only 10 entries), so any
# real-catalogue dish whose cuisine wasn't one of those 10 got cuisine_group=None -> zone=None
# (measured: 536 of 810 real dishes, 66%). Transcribed as a static table (like fixtures.CUISINES
# already is) rather than read live from cuisines_v4.csv at runtime, because a live CSV read would
# need cuisines_v4.csv added to ghar_re_service/scripts/export_bundle.py's CONFIG_FILES allow-list
# to keep working inside a baked deployment bundle — out of scope for this fix (export_bundle.py is
# explicitly not touched here). Verified identical to fixtures.CUISINES for all 10 legacy cuisines
# (same cuisine_group in both sources), so this introduces no drift for the 39-dish golden sample.
CUISINE_GROUP_MAP = {
    "american": "american", "andhra": "south_indian", "anglo_indian": "anglo_indian",
    "arunachali": "northeast_indian", "assamese": "east_indian", "awadhi": "mughlai_nawabi",
    "bengali": "east_indian", "bhutanese": "bhutanese", "bihari": "north_indian",
    "bundelkhandi": "north_indian", "burmese": "burmese", "chettinad": "south_indian",
    "chhattisgarhi": "central_indian", "chinese_authentic": "chinese_asian",
    "continental": "continental", "coorg": "south_indian", "delhi": "north_indian",
    "goan": "west_indian", "gujarati": "west_indian", "himachali": "north_indian",
    "hyderabadi": "mughlai_nawabi", "indian_bakery": "street_food",
    "indian_tibetan": "chinese_asian", "indo_chinese": "chinese_asian", "indori": "central_indian",
    "italian": "italian", "japanese": "japanese", "jharkhandi": "east_indian",
    "karnataka": "south_indian", "kashmiri": "north_indian", "kerala": "south_indian",
    "kolhapuri": "west_indian", "konkani": "west_indian", "korean": "korean",
    "kutchi": "west_indian", "lebanese": "middle_eastern", "madhya_pradesh": "central_indian",
    "maharashtrian": "west_indian", "malabar": "south_indian", "malvani": "west_indian",
    "mangalorean": "south_indian", "manipuri": "northeast_indian", "mediterranean": "mediterranean",
    "meghalayan": "northeast_indian", "mexican": "mexican",
    "middle_eastern_generic": "middle_eastern", "mizo": "northeast_indian",
    "mughlai": "mughlai_nawabi", "naga": "northeast_indian", "odia": "east_indian",
    "parsi": "west_indian", "punjabi": "north_indian", "rajasthani": "north_indian",
    "sikkimese": "northeast_indian", "sindhi": "north_indian",
    "street_food_generic": "street_food", "tamil": "south_indian", "telangana": "south_indian",
    "thai": "thai", "tripuri": "northeast_indian", "udupi": "south_indian", "up": "north_indian",
    "uttarakhandi": "north_indian", "vidarbha": "west_indian", "vietnamese": "vietnamese",
}

# ---------------------------------------------------------------------------
# State 2-letter code -> full name normalization.
#
# The live app writes profiles.home_state as the 2-letter code ("MP"), NOT the full name — it
# REFERENCES re_engine.re_states(state_code) (see mobile/src/onboarding/toHouseholdWrite.ts, which
# holds the authoritative name→code map for all 36 states/UTs). Every state-keyed structure in this
# engine (STATE_ZONE, community_priors, the persona-DB cohort_matrix/state_profile, comfort heroes)
# keys on the FULL NAME. So an unmapped code silently no-ops region resolution, comfort heroes,
# community priors AND the WP-16 cohort layer — the confirmed root cause of "weird" cross-regional
# plates for real users (test_10: home_state "MP" → region None → no cohort anchor). normalize_state()
# is applied at the RE entry (derivation.derive_theta) so the engine is robust to BOTH the code and
# the full name; a value that is already a full name (or an unknown token) passes through unchanged.
# ---------------------------------------------------------------------------
STATE_CODE_TO_NAME = {
    "AN": "Andaman & Nicobar Islands", "AP": "Andhra Pradesh", "AR": "Arunachal Pradesh",
    "AS": "Assam", "BR": "Bihar", "CH": "Chandigarh", "CT": "Chhattisgarh",
    "DN": "Dadra & Nagar Haveli and Daman & Diu", "DL": "Delhi", "GA": "Goa", "GJ": "Gujarat",
    "HR": "Haryana", "HP": "Himachal Pradesh", "JK": "Jammu & Kashmir", "JH": "Jharkhand",
    "KA": "Karnataka", "KL": "Kerala", "LA": "Ladakh", "LD": "Lakshadweep", "MP": "Madhya Pradesh",
    "MH": "Maharashtra", "MN": "Manipur", "ML": "Meghalaya", "MZ": "Mizoram", "NL": "Nagaland",
    "OD": "Odisha", "PY": "Puducherry", "PB": "Punjab", "RJ": "Rajasthan", "SK": "Sikkim",
    "TN": "Tamil Nadu", "TS": "Telangana", "TR": "Tripura", "UP": "Uttar Pradesh",
    "UK": "Uttarakhand", "WB": "West Bengal",
}


def normalize_state(value):
    """Map a 2-letter state code ('MP') to the full name the engine keys on ('Madhya Pradesh').
    A value that is already a full name — or any token not in the code table — is returned
    unchanged, so this is safe to apply unconditionally at the RE entry point."""
    if value is None:
        return value
    return STATE_CODE_TO_NAME.get(value.strip().upper(), value)


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
    """Build one COMFORT_HERO_MAP row. `verified` (True/False, matching the KB's own ✓/⚑ markers)
    decides the row's data_source: a KB-verified hero is 'real', an unverified one is 'stub' —
    this keeps that provenance rule in one place instead of repeating it on every row below."""
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
#
# ⚠️ KNOWN GAP, confirmed against the real 810-dish catalogue (surfaced by a failing e2e test,
# deliberately NOT fixed here — same discipline as pairing.py's b_protein comment): "Kanda Bhaji"
# (COMFORT_HERO_MAP's West-MH rain entry) does not exist under that name anywhere in
# ghar_re_service/data/bundle/catalogue.json, or under any close spelling — the comfort-hero lift
# for that specific entry is a silent no-op in production. Separately, COMFORT_HERO_MAP's
# "Pithla-Bhakri" (hyphen) has no entry here, so it falls back to itself literally — but the real
# catalogue's dish is named "Pithla Bhakri" (space), so that lift is also a silent no-op. West-MH
# rain still has two OTHER correctly-resolving heroes (Vada Pav, Sol Kadhi, both real dish names,
# neither needs an entry here), so this zone/weather combo isn't fully dead — just two of its four
# configured heroes are. Picking a replacement dish for "Kanda Bhaji" or fixing the
# "Pithla-Bhakri"/"Pithla Bhakri" mismatch is a recommendation-quality decision for the
# Founder/domain owner, not a mechanical fix — do not silently guess a substitution here.
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


# ---------------------------------------------------------------------------
# CLASS-FIRST COHORT LAYER — curated dish->class lookup (WP-15, retained by WP-16).
#
# Wires data/source/Indian_Meal_Cohort_Persona_DB_v3.xlsx (41 personas, 131 meal classes, 2952
# cohorts, 1050 curated class->dish rows) into the Core Spine master formula's own
# `w_cohort · S_cohort(x;cohort)` term — a term that existed in the frozen scoring equation since
# Spine v1.0 but had NO implementation until WP-15.
#
# THIS module now owns only the dish -> meal_class_code lookup. The cohort MATCHING and the graded
# class-affinity computation moved to ghar_re_core.cohort_intel in WP-16, which replaced WP-15's
# binary best-single-cohort-row match (the old `cohort_class_mix` / `_best_cohort_row` here) with a
# migration-blended, model-learned graded affinity that generalizes across household feature
# combinations. This keeps the two responsibilities separate: knowledge.py = authored reference
# tables; cohort_intel.py = the learned cohort model. See cohort_intel.py's docstring for the design.
#
# Class-fit remains one soft additive score term (never a filter, never a candidate-generation
# gate), and the cohort is matched LIVE from theta — no persona ID is ever stored or looked up
# (the retired RE-DOC-03 fixed-persona architecture stays retired; only its SCIENCE is un-retired).
#
# Coverage is HONEST, not padded: exact case-insensitive name match against the real 810-dish
# catalogue finds meal_class_code for 129 dishes (~16%). Every other dish's S_cohort term is
# exactly 0.0 — the same "absent term contributes nothing" pattern base()'s W_SIG already uses
# for unscored dishes, not a fabricated boost.
# ---------------------------------------------------------------------------
import csv as _csv
import os as _os

_DISH_TO_CLASS = None
_DISH_OVERRIDES = None
_DISH_TO_CLASSES = None  # dish -> full set of classes (multi-membership; WP-17.1)


def _load_class_first_csv(name):
    """Read an extracted class-first CSV from class_first_v1/ underneath ghar_re_core.config.SRC —
    the SAME config-directory seam every other runtime config file uses (respects
    GHAR_RE_CONFIG_DIR, so it resolves correctly from both a checked-out repo and the service's
    baked bundle; see RE-DOC-10 §8 / config.py on why a path relative to this file would break in a
    container). Callers cache into a module-level global so the file is parsed once per process."""
    from ghar_re_core.config import SRC
    path = _os.path.join(SRC, "class_first_v1", name)
    with open(path, newline="") as f:
        return list(_csv.DictReader(f))


def dish_to_class_code(dish_name):
    """dish_name -> meal_class_code. Two static, checked-in sources, in precedence order:
      1. the curated Class_Dish_Options_v3 map (case-insensitive EXACT match — authored truth), then
      2. dish_class_map.csv — WP-17's full-coverage nutritionist/chef classification: EVERY
         catalogue dish assigned its best meal class offline (classify_dishes.py), each row tagged
         method (curated_exact / chef_rubric) + confidence. This lifted coverage from 202/810 to
         810/810 — the coverage that was the ceiling on the whole class-first cohort plan.
    Still NO fuzzy matching at RUNTIME — both are static lookups over a reviewed, checked-in file, so
    the classification is a deterministic offline artifact, never a live guess. Returns None only if
    the dish is in neither source (e.g. a brand-new dish added after the last classify run)."""
    global _DISH_TO_CLASS, _DISH_OVERRIDES
    if _DISH_TO_CLASS is None:
        _DISH_TO_CLASS = {}
        for r in _load_class_first_csv("class_dish_options.csv"):
            _DISH_TO_CLASS.setdefault(r["dish_name"].strip().lower(), r["meal_class_code"])
        _DISH_OVERRIDES = {}
        try:
            for r in _load_class_first_csv("dish_class_map.csv"):
                if r["meal_class_code"]:
                    _DISH_OVERRIDES.setdefault(r["dish_name"].strip().lower(), r["meal_class_code"])
        except FileNotFoundError:
            pass  # map is optional; exact curated map still works without it
    key = dish_name.strip().lower()
    return _DISH_TO_CLASS.get(key) or _DISH_OVERRIDES.get(key)


def dish_to_class_codes(dish_name):
    """dish_name -> the FULL set of meal_class_codes the dish belongs to (WP-17.1 multi-membership).
    A dish is NOT one-to-one with a class: the same dal-rice is a lunch LD_DAL_RICE_COMFORT AND a
    light dinner DN_LIGHT_DAL_RICE. dish_to_class_code (above) still returns the single PRIMARY class
    (for S_cohort scoring + plan labelling); this returns every class — the primary plus every
    chef_rubric_secondary row in dish_class_map.csv, unioned with the curated exact map. Used to build
    a CLASS's dish pool (meal_planner.dishes_for_class / _class_dish_counts): without it the
    behavioural DN_ dinner classes held 0–1 dishes and the plan fell back to regional LD_ plates.
    Returns a possibly-empty frozenset (never None)."""
    global _DISH_TO_CLASS, _DISH_OVERRIDES, _DISH_TO_CLASSES
    if _DISH_TO_CLASSES is None:
        dish_to_class_code(dish_name)  # ensure the two static sources are parsed into the globals
        _DISH_TO_CLASSES = {}
        for k, c in (_DISH_TO_CLASS or {}).items():
            _DISH_TO_CLASSES.setdefault(k, set()).add(c)
        try:
            for r in _load_class_first_csv("dish_class_map.csv"):
                if r["meal_class_code"]:
                    _DISH_TO_CLASSES.setdefault(r["dish_name"].strip().lower(), set()).add(
                        r["meal_class_code"])
        except FileNotFoundError:
            pass
    return frozenset(_DISH_TO_CLASSES.get(dish_name.strip().lower(), ()))
