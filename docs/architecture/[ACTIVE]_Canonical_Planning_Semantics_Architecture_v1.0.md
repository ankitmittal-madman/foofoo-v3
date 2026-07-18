# [ACTIVE]_Canonical_Planning_Semantics_Architecture_v1.0

**Status:** ACTIVE — architectural recommendation (not yet implemented)
**Date:** 2026-07-17
**Origin:** `[ACTIVE]_Persona_Master_Decomposition_and_Canonical_Inference_Model_v1.0` (the investigation), validated and extended through direct empirical testing (toddler/teenager single-row finding) in the Founder review session that followed it.
**Status of prior conclusion:** This document **revises** the investigation's earlier position that the household archetype layer should be preserved unchanged. Real evidence (below) showed the condition/modifier portion of that layer is not a genuine catalog — it's a set of rules wearing persona costumes. This is a correction, stated openly, not a silent change of mind.

---

## 1. The core architectural decision

FooFoo's persona system is actually **two different things that got merged into one 41-row table**, and they need to be architecturally separated:

1. **Household composition** (who lives here, what region they're from) — a real, irreducible fact collected once at onboarding. No further data exists to derive it from. **This stays a compact catalog.**
2. **Planning conditions** (has a toddler, is managing diabetes, is fitness-focused, cooks elaborately, is budget-conscious) — these are not identities. They are **derived facts about individual household members**, each with its own independent planning implication, and they must be able to **combine freely** — a household can have a toddler *and* a diabetic elder *and* a fitness-focused parent simultaneously. **This becomes a rules-based inference layer, not a table of rows.**

The evidence for this split, in one sentence each: composition facts (age band groupings, region) have no smaller source data to derive from — they *are* the source data. Condition facts (toddler, teenager, fitness) each appeared as **exactly one row** in the 41-persona catalog regardless of what else varied, meaning the catalog had already collapsed each condition to a single rule — it just never got extracted as one.

---

## 2. The architecture

```
                    +-----------------------------------+
                    |   COMPOSITION LAYER (kept)         |
                    |   Who + where -- from onboarding   |
                    |   Small, stable, cataloged         |
                    +------------------+------------------+
                                       | feeds cold-start prior
                                       v
+---------------------------------------------------------------+
|              PLANNING SEMANTICS LAYER (new)                    |
|                                                                 |
|  Real household member data (age, condition, role)             |
|              |                                                 |
|              v                                                 |
|  Independent condition rules (each fires independently):       |
|    - Life-stage conditions (toddler, teenager, infant...)       |
|    - Health conditions (diabetic, hypertension, recovery...)    |
|    - Lifestyle goals (fitness, weight loss...)                  |
|    - Cooking capability (elaborate, needs instruction...)       |
|    - Economic/behavioral preference (budget, foodie...)         |
|              |                                                 |
|              v                                                 |
|  SHARED SEMANTIC ATTRIBUTES (the actual reusable layer --       |
|  multiple conditions can each set/adjust the SAME attribute,    |
|  instead of each condition owning its own boost-class list):    |
|    - texture (soft / normal)                                    |
|    - spice_tolerance (low / medium / high)                      |
|    - protein_target (standard / high)                           |
|    - sodium_target (standard / restricted)                      |
|    - glycemic_target (standard / low-GI)                        |
|    - recipe_complexity_bias (simple / normal / elaborate)        |
|    - cost_bias (budget / normal / premium)                      |
|    - novelty_bias (familiar / normal / experimental)             |
|  (e.g. BOTH "toddler" and "elderly, soft-food-needs" set         |
|  texture=soft -- the attribute is shared, not duplicated)        |
|              |                                                 |
|              v                                                 |
|  ONE mapping from attribute combinations -- boost classes /     |
|  meal-class scoring adjustments (defined once, reused by        |
|  every condition that sets the relevant attributes)             |
+---------------------------------+-------------------------------+
                                  |
                                  v
                    Recommendation Engine (existing scoring
                    formula -- CohortPrior/ContentMatch/History/
                    Context/Explore -- unchanged in structure)
```

**What this fixes directly:** a household with an elder health condition *and* an infant no longer needs a row called `elder_and_child_possible` — it gets both rules independently, and both fire. A future household type that's never been seen before (teenager + diabetic grandmother + fitness-conscious father) doesn't need a new persona row at all — every condition it contains already has its own rule.

---

## 3. The condition dimension catalog (derived from real data, not invented)

Each of these already exists in the research, either as a `lifecycle_health`/`household_stage` mention or a `dependent_addon_default`/`health_overlay_default`/`cook_overlay_default` flag. This table makes them independent and explicit instead of bound to a persona row:

| Condition | Source evidence | Semantic attributes it sets | Combinable? |
|---|---|---|---|
| Infant / toddler / school-child / teenager (life stage) | Single-row pattern confirmed for toddler (P10) and teenager (P12) | `texture=soft` (infant/toddler only), `spice_tolerance=low` (young child), `protein_target=high` (teenager) | Yes — multiple children of different ages can coexist |
| Diabetic / hypertension / recovery (health condition) | `dependent_addon_default` values, `health_overlay_default=Y` | `glycemic_target=low-GI`, `sodium_target=restricted`, `texture=soft` (recovery) | Yes — a household can have more than one health condition present |
| Pregnant / postpartum / lactating | Distinct `dependent_addon_default` values already present | `protein_target=high`, nutrient-density flags, specific-avoidance list | Yes |
| Fitness / weight-loss (lifestyle goal) | `health_overlay_default=Y`, clean `dependent_addon_default` values | `protein_target=high` (fitness) or calorie-adjusted (weight-loss) | Yes |
| Cooking capability (elaborate cook / needs instruction) | `cook_overlay_default` flag | `recipe_complexity_bias` | This modifies *the household's* cooking, not a specific member — attaches at household level |
| Economic / behavioral preference (budget, foodie, picky) | `lifecycle_health`/`household_stage` free text | `cost_bias`, `novelty_bias` | Yes |
| Diet / religious constraint (Jain, vegetarian, non-veg mode) | `nonveg_mode`, already a clean enum | Hard constraint, not a soft bias — bypasses this layer entirely | Already correctly modeled — no change needed |

**The point of the middle column:** notice `texture=soft` is set by *three different conditions* (toddler, recovery patient, and — if it existed — an elderly member with dental issues). Under the old design, each of those would need its own boost-class list that happens to independently arrive at soft-textured dishes. Under this design, they all just set the same attribute, and one shared rule (`texture=soft — boost these meal classes`) serves all three. This is where the real scalability comes from — not from having rules instead of personas, but from those rules converging on a small, reusable attribute vocabulary instead of each owning its own downstream logic.

**Deliberately excluded from this layer:** diet/religious constraints are *already* correctly modeled as a clean, reusable, hard-constraint dimension (`nonveg_mode`) — this document doesn't touch that; it was never part of the problem.

---

## 4. What stays exactly as it is, and why

- **`nonveg_mode`, `time_pressure`, `main_cohort_id`** — already clean, reusable dimensions. No change.
- **The household composition catalog** (a compact version of today's archetype layer, covering solo/couple/joint-family × region) — retained specifically because it's the **cold-start prior mechanism**. At Day 0, before any real per-member condition data exists in useful volume, the system still needs *something* to start from, and "what kind of household is this, roughly, and from where" is a real, irreducible signal research already captured well. This is not the same claim as "the 41-row catalog should stay as-is" — it's a much smaller, composition-only version of it, with all the condition-specific rows (toddler, teenager, fitness, etc.) removed because those are now handled by the rules layer instead.
- **The RE's core scoring formula** (`CohortPrior + ContentMatch + PersonalHistory + ContextFit + ExplorationBonus`, hard constraints before scoring, safety gates after) — structurally unchanged. This document adds a new input to `ContentMatch`/candidate filtering (the combined set of active condition rules for a household), it does not redesign the scoring pipeline itself.

---

## 5. What changes, concretely

1. **`household_members.segment`** (currently 8 hardcoded values) gets replaced or extended to carry the real condition vocabulary already proven out in the research (the ~18-20 clean `dependent_addon_default`-style values), so a real family member's row can carry *multiple* independent condition tags rather than being forced into one of 8 buckets.
2. **Compound labels retire.** `elder_and_child_possible`, `child_plus_diabetic_or_elderly_member`, and similar hand-written combination labels are replaced by allowing multiple independent condition tags per household — the combination emerges naturally instead of needing its own row.
3. **The addon generation logic (LF-C)** — currently unbuilt anyway (per the earlier Wave 3 readiness finding) — should be designed against this rules layer from the start, rather than against the old 20-value single-select vocabulary. This is good timing: nothing needs to be un-built, since LF-C was never implemented yet.
4. **The 41-persona catalog shrinks.** Once condition rows (toddler, teenager, fitness, diabetic, etc.) are extracted into the rules layer, what's left is the genuine composition-and-region catalog — likely a much smaller set, though the exact resulting count needs a follow-up pass to confirm (see Open Questions).

---

## 6. What this does NOT do

- It does not discard the research. Every rule in Section 3 traces directly to a value already present in the workbook — this is extraction, not invention.
- It does not touch the RE's hard-constraint/safety-gate discipline, which remains just as strict for the new condition rules as for existing constraints.
- It does not require rebuilding anything already shipped (candidate repository, weight ladder, cold-start fallback) — those operate downstream of this layer and are unaffected in structure.
- It does not eliminate cohorts/personas as a concept — it narrows what they're responsible for.

---

## 7. Migration path (phased, not a rewrite)

1. **Phase 1 — extract the rules, don't touch the schema yet.** Formally document each condition dimension (Section 3) as an explicit rule: trigger condition — planning implication. This is a documentation/design task, buildable now, independent of any migration.
2. **Phase 2 — fix the vocabulary.** Resolve `household_members.segment` to carry the real condition vocabulary (this directly continues the investigation already underway into the segment mismatch) and allow multiple tags per member.
3. **Phase 3 — build LF-C (add-ons) against the new rules layer**, not the old one — since it doesn't exist yet, there's nothing to migrate here, only to build correctly the first time.
4. **Phase 4 — shrink the persona/cohort catalog** to composition-and-region only, once Phases 1–3 are stable and it's clear the condition-driven boost classes are being generated correctly by rules instead of by row lookup.

Deliberately sequenced so cold-start behavior (which depends on the composition catalog) is never disrupted while the condition layer is being rebuilt underneath it.

---

## 8. Open questions (genuinely open, not decided here)

- **Exactly how many composition-only archetypes remain** once condition-driven rows are extracted — this needs a real pass through all 41 rows classifying each as composition vs. condition-driven, not just the two tested here (toddler, teenager). Recommend this as the next concrete investigation. **Answered by `[ACTIVE]_Phase1_Persona_Decomposition_Catalog_v1.0.md` §1/§4**, which performed exactly this pass: ~5 core composition archetypes (Solo, Couple, Family-with-children, Joint/Multi-generation, Elderly-couple) plus 2–3 sub-variants, not dozens — see the corrected closing note below.
- **Where cooking-capability rules attach** — household-level or a specific member (e.g., whichever member is marked as the primary cook) — the research doesn't fully resolve this, and it's worth a short, targeted check before Phase 2. **Answered by the same Catalog §3/§4:** household-scoped — every cooking-capability row in the source data describes the household's cooking arrangement, never an individual member's dietary need.
- **Whether any condition rules should have priority/conflict resolution** (e.g., a diabetic member who is also pregnant — do both rules apply additively, or does one dominate?) — not addressed by any evidence found so far; flagged as a genuine gap requiring either new research or an explicit Founder judgment call, not something to resolve by assumption. **Resolved in §9c below.**

---

## 9. The inference layer, fully resolved (added after Founder review)

Three refinements, each moving the design from "conditions — rules" to a true inference layer where the RE never sees a condition label at all:

**9a. Semantic attributes live in genome space — not a new vocabulary.** The attribute set (texture, spice_tolerance, protein_target...) deliberately mirrors existing Food DNA dimensions (RE-DOC-02: dimension 3 spice level, dimension 4 texture, dimension 9 protein level). The inference layer's output is therefore a *needs-profile expressed in the same vector space as dish genomes*. Consequence: the RE consumes derived implications natively through the existing ContentMatch similarity computation — no new scoring input, no new mechanism. Condition labels (toddler, fitness, diabetic) exist only upstream, inside the inference layer; the runtime scoring path operates purely on genome-space semantics. This is the full realization of "the RE operates on derived planning implications rather than condition labels."

**9b. Member scoping IS the routing rule (resolves the long-open overlay question) — revised to three channels per the Canonical Planning Model.** Whether a semantic need influences the shared meal, a component of it, or a separate dish is determined by a preference ordering whose primary principle is **maintain one shared family meal whenever safely possible** (evidence: P35 hidden-vegetables, P10 spillover plate, P41 split-plating — see Canonical Planning Model §1):
- **Absorb** — the shared meal itself adjusts (whole household benefits or isn't harmed). Preferred whenever safely possible.
- **Swap** — the shared meal stays one meal; one member's plate substitutes one component (millet roti for wheat roti). Second preference — minimal disruption. *(This channel was missing from this document's first draft; recovered from P41's own text: "add-on components and swaps, not primary meal replacement.")*
- **Add** — a separate small dish, only when the need cannot be met inside the shared meal (infant porridge, teen protein). Additive, never substitutive — consistent with the ratified add-on philosophy.
- Safety-class constraints (allergen, diet, religion) — **hard constraint channel**, bypassing soft scoring entirely, as already ratified.
The same condition can route differently in different households. "Fitness" was never architecturally special — it is simply a condition that frequently applies household-wide.

**9b-supplement — additional semantic attributes recovered from free text** (Canonical Planning Model §0): `repeat_tolerance` (maps onto the existing variety engine's cooldown/MMR settings per household), `meal_timing_pattern` (early dinner, heavy breakfast, frequent small meals), `weekday_weekend_rhythm` (already partially supported by meal classes' day-type fit scores), and `indulgence_policy` (scheduled relief within restriction goals). These join the attribute vocabulary in §3/§9a.

**9c. Conflict resolution mostly dissolves in attribute space.** Apparent condition-level conflicts (pregnant + diabetic) are usually orthogonal attributes (protein_target=high AND glycemic_target=low-GI — both apply; this is in fact correct gestational-diabetes handling emerging by default). True conflicts require the *same attribute at the same scope* — rare, because member scoping separates most cases into different members' add-ons. For the residue, one dominance rule suffices: **safety-derived attribute values (low-GI, restricted sodium, soft texture for medical recovery) always outrank preference-derived values (novelty, cost, elaborateness).** This replaces the open conflict-resolution question in Section 8 with a concrete, small design.

**9d. Practical consequence for the cohort-prior gap (FD-07).** A composition-only catalog collapses the persona × state × diet_mode × city_tier cohort matrix (currently 2,952 rows) to a fraction of its size — materially shrinking the still-unsourced cohort-prior research burden. The architecture change makes an old unsolved problem smaller as a side effect.

*Section 8's open question on conflict resolution is superseded by 9c. The other two open questions (composition-archetype count; cooking-capability attachment point) are answered by `[ACTIVE]_Phase1_Persona_Decomposition_Catalog_v1.0.md` §1/§3/§4 (composition ≈ 5 archetypes + region axis; cooking-capability is household-scoped) — the Catalog's own §1 headline flags that the exact final archetype count still merits one confirmatory pass through all 41 rows against the composition/condition split it applied, which is the only residual, non-blocking follow-up.*

---

## Founder sign-off

Approve this architecture as the direction for the condition/overlay layer redesign (Phases 1–4 above), superseding the "preserve the 41-row catalog as-is" conclusion from the prior investigation document: _______________________ Date: ___________

Approve this architecture as the direction for the condition/overlay layer redesign (Phases 1–4 above), superseding the "preserve the 41-row catalog as-is" conclusion from the prior investigation document: _______________________ Date: ___________
