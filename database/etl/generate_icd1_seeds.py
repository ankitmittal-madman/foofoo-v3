#!/usr/bin/env python3
"""
FooFoo — WP-6D-gen — Canonical Seed Generator (ICD-1 content layer)
====================================================================

Deterministic ETL that reads the Founder-supplied canonical source files in
data/source/ and emits the ICD-1 content-layer seed migrations (103-109),
their paired rollbacks, and the Deferred Knowledge Register.

Design principles (per WP-6 governance + Founder directives 2026-07-14):
- Repository-first, evidence-first: every value comes from a source file; no
  fabrication, no placeholder rows, no invented dishes/nutrition/mappings.
- Deterministic + idempotent: stable ordering; INSERT ... ON CONFLICT DO NOTHING;
  paired rollbacks. Re-running produces byte-identical output.
- Provenance: every emitted migration carries a header naming the source
  workbook/sheet, transformation version, generation timestamp, and the
  business rules applied (Founder standing rule 2026-07-14).
- ICD-1 (Option C): only dishes present in the canonical master dataset
  (dishes.xlsx / dishes_810) are seeded. Recommendation entries that reference
  dishes absent from that catalog are NOT fabricated; they are recorded in the
  Deferred Knowledge Register for future knowledge expansion.

SCOPE: content layer only (public schema). The re_engine reference/persona/
cohort/plan/class layer is intentionally NOT generated here — several of its
NOT-NULL columns (day_type, cuisine_family, diet_mode, primary_diet) and its
key crosswalks (state_code/region, persona_code) and cohort tier-vs-diet_mode
structure (GAP-002) have no value in the master workbook and require a separate
RE-Reference-Normalization decision. Generating them now would require inventing
business data, which is forbidden.

This script only reads the source files and writes .sql / register files. It
does NOT connect to any database. Loading is WP-6E (Founder-approved).
"""
import csv, re, zipfile, hashlib, datetime
from xml.etree import ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "data" / "source"
SEEDS = ROOT / "database" / "seeds"
ROLLBACK = ROOT / "database" / "rollback"
REGISTER_DIR = ROOT / "docs" / "project-history" / "work-packages"

TRANSFORM_VERSION = "WP-6D-gen v1.0"
GEN_TS = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
RNS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"

# ------------------------------------------------------------------ helpers
def sha256(path):
    h = hashlib.sha256()
    h.update(Path(path).read_bytes())
    return h.hexdigest()

def sql_str(v):
    """Escape a Python value as a SQL string literal (or NULL)."""
    if v is None or v == "":
        return "NULL"
    return "'" + str(v).replace("'", "''") + "'"

def sql_bool(v):
    return "true" if str(v).strip().upper() in ("Y", "YES", "TRUE", "1") else "false"

def text_array(items):
    inner = ", ".join(sql_str(i) for i in items if i not in (None, ""))
    return f"ARRAY[{inner}]::text[]" if inner else "ARRAY[]::text[]"

def read_csv(name):
    with open(SRC / name, newline="") as f:
        return list(csv.DictReader(f))

def xlsx_sheet(path, sheet_name):
    """Return list of dict rows for a sheet, keyed by header, using column-letter alignment."""
    z = zipfile.ZipFile(path)
    ss = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall(NS + "si"):
            ss.append("".join(t.text or "" for t in si.iter(NS + "t")))
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    relmap = {r.get("Id"): r.get("Target")
              for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
    def cval(c):
        t = c.get("t")
        if t == "inlineStr":
            isel = c.find(NS + "is")
            return "".join(x.text or "" for x in isel.iter(NS + "t")) if isel is not None else ""
        v = c.find(NS + "v")
        if v is None:
            return ""
        return ss[int(v.text)] if t == "s" else v.text
    for s in wb.iter(NS + "sheet"):
        if s.get("name") == sheet_name:
            tgt = relmap[s.get(RNS + "id")]
            spath = "xl/" + tgt if not tgt.startswith("/") else tgt[1:]
            sh = ET.fromstring(z.read(spath))
            rows = sh.findall(".//" + NS + "row")
            # header by column letter
            hdr = {}
            for c in rows[0].findall(NS + "c"):
                col = re.match(r"[A-Z]+", c.get("r")).group()
                hdr[col] = cval(c)
            out = []
            for r in rows[1:]:
                d = {}
                for c in r.findall(NS + "c"):
                    col = re.match(r"[A-Z]+", c.get("r")).group()
                    if col in hdr:
                        d[hdr[col]] = cval(c)
                out.append(d)
            return out
    raise KeyError(sheet_name)

def header_block(migration, title, sources, business_rules):
    src_lines = "\n".join(f"--   source: {s}" for s in sources)
    br_lines = "\n".join(f"--   - {b}" for b in business_rules)
    return f"""-- Migration: {migration}
-- Title: {title}
-- Layer: ICD-1 content ({TRANSFORM_VERSION})
-- Generated: {GEN_TS}  by database/etl/generate_icd1_seeds.py (deterministic)
-- Transformation version: {TRANSFORM_VERSION}
-- Provenance (source workbook/sheet + checksum):
{src_lines}
-- Business rules applied:
{br_lines}
-- Idempotency: INSERT ... ON CONFLICT DO NOTHING. Re-runnable. Paired _rollback.sql.
-- NOTE: supersedes the illustrative rows in 101/102 for the same tables (never edited in place).
"""

def norm_name(s):
    s = s.lower().strip()
    s = re.sub(r"\(.*?\)", "", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()

# ------------------------------------------------------------------ allergen map
# Provenance: DOC-P3-03 §07 (line 163) — frozen 7-bit allergen model; CDM Invariant 3.
ALLERGEN_BIT = {
    "peanuts": 1, "tree_nuts": 1,   # bit 0 — Nuts / peanuts
    "dairy": 2,                     # bit 1
    "gluten": 4,                    # bit 2
    "shellfish": 8,                 # bit 3
    "egg_allergen": 16,             # bit 4
    "soy": 32,                      # bit 5
    "sesame": 64,                   # bit 6
    # fish, mustard -> no bit in the frozen model (safety-scope decision, deferred).
}
ALLERGEN_UNMAPPED = {"fish", "mustard"}

DIFFICULTY_MAP = {"easy": "beginner", "medium": "intermediate", "hard": "advanced"}

def main():
    report = {}
    checksums = {f.name: sha256(f)[:16] for f in SRC.iterdir() if f.is_file()}

    # ===================== 103 — ingredients =====================
    ing = read_csv("ingredients_v5.csv")
    ing_names = set()
    unmapped_allergen = []
    lines = [header_block(
        "103_seed_ingredients.sql", "public.ingredients — canonical ingredient set",
        [f"ingredients_v5.csv (sha256:{checksums['ingredients_v5.csv']}) — {len(ing)} rows"],
        ["name = source `name` (slug form, so dish ingredient tokens resolve) [TR-001/002]",
         "is_veg = (diet_type == 'veg')  [source diet_type in {veg,non_veg,egg}]",
         "is_vegan = (is_vegan == 'Y')  [Batch2 B2-CAN-RULE-002]",
         "is_jain_excluded = (is_jain_compatible == 'N')  [polarity inversion, TR-007; Batch2 Attribute Matrix]",
         "allergen_flags = bitwise OR of allergen_type->bit  [TR-008; DOC-P3-03 §07 L163 7-bit model]",
         "allergen types 'fish','mustard' have no frozen bit -> contribute 0 (deferred safety-scope)"]),
        "SET client_min_messages = warning;",
        "BEGIN;"]
    for r in ing:
        name = r["name"].strip()
        if not name or name in ing_names:
            continue
        ing_names.add(name)
        is_veg = sql_bool("Y" if r["diet_type"].strip() == "veg" else "N")
        is_vegan = sql_bool(r.get("is_vegan", "N"))
        is_jain_excluded = sql_bool("Y" if r.get("is_jain_compatible", "").strip().upper() == "N" else "N")
        flags = 0
        if r.get("is_allergen", "").strip().upper() == "Y":
            at = r.get("allergen_type", "").strip().lower()
            if at in ALLERGEN_BIT:
                flags |= ALLERGEN_BIT[at]
            elif at in ALLERGEN_UNMAPPED:
                unmapped_allergen.append((name, at))
        is_active = sql_bool(r.get("is_active", "Y"))
        lines.append(
            f"INSERT INTO public.ingredients (name,is_veg,is_vegan,is_jain_excluded,allergen_flags,is_active) "
            f"VALUES ({sql_str(name)},{is_veg},{is_vegan},{is_jain_excluded},{flags},{is_active}) "
            f"ON CONFLICT (name) DO NOTHING;")
    lines.append("COMMIT;")
    (SEEDS / "103_seed_ingredients.sql").write_text("\n".join(lines) + "\n")
    (ROLLBACK / "103_seed_ingredients_rollback.sql").write_text(
        "-- Rollback 103 — remove canonical ingredient set\nBEGIN;\nDELETE FROM public.ingredients WHERE name IN (\n  "
        + ",\n  ".join(sql_str(n) for n in sorted(ing_names)) + "\n);\nCOMMIT;\n")
    report["ingredients"] = len(ing_names)
    report["allergen_unmapped"] = unmapped_allergen

    # ===================== 104 — tags =====================
    tags = read_csv("tags_v4.csv")
    tag_keys = []
    seen = set()
    lines = [header_block(
        "104_seed_tags.sql", "public.tags — controlled genome/vocabulary tags",
        [f"tags_v4.csv (sha256:{checksums['tags_v4.csv']}) — {len(tags)} rows"],
        ["tag_name = source `value` [TR-001/002]; dimension = source `category`",
         "tier = int(tier_x)  [TR-009]; is_user_facing = (is_user_facing=='Y')",
         "vector_position: provisional (900000+i) at insert, then deterministically reassigned",
         "  by public.fn_assign_tag_vector_positions() (migration 023) — ORDER BY tier,dimension,tag_name"]),
        "BEGIN;"]
    i = 0
    for r in tags:
        dim = r["category"].strip()
        val = r["value"].strip()
        key = (dim, val)
        if key in seen:
            continue
        seen.add(key)
        tier = re.sub(r"[^0-9]", "", r.get("tier", "")) or "3"
        uf = sql_bool(r.get("is_user_facing", "N"))
        lines.append(
            f"INSERT INTO public.tags (tag_name,dimension,tier,is_user_facing,vector_position) "
            f"VALUES ({sql_str(val)},{sql_str(dim)},{int(tier)},{uf},{900000 + i}) "
            f"ON CONFLICT (dimension,tag_name) DO NOTHING;")
        tag_keys.append(key)
        i += 1
    lines.append("-- Deterministic genome-vector position assignment (migration 023):")
    lines.append("SELECT public.fn_assign_tag_vector_positions();")
    lines.append("COMMIT;")
    (SEEDS / "104_seed_tags.sql").write_text("\n".join(lines) + "\n")
    (ROLLBACK / "104_seed_tags_rollback.sql").write_text(
        "-- Rollback 104 — remove canonical tag set\nBEGIN;\n"
        + "".join(f"DELETE FROM public.tags WHERE dimension={sql_str(d)} AND tag_name={sql_str(v)};\n"
                  for d, v in tag_keys) + "COMMIT;\n")
    report["tags"] = len(tag_keys)

    # ===================== 105 — cuisines =====================
    cz = read_csv("cuisines_v4.csv")
    cz_names = []
    lines = [header_block(
        "105_seed_cuisines.sql", "public.cuisines — cuisine reference (groups denormalized)",
        [f"cuisines_v4.csv (sha256:{checksums['cuisines_v4.csv']}) — {len(cz)} rows",
         "cuisine_groups_v4 2.csv — groups carried as denormalized cuisine_group text (Freeze Pack A)"],
        ["direct column map [TR-001/002]; parent_cuisine/state_origin blank -> NULL",
         "cuisine_group kept as text (no FK to a groups table) — Architecture Freeze §3 Pack A",
         "state_origin NOT FK'd to re_states (63 values incl. non-Indian) — Batch3 finding"]),
        "BEGIN;"]
    for r in cz:
        nm = r["name"].strip()
        if not nm or nm in cz_names:
            continue
        cz_names.append(nm)
        lines.append(
            "INSERT INTO public.cuisines (name,display_name,cuisine_group,parent_cuisine,state_origin,description,tier,is_user_facing,is_active) VALUES ("
            f"{sql_str(nm)},{sql_str(r.get('display_name'))},{sql_str(r.get('cuisine_group'))},"
            f"{sql_str(r.get('parent_cuisine'))},{sql_str(r.get('state_origin'))},{sql_str(r.get('description'))},"
            f"{sql_str(r.get('tier'))},{sql_bool(r.get('is_user_facing','Y'))},{sql_bool(r.get('is_active','Y'))}) "
            "ON CONFLICT (name) DO NOTHING;")
    lines.append("COMMIT;")
    (SEEDS / "105_seed_cuisines.sql").write_text("\n".join(lines) + "\n")
    (ROLLBACK / "105_seed_cuisines_rollback.sql").write_text(
        "-- Rollback 105\nBEGIN;\nDELETE FROM public.cuisines WHERE name IN (\n  "
        + ",\n  ".join(sql_str(n) for n in cz_names) + "\n);\nCOMMIT;\n")
    report["cuisines"] = len(cz_names)

    # ===================== dishes.xlsx =====================
    dishes = xlsx_sheet(SRC / "dishes.xlsx", "dishes_810")
    combo_names = {norm_name(r["combo_name"]) for r in read_csv("dish_combos_v2_20260520.csv")}
    # ICD-1 dish catalog: dishes_810 minus rows whose name matches a combo header (Batch4 B4-CAN-EX-001 basis)
    dish_rows, excluded_combo = [], []
    seen_d = set()
    for d in dishes:
        nm = (d.get("Dish Name") or "").strip()
        if not nm:
            continue
        if norm_name(nm) in combo_names:
            excluded_combo.append(nm)
            continue
        if nm in seen_d:
            continue
        seen_d.add(nm)
        dish_rows.append(d)

    # ===================== 106 — dishes =====================
    lines = [header_block(
        "106_seed_dishes.sql", "public.dishes — ICD-1 canonical dish catalog (core columns only)",
        [f"dishes.xlsx / dishes_810 (sha256:{checksums['dishes.xlsx']}) — {len(dishes)} rows"],
        ["ICD-1: standalone dishes only; rows whose name matches a dish_combos_v2 header excluded to combos",
         "meal_occasion = split(Meal Types, ',') -> text[]; cook_time_minutes = Total Mins",
         "difficulty: easy->beginner, medium->intermediate, hard->advanced [TR-010]",
         "calories/serving_size/food_dna_tier_1 = Calories/Serving Size/tier_1 (migration 022)",
         "cuisine_id resolved from Cuisines slug -> public.cuisines(name)",
         "name_hindi/name_regional left NULL (alias unification deferred — Freeze Pack A opt c)",
         "diet_type/is_jain/allergen_flags/genome_vector NOT seeded — trigger-derived (CDM Invariant 6)"]),
        "BEGIN;"]
    for d in dish_rows:
        nm = d["Dish Name"].strip()
        mo = [x.strip() for x in (d.get("Meal Types") or "").split(",") if x.strip()]
        diff = DIFFICULTY_MAP.get((d.get("Difficulty") or "").strip().lower(), "intermediate")
        ck = re.sub(r"[^0-9]", "", d.get("Total Mins", "") or "") or "0"
        cal = re.sub(r"[^0-9]", "", d.get("Calories", "") or "")
        cal = cal if cal else "NULL"
        cuisine = (d.get("Cuisines") or "").split(",")[0].strip()
        cuisine_sub = (f"(SELECT id FROM public.cuisines WHERE name={sql_str(cuisine)})"
                       if cuisine else "NULL")
        lines.append(
            "INSERT INTO public.dishes (name,description,meal_occasion,cook_time_minutes,difficulty,calories,serving_size,food_dna_tier_1,cuisine_id,is_indian_only,is_active) VALUES ("
            f"{sql_str(nm)},{sql_str(d.get('Short Description'))},{text_array(mo)},{int(ck)},{sql_str(diff)},"
            f"{cal},{sql_str(d.get('Serving Size'))},{sql_str(d.get('tier_1'))},{cuisine_sub},true,"
            f"{sql_bool(d.get('Is Active','Y'))}) ON CONFLICT (name) DO NOTHING;")
    lines.append("COMMIT;")
    (SEEDS / "106_seed_dishes.sql").write_text("\n".join(lines) + "\n")
    (ROLLBACK / "106_seed_dishes_rollback.sql").write_text(
        "-- Rollback 106 (cascades to dish_ingredients/dish_tags via ON DELETE CASCADE)\nBEGIN;\n"
        "DELETE FROM public.dishes WHERE name IN (\n  "
        + ",\n  ".join(sql_str(d['Dish Name'].strip()) for d in dish_rows) + "\n);\nCOMMIT;\n")
    report["dishes"] = len(dish_rows)
    report["dishes_excluded_combo"] = excluded_combo

    # ===================== 107 — dish_ingredients =====================
    matched, skipped = 0, 0
    orphan_tokens = {}
    lines = [header_block(
        "107_seed_dish_ingredients.sql", "public.dish_ingredients — dish->ingredient junction (fires derivation)",
        [f"dishes.xlsx / dishes_810 `Ingredients` column (sha256:{checksums['dishes.xlsx']})"],
        ["tokens = split(Ingredients, ','); resolved to public.ingredients(name) [TR-004]",
         "tokens with no matching ingredient are SKIPPED (logged), never fabricated",
         "firing this junction triggers fn_derive_dish_attributes (migration 010) -> derived dish columns"]),
        "BEGIN;"]
    for d in dish_rows:
        nm = d["Dish Name"].strip()
        toks = [t.strip() for t in (d.get("Ingredients") or "").split(",") if t.strip()]
        present = [t for t in toks if t in ing_names]
        for t in toks:
            if t not in ing_names:
                orphan_tokens[t] = orphan_tokens.get(t, 0) + 1
                skipped += 1
        if present:
            matched += len(present)
            in_list = ", ".join(sql_str(t) for t in present)
            lines.append(
                "INSERT INTO public.dish_ingredients (dish_id,ingredient_id) "
                f"SELECT d.id, i.id FROM public.dishes d JOIN public.ingredients i ON i.name IN ({in_list}) "
                f"WHERE d.name={sql_str(nm)} ON CONFLICT DO NOTHING;")
    lines.append("COMMIT;")
    (SEEDS / "107_seed_dish_ingredients.sql").write_text("\n".join(lines) + "\n")
    (ROLLBACK / "107_seed_dish_ingredients_rollback.sql").write_text(
        "-- Rollback 107\nBEGIN;\nDELETE FROM public.dish_ingredients WHERE dish_id IN "
        "(SELECT id FROM public.dishes WHERE name IN (\n  "
        + ",\n  ".join(sql_str(d['Dish Name'].strip()) for d in dish_rows) + "\n));\nCOMMIT;\n")
    report["dish_ingredient_links"] = matched
    report["dish_ingredient_orphan_tokens"] = orphan_tokens

    # ===================== 108 — dish_tags =====================
    tagvocab = {}
    for (dim, val) in tag_keys:
        tagvocab.setdefault(dim, set()).add(val.lower())
    # dish attribute column -> tag dimension (only dimensions that exist in the tag master)
    ATTR_DIM = {
        "Primary Taste": "primary_taste", "Texture": "texture", "Richness": "richness",
        "Mouthfeel": "mouthfeel", "Aroma Profile": "aroma_profile", "Fermentation": "fermentation",
        "Serving Temp": "serving_temp", "Weather Affinity": "weather_affinity",
        "Cooking Method": "cooking_method", "Dish Category": "dish_category", "Meal Types": "meal_type",
    }
    link_count, tag_orphans = 0, {}
    lines = [header_block(
        "108_seed_dish_tags.sql", "public.dish_tags — dish->genome-tag junction (fires vector update)",
        [f"dishes.xlsx / dishes_810 genome columns (sha256:{checksums['dishes.xlsx']})"],
        ["each dish attribute value linked to public.tags(dimension,tag_name) where it exists",
         "confidence = 1.0 (source-declared attribute); values with no matching tag SKIPPED (logged)",
         "Spice/Sweetness/Heaviness skipped: no matching tag dimension in tags_v4 (migration 022 note)",
         "firing updates dishes.genome_vector via fn_update_dish_genome_vector (migration 010)"]),
        "BEGIN;"]
    for d in dish_rows:
        nm = d["Dish Name"].strip()
        for col, dim in ATTR_DIM.items():
            if dim not in tagvocab:
                continue
            vals = [v.strip() for v in (d.get(col) or "").split(",") if v.strip()]
            present = [v for v in vals if v.lower() in tagvocab[dim]]
            for v in vals:
                if v.lower() not in tagvocab[dim]:
                    tag_orphans[f"{dim}:{v}"] = tag_orphans.get(f"{dim}:{v}", 0) + 1
            if present:
                link_count += len(present)
                in_list = ", ".join(sql_str(v) for v in present)
                lines.append(
                    "INSERT INTO public.dish_tags (dish_id,tag_id,confidence) "
                    f"SELECT d.id, t.id, 1.0 FROM public.dishes d JOIN public.tags t "
                    f"ON t.dimension={sql_str(dim)} AND t.tag_name IN ({in_list}) "
                    f"WHERE d.name={sql_str(nm)} ON CONFLICT DO NOTHING;")
    lines.append("COMMIT;")
    (SEEDS / "108_seed_dish_tags.sql").write_text("\n".join(lines) + "\n")
    (ROLLBACK / "108_seed_dish_tags_rollback.sql").write_text(
        "-- Rollback 108\nBEGIN;\nDELETE FROM public.dish_tags WHERE dish_id IN "
        "(SELECT id FROM public.dishes WHERE name IN (\n  "
        + ",\n  ".join(sql_str(d['Dish Name'].strip()) for d in dish_rows) + "\n));\nCOMMIT;\n")
    report["dish_tag_links"] = link_count
    report["dish_tag_orphans_distinct"] = len(tag_orphans)

    # ===================== 109 — dish_combos + items =====================
    combos = read_csv("dish_combos_v2_20260520.csv")
    items = read_csv("dish_combo_items_v2_20260520.csv")
    COMBO_TYPE = {"inseparable", "base_with_sides", "thali"}
    lines = [header_block(
        "109_seed_dish_combos.sql", "public.dish_combos + dish_combo_items",
        [f"dish_combos_v2_20260520.csv ({len(combos)}) + dish_combo_items_v2_20260520.csv ({len(items)})"],
        ["combo_type validated against CHECK {inseparable,base_with_sides,thali}",
         "meal_occasion = split(meal_types, ',') -> text[]",
         "item role -> 3-value CHECK; component_type -> 8-value CHECK (migration 025)",
         "combo item dish_id resolved from public.dishes(name); unresolved items skipped (ICD-1)"]),
        "BEGIN;"]
    combo_names_seed = []
    for c in combos:
        cn = c["combo_name"].strip()
        ct = c.get("combo_type", "").strip()
        if ct not in COMBO_TYPE:
            continue
        combo_names_seed.append(cn)
        mo = [x.strip() for x in (c.get("meal_types") or "").split(",") if x.strip()]
        lines.append(
            "INSERT INTO public.dish_combos (combo_name,combo_type,meal_occasion,is_active) VALUES ("
            f"{sql_str(cn)},{sql_str(ct)},{text_array(mo)},{sql_bool(c.get('is_active','Y'))});")
    for it in items:
        cn = it["combo_name"].strip()
        dn = it["dish_name"].strip()
        role = it.get("role", "").strip()
        comp = role if role in {"primary", "bread", "carb_base", "accompaniment", "condiment", "dessert", "beverage", "standalone"} else None
        role3 = role if role in {"primary", "side", "accompaniment"} else "side"
        lines.append(
            "INSERT INTO public.dish_combo_items (combo_id,dish_id,role,component_type,is_default,is_swappable,sort_order) "
            f"SELECT dc.id, d.id, {sql_str(role3)}, {sql_str(comp)}, {sql_bool(it.get('is_default','Y'))}, "
            f"{sql_bool(it.get('is_swappable','N'))}, {int(re.sub(r'[^0-9]','',it.get('sort_order','0') or '0') or 0)} "
            f"FROM public.dish_combos dc, public.dishes d WHERE dc.combo_name={sql_str(cn)} AND d.name={sql_str(dn)} "
            "ON CONFLICT DO NOTHING;")
    lines.append("COMMIT;")
    (SEEDS / "109_seed_dish_combos.sql").write_text("\n".join(lines) + "\n")
    (ROLLBACK / "109_seed_dish_combos_rollback.sql").write_text(
        "-- Rollback 109 (items cascade with combos)\nBEGIN;\nDELETE FROM public.dish_combos WHERE combo_name IN (\n  "
        + ",\n  ".join(sql_str(n) for n in combo_names_seed) + "\n);\nCOMMIT;\n")
    report["combos"] = len(combo_names_seed)

    # ===================== Deferred Knowledge Register =====================
    content_norm = set()
    for d in dish_rows:
        content_norm.add(norm_name(d["Dish Name"]))
        for a in (d.get("Alternate Names") or "").split(","):
            if a.strip():
                content_norm.add(norm_name(a))
    def deferred_from(csv_or_sheet, field, source_label, loader):
        cnt = {}
        for r in loader:
            nm = (r.get(field) or "").strip()
            if not nm:
                continue
            if norm_name(nm) not in content_norm:
                cnt[nm] = cnt.get(nm, 0) + 1
        return [(nm, source_label, "referenced dish absent from ICD-1 master catalog", n)
                for nm, n in sorted(cnt.items())]
    deferred = []
    deferred += deferred_from(None, "dish_name", "Class_Dish_Options_v3 (Indian_Meal_Cohort_Persona_DB_v3.xlsx)",
                              xlsx_sheet(SRC / "Indian_Meal_Cohort_Persona_DB_v3.xlsx", "Class_Dish_Options_v3"))
    deferred += deferred_from(None, "dish_or_component_name", "Addon_Dish_Options (Indian_Meal_Cohort_Persona_DB_v3.xlsx)",
                              xlsx_sheet(SRC / "Indian_Meal_Cohort_Persona_DB_v3.xlsx", "Addon_Dish_Options"))
    deferred += deferred_from(None, "dish_name", "region_food_affinity.csv", read_csv("region_food_affinity.csv"))

    csv_path = REGISTER_DIR / "[ACTIVE]_WP-6_Deferred_Knowledge_Register_v1.0.csv"
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["deferred_dish_name", "source_file", "reason", "reference_count", "recommended_future_action"])
        for nm, src, reason, n in deferred:
            w.writerow([nm, src, reason, n,
                        "Introduce via curated import / admin addition / future dataset / UGC; then load the "
                        "deferred recommendation rows (re_class_dish_options / re_addon_dish_options / affinity) "
                        "referencing it. No schema change required."])
    report["deferred_rows"] = len(deferred)
    report["deferred_distinct_sources"] = {
        "class_dish_options": sum(1 for x in deferred if x[1].startswith("Class_Dish")),
        "addon_dish_options": sum(1 for x in deferred if x[1].startswith("Addon")),
        "region_food_affinity": sum(1 for x in deferred if x[1].startswith("region")),
    }

    # ------------------------------------------------------------------ summary
    print("=== WP-6D-gen generation summary ===")
    for k, v in report.items():
        if isinstance(v, (dict, list)) and k not in ("deferred_distinct_sources",):
            print(f"  {k}: {len(v)}" + (f" (e.g. {list(v)[:5]})" if v else ""))
        else:
            print(f"  {k}: {v}")

if __name__ == "__main__":
    main()
