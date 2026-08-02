"""
prepare_cohort_intel — OFFLINE data-prep + model training for the WP-16 Cohort Intelligence layer.

Reads data/source/Indian_Meal_Cohort_Persona_DB_v3.xlsx (the authored "science", precomputed) and
produces the two RUNTIME artifacts the live engine actually loads (never the .xlsx at runtime):

  data/source/class_first_v1/
    migration_overlay.csv      - City_Migration_Overlay_v3 (origin x dest -> home/local/nat blend)
    state_profile.csv          - State_Profile_v3 (state -> region_archetype, class pools, nonveg)
    nonveg_logic.csv           - NonVeg_Logic_v3 (state -> weekly nonveg/egg cadence)
    persona_master.csv         - Persona_Master_v3 (41 sub-cohort anchors + boost classes)
    subcohort_routing.csv      - Subcohort_Routing (main->sub cohort routing)
    main_cohort_hierarchy.csv  - Main_Cohort_Hierarchy (5 onboarding main cohorts)
    cohort_class_model.json    - the TRAINED factorized class-affinity model (see below)

THE MODEL (cohort_class_model.json)
-----------------------------------
This is the "make it as intelligent as the excel, derived not copied" core (WP-16). The excel's
Weekly_Class_Plan_v3 (20,664 rows = 2,952 cohorts x 7 days) is treated as an authored LABELLED
dataset: for every (cohort, day-of-week, slot) it names a primary/secondary/tertiary meal class.
Joined to each cohort's feature row (state, region, city tier, time-pressure, nonveg mode, main
cohort, lifecycle/health), those become (features, slot, day-type) -> class training examples,
weighted primary=3 / secondary=2 / tertiary=1.

We fit a FACTORIZED LOG-LINEAR (Naive-Bayes-style) affinity model: for each (slot, day-type) and
each feature value v, a smoothed class-propensity distribution p_{f,v}(class). A household's
affinity for a class is the pooled product of its feature factors (sum of log-propensities),
softmax-normalized over the slot's classes, then scaled so the best class = 1.0. This GENERALIZES:
a household whose exact state x tier x persona cohort was never enumerated in the excel still gets a
sensible graded plan from the product of its individual feature propensities -- learned from data,
not a nearest-row lookup, and not a copy of any single precomputed cohort row.

Only features RECOMPUTABLE from theta at runtime are used (see ghar_re_core/cohort_intel.py's
theta_features()), so the model is actually usable live. Pure-Python/JSON output: the runtime loads
it with the stdlib json module and scores with no numpy/sklearn dependency, keeping the Fly.io
bundle lean (RE-DOC-10 section 8 baked-bundle contract).

Run:  cd ghar_re_service && PYTHONPATH=..:. python3 -m ghar_re_service.scripts.prepare_cohort_intel
"""

import csv
import json
import math
import os

import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
XLSX = os.path.join(REPO, "data", "source", "Indian_Meal_Cohort_Persona_DB_v3.xlsx")
OUT = os.path.join(REPO, "data", "source", "class_first_v1")

SLOTS = ["breakfast", "lunch", "snack", "dinner"]
DAYTYPES = ["weekday", "weekend"]
# primary/secondary/tertiary label weights (authored preference ordering -> soft supervision).
RANK_WEIGHT = {"primary": 3.0, "secondary": 2.0, "tertiary": 1.0}
LAPLACE = 0.5  # smoothing so an unseen (feature,class) pair is small-but-nonzero, never a hard 0.

# The feature columns the model factorizes over. EVERY one must be reproducible from theta at
# runtime by ghar_re_core.cohort_intel.theta_features() — that is the contract that makes the model
# usable live rather than only replayable on the training cohorts.
FEATURES = [
    "state_ut",
    "region_archetype",
    "city_tier_code",
    "main_cohort_id",
    "time_pressure",
    "nonveg_mode",
]


def _rows(ws):
    """Yield each data row of a worksheet as a dict keyed by its header row."""
    it = ws.iter_rows(values_only=True)
    header = [str(h) if h is not None else "" for h in next(it)]
    for r in it:
        yield dict(zip(header, r, strict=False))


def _dump_csv(name, header, rows):
    """Write one extracted sheet to class_first_v1/<name> with an explicit column order."""
    path = os.path.join(OUT, name)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in header})
    print(f"  wrote {name} ({len(rows)} rows)")


def extract_aux(wb):
    """Extract the auxiliary reference sheets the runtime cohort layer joins against."""
    print("Extracting auxiliary CSVs...")
    _dump_csv(
        "migration_overlay.csv",
        [
            "origin_state_ut",
            "destination_group_code",
            "destination_group_name",
            "home_state_signature_weight",
            "current_city_lifestyle_weight",
            "national_modern_weight",
            "overlay_meal_classes",
            "planning_rule",
        ],
        list(_rows(wb["City_Migration_Overlay_v3"])),
    )
    _dump_csv(
        "state_profile.csv",
        [
            "state_id",
            "state_ut",
            "region_archetype",
            "tier1_or_metro_proxy_cities",
            "tier2_representative_cities",
            "nonveg_intensity",
            "primary_staple_base",
            "breakfast_class_pool",
            "weekday_lunch_class_pool",
            "weekday_dinner_class_pool",
            "weekend_special_class_pool",
            "snack_class_pool",
            "nonveg_class_pool",
        ],
        list(_rows(wb["State_Profile_v3"])),
    )
    _dump_csv(
        "nonveg_logic.csv",
        [
            "state_ut",
            "nonveg_intensity",
            "default_omnivore_meals_week",
            "egg_meals_week_default",
            "chicken_meals_week_default",
            "fish_or_seafood_meals_week_default",
            "mutton_or_red_meat_meals_week_default",
            "preferred_nonveg_classes",
        ],
        list(_rows(wb["NonVeg_Logic_v3"])),
    )
    _dump_csv(
        "persona_master.csv",
        [
            "persona_id",
            "persona_name",
            "age_band",
            "household_stage",
            "lifecycle_health",
            "cook_dependency",
            "time_pressure",
            "nonveg_mode",
            "bf_boost_classes",
            "ld_boost_classes",
            "sn_boost_classes",
            "dn_boost_classes",
            "main_cohort_id",
            "sub_cohort_id",
            "sub_cohort_label",
            "can_be_overlay",
        ],
        list(_rows(wb["Persona_Master_v3"])),
    )
    _dump_csv(
        "subcohort_routing.csv",
        [
            "main_cohort_id",
            "main_cohort_label",
            "sub_cohort_id",
            "sub_cohort_label",
            "maps_to_persona_id",
            "persona_name",
            "show_as_chip_text",
        ],
        list(_rows(wb["Subcohort_Routing"])),
    )
    _dump_csv(
        "main_cohort_hierarchy.csv",
        ["main_cohort_id", "main_cohort_label", "user_understands_as"],
        list(_rows(wb["Main_Cohort_Hierarchy"])),
    )


def build_cohort_features(wb):
    """cohort_id -> {feature: value} using Cohort_Matrix_v3 joined to State_Profile_v3 for the
    region_archetype (Cohort_Matrix has no region column of its own)."""
    state_region = {r["state_ut"]: r["region_archetype"] for r in _rows(wb["State_Profile_v3"])}
    feats = {}
    for r in _rows(wb["Cohort_Matrix_v3"]):
        cid = r["cohort_id"]
        feats[cid] = {
            "state_ut": r["state_ut"],
            "region_archetype": state_region.get(r["state_ut"], "UNKNOWN"),
            "city_tier_code": r["city_tier_code"],
            "main_cohort_id": r["main_cohort_id"],
            "time_pressure": (r["time_pressure"] or "medium"),
            "nonveg_mode": (r["nonveg_mode"] or "default"),
        }
    return feats


def train_model(wb, cohort_feats):
    """Fit the factorized class-affinity model from Weekly_Class_Plan_v3. Returns the JSON-able
    model dict. Counting-based ML: weighted class counts per (slot, day-type, feature, value),
    turned into smoothed log-propensities. Deterministic — same xlsx always gives the same model."""
    # counts[(slot, daytype)][feature][value][class] = weighted count
    counts = {(s, d): {f: {} for f in FEATURES} for s in SLOTS for d in DAYTYPES}
    classes = {(s, d): set() for s in SLOTS for d in DAYTYPES}
    n_examples = 0

    for row in _rows(wb["Weekly_Class_Plan_v3"]):
        cid = row["cohort_id"]
        cf = cohort_feats.get(cid)
        if cf is None:
            continue
        daytype = "weekend" if (row.get("weekday_weekend") == "Weekend") else "weekday"
        for slot in SLOTS:
            key = (slot, daytype)
            for rank, w in RANK_WEIGHT.items():
                cls = row.get(f"{slot}_{rank}_class")
                if not cls or cls == "none":
                    continue
                classes[key].add(cls)
                for f in FEATURES:
                    v = cf[f]
                    fv = counts[key][f].setdefault(v, {})
                    fv[cls] = fv.get(cls, 0.0) + w
                    n_examples += 1

    # counts -> smoothed log-propensity p_{f,v}(class) over the slot's class vocabulary.
    model = {
        "meta": {
            "trained_from": "Indian_Meal_Cohort_Persona_DB_v3.xlsx :: Weekly_Class_Plan_v3",
            "features": FEATURES,
            "rank_weights": RANK_WEIGHT,
            "laplace": LAPLACE,
            "n_label_examples": n_examples,
            "model_type": "factorized_loglinear_naive_bayes",
            "note": (
                "Per (slot,day-type,feature,value): smoothed class propensity. Runtime pools "
                "log-propensities across a household's feature values, softmax over classes, "
                "then scales so the top class = 1.0. See prepare_cohort_intel.py docstring."
            ),
        },
        "slots": {},
    }
    for (slot, daytype), fmap in counts.items():
        vocab = sorted(classes[(slot, daytype)])
        vset = set(vocab)
        part = {"classes": vocab, "features": {}}
        for f in FEATURES:
            part["features"][f] = {}
            for v, cls_counts in fmap[f].items():
                total = sum(cls_counts.get(c, 0.0) for c in vocab) + LAPLACE * len(vocab)
                logp = {}
                for c in vocab:
                    p = (cls_counts.get(c, 0.0) + LAPLACE) / total
                    logp[c] = round(math.log(p), 5)
                part["features"][f][v] = logp
        model["slots"][f"{slot}|{daytype}"] = part
        # keep vset referenced (defensive; vocab already filters)
        assert vset == set(vocab)
    return model


import re  # noqa: E402  (kept near its only use — the offline override matcher below)

CATALOGUE = os.path.join(REPO, "ghar_re_service", "data", "bundle", "catalogue.json")


def _norm_tokens(name):
    """Normalize a dish name to a token list for the override matcher: drop parenthetical
    qualifiers ('Lassi (Sweet)' -> 'lassi'), lowercase, strip punctuation."""
    name = re.sub(r"\([^)]*\)", "", name)
    return re.sub(r"[^a-z0-9 ]", " ", name.lower()).split()


def generate_overrides():
    """WP16-F1: raise dish->class coverage PRECISION-SAFELY, offline, into a reviewed static file
    (class_first_v1/dish_class_overrides.csv) that knowledge.dish_to_class_code consults AFTER the
    exact curated map — so there is still NO fuzzy matching at runtime, only a checked-in lookup.

    Rule: a real-catalogue dish that has no exact curated class is matched to a curated class ONLY
    when EVERY curated dish name whose token set is a subset/superset of the dish's tokens agrees on
    the same meal_class_code. Ambiguous dishes (e.g. 'Chole' -> chole-bhature vs rajma-chole; 'Poha'
    -> multiple classes) stay unmatched (0.0) rather than being guessed wrong. This is deliberately
    HIGH-PRECISION, not high-recall: a wrong class would push a dish into the wrong cohort plan,
    which is worse than an honest 0. The output is committed and reviewable, never applied blind."""
    if not os.path.isfile(CATALOGUE):
        print("  (skip overrides: bundle catalogue.json not present)")
        return
    rows = list(_rows_csv(os.path.join(OUT, "class_dish_options.csv")))
    exact = {}
    cur = []  # (tokenset, class)
    for r in rows:
        toks = _norm_tokens(r["dish_name"])
        if toks:
            exact.setdefault(" ".join(toks), r["meal_class_code"])
            cur.append((set(toks), r["meal_class_code"]))
    with open(CATALOGUE) as cf:
        dishes = [d["name"] for d in json.load(cf)]
    overrides = []
    for name in dishes:
        toks = _norm_tokens(name)
        key = " ".join(toks)
        if not toks or key in exact:
            continue  # empty or already covered by the exact curated map
        dt = set(toks)
        cands = {c for ts, c in cur if ts and (ts <= dt or dt <= ts)}
        if len(cands) == 1:  # unanimous agreement -> safe
            overrides.append((name, next(iter(cands))))
    overrides.sort()
    path = os.path.join(OUT, "dish_class_overrides.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["dish_name", "meal_class_code", "match_method"])
        for name, code in overrides:
            w.writerow([name, code, "unanimous_token_agreement"])
    print(f"  wrote dish_class_overrides.csv ({len(overrides)} precision-safe overrides)")


def _rows_csv(path):
    """Small local CSV reader (the aux CSVs are already written by the time overrides run)."""
    with open(path, newline="") as f:
        yield from csv.DictReader(f)


def main():
    """Extract aux CSVs, train the model, then generate the precision-safe dish->class overrides."""
    os.makedirs(OUT, exist_ok=True)
    wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
    extract_aux(wb)
    print("Training factorized class-affinity model...")
    cohort_feats = build_cohort_features(wb)
    model = train_model(wb, cohort_feats)
    path = os.path.join(OUT, "cohort_class_model.json")
    with open(path, "w") as f:
        json.dump(model, f, separators=(",", ":"), sort_keys=True)
    size_kb = os.path.getsize(path) / 1024.0
    print(
        f"  wrote cohort_class_model.json ({model['meta']['n_label_examples']} label examples, "
        f"{len(model['slots'])} slot/day-type partitions, {size_kb:.0f} KB)"
    )
    print("Generating precision-safe dish->class overrides (WP16-F1)...")
    generate_overrides()


if __name__ == "__main__":
    main()
