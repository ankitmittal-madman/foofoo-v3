# STATUS

ARCHIVED

## Reason

Implementation completed.

This document is retained for historical reference only.

It must not be used as the primary implementation guide.

Refer to the active documentation for the current source of truth.

---

STATUS: ARCHIVED
Reason: Superseded by docs/archive/audits/re_audit_v2/ (the 2026-08-04 clean-room re-audit), which is itself superseded by docs/active/. Kept for historical reference only.

# Phase 4 — Food Ontology Audit

Checks RE-DOC-02's "Food Graph" ontology (node types Dish/Ingredient/AllergenFlag/MealClass/
UserProfile/MemberSegment with typed edges: contains_ingredient, is_allergen, can_substitute,
belongs_to_class) against what actually exists in `database/migrations/*.sql` and `ghar_re_core`.

## 1. Is there a real graph structure, or flat FK relationships?

**Flat FK relationships — no generic graph/edge table exists.** Every "edge type" RE-DOC-02
describes is implemented as its own dedicated relational table with typed FKs, not as rows in a
generic `(node_a, edge_type, node_b)` edges table:

| RE-DOC-02 edge type | Real implementation | Evidence |
|---|---|---|
| `contains_ingredient` | `ghar_re.dish_ingredients(dish_id, ingredient_id, is_main_ingredient)` (034 L117-124); real-catalogue analogue `public.dish_ingredients` seeded via `database/seeds/107_seed_dish_ingredients.sql` | `034_ghar_re_schema_and_catalogue.sql` |
| `is_allergen` | Not a dish→allergen edge at all — implemented as a **bitmask column** `ingredients.allergen_flags integer`, unioned via `bit_or()` up to the dish level by trigger `fn_sync_profile_allergen_union`-family (010) | `database/migrations/010_trigger_functions_and_triggers.sql` L46-95 |
| `can_substitute` | `ghar_re.dish_variants(from_dish_id, to_dish_id, variant_type)` — variant_type CHECK IN ('veg_swap','jain','vegan','no_onion_garlic','farali','lighter','protein_swap') (036 C.2) | `database/migrations/036_ghar_re_safety_support.sql` L21-30 |
| `belongs_to_class` | `dishes.hero_role` / `dish_category` fields (multi-hot / enum on the dish row itself, 034 L74/92) — not an edge to a separate MealClass node; also `re_engine` has `re_meal_classes` (seed `112_seed_re_meal_classes.sql`) as a reference table, joined by FK, not a graph edge | `034_ghar_re_schema_and_catalogue.sql`; `database/seeds/112_seed_re_meal_classes.sql` |

Each of these is a **purpose-built table with its own schema and constraints** — this is more
rigid/typed than a generic graph (good for query performance and integrity, e.g. CHECK constraints
on `variant_type`), but it means there is **no unified traversable graph** the way RE-DOC-02's
Food Graph ontology envisions (no single edges table, no generic node-type dispatch). "Allergen
propagation" in particular is not graph traversal — it's a **bitwise OR aggregation** computed by
Postgres triggers at write time, which is architecturally simpler than the described ontology but
functionally narrower (can't express arbitrary multi-hop derivation without new bit positions).

## 2. Ingredient substitution table

Exists: `ghar_re.dish_variants` (migration 036, C.2, `034` prerequisite). Confirmed **schema-only /
near-empty**:
- Golden-sample seed `database/seeds/121_ghar_re_golden_sample.sql` inserts only **2 rows** into
  `ghar_re.dish_variants` (counted via `grep -oP "(?<=INSERT INTO )[a-zA-Z_.]+" | sort | uniq -c`
  → `2 ghar_re.dish_variants`).
- No seed file for the real 810-dish catalogue's variant graph was found (`find database/seeds
  -iname "*variant*"` returns nothing — not checked exhaustively beyond a name-pattern search, so
  absence is evidence of omission, not proof, but no variant seed file exists under the naming
  convention used by every other seed).
- Core Spine itself calls this `[DB-designed]`/OPEN, register ID **SP-F14**: "schema designed to
  carry it; powers the explicit veg-day 1:1 substitution (v1 just refills from the veg pool)" —
  i.e., the frozen spec **explicitly confirms v1 does not use this table for its actual
  substitution logic**; veg-day substitution today is pool-refill only, not graph traversal.

## 3. Allergen propagation logic — hidden-derivative layer status

`grep -rn "allergen" ghar_re_core database/migrations` shows:
- **Basic explicit-flag pass**: `pass_allergen(x,H) = (x.allergens ∩ H.allergens) == empty`
  (Core Spine §2 A3) — implemented via the `allergen_flags` bitmask + `bit_or` trigger described
  above.
- **Hidden-derivative table**: `ghar_re.allergen_hidden_derivatives` (migration 036, C.1):
  ```sql
  CREATE TABLE ghar_re.allergen_hidden_derivatives (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    surface_token  text NOT NULL,
    hidden_allergen text NOT NULL,
    note text,
    is_active boolean NOT NULL DEFAULT false,   -- inert until safety-verified pre-launch
    data_source ghar_re.data_source_kind NOT NULL
  );
  ```
  Migration comment states explicitly: *"Rows here are inert until wired"* and *"population +
  folding into filter A3 is a PRE-LAUNCH deferred item... Do NOT attempt the allergen
  hidden-derivative table"* (per the migration's own Task 3 note).
- **Row count**: `grep -rln "allergen_hidden_derivatives" database/seeds/*.sql` returns **no
  matches** — zero seed files touch this table. Combined with `is_active DEFAULT false`, this
  confirms the table is **schema-present, zero rows, structurally inert** — exactly matching
  RE-DOC-12's characterization (per the task brief) and Core Spine Appendix D / register
  **SP-F13, tagged `[SAFETY]`, status `OPEN — PRE-LAUNCH`**.
- **Practical implication**: allergen filtering today only catches *explicit* ingredient-level
  allergens (e.g., a dish literally listing "peanut"). It does **not** catch the classic hidden
  case named in the docs themselves — hing (asafoetida) commonly cut with wheat flour, meaning a
  "gluten-free" claim could be wrong. The Spine itself flags this as the one item that must
  complete before public launch.

## 4. Religious / dietary ontology (Jain, vegan, halal, no-beef)

| Field | Real column | Populated? |
|---|---|---|
| Jain | `ghar_re.dishes.jain_compatible text CHECK IN ('Y','N') NOT NULL` (034 L98); prod `public.dishes.is_jain boolean`, trigger-derived from `ingredients.is_jain_compatible boolean` (008 L28, 010 L41/65/77) | Golden sample: all 39 dishes carry an explicit `jain=` value in `fixtures.py` (e.g. `jain="Y"` on Idli, Curd Rice, Ven Pongal, Moong Dal Khichdi, Dhokla, etc. — at least 9 of 39 dishes explicitly Jain-compatible, counted by inspection of `fixtures.py`). Real catalogue: `is_jain` is trigger-derived, NOT seeded directly (106 header: "diet_type/is_jain/allergen_flags/genome_vector NOT seeded — trigger-derived") — so its population for the 810-dish catalogue depends on `ingredients.is_jain_compatible` + `dish_ingredients` being fully seeded and the trigger firing; not independently row-counted in this audit. |
| Vegan | `diet_type` enum includes `'vegan'` (008 L27) in the **real production schema**. **Not present** in the `ghar_re` schema's `diet` field, which is only `CHECK (diet IN ('veg','egg','non_veg'))` (034) — **no `vegan` option in the golden-sample/live-scoring engine's own diet field.** | Schema exists in `public.dishes` only; the actual scoring engine (`ghar_re_core`/`ghar_re.dishes`) has no vegan category — Q5/Q6 diet filter in the Core Spine (§2 A1) only enumerates veg/eggetarian/non_veg, no vegan branch. |
| Halal | **No field found anywhere.** Not in `public.dishes`, not in `ghar_re.dishes`, not in the Core Spine's filter list (§2 Part A lists only Diet/Jain/Allergen/Weaning/Mode/Calorie filters), not in `data/source/*`. | Not implemented. |
| No-beef / no-pork / no-red-meat | Referenced only as **prose in the Core Spine**: "if H.diet == 'non_veg': TRUE, minus specific meat exclusions in Q6 (e.g. no_beef / no_pork / no_red_meat → exclude those ingredient classes)" (§2 A1). No column, no table, no seed data found implementing this exclusion — it is a **described-but-unbuilt** filter branch. | Not implemented — spec-only. |

## 5. MealClass / MemberSegment nodes

- `re_engine.re_meal_classes` — a real reference table, seeded (`database/seeds/112_seed_re_meal_classes.sql`) — functions as the "MealClass" node type, but it is joined by ordinary FK from cohort/plan tables, not addressed via a generic graph edge.
- No `MemberSegment` node/table by that name was found; the closest concept is `re_engine.re_cohorts` (seed `113_seed_re_cohorts.sql`) and household `q1_household_type`/member age bands used directly in scoring (Core Spine §2 B5/B6), not modeled as ontology nodes.

## Summary

- **Food Graph as a literal graph**: not built. Every typed edge in RE-DOC-02 is realized as its
  own bespoke relational table (dish_ingredients, dish_variants) or a bitmask column
  (allergen_flags), which is a reasonable simplification for a rule-first Postgres system but is
  architecturally distinct from a graph/ontology model — there is no traversal-capable, generically
  typed edge store anywhere in `database/migrations`.
- **Ingredient substitution**: schema exists (`ghar_re.dish_variants`), essentially unpopulated (2
  rows, golden sample only), and the Core Spine's own register (SP-F14) confirms v1 doesn't use it
  — veg-day handling is pool-refill, not graph substitution.
- **Allergen hidden-derivative table** (migration 036): schema exists, `is_active DEFAULT false`,
  **zero seed rows found** — confirmed still inert, matching RE-DOC-12's stated PRE-LAUNCH-blocking
  status (Core Spine register SP-F13).
- **Religious/dietary ontology**: only Jain is a real, filter-integrated hard constraint. Vegan
  exists as a schema value in `public.dishes.diet_type` but is absent from the actual scoring
  engine's diet enum. Halal has no implementation anywhere. No-beef/no-pork/no-red-meat exclusions
  are described in prose in the Core Spine but have no supporting column/table/seed evidence of
  being built.

## Evidence index
- `database/migrations/008_content_core.sql`, `010_trigger_functions_and_triggers.sql`,
  `034_ghar_re_schema_and_catalogue.sql`, `036_ghar_re_safety_support.sql`
- `database/seeds/121_ghar_re_golden_sample.sql` (row counts via `grep -oP "(?<=INSERT INTO
  )[a-zA-Z_.]+" | sort | uniq -c` → `2 ghar_re.dish_variants`, `39 ghar_re.dishes`, `269
  ghar_re.dish_ingredients`, `39 ghar_re.sig_scores`, `39 ghar_re.dish_macro`, `7
  ghar_re.households`, `6 ghar_re.region_food_affinity`)
- `grep -rln "allergen_hidden_derivatives" database/seeds/*.sql` → no matches (zero seed rows)
- `ghar_re_core/fixtures.py` (read in full, 517 lines) for Jain-flag inspection
- `docs/architecture/ghar-re/ghar_re_v1_0_core_spine_FROZEN.md` (read in full, 730 lines) — Appendix
  D/E and Future/Deferred/RFC Register (SP-F13, SP-F14) for status confirmation
