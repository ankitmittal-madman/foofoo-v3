# [ACTIVE]_Phase3_5_Architecture_Freeze_v1.0

**Final checkpoint of Phase 3.5 — Architecture Freeze, Closure Recommendation, Phase 4 Readiness**
**Scope:** Evaluation and one direct revalidation only. No redesign. No new AGR/SER created. No frozen document reopened.
**Date:** 2026-07-03 · **Status:** Draft — Ready for Founder Review

---

## 1. Baseline Verification

| Item | Verified State |
|---|---|
| Phase 3 | COMPLETE / APPROVED / FROZEN |
| Batches 1–6 | COMPLETE / FROZEN (confirmed via each batch's own freeze artifact) |
| Project Integration Review | COMPLETE — `Phase3_5_Project_Integration_Review_v1.0` |
| Architecture Decision Review | COMPLETE — `Phase3_5_Architecture_Decision_Review_v1.0`, 3 Group A decisions identified (cuisine, tag vectors, combo roles) |
| Document consistency | No new duplicate ACTIVE documents found. `DOC-P3-11` project file remains at v1.20 pending the v1.21 filing already flagged in the prior review — unchanged, non-blocking, noted again for completeness, not re-litigated |

No frozen document reopened during this verification.

---

## 2. GC-AGR-002 Revalidation

**Original finding (Batch 1, frozen):** `re_meal_classes.slot` CHECK constraint (`_ACTIVE__003_reference_tier1_1_1.sql`) allows exactly 4 values: `('breakfast','lunch','dinner','addon')`. Batch 1's Canonicalization tallied 22 of 131 canonical Meal Class rows carrying a `slot_group` value of `'Snack'` — outside the allowed set.

**Revalidation method:** Read `Indian_Meal_Cohort_Persona_DB_v3.xlsx`'s `Meal_Class_Master_v3` sheet directly — 131 data rows (matching Seed Gate S-06's target exactly), column `slot_group` confirmed as the exact source column Batch 1 canonicalized. Full-column tally performed, no sampling.

**Result:**

| `slot_group` value | Row count | In CHECK-allowed set? |
|---|---|---|
| `Lunch/Dinner` | 68 | ❌ No |
| `Breakfast` | 26 | ✅ Yes (case-insensitive match to `breakfast`) |
| `Snack` | 22 | ❌ No |
| `Dinner` | 15 | ✅ Yes (case-insensitive match to `dinner`) |

**The original 22-row `'Snack'` finding is confirmed exactly** — 22 of 131, matching Batch 1's frozen tally precisely, now verified against real data instead of the illustrative subset.

**New finding, not previously counted:** `'Lunch/Dinner'` (68 rows, 51.9% of the table) is a **compound value** that also fails the CHECK constraint as written — it doesn't match `'lunch'` or `'dinner'` individually, and the schema has no mechanism for a class to belong to two slots at once. **This means the real violation count is 90 of 131 rows (68.7%), not 22 of 131 (16.8%) as originally scoped.**

**Determination: STILL VALID — and materially understated.**

This is not "Invalid" (the original finding is fully confirmed, not contradicted) and not merely "Partially Valid" in the sense of being overstated — if anything the opposite is true: the real dataset reveals the true blast radius is over 4x larger than Batch 1's illustrative-data finding suggested. GC-AGR-002 should **not** be closed. It should be **updated with corrected scope** before any AGR is drafted from it, since drafting a fix scoped to "22 rows, one missing value" would leave 68 additional rows (the `Lunch/Dinner` compound-value rows) unaddressed.

**Recommendation:** Do not close GC-AGR-002. Flag its scope as requiring revision (22→90 rows, 1→2 distinct violation patterns: a missing enum value, and a compound/multi-slot value the current single-valued `slot` column cannot represent at all) before Founder approval is sought. This is evidence-driven, not a new architectural opinion — the compound-value pattern is a structurally different problem from a missing enum value (it suggests `slot` may need to become an array or the schema may need a many-to-many class↔slot relationship, not just a wider CHECK list), which changes what kind of fix is appropriate. No option is selected here.

---

## 3. Architecture Approval Pack A — Content Model

*(Cuisine persistence, dish attributes, alias strategy)*

### Cuisine Persistence
- **Evidence:** 100% of 810 dishes and 100% of 35 combos carry a valid cuisine value; zero destination column exists on either `public.dishes` or `public.dish_combos` in frozen `DOC-P3-04 v1.3`.
- **Options:** (a) FK to new `public.cuisines` table seeded from `cuisines_v4.csv`; (b) plain `cuisine text` column, no FK; (c) do not persist.
- **Trade-offs:** (a) matches the project's existing FK-everywhere discipline but is the largest single schema change pending; (b) is faster but reintroduces unconstrained text; (c) costs nothing but discards a Genome-relevant signal.
- **Recommended option:** **(a) — FK to a new `public.cuisines` table.** Reasoning: every other controlled vocabulary in the frozen schema (`re_states`, `tags`, `ingredients`) uses an FK-backed reference table, not a free-text column; departing from that pattern here would be the one inconsistency in an otherwise uniform schema, and the source data (`cuisines_v4.csv`, 65 rows, hierarchical with `cuisine_group`/`parent_cuisine`) is already shaped exactly like a reference table, not a flat tag.
- **Business impact:** High — cuisine filtering/display is a basic expected feature.
- **Seed impact:** Critical — 845 rows across 2 tables, the highest row-count blocker in the project.
- **Cross-batch impact:** Resolves CBD-002, B4-GAP-001, B5-GAP-003, B3-RES-001/002 simultaneously.

### Dish Attributes (spice, sweetness, heaviness, calories, serving size, Food DNA tier)
- **Evidence:** All 6 attributes populated on all 810 dishes; none has a destination column.
- **Options:** (a) add all 6 as columns on `public.dishes`; (b) add only `tier_1` (confirmed RE-relevant per `RE-DOC-02`/`RE-DOC-03`), defer the other 5; (c) fold spice/sweetness/heaviness into `dish_tags` as new tier-2 genome dimensions, keep calories/serving_size as plain columns.
- **Trade-offs:** (a) simplest, but mixes genome-relevant and pure-display attributes in one bucket; (b) minimal-footprint but leaves calorie/serving-size display broken; (c) matches the project's stated genome-via-tags pattern most closely but requires a judgment call on which attributes are "genome" vs. "display."
- **Recommended option:** **(c) — split by function: spice/sweetness/heaviness into `dish_tags` as new tier-2 dimensions; calories/serving_size/`tier_1` as plain columns on `dishes`.** Reasoning: `RE-DOC-02`'s own genome model already treats exactly this kind of taste/texture attribute as tag dimensions (e.g., existing tier-2 tags like `richness`, `primary_taste`), so spice/sweetness/heaviness fit an established pattern rather than needing new columns; calories and serving_size have no genome role in any RE-DOC and are purely display data, matching how `Prep Mins`/`Cooks Mins` were already treated in Batch 4; `tier_1` is a dish-level scalar the genome-vector trigger already expects to read from somewhere, making a plain column the natural fit.
- **Business impact:** Medium-High — calories/serving size are common expectations; spice/sweetness/heaviness likely feed filtering or ContentMatch.
- **Seed impact:** High — all 810 dishes.
- **Cross-batch impact:** None beyond Batch 4 itself.

### Alias Strategy
- **Evidence:** `dishes.xlsx`'s `Alternate Names` supports exactly 2 fixed slots; source data is unbounded; `term_synonyms_v2.csv` provides an independent, language-tagged mechanism with 79-of-93 confirmed overlap, 62 corroborated without conflict.
- **Options:** (a) unify into one `dish_aliases` junction table using the 3 evidenced categories (regional/language, spelling variation, word-order variation); (b) widen the fixed-slot columns; (c) keep both mechanisms as-is.
- **Trade-offs:** (a) most correct long-term, reuses already-evidenced categories, but requires a new table and a migration decision for the 62 already-populated overlapping dishes; (b) smaller change, doesn't address duplication; (c) costs nothing but permanently caps richness at 2 per dish.
- **Recommended option:** **(c) — keep as-is for Phase 9, revisit as a post-launch SER.** Reasoning: this is the one Pack A item with the lowest seed impact (up to 17 dishes affected, none blocking) and the lowest business impact (search/discovery quality, not core function) of the three — spending a schema-migration decision here now would use Founder attention that Decision-1/2 (cuisine, dish attributes) need more urgently; nothing about seeding correctly today depends on resolving this first.
- **Business impact:** Low-Medium.
- **Seed impact:** Medium — up to 17 dishes.
- **Cross-batch impact:** Resolves CBD-001 entirely, whenever addressed.

---

## 4. Architecture Approval Pack B — Recommendation Engine

*(Tag vectors, regional affinity, Food DNA)*

### Tag Vectors / Food DNA Genome Mechanism
- **Evidence:** `public.tags` naming/uniqueness conflict + missing `vector_position` values (B3-RES-003/004), blocking the entire genome-vector trigger mechanism for all 810 dishes. A deterministic assignment algorithm is already drafted (tier ascending → category → value, alphabetically; sequential integers 0–110).
- **Options:** Confirm the drafted algorithm as-is, or specify a different deterministic ordering rule.
- **Trade-offs:** Confirming costs nothing further; a different rule requires redrafting, not rediscovery.
- **Recommended option:** **Confirm the drafted algorithm as-is.** Reasoning: the algorithm is fully deterministic, reproducible, and was derived directly from the existing tier/category/value structure already frozen in `tags_v4.csv` — it doesn't introduce any new judgment call beyond alphabetical tie-breaking, which is about as low-risk a default as exists; no evidence anywhere in 6 batches suggests a different ordering would serve the genome-vector mechanism better.
- **Business impact:** Critical — the RE's core ContentMatch scoring cannot function without this.
- **Seed impact:** Critical — blocks all `dish_tags` population, all 810 dishes, all 11 categories.
- **Cross-batch impact:** Resolves CBD-003 entirely; unblocks B4-GAP-012.

### Regional Affinity Persistence
- **Evidence:** `region_food_affinity.csv` — 136 rows, dish-level affinity to specific states (0.80–0.95); no destination table exists.
- **Options:** (a) new table `re_engine.re_dish_regional_affinity`; (b) fold into `dish_tags` as a new dimension, reusing `confidence`; (c) do not persist as a structured RE signal.
- **Trade-offs:** (a) cleanest semantic fit, but a net-new table; (b) reuses infrastructure but overloads `confidence`'s established meaning (tag-assignment certainty ≠ regional strength); (c) costs nothing now but discards a confirmed-real signal.
- **Recommended option:** **(a) — new dedicated table.** Reasoning: `dish_tags.confidence` has one clear, already-load-bearing meaning across all 11 existing tag categories (how certain the AI/human tagger was), and overloading it with a second, unrelated meaning (regional affinity strength) for just this one new dimension would make every future read of `confidence` ambiguous without checking which dimension it's attached to — a new table keeps the two concepts cleanly separable at zero cost to the 11 categories already working correctly.
- **Business impact:** Medium — improves regional personalization; product functions without it at MVP.
- **Seed impact:** High — 136 rows; also the natural consumer of Batch 1's now-confirmed-present full `re_states` dataset.
- **Cross-batch impact:** Resolves B6-GAP-001; supersedes B6-CBD-001.

### Food DNA (general)
- **Evidence:** No new Food DNA finding beyond what's captured in the tag-vector and dish-attribute items above — `tier_1`/`tier_2` observed populated on all 810 dishes (Batch 4), `tier_3` absent but confirmed intentional per `RE-DOC-02`'s own tier definitions (Batch 4 §7).
- **Determination:** No separate decision needed — Food DNA's outstanding items are fully covered by the Tag Vector item above (this Pack) and the dish-attribute `tier_1` item (Pack A). Not double-tracked here.

---

## 5. Architecture Approval Pack C — Relationship Model

*(Combo roles, combo matching)*

### Combo Role Vocabulary
- **Evidence:** Live CHECK allows 3 values; actual data uses 8; 31 of 74 rows (41.9%) would hard-fail insert; `side` (schema-allowed) used in 0 rows. 3-option pack already exists (`Batch5_Pipeline_Package_v1.1` Task 3).
- **Options:** (A) expand CHECK to 8 values; (B) collapse 6 extra values onto the existing 3; (C) add a second `component_type` column, leave `role` unchanged.
- **Trade-offs:** (A) preserves full semantic granularity, widest enum; (B) no schema change, but destroys the substitution-axis distinction (bread vs. carb_base) the Relationship Intelligence findings depend on; (C) preserves both constraint and detail, at the cost of a net-new column and denormalization.
- **Recommended option:** **(C) — add `component_type`, leave `role` unchanged.** Reasoning: this is the only option that requires zero change to already-seeded or already-validated `role` values (nothing currently passing the CHECK needs to be touched), and it directly preserves the two relationship-intelligence findings this project already evidenced and would otherwise lose — that bread and carb_base are genuinely different substitution classes (B5-OBS-RULE-005) and that dessert/condiment are never substitution targets (B5-OBS-RULE-006). Option B actively discards evidence already gathered; Option A works but changes the meaning of an existing, currently-passing constraint for no added benefit over C.
- **Business impact:** High — combo composition/swap UI depends on `role`/`component_type` being queryable correctly.
- **Seed impact:** Critical — 31 of 74 combo_item rows.
- **Cross-batch impact:** None beyond Batch 5.

### Combo Matching (dish_name → dish_id resolution)
- **Evidence:** Already reclassified Architecture-owned (`Batch5_Pipeline_Package_v1.1` Task 4) — FK target exists, only a deterministic string-matching method is undecided.
- **Determination:** Not a Founder decision. No option pack needed here — Architecture proceeds with an exact-match-first, case-normalized fallback approach (the simplest deterministic method consistent with the evidence that dish names are already unique per Batch 4's `B4-OBS-RULE-002`), unless Architecture finds a match failure during implementation, at which point it's reported, not silently worked around.
- **Business impact:** High (all 74 combo_item rows need this to seed) but not Founder-blocking.
- **Seed impact:** High.
- **Cross-batch impact:** None.

---

## 6. Architecture Freeze Assessment

**READY TO FREEZE, conditional on Founder approval of the 3 Packs above (A, B, C) plus the corrected-scope GC-AGR-002 finding.**

No internal architectural contradiction was found anywhere across all 6 batches or this final review — every gap identified throughout the project has been an *absence* (missing column/table) or a *narrowness* (CHECK constraint too tight), never a genuine design contradiction requiring the frozen schema to be redesigned. The one new finding this session (`Lunch/Dinner` compound-value rows) is a **scope correction to an already-known item**, not a new category of problem — it was found using the same CHECK-constraint-vs-real-data method that surfaced GC-AGR-002 in the first place, just applied more completely.

All 6 architecture decisions across the 3 Packs are additive (new column/table) or corrective-narrow (widen/extend one constraint) — none require touching or redesigning any already-frozen structural element (`public.dishes`, `public.dish_combos`, `public.tags`, `re_engine.re_meal_classes` core structure all remain as designed; only their constraint boundaries or missing columns are in question).

---

## 7. Phase 3.5 Closure Recommendation

| Dimension | Status |
|---|---|
| Knowledge acquisition | ✅ Complete — 6 domains, ~1,300+ combined rows (Batches 2–6) plus the full master workbook (22 sheets, confirmed present and matching every Seed Gate target) |
| Canonicalization | ✅ Complete — 25 canonical entities, 0 unresolved merge conflicts across all 6 batches |
| Mapping | ✅ Complete — every attribute in every batch mapped, blocked, or explicitly marked Not Applicable; 0 silent omissions |
| Gap Analysis | ✅ Complete — 60 total GAPs raised across 6 batches (23+7+6+13+7+4), 100% carrying a classification and resolution path |
| Resolution | ✅ Complete — 60 RES records, 0 unresolved-to-a-path |
| Cross-batch validation | ✅ Complete — 5 CBDs raised, all evaluated in the PIR (1 resolved-partially, 2 deferred, 2 blocking-now-packaged, 1 superseded) |
| Architecture | **✅ Ready to freeze, conditional on Pack A/B/C approval** (§6) |
| Governance | ✅ Stable — `DOC-P3-09 v1.3` current, no expansion needed this session, `DOC-P3-12` backlog appropriately holds only cosmetic items |
| Lineage | ✅ 100% — 0 orphan chains found across all 6 batches (confirmed independently in the PIR, reconfirmed here by inheritance, not re-audited) |
| Seed readiness | ✅ High for the majority of content; blocked only on the items now packaged into A/B/C, plus the corrected-scope GC-AGR-002 |

**Minimum required action before formal closure:** Founder approval of the 3 Approval Packs (recommended options: 1a, 2c(dish attrs)/confirm-algorithm(tags)/new-table(regional), 3C) and acknowledgment of GC-AGR-002's corrected scope (90 rows, 2 violation patterns, not 22/1). No further Discovery, Canonicalization, Mapping, Gap Analysis, or Resolution work remains for any of the 6 batches.

---

## 8. Phase 4 Readiness (verification only — Phase 4 not executed)

**Inputs available:** `DOC-05` (Information Architecture, 35 MVP screens), `DOC-06` (UX Design System), `RE-DOC-01`'s API contract, all frozen Phase 3 architecture documents, and — once Phase 9 completes — a fully seeded database matching every Seed Gate target.

**Expected objectives (per `Engineering_Handover...v1.3` Part 9/10, inherited, not redefined here):** DOC-P4-01 (Frontend Implementation Spec), DOC-P4-02, Edge Function/RE runtime code written against the now-frozen schema.

**Known risks carried into Phase 4:**
- `AGR-P3-07-001` (DPDP minor-protection, no age-verification mechanism) remains open — a Group B launch blocker per the Architecture Decision Review, relevant to Phase 4's onboarding implementation (BUILD-02).
- BUILD-02's hard requirement (fully dynamic, engine-driven onboarding, no hardcoded question sequence) depends on `re_routing_rules` being fully seeded — currently only 8-of-8 per the frozen DDL's Seed Gate S-05 target, already small and low-risk, but worth Phase 4's awareness.
- The corrected-scope GC-AGR-002 finding (§2) directly affects `re_meal_classes.slot`, which Phase 4's UI will need to read correctly — Phase 4 work touching meal-class display should wait for this to resolve, not assume the original 4-value enum.

**Dependencies:** Phase 4 cannot meaningfully begin frontend work against real data until Phase 9 (Seed Data Generation) completes; Phase 4 *specification* work (DOC-P4-01/02 authoring) can proceed in parallel with Phase 9, since it depends on the frozen schema shape, not on seeded row content.

---

## 9. Regression Review

- ✅ No Batch 1–6 frozen document modified or reopened for edit
- ✅ No Discovery, Canonicalization, Mapping, Gap Analysis, or Resolution recreated for any batch
- ✅ No lineage changed
- ✅ No schema changed — all recommended options in Packs A/B/C remain unselected by the Founder; recommendations are stated but not enacted
- ✅ No architecture changed
- ✅ No governance expansion — no new permanent framework introduced; this document is a one-time closure checkpoint
- ✅ GC-AGR-002 revalidation (§2) is a direct, evidence-based re-check against newly-available real data — not a reopening of Batch 1's frozen Canonicalization/Gap Analysis packages (their content is unchanged; only this review's own new tally is new)
- ✅ Only evaluations performed, with recommended options explicitly stated as recommendations, not selections — the Founder retains the actual decision in every Pack

---

## 10. Persistence Manifest

**Created:**
- `[ACTIVE]_Phase3_5_Architecture_Freeze_v1.0.md`

**Updated (flagged, not executed):**
- `[ACTIVE]_DOC-P3-11_Discovery_Execution_Register_v1.21.md` still pending standalone filing (unchanged from the prior review's flag — not re-elevated as a new issue)
- GC-AGR-002's tracked record (wherever the Founder maintains it — `DOC-P3-05_Architecture_Gap_Register` or equivalent) should have its scope corrected from "22 rows, 1 missing value" to "90 rows, 2 violation patterns" per §2 — flagged for Founder/Architecture action, not edited by this document

**Supersedes:** None — first-issue document.

No historical file renamed. No historical file deleted. Founder manages historical file lifecycle manually, per `DOC-P3-09` §06E. No new permanent governance framework introduced.

---

## 11. Founder Decision Summary

1. **Approve Pack A** (recommended: cuisine via FK table; dish attributes split between tags and plain columns; alias strategy deferred as-is).
2. **Approve Pack B** (recommended: confirm drafted tag algorithm; regional affinity via new dedicated table).
3. **Approve Pack C** (recommended: combo roles via new `component_type` column, `role` unchanged; combo matching proceeds under Architecture ownership).
4. **Acknowledge GC-AGR-002's corrected scope** (90 rows / 2 violation patterns, not 22 rows / 1) before any AGR is drafted from it.

---

# FINAL ANSWERS

**1. Can Architecture now be frozen? YES** — conditional on approval of Packs A/B/C above; no unconditional freeze is claimed since 3 decisions remain genuinely open.

**2. Can Phase 3.5 now be closed? NO** — not yet; closure requires the same Pack A/B/C approvals plus acknowledgment of GC-AGR-002's corrected scope. Once approved, closure can follow immediately — no further batch work of any kind remains.

**3. Can Phase 4 begin? YES, for specification work only** (DOC-P4-01/02 authoring against the frozen schema shape); **NO for implementation work depending on seeded data**, which requires Phase 9 to complete first.

Founder sign-off: _______________________ Date: ___________
