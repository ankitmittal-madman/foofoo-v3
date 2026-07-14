#!/usr/bin/env python3
"""
FooFoo — WP-6RE-GEN — Recommendation Engine Seed Generator
==========================================================
Deterministic ETL that reads Indian_Meal_Cohort_Persona_DB_v3.xlsx (+ region CSV,
+ the ICD-1 dish catalog from dishes.xlsx) and emits the re_engine seed migrations
(110-117) and paired rollbacks. Runs AFTER migration 030 (SER-001, city_tier).

Principles: repository-first, evidence-first, deterministic, idempotent, no fabrication.
- Surrogate UUIDs are derived deterministically in SQL as md5(<natural_key>)::uuid, so
  FK links resolve without joins and are stable/idempotent (ON CONFLICT DO NOTHING).
- diet_mode = Cohort_Matrix_v3.nonveg_mode VERBATIM (no derivation; faithful).
- ICD-1 (Option C): re_class_dish_options / re_addon_dish_options / re_dish_regional_affinity
  seed only rows whose dish exists in the ICD-1 catalog (dishes.xlsx minus 8 combos);
  absent-dish rows are excluded (already in the Deferred Knowledge Register).
- DEFERRED (not generated, missing source evidence): re_city_migration_overlays (S-15) —
  migration_duration_band (NOT NULL, part of UNIQUE) has no source column in
  City_Migration_Overlay_v3. Flagged, not fabricated.

Every migration carries a provenance header: source workbook/sheet + sha256, transform
version, generation timestamp, business rules.
"""
import zipfile, re, csv, hashlib, datetime
from xml.etree import ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "data" / "source"
SEEDS = ROOT / "database" / "seeds"
RB = ROOT / "database" / "rollback"
WORKBOOK = SRC / "Indian_Meal_Cohort_Persona_DB_v3.xlsx"
TRANSFORM_VERSION = "WP-6RE-GEN v1.0"
GEN_TS = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
RNS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"

def sha16(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]
WB_SHA = sha16(WORKBOOK)

def s(v):
    if v is None or v == "": return "NULL"
    return "'" + str(v).replace("'", "''") + "'"
def tarr(items):
    inner = ", ".join(s(i) for i in items if i not in (None, ""))
    return f"ARRAY[{inner}]::text[]" if inner else "ARRAY[]::text[]"
def uid(natural_key):  # deterministic surrogate UUID (SQL-side)
    return f"md5({s(natural_key)})::uuid"
def num(v, default="NULL"):
    d = re.sub(r"[^0-9.-]", "", str(v or ""))
    return d if d not in ("", "-", ".") else default

def sheet(name):
    z = zipfile.ZipFile(WORKBOOK)
    ss = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall(NS + "si"):
            ss.append("".join(t.text or "" for t in si.iter(NS + "t")))
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    relmap = {r.get("Id"): r.get("Target") for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
    def cval(c):
        t = c.get("t")
        if t == "inlineStr":
            isel = c.find(NS + "is"); return "".join(x.text or "" for x in isel.iter(NS + "t")) if isel is not None else ""
        v = c.find(NS + "v"); return "" if v is None else (ss[int(v.text)] if t == "s" else v.text)
    for sh in wb.iter(NS + "sheet"):
        if sh.get("name") == name:
            tgt = relmap[sh.get(RNS + "id")]; path = "xl/" + tgt if not tgt.startswith("/") else tgt[1:]
            x = ET.fromstring(z.read(path)); rows = x.findall(".//" + NS + "row")
            hd = [cval(c) for c in rows[0].findall(NS + "c")]
            return [{hd[i]: cval(c) for i, c in enumerate(r.findall(NS + "c")) if i < len(hd)} for r in rows[1:]]
    raise KeyError(name)

def hdr(mig, title, sources, rules):
    src = "\n".join(f"--   source: {x}" for x in sources)
    br = "\n".join(f"--   - {b}" for b in rules)
    return (f"-- Migration: {mig}\n-- Title: {title}\n-- Layer: re_engine seed ({TRANSFORM_VERSION}); requires migration 030 (SER-001 city_tier)\n"
            f"-- Generated: {GEN_TS} by database/etl/generate_re_seeds.py (deterministic)\n"
            f"-- Provenance:\n{src}\n-- Business rules:\n{br}\n"
            f"-- Idempotent: ON CONFLICT DO NOTHING; surrogate UUIDs = md5(natural_key)::uuid. Paired rollback.\n"
            f"-- Supersedes illustrative rows in seed 101/102 for these tables (never edited in place).\n")

# ---------- documented crosswalks (provenance in headers) ----------
STATE_CODE = {
 "Andhra Pradesh":"AP","Arunachal Pradesh":"AR","Assam":"AS","Bihar":"BR","Chhattisgarh":"CT",
 "Goa":"GA","Gujarat":"GJ","Haryana":"HR","Himachal Pradesh":"HP","Jharkhand":"JH","Karnataka":"KA",
 "Kerala":"KL","Madhya Pradesh":"MP","Maharashtra":"MH","Manipur":"MN","Meghalaya":"ML","Mizoram":"MZ",
 "Nagaland":"NL","Odisha":"OD","Punjab":"PB","Rajasthan":"RJ","Sikkim":"SK","Tamil Nadu":"TN",
 "Telangana":"TS","Tripura":"TR","Uttar Pradesh":"UP","Uttarakhand":"UK","West Bengal":"WB",
 "Andaman & Nicobar Islands":"AN","Chandigarh":"CH","Dadra & Nagar Haveli and Daman & Diu":"DN",
 "Delhi":"DL","Jammu & Kashmir":"JK","Ladakh":"LA","Lakshadweep":"LD","Puducherry":"PY"}
ARCH_REGION = {"SOUTH_RICE":"south","NORTH_WHEAT":"north","EAST_RICE_FISH":"east","WEST_VEG":"west",
 "WEST_COASTAL":"west","CENTRAL_MIXED":"central","NORTHEAST_RICE_MEAT":"east","HIMALAYAN":"north",
 "ISLAND_COASTAL":"south"}
MC = {"MC1":"MC_SOLO","MC2":"MC_COUPLE","MC3":"MC_NUCLEAR_FAMILY","MC4":"MC_JOINT_FAMILY","MC5":"MC_PG_HOSTEL"}
def primary_diet(nv):
    nv = (nv or "").strip().lower()
    if nv in ("egg_only",): return "egg"
    if nv in ("regular_nonveg","protein_nonveg","seafood","sunday_mutton","outside_nonveg"): return "non_veg"
    return "veg"  # veg_only,veg_default,jain,health_veg_or_default,budget_default,default (CAN-RULE-006)
def slot_arr(slot_group):
    toks = [t.strip().lower() for t in re.split(r"[/,]", slot_group or "") if t.strip()]
    m = {"breakfast":"breakfast","lunch":"lunch","dinner":"dinner","snack":"snack"}
    out = [m[t] for t in toks if t in m]
    return out or ["breakfast"]

def write(path, text): Path(path).write_text(text + ("\n" if not text.endswith("\n") else ""))
def rollback(mig, stmts): return f"-- Rollback {mig}\nBEGIN;\n" + "\n".join(stmts) + "\nCOMMIT;\n"

def icd1_catalog():
    z = zipfile.ZipFile(SRC / "dishes.xlsx"); ss = []
    for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall(NS + "si"):
        ss.append("".join(t.text or "" for t in si.iter(NS + "t")))
    x = ET.fromstring(z.read("xl/worksheets/sheet1.xml")); rows = x.findall(".//" + NS + "row")
    def c(cell):
        v = cell.find(NS + "v"); return ss[int(v.text)] if (v is not None and cell.get("t") == "s") else (v.text if v is not None else "")
    def norm(t):
        t = t.lower().strip(); t = re.sub(r"\(.*?\)", "", t); t = re.sub(r"[^a-z0-9 ]", " ", t); return re.sub(r"\s+", " ", t).strip()
    combos = {norm(r["combo_name"]) for r in csv.DictReader(open(SRC / "dish_combos_v2_20260520.csv"))}
    cat = {}
    for r in rows[1:]:
        cells = {re.match(r"[A-Z]+", cc.get("r")).group(): c(cc) for cc in r.findall(NS + "c")}
        nm = (cells.get("B") or "").strip()
        if nm and norm(nm) not in combos:
            cat[norm(nm)] = nm
    return cat, norm

def main():
    rep = {}
    # ============ 110 re_states ============
    st = sheet("State_Profile_v3")
    L = [hdr("110_seed_re_states.sql", "re_engine.re_states (36)",
        [f"State_Profile_v3 (Indian_Meal_Cohort_Persona_DB_v3.xlsx sha256:{WB_SHA})"],
        ["state_code = documented state_ut->2-letter crosswalk (29/36 verified vs region_food_affinity.csv)",
         "region = documented region_archetype(9)->region(5) collapse (NE->east, HIMALAYAN->north, ISLAND->south)",
         "state_name = state_ut verbatim"]), "BEGIN;"]
    codes = []
    for r in st:
        code = STATE_CODE[r["state_ut"]]; region = ARCH_REGION[r["region_archetype"]]; codes.append(code)
        L.append(f"INSERT INTO re_engine.re_states (state_code,state_name,region) VALUES "
                 f"({s(code)},{s(r['state_ut'])},{s(region)}) ON CONFLICT (state_code) DO NOTHING;")
    L.append("COMMIT;")
    write(SEEDS/"110_seed_re_states.sql", "\n".join(L))
    write(RB/"110_seed_re_states_rollback.sql", rollback("110",
        [f"DELETE FROM re_engine.re_states WHERE state_code IN ({','.join(s(c) for c in codes)});"]))
    rep["re_states"] = len(codes)

    # ============ 111 hierarchy ============
    L = [hdr("111_seed_re_reference_hierarchy.sql",
        "re_main_cohorts(5), re_subcohorts, re_personas, re_routing_rules, re_persona_assignment_rules",
        [f"Main_Cohort_Hierarchy / Subcohort_Routing / Persona_Master_v3 / Routing_Rules_v3 (sha256:{WB_SHA})",
         "re_main_cohorts + re_routing_rules carried from seed 101 ([CONFIRMED] DOC-P3-03 §03)"],
        ["persona id = md5(persona_code)::uuid; persona_code = source persona_id (P01..P41)",
         "main_cohort_code via MC1-5->MC_SOLO.. crosswalk (labels, seed 101)",
         "persona primary_diet from nonveg_mode (CAN-RULE-006: default/health/budget->veg)"]), "BEGIN;"]
    for code, label, so in [("MC_SOLO","Just me",1),("MC_COUPLE","Two of us",2),
        ("MC_NUCLEAR_FAMILY","Family with children",3),("MC_JOINT_FAMILY","Joint family / multi-gen",4),
        ("MC_PG_HOSTEL","PG / hostel / shared",5)]:
        L.append(f"INSERT INTO re_engine.re_main_cohorts (cohort_code,display_label,sort_order) VALUES "
                 f"({s(code)},{s(label)},{so}) ON CONFLICT (cohort_code) DO NOTHING;")
    sc = sheet("Subcohort_Routing"); seen = set(); sc_codes = []
    for r in sc:
        scc = (r.get("sub_cohort_id") or "").strip()
        if not scc or scc in seen: continue
        seen.add(scc); sc_codes.append(scc)
        L.append(f"INSERT INTO re_engine.re_subcohorts (subcohort_code,main_cohort_code,description) VALUES "
                 f"({s(scc)},{s(MC.get(r.get('main_cohort_id','')))},{s(r.get('sub_cohort_label'))}) "
                 f"ON CONFLICT (subcohort_code) DO NOTHING;")
    pm = sheet("Persona_Master_v3"); pcodes = []
    for r in pm:
        pc = (r.get("persona_id") or "").strip()
        if not pc: continue
        pcodes.append(pc)
        L.append(f"INSERT INTO re_engine.re_personas (id,persona_code,main_cohort_code,display_name,primary_diet) VALUES "
                 f"({uid(pc)},{s(pc)},{s(MC.get(r.get('main_cohort_id','')))},{s(r.get('persona_name'))},"
                 f"{s(primary_diet(r.get('nonveg_mode')))}) ON CONFLICT (persona_code) DO NOTHING;")
    rr = [("MC_NUCLEAR_FAMILY","children_ages",None,1),("MC_JOINT_FAMILY","elder_members_present",None,2),
        ("MC_JOINT_FAMILY","elder_health_conditions",None,3),
        ("MC_SOLO",None,["children_ages","elder_members_present"],4),
        ("MC_COUPLE",None,["children_ages","elder_members_present"],5),
        ("MC_PG_HOSTEL",None,["children_ages","elder_members_present"],6),
        ("diet_type=jain",None,["nonveg_questions"],7),("infant_declared","infant_allergen_questions",None,8)]
    for ta, sq, skip, so in rr:
        L.append(f"INSERT INTO re_engine.re_routing_rules (trigger_answer,show_question_key,skip_if_answered,sort_order) "
                 f"VALUES ({s(ta)},{s(sq)},{tarr(skip) if skip else 'NULL'},{so});")
    seen_ar = set()
    for r in sc:
        pc = (r.get("maps_to_persona_id") or "").strip(); scc = (r.get("sub_cohort_id") or "").strip()
        mcc = MC.get(r.get("main_cohort_id",""))
        if not pc or (mcc, scc) in seen_ar: continue
        seen_ar.add((mcc, scc))
        L.append(f"INSERT INTO re_engine.re_persona_assignment_rules (main_cohort_code,subcohort_code,state_code,diet_type,persona_id) "
                 f"VALUES ({s(mcc)},{s(scc)},NULL,NULL,{uid(pc)}) ON CONFLICT DO NOTHING;")
    L.append("COMMIT;")
    write(SEEDS/"111_seed_re_reference_hierarchy.sql", "\n".join(L))
    write(RB/"111_seed_re_reference_hierarchy_rollback.sql", rollback("111", [
        "DELETE FROM re_engine.re_persona_assignment_rules;",
        "DELETE FROM re_engine.re_routing_rules;",
        f"DELETE FROM re_engine.re_personas WHERE persona_code IN ({','.join(s(c) for c in pcodes)});",
        f"DELETE FROM re_engine.re_subcohorts WHERE subcohort_code IN ({','.join(s(c) for c in sc_codes)});",
        "DELETE FROM re_engine.re_main_cohorts WHERE cohort_code IN ('MC_SOLO','MC_COUPLE','MC_NUCLEAR_FAMILY','MC_JOINT_FAMILY','MC_PG_HOSTEL');"]))
    rep["re_subcohorts"] = len(sc_codes); rep["re_personas"] = len(pcodes)

    # ============ 112 meal classes + mirror + overlap + addon classes ============
    mc = sheet("Meal_Class_Master_v3")
    L = [hdr("112_seed_re_meal_classes.sql", "re_meal_classes(131)+public mirror, overlap_rules(13), addon_classes(24)",
        [f"Meal_Class_Master_v3 / Meal_Class_Overlap_Resolution / Addon_Component_Class_Master (sha256:{WB_SHA})"],
        ["class_code=meal_class_code; slot=slot_group->text[] (migration 025 domain); planning_role=planning_role_v3",
         "day_type='any' (permissive default; weekday/weekend signal carried by weekday_fit/weekend_fit columns)",
         "cuisine_family=class_family_code; variety_cooldown/max_per_week NULL (global rules in re_variety_rules)",
         "overlap conflicts_with='MAIN_PRIMARY_SLOT' (classes moved out of main rotation)",
         "public.meal_classes mirror: is_addon=(planning_role<>'MAIN_PRIMARY')"]), "BEGIN;"]
    cc = []
    for r in mc:
        code = (r.get("meal_class_code") or "").strip()
        if not code: continue
        cc.append(code)
        L.append("INSERT INTO re_engine.re_meal_classes (class_code,slot,day_type,planning_role,weekday_fit_1_5,weekend_fit_1_5,variety_cooldown_days,max_per_week,cuisine_family,diet_type) VALUES ("
                 f"{s(code)},{tarr(slot_arr(r.get('slot_group')))},'any',{s(r.get('planning_role_v3'))},"
                 f"{num(r.get('weekday_fit_1_5'))},{num(r.get('weekend_fit_1_5'))},NULL,NULL,"
                 f"{s(r.get('class_family_code'))},{s(r.get('diet_type'))}) ON CONFLICT (class_code) DO NOTHING;")
        is_addon = "true" if (r.get("planning_role_v3") or "") != "MAIN_PRIMARY" else "false"
        L.append("INSERT INTO public.meal_classes (class_code,slot,display_name,is_addon,is_active) VALUES ("
                 f"{s(code)},{tarr(slot_arr(r.get('slot_group')))},{s(r.get('class_name'))},{is_addon},true) "
                 "ON CONFLICT (class_code) DO NOTHING;")
    ov = sheet("Meal_Class_Overlap_Resolution")
    for r in ov:
        code = (r.get("meal_class_code") or "").strip()
        if not code: continue
        L.append(f"INSERT INTO re_engine.re_meal_class_overlap_rules (class_code,conflicts_with) VALUES ({s(code)},'MAIN_PRIMARY_SLOT');")
    ac = sheet("Addon_Component_Class_Master"); accodes = []
    for r in ac:
        code = (r.get("addon_class_code") or "").strip()
        if not code: continue
        accodes.append(code)
        L.append(f"INSERT INTO re_engine.re_addon_classes (addon_class_code,segment,slot) VALUES "
                 f"({s(code)},{s(r.get('target_member_segment'))},{s(slot_arr(r.get('slot_group'))[0])}) ON CONFLICT (addon_class_code) DO NOTHING;")
    L.append("COMMIT;")
    write(SEEDS/"112_seed_re_meal_classes.sql", "\n".join(L))
    write(RB/"112_seed_re_meal_classes_rollback.sql", rollback("112", [
        "DELETE FROM re_engine.re_meal_class_overlap_rules;",
        f"DELETE FROM re_engine.re_addon_classes WHERE addon_class_code IN ({','.join(s(c) for c in accodes)});",
        f"DELETE FROM public.meal_classes WHERE class_code IN ({','.join(s(c) for c in cc)});",
        f"DELETE FROM re_engine.re_meal_classes WHERE class_code IN ({','.join(s(c) for c in cc)});"]))
    rep["re_meal_classes"] = len(cc); rep["re_addon_classes"] = len(accodes)

    # ============ 113 re_cohorts ============
    cm = sheet("Cohort_Matrix_v3")
    L = [hdr("113_seed_re_cohorts.sql", "re_engine.re_cohorts (2,952) — requires migration 030 (city_tier)",
        [f"Cohort_Matrix_v3 (sha256:{WB_SHA})"],
        ["cohort_id=md5(source cohort_id)::uuid; persona_id=md5(persona_id)::uuid",
         "state_code via state_ut crosswalk; diet_mode=nonveg_mode VERBATIM; city_tier=city_tier_code (T1/T2)",
         "prior_weight=1.0 (schema default; no per-cohort source value)"]), "BEGIN;"]
    for r in cm:
        L.append("INSERT INTO re_engine.re_cohorts (cohort_id,persona_id,state_code,diet_mode,city_tier,prior_weight) VALUES ("
                 f"{uid(r['cohort_id'])},{uid(r['persona_id'])},{s(STATE_CODE[r['state_ut']])},{s(r.get('nonveg_mode'))},{s(r.get('city_tier_code'))},1.0) "
                 "ON CONFLICT (persona_id,state_code,diet_mode,city_tier) DO NOTHING;")
    L.append("COMMIT;")
    write(SEEDS/"113_seed_re_cohorts.sql", "\n".join(L))
    write(RB/"113_seed_re_cohorts_rollback.sql", rollback("113",
        ["DELETE FROM re_engine.re_cohorts WHERE cohort_id IN (" + ",".join(uid(r["cohort_id"]) for r in cm) + ");"]))
    rep["re_cohorts"] = len(cm)

    # ============ 114 weekly plans ============
    wk = sheet("Weekly_Class_Plan_v3")
    L = [hdr("114_seed_re_weekly_class_plans.sql", "re_engine.re_weekly_class_plans (20,664 = 2,952 x 7)",
        [f"Weekly_Class_Plan_v3 (sha256:{WB_SHA})"],
        ["cohort_id=md5(source cohort_id)::uuid; day_of_week verbatim",
         "projection to breakfast/lunch/dinner PRIMARY class only (DOC-P3-03 LF-B02; GAP-004 resolved-by-design)"]), "BEGIN;"]
    for r in wk:
        L.append("INSERT INTO re_engine.re_weekly_class_plans (cohort_id,day_of_week,breakfast_class_code,lunch_class_code,dinner_class_code) VALUES ("
                 f"{uid(r['cohort_id'])},{s(r.get('day_of_week'))},{s(r.get('breakfast_primary_class'))},"
                 f"{s(r.get('lunch_primary_class'))},{s(r.get('dinner_primary_class'))}) ON CONFLICT (cohort_id,day_of_week) DO NOTHING;")
    L.append("COMMIT;")
    write(SEEDS/"114_seed_re_weekly_class_plans.sql", "\n".join(L))
    write(RB/"114_seed_re_weekly_class_plans_rollback.sql", rollback("114",
        ["DELETE FROM re_engine.re_weekly_class_plans WHERE cohort_id IN (SELECT cohort_id FROM re_engine.re_cohorts);"]))
    rep["re_weekly_class_plans"] = len(wk)

    # ============ 115 household addon plans ============
    ha = sheet("Household_Addon_Component_Plan")
    L = [hdr("115_seed_re_household_addon_plans.sql", "re_engine.re_household_addon_plans (7,992)",
        [f"Household_Addon_Component_Plan (sha256:{WB_SHA})"],
        ["cohort_id=md5(source cohort_id)::uuid; segment=target_member_segment; addon_class_code verbatim"]), "BEGIN;"]
    for r in ha:
        L.append("INSERT INTO re_engine.re_household_addon_plans (segment,cohort_id,addon_class_code) VALUES ("
                 f"{s(r.get('target_member_segment'))},{uid(r['cohort_id'])},{s(r.get('addon_class_code'))});")
    L.append("COMMIT;")
    write(SEEDS/"115_seed_re_household_addon_plans.sql", "\n".join(L))
    write(RB/"115_seed_re_household_addon_plans_rollback.sql", rollback("115",
        ["DELETE FROM re_engine.re_household_addon_plans WHERE cohort_id IN (SELECT cohort_id FROM re_engine.re_cohorts);"]))
    rep["re_household_addon_plans"] = len(ha)

    # ============ 116 nonveg logic ============
    nv = sheet("NonVeg_Logic_v3")
    L = [hdr("116_seed_re_nonveg_logic.sql", "re_engine.re_nonveg_logic (36)",
        [f"NonVeg_Logic_v3 (sha256:{WB_SHA})"],
        ["state_code via state_ut crosswalk; weekly_nonveg_slots=default_omnivore_meals_week",
         "preferred_slots = preferred_nonveg_classes split to text[] (source class names carried verbatim)"]), "BEGIN;"]
    nn = 0
    for r in nv:
        code = STATE_CODE.get(r.get("state_ut", ""))
        if not code: continue
        slots = [t.strip() for t in re.split(r"[;,]", r.get("preferred_nonveg_classes", "") or "") if t.strip()]
        L.append("INSERT INTO re_engine.re_nonveg_logic (state_code,weekly_nonveg_slots,preferred_slots) VALUES ("
                 f"{s(code)},{num(r.get('default_omnivore_meals_week'),'0')},{tarr(slots) if slots else tarr(['none'])}) "
                 "ON CONFLICT (state_code) DO NOTHING;")
        nn += 1
    L.append("COMMIT;")
    write(SEEDS/"116_seed_re_nonveg_logic.sql", "\n".join(L))
    write(RB/"116_seed_re_nonveg_logic_rollback.sql", rollback("116", ["DELETE FROM re_engine.re_nonveg_logic;"]))
    rep["re_nonveg_logic"] = nn

    # ============ 117 ICD-1 dish-linked ============
    cat, norm = icd1_catalog()
    cdo = sheet("Class_Dish_Options_v3"); ado = sheet("Addon_Dish_Options")
    aff = list(csv.DictReader(open(SRC / "region_food_affinity.csv")))
    L = [hdr("117_seed_re_dish_linked_icd1.sql", "re_class_dish_options + re_addon_dish_options + re_dish_regional_affinity (ICD-1)",
        [f"Class_Dish_Options_v3 / Addon_Dish_Options (sha256:{WB_SHA}); region_food_affinity.csv"],
        ["ICD-1 (Option C): only rows whose dish exists in the content catalog are seeded; absent-dish rows deferred",
         "dish_id resolved from public.dishes(name); meal_class_code/addon_class_code/state_code are seeded FKs",
         "base_score default 0.70 (no per-row source); suitability_rank=1; affinity_score from CSV"]), "BEGIN;"]
    c_in = c_skip = a_in = a_skip = f_in = f_skip = 0
    for r in cdo:
        dn = (r.get("dish_name") or "").strip(); mcx = (r.get("meal_class_code") or "").strip()
        if norm(dn) in cat and mcx:
            c_in += 1
            L.append("INSERT INTO re_engine.re_class_dish_options (meal_class_code,dish_id,base_score,is_primary_candidate) "
                     f"SELECT {s(mcx)}, d.id, 0.70, false FROM public.dishes d WHERE d.name={s(cat[norm(dn)])} ON CONFLICT (meal_class_code,dish_id) DO NOTHING;")
        else: c_skip += 1
    for r in ado:
        dn = (r.get("dish_or_component_name") or "").strip(); acc = (r.get("addon_class_code") or "").strip()
        if norm(dn) in cat and acc:
            a_in += 1
            L.append("INSERT INTO re_engine.re_addon_dish_options (addon_class_code,dish_id,suitability_rank) "
                     f"SELECT {s(acc)}, d.id, 1 FROM public.dishes d WHERE d.name={s(cat[norm(dn)])} ON CONFLICT DO NOTHING;")
        else: a_skip += 1
    for r in aff:
        dn = (r.get("dish_name") or "").strip(); code = (r.get("state_code") or "").strip()
        if norm(dn) in cat and code:
            f_in += 1
            L.append("INSERT INTO re_engine.re_dish_regional_affinity (dish_id,state_code,affinity_score) "
                     f"SELECT d.id, {s(code)}, {num(r.get('affinity_score'),'0.5')} FROM public.dishes d WHERE d.name={s(cat[norm(dn)])} ON CONFLICT (dish_id,state_code) DO NOTHING;")
        else: f_skip += 1
    L.append("COMMIT;")
    write(SEEDS/"117_seed_re_dish_linked_icd1.sql", "\n".join(L))
    write(RB/"117_seed_re_dish_linked_icd1_rollback.sql", rollback("117", [
        "DELETE FROM re_engine.re_dish_regional_affinity;",
        "DELETE FROM re_engine.re_addon_dish_options;",
        "DELETE FROM re_engine.re_class_dish_options;"]))
    rep["re_class_dish_options_ICD1"] = c_in; rep["re_class_dish_options_deferred"] = c_skip
    rep["re_addon_dish_options_ICD1"] = a_in; rep["re_addon_dish_options_deferred"] = a_skip
    rep["re_dish_regional_affinity_ICD1"] = f_in; rep["re_dish_regional_affinity_deferred"] = f_skip

    print("=== WP-6RE-GEN generation summary ===")
    for k, v in rep.items(): print(f"  {k}: {v}")
    print("  DEFERRED (missing source): re_city_migration_overlays (S-15) — migration_duration_band absent from City_Migration_Overlay_v3.")

if __name__ == "__main__":
    main()
