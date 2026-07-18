# [ACTIVE]_Canonical_Planning_Model_v1.0

**Status:** ACTIVE — product-thinking artifact; no implementation, no schema, no code
**Date:** 2026-07-17
**Position in the stack:** Planning Knowledge Library (Phase 1/1B) — **this document** — Food Genome — Recommendation Engine
**One question answered:** *How should FooFoo think before it recommends?*

---

## 0. New evidence found first (the free-text audit)

Before designing the reasoning model, the previously unread `revealed_behavior_summary` column (all 41 rows) was audited for trapped planning knowledge. **Significant knowledge exists there that Phase 1B did not extract:**

| Trapped knowledge | Evidence (verbatim fragments) | What it is |
|---|---|---|
| **Repeat tolerance** | P01 "repeat tolerant", P12/P27/P37 "low(er) repeat tolerance" | A missing semantic attribute — maps directly onto the existing variety engine's cooldown/MMR settings, per household |
| **Meal timing** | P14 "early dinner", P38 "heavier breakfast, late lunch", P36 "frequent small meals" | A missing attribute family: when and how often, not just what |
| **Weekday/weekend rhythm** | P04 "weekday quick; weekend experimental", P30 "weekday egg/chicken, weekend special", P33 "Sunday mutton" | A pervasive temporal frame — partially supported already (meal classes carry weekday/weekend fit scores) but never modeled as household-level knowledge |
| **The swap mechanism** | **P41: "child/elder/diabetic needs are handled as add-on components and swaps, not as primary meal replacement"** | The research names **three** channels — add-on, **swap**, and shared-bias — where our architecture modeled only two. A swap replaces one component *within* the shared meal (e.g., the diabetic elder gets millet roti while the family has wheat roti) without adding a dish or changing the family's meal identity |
| **Rotation logic** | P05 "alternates two home-state signatures", P29 "dual-state rotations across week" | Deliberate alternation patterns — richer than a boost; a *structure* over the week |
| **Controlled indulgence** | P17 "controlled indulgence" | Weight-loss is planned *with* scheduled relief, not as unbroken restriction — a sustainability intent |
| **Coherence** | P13 "multi-dish meals... high coherence" | Multi-dish meals must go together as a plate — a plate-level constraint, not a per-dish score |
| **Concealment strategy** | P35 "adult vegetables hidden/rotated" | A preparation strategy for picky children — knowledge about *how* to serve, not what |
| **Parallel meal tracks** | P08 "adult meals quick; infant milk; mother supportive meals" | One household can run three simultaneous meal tracks |

**Consequence, stated openly:** Phase 1B's extraction was complete for the *boost-class* knowledge but not for the *planning-behavior* knowledge. The attribute vocabulary needs these additions: `repeat_tolerance`, `meal_timing_pattern`, `weekday_weekend_rhythm`, `indulgence_policy`, and the routing options need a third channel: **swap**.

---

## 1. The reasoning journey (how an expert would think)

A nutritionist handed a household profile does not start with food. They start with people, and they reason in this order:

**First — Who is here?** Composition: how many people, roughly what ages, living in what arrangement. This frames everything but decides nothing yet.

**Second — What is non-negotiable?** Allergies, religious rules, hard diet identity (Jain, vegetarian). These are not preferences to weigh; they are boundaries that remove options permanently. An expert settles these first precisely so they never have to think about them again.

**Third — Who needs individual attention?** Scan the members for conditions: the toddler, the diabetic elder, the pregnant member. Each flagged member gets a *need*, held separately.

**Fourth — For each need: how should it be met?** This is the decision the research's P41 row states in its own words. Three ways to meet a member's need, in order of preference:
1. **Absorb into the shared meal** — maximum family harmony; everyone eats together (everyone can eat lower-oil food; the family meal simply becomes lower-oil).
2. **Swap a component** — minimal disruption; the shared meal stays one meal, one member's plate substitutes one element (millet roti for wheat roti; unsalted portion set aside before seasoning).
3. **Add a component** — only when the need cannot be met inside the shared meal at all; a separate small dish is made (infant porridge, teen's extra protein).

**The primary principle behind this ordering is: *maintain one shared family meal whenever safely possible.*** Effort minimization is a real secondary benefit, but it is a consequence, not the cause — proven by three research rows where harmony and effort point in *opposite* directions and households choose harmony: P35's "adult vegetables hidden/rotated" (concealment is harder than a separate plain kid's plate — done anyway to keep the child in the family meal); P10's "toddler spillover plate" (the toddler eats from the family's food, not a dedicated track); P41's own cook-dependency, "split plating" (setting aside an unsalted portion mid-cooking is fiddlier than a separate small dish — chosen anyway, because the meal stays one meal). This is commensality — the shared meal as the unit of family life — and it is the deepest product principle in the research: FooFoo plans *meals for a family*, not *diets for individuals who happen to share a kitchen*. Cooking capacity still acts as a real feasibility ceiling (§5), but the *preference order itself* exists to protect the shared meal, with "safely possible" as its only override.

**Fifth — What is this household's rhythm?** Weekday vs. weekend character, meal timing, how much repetition they tolerate, whether indulgence is scheduled. This is the *frame of the week* — it structures when things happen, while the needs structure what.

**Sixth — Only now, food.** With boundaries set, needs routed, and rhythm framed, the expert forms concrete meal intentions — and this is exactly the point where FooFoo's existing machinery (attributes — classes — genome — scoring) takes over.

---

## 2. The complete inventory of planning decisions

Every distinct decision an expert makes, made explicit:

1. What kind of household is this? (composition)
2. What can never be served? (safety/identity boundaries)
3. Which members carry conditions? (member scan)
4. Which needs are shared vs. individual? (scope resolution)
5. For each individual need — absorb, swap, or add? (channel routing — the P41 decision)
6. Do any needs conflict on the same attribute at the same scope? If so, safety-derived wins. (conflict resolution — already designed in §9c of the architecture doc)
7. What is the weekly rhythm? (weekday/weekend character, timing, repeat tolerance, indulgence schedule)
8. How much cooking capacity exists? (a feasibility ceiling on how many swaps/add-ons the plan can afford — see §6, missing thinking)
9. What are the resulting meal-level targets? (semantic attributes per meal, per track)
10. What structural rotation applies? (dual-region alternation, festival/fasting day substitutions)
11. Which meal classes satisfy the targets? (Phase 1B's rules)
12. Which dishes, in what variety pattern? (existing RE: genome match, variety engine, safety gates)

Decisions 1–10 are planning. Decisions 11–12 are recommendation. **The boundary between "planning intelligence" and "recommendation engine" sits exactly between 10 and 11** — everything above it produces intent; everything below it selects food.

---

## 3. Does a Planning Intent layer exist? (tested, not assumed)

The instruction was to keep this layer only if evidence supports it. **The evidence supports it — narrowly.** Two proofs:

- **Same attribute, different intent, different plan.** `calorie=restricted` under intent *"sustainable weight loss"* produces P17's "controlled indulgence" (scheduled relief); the same attribute under a hypothetical *"strict medical restriction"* would not. The attribute alone cannot distinguish these — the intent can.
- **Intent without a condition.** The research gives elderly households low-GI breakfasts *preventively* — no diabetes exists, so no condition fires, yet the planning behavior exists. The carrier of that behavior is an intent ("protect aging metabolism"), not a condition.

**But the layer is thin.** Most conditions map to attributes without any meaningful intent in between (toddler — soft texture needs no purpose statement to work). So: the model includes intent as an *optional* annotation that exists for exactly the cases that need it — trade-off policies (indulgence), preventive care, and explainability — rather than as a mandatory step every condition passes through. Forcing every condition through an intent layer would be architecture theater; having it available where it changes the outcome is real.

---

## 4. The derived planning hierarchy

Derived from the reasoning above — note it is *not* a single chain; rhythm and capacity sit alongside, not inside, the member chain:

```
                    Household
                   /         \
            Composition      Members
                 |              |
        (cold-start frame)   Conditions ──→ Needs ──→ [optional: Intent]
                 |              |                          |
                 |         Channel routing            Attributes
                 |        (absorb / swap / add)      (genome-space)
                 |              \                        /
                 |               \                      /
        Weekly Rhythm ─────────→ Meal-level targets, per track
        (weekday/weekend,               |
         timing, repeat            Meal Classes  — Phase 1B rules
         tolerance,                     |
         indulgence)              [ RE takes over:
        Cooking Capacity ──────→ genome match, variety,
        (feasibility ceiling)      safety gates, scoring ]
```

---

## 5. Canonical decision ordering (with the "never before" rules)

1. **Safety boundaries always first.** Nothing else may run before allergens/diet/religion are fixed — because every later decision must operate inside them, and no later decision may ever relax them.
2. **Member scan before channel routing** — you cannot route a need you haven't found.
3. **Channel routing before target-setting** — a need's attributes attach to *different meals* depending on its channel (a swap's attributes attach to one component; an add-on's to its own dish).
4. **Rhythm and capacity before finalizing routing** — capacity can force a downgrade (a household whose cook can't manage three add-ons may need more absorb/swap and fewer adds). This is the one feedback loop in the sequence, and it's why rhythm/capacity sit beside the chain, not after it.
5. **Taste and preference last, always.** Preference may influence *which* safe, need-satisfying dish is chosen — never *whether* a need is met. An expert never reverses this.

---

## 6. Explainability: the reasoning chain every recommendation can produce

Every recommendation becomes traceable as a human sentence assembled from the chain:

*"Millet roti swap for Grandfather because: he has diabetes (condition) — manage glucose (intent) — low-GI target (attribute) — swap channel (family meal unchanged, per household preference for shared meals) — millet roti (class/dish match). The family's meal is unchanged because his need was met by swap, not replacement."*

Every link already exists in the model: member — condition — [intent] — attribute — channel — class — dish. No black box appears anywhere in the planning layers; the only statistical component (scoring/exploration) sits *after* all reasoning is fixed, choosing among already-valid options — which is exactly where statistics belongs.

---

## 7. Stress test: four households that never existed in Persona Master

The test is whether the *reasoning process* stays stable — not whether outputs are correct.

**Toddler + Elderly + Fitness parent:** boundaries — none special; scan — 3 flagged members; routing — toddler: add (soft porridge track), elderly: swap-first (soft/early-dinner components), fitness: absorb-or-add depending whether other adults share it; rhythm — early dinner (elderly) shapes the whole household's dinner slot; targets per track; classes per Phase 1B Rules A+B+C. **Process stable.** Notable: elderly timing affects the *shared* rhythm while toddler needs stay in the add-on track — the model expresses this naturally because rhythm and needs are separate layers.

**Pregnant + Vegetarian + Working couple:** vegetarian = boundary (first); pregnant = condition — intent (support pregnancy) — protein/iron targets inside veg constraint (Rule B's diet gate already handles this); working = time pressure — rhythm (quick weekdays); routing — mostly absorb (both adults benefit from balanced meals). **Stable, and simpler than it looks** — most needs absorb.

**Joint family + Diabetic + Teenager + Seafood preference:** seafood = diet-pattern (preference, not boundary — outranked by any member's actual restriction); diabetic — swap-first per P41's own logic; teen — add (extra protein components); coherence constraint (P13) applies to the multi-dish thali; capacity check matters — joint family cooking supports more tracks. **Stable; capacity ceiling earns its place.**

**Elderly couple + Recovery + Budget:** elderly+recovery converge on identical attributes (Rule A — the research itself proved this with identical class lists); budget = cost_bias on selection, never on whether needs are met (ordering rule 5). **Stable; the conflict everyone would expect (budget vs. medical needs) never occurs because ordering forbids it.**

**Verdict: the reasoning process is stable across all four.** No new mechanism was needed for any of them; every household resolved into the same sequence with different values.

---

## 8. Missing thinking — what a human expert does that this model still cannot

Honestly listed, no implementation proposed:

1. **Portions and quantities.** The model reasons entirely in *kinds* of food. An expert also reasons in *amounts* — a teen's need is partly "more," not just "different." Nothing in the current knowledge represents quantity.
2. **Weekly nutritional adequacy.** An expert mentally tracks "did this week deliver enough iron/protein/vegetables overall?" The model plans meal-by-meal with variety windows but has no week-level nutritional accounting.
3. **Cooking capacity as a real constraint.** §5 names the feasibility ceiling, but no knowledge exists about how much a given cooking arrangement can actually produce (how many simultaneous tracks can one cook manage?). The cook-capability conditions describe *skill*, not *capacity*.
4. **Leftover planning.** The free text mentions leftovers as behavior (P25, P37); an expert *plans* them deliberately (cook once, eat twice). The model treats leftovers as a class preference, not a planning strategy.
5. **Grocery/seasonal availability.** Seasonal affinity exists in the genome; an expert also reasons "what's actually in the kitchen / in season / affordable this week." No ingredient-availability reasoning exists.
6. **Preparation strategies.** P35's "vegetables hidden/rotated" is knowledge about *how to prepare and present*, a dimension the model can carry as advice but cannot reason over.
7. **Outcome adaptation.** An expert adjusts when the diabetic member's numbers improve or the picky child starts accepting vegetables. The learning loop adapts to *acceptance*, not to *outcomes* — a deliberate MVP boundary worth naming as a boundary.

---

## 9. Self-challenge (per the mandate)

- **Assumption revised (Founder-prompted, then evidence-confirmed):** this document's first draft attributed the absorb→swap→add ordering to cooking effort. Tested against the discriminating cases (P35 hidden vegetables, P10 spillover plate, P41 split plating — all instances where households accept *more* effort to preserve the shared meal), the true primary principle is **shared-meal preservation**, with effort as a consequence. Revised in §1.
- **Assumption revised:** the architecture doc's two-channel routing (add-on / shared-bias) was **incomplete** — P41's own text mandates three (absorb / swap / add). Revised openly here; the swap channel is the single most consequential finding of this exercise, and it came from a column nobody had read.
- **Assumption confirmed:** the optional-intent conclusion (§3) was tested against the instruction "do not force this layer to exist" — evidence supports its existence for a minority of cases, so it's included as optional rather than mandatory. That is the honest middle, not a hedge.
- **Assumption held under pressure:** the genome-space attribute decision survived the stress tests unchanged — all four novel households resolved into existing attribute vocabulary plus the new rhythm additions from §0.
