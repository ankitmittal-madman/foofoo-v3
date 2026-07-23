# Ghar RE v1 — Derived-Attribute Layer (Reconciled)

*Canonical, consolidated derivation layer. Supersedes the D-references scattered across the three research documents (main research doc, E/W top-up, six-dimension doc). This is research/logic, not codification — no weights or schema, but written so codification can lift each derivation directly. Each derivation states: inputs → output → what the new research changed → DERIVE/LEARN/ASK → interactions → open issues.*

---

## How the layer fits the engine

The pipeline is unchanged:

**raw onboarding + context → D-layer computes a derived profile → derived profile selects palette slices + sets base weights → Q15 applies the gain → constraints filter → score dry & liquid pools → pair (compatibility) → diversify into 7 ranked plates → carb attaches as editable default → live re-rank on any change → log outcomes.**

Two things to hold clearly:

- **The D-layer is *logic* (how a household selects), distinct from the *palette* (what's true about regional food, in the state/sub-region/city documents).** The D-layer reads the palette; it is not the palette.
- **Lifestyle (Healthy / Gym-Goer / Casual) is NOT a derivation.** It is the **Q15 gain**, applied *after* the D-layer. Do not model it as a D-node; it re-ranks the pool the D-layer has already shaped. Awesome Taste is the skip default.

## Computation order (the dependency DAG)

Some derivations feed others, so they must compute in order:

1. **Context expansion first:** Q4 → city + city-tier + climate zone; system date → weekday/weekend, season, active festival/fast windows.
2. **Independent nodes:** **D1** (income/price-sensitivity), **D4** (origin↔local blend), **D5** (household constraint-set), **D6** (tiered constraint profile) — none depend on another D.
3. **Dependent nodes:** **D2** (time-pressure routing) needs D1; **D3** (adventurousness) needs D1 and D4.
4. **Behavioural node, v2+:** **D7** (latent-attribute inference) runs only once history exists.

So: *context → {D1, D4, D5, D6} → {D2 needs D1; D3 needs D1+D4} → (v2) D7.*

---

## D1 — Disposable income & price-sensitivity

**Inputs:** Q2 (no. of working professionals) × Q1 (household size/dependents) × Q4 (city cost-tier) × Q12 (age) — plus two affluence *behaviour-ish* signals available at onboarding: Q13 (hired cook present?) and Q14 (eat-out frequency).

**Output:** an income/price-sensitivity **band + a confidence score**, which unlocks: openness to exotic/premium produce (broccoli, zucchini, bell peppers, avocado, asparagus, exotic mushrooms, baby corn), protein frequency and premium-ness, order-in budget, ingredient-brand tolerance.

**What the new research changed (the reconciliation).** The original D1 assumed income was cleanly derivable. The who-cooks research (six-dim doc, Section 6) showed income is the **routing key** for D2 (OUTSOURCE vs SIMPLIFY vs DELEGATE) and that a naive proxy can mis-route a materially time-pressured household. The fix is not to abandon derivation but to make it **explicit, confidence-scored, and conservative when unsure**:

- **Strong upward signals:** Q13 = hired domestic cook present (a real affluence marker per the Section 6 prevalence work — concentrated in Tier-1/2 upper-middle/HNI households), Q14 = high eat-out frequency, Q4 = Tier-1 metro, Q2 = 2 earners with Q1 = no dependents.
- **Downward signals:** single earner + multiple dependents, smaller-city tier.
- **Confidence:** high when several signals agree; low when they conflict (e.g., Tier-1 metro but single earner with dependents). **On low confidence, lean conservative — do not over-surface premium/exotic; default to mainstream-affordable heroes.**

**DERIVE / LEARN / ASK:** **DERIVE via the proxy above; LEARN-correct from order-in/premium-pick behaviour in v2.** Do **not** add an income question yet — see the consolidated income decision at the end. This is the one place where "ask" is a live candidate, held back deliberately.

**Interactions:** D1 modulates D2 (routing) and D3 (adventurousness — money widens the roam). **Conditional, not additive:** two earners + no dependents + Tier-1 = low price-sensitivity → exotic/premium open; two earners + kids + parents = higher dependency ratio → more value-conscious even at the same earner count.

**Open issue:** the proxy's reliability is unmeasured until we have usage. Carries a defined promote-to-ASK trigger (below).

---

## D2 — Time-pressure routing

**Inputs:** Q2 × Q13 × Q14, **modulated by D1**.

**Output:** resolves "time pressure" into one of **{SIMPLIFY in-house · DELEGATE to cook · OUTSOURCE/order}** plus an **effort/complexity ceiling** for home heroes — *not* a flat effort penalty.

**What the new research changed.** Section 6 (who cooks) gave this node its full structure. The **cook's identity sets the ceiling**, and **income sets the branch**:

- **Self-cooks (busy professional):** low weekday ceiling — quick, one-pot, prep-ahead; sharp weekday↔weekend divergence (elaborate on weekends).
- **Family member (homemaker/parent):** high ceiling — elaborate, traditional, daily-fresh feasible.
- **Hired domestic cook:** ceiling *lifted* (elaborate daily despite time pressure) **but** introduces a learnable **cook's-region repertoire bias** + a consistency/availability discount (cook's day off, skill).
- **Order-in / tiffin:** ~zero home ceiling → route to restaurant/tiffin-appropriate heroes; tiffin implies a standardised weekday rotation.

The **branch by income (D1):** same trigger (high Q2 + low time) routes to **OUTSOURCE for high income, SIMPLIFY for low income, DELEGATE when a cook is present.**

**DERIVE / LEARN / ASK:** **DERIVE** the branch and ceiling from Q13 × Q2 × Q14 × D1; **LEARN** the cook's-region repertoire bias from behaviour.

**Interactions:** depends on D1; stacks with D5 (a multi-gen household with a hired cook can sustain elaborate traditional cooking the same structure self-cooking cannot); feeds weekday/weekend hero weighting.

---

## D3 — Adventurousness / cuisine-promiscuity

**Inputs:** Q1 (single/young couple) × Q12 (age band) × **D1** (income) × **D4** (migration exposure) × Q14 (eat-out).

**Output:** how far to roam from the origin palette (origin-comfort ↔ pan-Indian ↔ global), and **where** novelty is allowed (experimentation concentrates at dinner and weekends; breakfast and weekdays stay comfort/origin).

**What the new research changed.** Section 3 (age) gave a finer **novelty curve by band** — peaks at teen / young-adult (highest order-in, highest experimentation), settles through adult, and **drops in middle-age and elderly (comfort-traditional)**. Section 5 (household) added: **couples experiment more; couples-with-kids revert to familiar/mild; joint families have low per-head experimentation.**

**DERIVE / LEARN / ASK:** **DERIVE** the starting adventurousness; **LEARN** the true roam from accept/reject behaviour (a conservative-looking profile that keeps trying new dishes gets loosened).

**Interactions:** depends on D1 and D4; bounded by D5 (a binding toddler/elder pulls shared heroes back to comfort regardless of an adventurous adult — keep novelty in the *extra* plates of the 7, not the shared hero).

---

## D4 — Origin↔local blend (migration)

**Inputs:** Q3 (home state) vs Q4 (current city/state), modulated by Q1 (elders ↑ retention), Q12, and **tenure-in-city (learned)**.

**Output:** a **blend weight** between the home-state palette and the local-city palette, with slot-specific stickiness.

**What the new research changed.** This node is now well-instrumented from **two layers**:

- **Strand B (main doc)** = the corridor + theory: intra-India corridors, retention-vs-adoption, decay-with-tenure.
- **Section 2 (six-dim doc)** = the eight concrete metro targets to blend *toward*: Mumbai (coastal-Maharashtrian + Bombay street), Pune (Maharashtrian + IT-cosmopolitan), Ahmedabad (Gujarati + Jain veg), Delhi-NCR (Punjabi-Mughlai pan-North), Bengaluru (Udupi/South + all-India + heavy delivery), Chennai (Tamil + tiffin), Hyderabad (Telugu + Deccani biryani), Kolkata (Bengali + Marwari + Indo-Chinese).

**Slot stickiness (the retain/adopt rule):** RETAIN = breakfast + festival/fast foods + the dal-rice-roti dinner structure; ADOPT = local lunch staples, local produce, local convenience/street food.

**Strongest blend overrides flagged:** **Ahmedabad** (strong veg-environment pressure — down-weight non-veg availability even for non-veg origin) and **Chennai** (rice/tiffin pressure — shift breakfast toward tiffin, lunch toward rice-sambar even for North origin).

**DERIVE / LEARN / ASK:** **DERIVE** the initial blend from Q3≠Q4 + the city profile; **LEARN** tenure and the true decay rate per household (the genuinely thin part — food-acculturation speed is not rigorously measured, so the initial blend is a *default the user corrects*).

**Interactions:** feeds D3 (migration exposure raises roam); modulated by D5 (elders raise retention).

---

## D5 — Household selection-constraint set

**Inputs:** Q1 (household structure) × Q12 (age bands present).

**Output:** which member's constraints **bind**, the **variety/recency pressure**, **texture/mildness floors**, **dinner timing/lightness**, and **portion/batch** posture.

**What the new research changed.** This node went from a sketch to full depth via **Section 5 (six household structures)** and **Section 3 (eight age bands)**:

- **Structure (Q1):** SINGLE (high repetition tolerance, one-pot, small portion, high order-in) · COUPLE (two palates, experiment, weekend indulgence) · COUPLE+KIDS (child dictates → mild/familiar, faster variety fatigue, nutrition ↑) · COUPLE+KIDS+PARENTS (**hardest case** — must satisfy elder-soft/light/traditional AND kid-mild simultaneously) · JOINT FAMILY (standardised batch menus, low per-head novelty, strong veg-day/fasting) · FLATMATES (individual plates, not a household plate; convenience, order-in).
- **Age (Q12):** the **weaning band (6mo–2yr) is the one HARD FILTER** (mild, soft, no-chilli, low-salt); toddler = strong mildness; elderly = soft-texture + light/early dinner + traditional.

**The governing rule:** apply the **most-restrictive-member floor** to *shared* heroes (the youngest child and oldest elder set the mildness/texture floor), while still allowing an indulgent hero elsewhere in the 7-plate list for unconstrained members (the across-7 variety guard absorbs this).

**DERIVE / LEARN / ASK:** **DERIVE** from Q1 × Q12; **LEARN** the household's true variety-fatigue/recency tolerance (qualitative in the literature — harden only after behaviour confirms).

**Interactions:** stacks with D2 (effort ceiling — who can execute the constrained menu) and D3 (caps novelty on shared heroes).

---

## D6 — Tiered constraint profile

**Inputs:** Q5/Q6 (diet, non-veg types) × Q7 (veg-days) × Q8 (Jain) × Q9/Q10 (allergies) × Q11 (conditions, secondary) × Q3 (community/state prior).

**Output:** graded constraints, **not on/off switches:** veg gradients (pure veg / eggetarian / fish-but-no-meat / no-onion-garlic sattvic-Vaishnav), non-veg **cadence** (coastal fish-daily vs inland weekend-meat, red-meat avoidance), **Jain tiers** (root-veg, after-sunset/chauvihar, chaturmas/paryushan escalation, fermented/multi-seed), veg-day **substitution** (swap the meat hero for a veg/paneer hero on the household's veg-days, don't blank the slot), and **region × allergen collision severity** (peanut bites harder in Maharashtrian/South; coconut in Kerala/coastal; mustard in Bengali/Bihari/Kashmiri-Pandit; hing→hidden-wheat for gluten/celiac).

**What the new research changed.** Section 1 added **state diet-defaults (NFHS-5 leanings)** as the **soft community/state prior** that seeds D6 — e.g., Rajasthan/Gujarat/Haryana veg-leaning; Kerala/Goa/Bengal/coastal-AP non-veg-default; Bengal = fish-default-not-indulgence. These are **priors only, always overridden by the explicit Q5–Q8 answers.**

**DERIVE / LEARN / ASK:** the core is **ASKED** (Q5–Q8, Q9–Q11 — safety-critical, must not be derived); the **community prior and dish-level allergen/derivative conflicts are DERIVED** (from Q3 + dish-DNA); exact veg-day weekday and observance strictness are **LEARNED** (and feed D7).

**Interactions:** D6 produces the **hard filters** that run *first* at runtime; everything else only ranks. The veg-day case is a *scheduled substitution*, not a removal.

---

## D7 — Latent-attribute inference (v2/v3, from behaviour — never asked)

**Inputs:** behavioural signals over time (picks, the calibration like-taps, ad-hoc filter deviations) against the festival/fast calendar.

**Output:** inferred latent attributes — religion/observance, fasting participation, community sub-tradition — that **back-activate** the correct calendar and blend rules without ever asking a sensitive question.

**What the new research changed.** Nothing in the six new dimensions touched D7 — confirmed. It remains as specified in the main doc, anchored by the **festival/fast → signature-dish map** (Navratri/Shravan/Ekadashi farali → observant fasting Hindu → fast calendar on; sewain/sheer-khurma + mutton at Eid → Muslim household → Ramzan timing + no-pork default; Onam sadhya, Pongal, Baisakhi, Durga-Puja bhog, Christmas → region/community).

**DERIVE / LEARN / ASK:** **LEARN only (v2+).** Deliberately never ASK. Ethical by design — no sensitive question.

**Interactions:** writes back into D4 (community → blend/retention) and D6 (observance → veg-day/fasting tiers). Also the seed for v3 cohort clustering.

---

## The income decision — resolved (the one thing to confirm)

Income is the only attribute the layer cannot cleanly derive and the only live ASK candidate. **Recommendation: hold the line — do not add a question yet.** Resolve it in this order:

1. **DERIVE via proxy now (D1):** income_band ≈ f(Q4 city-tier, Q2 earners, Q1 dependents, Q13 hired-cook present, Q14 eat-out frequency, Q12 age), emitted **with a confidence score**, conservative-when-unsure.
2. **LEARN-correct in v2** from order-in and premium/exotic-pick behaviour.
3. **ASK only as a last resort**, and only if a measurable trigger fires.

**Promote-to-ASK trigger (define it now, act later):** if v2 data shows the proxy mis-routes D2 (OUTSOURCE/SIMPLIFY/DELEGATE) for a material share of high-time-pressure households — i.e., proxy-predicted routing disagrees with revealed behaviour beyond an agreed threshold — add **one coarse affordability question**, not a granular income field. Until then, onboarding stays at 15.

*(Note: the only other new-question candidate raised anywhere in the research is **community/sub-tradition** for D6/D7 sharpening — separate decision, also held as derive-then-learn unless you want it asked.)*

---

## Reconciliation summary

| Node | Status after reconciliation | New research absorbed | Derive / Learn / Ask |
|---|---|---|---|
| D1 income/price-sensitivity | Rewritten: explicit confidence-scored proxy | Section 6 (income as routing key) | DERIVE (proxy) + LEARN; ASK held |
| D2 time-pressure routing | Full structure added | Section 6 (who-cooks ceilings; income branch) | DERIVE + LEARN |
| D3 adventurousness | Refined | Section 3 (age novelty curve), Section 5 (structure) | DERIVE + LEARN |
| D4 origin↔local blend | Instrumented | Strand B (theory) + Section 2 (8 metro targets) | DERIVE + LEARN tenure/decay |
| D5 household constraint-set | Sketch → full depth | Section 5 (6 structures) + Section 3 (8 age bands) | DERIVE + LEARN variety-fatigue |
| D6 tiered constraints | Prior added | Section 1 (state diet-defaults as soft prior) | ASK core + DERIVE prior + LEARN veg-day |
| D7 latent inference | Unchanged (confirmed) | none | LEARN only (v2+) |

**Loose ends now closed:** the new research is folded back into the D-layer; lifestyle is correctly placed as the Q15 gain (not a D-node); and the income tension is resolved into a proxy-now / learn-next / ask-only-if-triggered path. The only decision left for you is whether you accept that income stance — if yes, the derivation layer is codification-ready.


---

## Future / Deferred / RFC Register  *(this document)*
*Quick-reference index of this document's forward-looking items. Convention: `[ID] [TAG] Title — trigger/what-it-needs — STATUS`. Tags: [v2]/[v3]/[KB]/[SAFETY]/[DATA]/[DB]/[later]/[parked]. Status: OPEN / RFC-DRAFTED / DONE(vX.Y). When this file is edited, update the relevant line so the freeze lineage stays in-place. Detailed rationale for each item is in the sections above.*

*Note: this is the rationale/reasoning document behind D1–D7. The frozen, implementable version is `ghar_re_v1_0_derivation_D1_D7_FROZEN.md` — track forward items there (IDs D-F1…D-F7). This document is reference; no separate open items beyond those.*

| ID | Tag | Item | Status |
|---|---|---|---|
| RECON-F1 | — | Superseded by frozen D1–D7 for implementation; kept as rationale record | REFERENCE |

