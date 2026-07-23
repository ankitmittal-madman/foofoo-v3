# Ghar RE v1 — Final Research Document: Weather, Pairing Guardrails, Carb Defaults, Modes & Deferred Register

## TL;DR
- **Weather is a DERIVED, TRANSIENT same-day signal** (from a weather API on Q4 location) that boosts/demotes comfort/thermal/fried/light tags — never a hard filter — and it MUST pull comfort heroes from the household's own regional palette (rainy-day Maharashtra → kanda bhaji; Bengal → khichuri-beguni; Tamil Nadu → rasam), not a generic pan-India pakora.
- **Pairing guardrails are codify-now NEGATIVE rules** (no two rich gravies, no two same-base gravies, no two dry heroes, keep one-region coherence, flag standalone complete dishes); POSITIVE "delightful match" affinities are explicitly deferred to **v2 learning**.
- **Carb defaults are a simple DERIVE rule** from region + liquid-hero type over the fixed set {Roti, Paratha, Poori, Rice}; observance/fasting/festival become **user-toggled MODES** (no panchang integration in v1), and a long Deferred/Parked register is captured with explicit "what it would take to build later" notes.

## Key Findings

**Honest evidence caveat up front:** Day-level (acute) weather→food response in India is documented heavily in food journalism, recipe media and Ayurvedic *ritucharya*, but is **rarely quantified**. A dedicated search for hard "rainy-day vs normal-day" comfort-food uplift numbers from Swiggy/Zomato/Blinkit/Zepto returned essentially none — platforms publish granular annual dish counts and festival spikes but do not break out weather effects on specific dishes. The cleanest quantified India datapoints are seasonal, not single-day. The most rigorous day-level evidence is academic and rural: **Stainier, Shah & Barreca (2025), NBER Working Paper w34047** (published in the *Journal of the Association of Environmental and Resource Economists*, Vol 13 No 2, 2026), using NSS data on 300,000+ rural households (2003–2012), found that **"a day above 110°F leads to a reduction of 4 kCal per person per day (roughly 1g of uncooked rice) from home-grown sources, and a 5 kCal per person per day increase in purchased food,"** and that one additional day above 110°F raises strong caloric undernourishment by 0.36 percentage points (≈3.1 million people). On the seasonal cooling side, **Dr Meenesh Shah, Chairman of NDDB & Mother Dairy, told Business Standard (Sharleen Dsouza, 2 June 2026): "We have seen over 30 per cent growth in ice creams, buttermilk and curd products which are largely consumed in the summer … a pick up in this trend over the last three to four years, particularly after Covid."** Treat the weather strand as **directionally strong, qualitatively robust, quantitatively thin** — which is exactly why it is implemented as a soft transient boost, not a hard rule.

---

## STRAND 1 (DEEP) — Weather-Driven Daily Food Response

### Framing & engine action
- **Distinction:** WEATHER = acute, day-level (it is raining today, a heatwave today, a cold snap today). SEASON = the macro calendar window (covered separately). This strand is only the acute layer.
- **Derivation:** DERIVE from a weather API keyed to the user's **Q4 current city/location** — current condition + temperature + rain/precipitation. No ASK.
- **Engine action:** a **transient, same-day BOOST/DEMOTE** on tags (comfort, thermal-warming, thermal-cooling, fried, light/hydrating). **Never a hard filter.** It nudges ranking within the 7-plate list; it does not remove dishes.
- **Two key interaction effects:**
  1. **Weather × Region (palette):** the SAME weather triggers DIFFERENT comfort heroes by state/cuisine. A rainy day must surface the household's own rainy-day heroes, not a generic pakora. This is the single most important design rule of the strand.
  2. **Weather × Meal-slot:** rain mostly hits the **snack/tea mood and dinner**; heat mostly **suppresses lunch heaviness** and pushes lighter dinners. The boost should be slot-aware.
- **"Mood" is explicitly OUT OF SCOPE now** — noted as a future related mode, not built in v1.

### (a) RAIN / MONSOON DAY — comfort-food response
- **Marries:** Q4 (location/weather), Q3 (home state → which comfort hero), Q13 (who cooks → fried-snack feasibility), Q15 (objective → how much indulgence is allowed).
- **Pan-India comfort pattern (well documented):** hot fried snacks + chai (pakora/bhajiya, samosa, vada), khichdi, hot soups (rasam, shorba), corn/bhutta, and ginger/pepper/tulsi teas; "hot, quick, familiar, a little lighter on digestion." Swiggy's "How India Swiggy'd 2025" (10th annual report, data Jan 1–Nov 30 2025) quantifies the comfort-snack ritual nationally: **"The Chai-Samosa ritual continued with 3.42 million Samosas and 2.9 million Adrak Chai ordered during snack time (3pm–7pm) in 2025"** — though notably with no rainy-day breakdown.
- **Documented monsoon AVOIDANCES:** raw leafy greens/salads (moisture-borne contamination), heavy/creamy foods ("choose dry over creamy"), street food, and — in some coastal traditions — seafood during peak monsoon (breeding season / freshness). Apply as a mild demote, never a filter.
- **Region/cuisine-wise rainy-day comfort heroes (for per-state palette codification):**
  - **Maharashtra:** kanda bhaji (onion bhajiya) + chai; batata poha; pithla-bhakri; sabudana.
  - **North India (Punjab/Delhi/UP):** pakora (aloo/onion/paneer) + adrak chai; samosa; stuffed/aloo parathas with pickle; kadhi-pakora.
  - **South India (Tamil Nadu/Karnataka/Andhra/Kerala):** rasam + rice + papad; pepper rasam (milagu rasam) and medu vada/garelu; bajji/bonda + filter coffee. Pepper rasam is explicitly "often prepared during colder months or when someone has a cold or cough."
  - **West Bengal:** khichuri (gobindobhog rice + moong dal) with beguni (battered fried eggplant), papad bhaja, omelette, and — when available — ilish (hilsa) fry. This is the iconic Bengali rainy-day plate.
  - **Gujarat:** dal-pakwan/bhajiya; dalwada (lentil fritters); makai (corn) preparations; methi/mixed bhajiya + chai.
  - **Rajasthan:** pyaaz kachori, bajra/gehun khichdi.
  - **Odisha/East:** khichdi + fried sides.
- **Engine action:** transient BOOST on `comfort`, `fried-snack`, `warm-soup`, `hot-beverage` tags; mild DEMOTE on `raw/salad` and (coastal, peak monsoon) `seafood`; boost weighted toward snack/tea and dinner slots. Boost must resolve to the household's regional hero set, not a global default.

### (b) PEAK SUMMER / HEATWAVE DAY — cooling/hydrating response
- **Marries:** Q4 (temperature/heat), Q3 (regional cooling hero), Q11 (conditions, as secondary demoter), Q15 (objective).
- **Pan-India cooling pattern:** curd rice, chaas/buttermilk, aam panna, sattu sharbat, light meals, curd-based dishes, watermelon/cucumber, lighter dinners; AVOIDANCE of heavy/fried/very-spicy foods. Appetite and digestion are weaker in heat (Ayurveda: agni diverted), so the plate should read lighter. Quantified seasonal corroboration: NDDB/Mother Dairy's **over 30% summer growth in ice creams, buttermilk and curd** (Meenesh Shah, Business Standard, 2 June 2026).
- **Region/cuisine-wise summer cooling heroes:**
  - **West coast (Maharashtra/Goa/Konkan):** sol kadhi (kokum + coconut milk), kokum sharbat; rice-led light meals.
  - **Tamil Nadu:** neer mor (spiced buttermilk), curd rice, tamarind/buttermilk-based light meals; pazhaya sadam (fermented rice).
  - **Odisha (+ Bengal/Assam/Jharkhand/Chhattisgarh):** pakhala/pakhala bhata (water/curd-fermented rice) with badi chura, saga bhaja, fried fish; Bengal panta bhat; Assam poita bhat. Pakhala is "generally eaten in the summer… viewed as refreshing," and "consumption is usually avoided in extreme cold."
  - **North/East India:** sattu sharbat, aam panna, bael sharbat, jaljeera; soaked poha; chilled curd rice.
  - **Gujarat/Rajasthan:** chaas (a "day without chaas in summer is a difficult day"), aamras with rotli/poori (seasonal), kadhi.
- **Engine action:** transient BOOST on `cooling`, `curd-based`, `hydrating`, `light` tags; DEMOTE `fried`, `rich-gravy`, `very-spicy`, heavy heroes; bias toward lighter lunch and dinner. Again, resolve to the regional cooling hero, not a generic curd rice.

### (c) WINTER / COLD SNAP DAY — warming/calorie-dense response
- **Marries:** Q4 (cold/temperature drop), Q3 (regional warming hero), Q12 (age — richness tolerance), Q15 (objective).
- **Pan-India warming pattern:** ghee, jaggery (gur), sesame (til), bajra/makki, warming spices (ginger, garlic, black pepper); richer and heavier permitted. Ayurveda's *Hemanta/Shishira* guidance: agni is strongest, so "unctuous, sweet, sour and salty" and heavier nourishing foods are recommended; cold/raw foods are discouraged.
- **Region/cuisine-wise winter warming heroes:**
  - **Punjab/North:** sarson da saag + makki di roti; gajar halwa; gond/dry-fruit laddoo; panjiri; nihari/paya (non-veg households).
  - **Gujarat:** undhiyu (winter mixed-veg), bajra no rotlo + ringan no olo with jaggery + white butter; methi thepla.
  - **Rajasthan:** bajra khichdi, bajra rotla.
  - **Maharashtra:** bajri/jowar bhakri with thecha/pithla; tilgul (Sankranti).
  - **Pan-India winter sweets:** til/sesame laddoo & gajak, moong dal halwa, gajar halwa — heavily clustered at Makar Sankranti/Lohri/Pongal (til-jaggery).
  - **Himalayan/Ladakh:** thukpa, skyu (warm stews).
- **Engine action:** transient BOOST on `warming`, `ghee-rich`, `calorie-dense`, `millet (bajra/makki)`, `jaggery/til` tags; relax the richness penalty (winter permits heavier). Resolve to the regional warming hero.

### (d) HUMID vs DRY heat (documented but qualitative)
- Ayurveda treats humid heat (late summer/early monsoon transition) as compounding **Kapha + Pitta + Vata**, weakening digestion further; dry desert heat skews more purely Pitta. Practical implication: in **humid heat**, lean harder into easily-digestible, fermented and probiotic items (pakhala, chaas, curd rice, light khichdi) and away from heavy/oily; in **dry heat**, hydration and cooling sharbats (sattu, aam panna, bael) dominate. **Evidence is qualitative/Ayurvedic, not quantified** — implement as a minor modifier on the cooling boost if the weather API exposes humidity, otherwise ignore. **DERIVE-if-available, else skip.**

### Source quality & gaps (Strand 1)
- **Strong & consistent:** the directional thermal logic (rain→fried/warm comfort; heat→cooling/light; cold→rich/warming) is corroborated across dozens of independent food-media sources, recipe authorities (Tarla Dalal, Veg Recipes of India, Hebbar's Kitchen), Wikipedia (Pakhala), and Ayurvedic *ritucharya* texts (Charaka Samhita summaries, Dabur, Art of Living). Regional hero mappings (Bengali khichuri-ilish, Odia pakhala, Konkan sol kadhi, Punjabi sarson-saag) are well sourced and uncontested.
- **Thin/contested:** **quantified day-level demand.** The most rigorous day-level India quantification is academic and rural — Stainier, Shah & Barreca (NBER w34047, 2025): a day above 110°F shifts ~5 kCal/person/day toward purchased food and away from home-grown sources. Seasonal cooling-demand quantification comes from Mother Dairy/NDDB's 30%+ summer growth (Business Standard, June 2026). Quick-commerce "2–3x summer demand" and "15–20% rider demand" figures are unnamed industry estimates (News Karnataka, Apr 29 2026) — treat as soft. Swiggy's "How India Swiggy'd 2025" quantifies the chai-samosa comfort pairing (3.42M samosas, 2.9M adrak chai) but provides **no rainy-day breakdown**. **Net: the strand is safe as a soft transient boost; it would be irresponsible to hard-code weather as a filter given the evidence base.**

---

## STRAND 2 (LIGHT) — Dish Pairing Guardrails (dry hero + liquid hero)

**Principle:** Codify the universal NEGATIVE guardrails now from culinary logic; LEARN the positive "delightful match" affinities from user behaviour in v2 (desk research on positive pairings is mediocre; real usage data is far better). Engine action = compatibility guardrails applied as penalties/exclusions **at the pairing step**, plus a standalone-dish flag.

### Codify-now NEGATIVE guardrails
1. **No two heavy/rich/creamy gravies together.** e.g., not dal makhani + butter paneer. Culinary balance principle: one rich + one light reads better than two rich; "fat is flavour" but two fats overwhelm. (Plating/balance sources: JWU, Culinary Pro, "heavy vs light foods.")
2. **No two dishes on the same base.** Avoid two tomato-onion gravies, two coconut gravies, or two of the same pulse/dal on one plate — kills contrast and variety.
3. **No two DRY heroes as "the pair."** The plate needs one moist/liquid element so the carb works (you need something to "mop up" with roti or moisten rice). A dry sabzi + dry sabzi + roti is incomplete.
4. **Keep within ONE region/cuisine coherence.** Don't pair Bengali shukto with Punjabi rajma; pair within the household's regional palette so the plate reads as one meal.
5. **Balance richness (one rich + one light).** The classic thali logic: one gravy-based + one dry sabzi, plus dal/kadhi/raita as the moistener. Cooling/light element offsets a richer one.
6. **Protein/veg balance nudges.** Prefer a pulse/protein liquid hero (dal, sambar, kadhi, rajma) with a vegetable dry hero, or vice versa, rather than two starchy or two protein-light items.

### Standalone "complete" dishes — flag, do NOT pair
These are complete plates on their own and should carry a **standalone flag** that suppresses the dry+liquid pairing logic:
- **biryani, khichdi/khichuri, pulao, pav bhaji, chole bhature, masala dosa, thali-type sets** (and close cousins: bisi bele bath, dal baati churma as a set, rajma chawal / kadhi chawal as one-plate combos).
- Note nuance: rajma and kadhi are *liquid heroes* that in practice are eaten as a near-complete one-plate meal with rice; flag them as "self-pairing to rice" rather than forcing a second hero.

### DERIVE vs LEARN vs ASK
- **Guardrails (1–6) + standalone flag = DERIVE/codify now** from culinary logic + dish metadata (richness tag, base tag, dry/liquid tag, region tag).
- **Positive affinities = LEARN in v2** from user accept/edit/repeat behaviour on the same scoring function.
- No ASK.

### Source quality & gaps (Strand 2)
- Negative guardrails rest on (a) universal culinary balance/contrast principles (reputable culinary-school sources) and (b) the well-documented thali structure (dal + one dry sabzi + one gravy + carb + raita). Both are solid for the "don't" rules.
- **Honest gap:** positive pairing affinities genuinely lack good desk-research support — confirming the decision to defer them to behavioural learning. Standalone-dish identification is uncontested.

---

## STRAND 3 (LIGHT) — Carb Default Rules (per region / dish)

**Principle:** The carb **floats** (not part of recommendation scoring), but each plate needs a sensible **editable default** carb. v1 carb set is fixed and small: **{ROTI, PARATHA, POORI, RICE}**. Millet/bajra/jowar roti rolls under "Roti" for now; **naan excluded** (not typical home food). Engine action = default-carb **derivation rule** (editable). **DERIVE from region + liquid-hero type.**

### Default-carb logic by liquid-hero type (strongest signal)
- **rajma → rice** (rajma chawal); also acceptable with roti.
- **sambar / rasam → rice** (South Indian rice-led meal).
- **kadhi → rice** (kadhi chawal); roti acceptable in some North-Indian homes → default rice, roti as edit.
- **chole → poori or rice** (chole-poori weekend/festive; chole-chawal everyday); bhature is the standalone form (flag, not a floating carb).
- **most North-Indian dals & sabzis → roti** (or roti+rice).
- **aloo sabzi (Punjabi weekend) → poori** (aloo-poori); **shrikhand → poori** (shrikhand-poori, Gujarati/Maharashtrian festive).

### Default-carb logic by region
| Region | Default carb (within {Roti, Paratha, Poori, Rice}) | Notes |
|---|---|---|
| Punjab / North (Delhi, UP, Haryana) | **Roti** (rice for rajma/kadhi/chole) | roti+rice both common; paratha for breakfast/weekend |
| South (TN, Karnataka, AP, Telangana, Kerala) | **Rice** (rice-dominant) | sambar/rasam/curd-rice all rice-led |
| West Bengal / Odisha / Coastal East | **Rice** (rice-dominant) | fish curry + rice, khichuri standalone |
| Gujarat | **Roti** (rotli) (+ rice) | rotli/bhakri staple; rice secondary; poori/aamras seasonal-festive |
| Rajasthan | **Roti** (+ rice) | bajra/wheat rotla under "Roti"; dal-baati is standalone |
| Maharashtra | **Roti** (bhakri/chapati) + rice | jowar/bajra bhakri under "Roti"; rice with varan/amti |
| Goa / Konkan coast | **Rice** | rice + fish curry / sol kadhi |
| Bihar / Jharkhand | **Roti** + rice | litti is standalone |

### Poori as a special-case default
Poori defaults only for **weekend/festive or specific pairings**: chole-poori, aloo-poori, shrikhand-poori, aamras-poori. It should NOT be the everyday default for any region.

### DERIVE vs LEARN vs ASK
- **DERIVE now** from (region of household/palette) + (liquid-hero type), with poori gated to festive/specific pairings. Always **editable** by the user. v2 can LEARN per-user carb preference (e.g., a low-carb household that always swaps rice→roti).

### Source quality & gaps (Strand 3)
- Region×carb mappings are well sourced (Gujarati dal-bhaat-rotli-shaak quartet; bhakri across Maharashtra/Karnataka/Rajasthan; South/East rice-dominance; rajma-chawal, kadhi-chawal, sambar/rasam-rice). Uncontested. The only judgement calls are the roti-vs-rice tie-breaks in North India (both common) — default to roti, rice as the obvious edit.

---

## SECTION A — MODES (user-toggled, replacing auto-services)

Deliberate v1 decision: **handle observance as user-toggled MODES/FILTERS, NOT automatic calendar/panchang/API services.** This avoids a panchang/calendar integration in v1.

- **FASTING MODE** (user toggles ON): swap to vrat/farali heroes — **sabudana, kuttu (buckwheat), singhara (water chestnut), rajgira (amaranth), samak/barnyard-millet rice, makhana, potato/sweet potato, sendha namak**; **exclude grains, regular rice/wheat, pulses, onion & garlic**. Spices narrow to cumin, black pepper, green chilli, ginger. (Engine: swap hero pool + hard-exclude grains/onion/garlic while mode active.)
- **FESTIVAL MODE** (user toggles ON): surface the festive plate via the festival→signature-dish map — **Onam → sadhya; Pongal → ven/sakkarai pongal; Diwali → festive sweets/snacks; Eid → sewai/biryani; Baisakhi → sarson-saag + makki roti; Durga Puja → bhog (khichuri + labra + payesh); Ganesh Chaturthi → modak; Makar Sankranti → til-jaggery/undhiyu.** (Engine: transient festive-plate boost.) Scale of festival demand is real and quantified nationally — Swiggy's "How India Swiggy'd 2025" reports **1.7 million kg of sweets, dry fruits and desserts ordered around Diwali**, **2.28 lakh modaks delivered for Ganesh Chaturthi**, and **2.2 lakh orders in just 60 minutes on Navratri Ashtami** — underscoring why the festive plate deserves a dedicated mode even without a calendar integration.
- **VEG / EGG FILTERS:** the veg-day behaviour becomes a **manual toggle**, not an auto veg-day calendar. (Engine: filter non-veg / egg per toggle state.)
- **WEATHER:** in scope NOW, DERIVED from weather API (Strand 1) — the one auto-service retained.
- **MOOD:** future mode, **out of scope now.**
- **Demotion of auto-inference:** auto-inferring observance (the old **D7 latent inference**) is therefore **demoted to a v2 nicety** — a prompt like "Shall we turn on Fasting Mode for you?" rather than a v1 dependency.

---

## SECTION B — Deferred / Parked Register

Each item: one-line "what it would need to connect/build later."

- **SNACK / TEA-TIME 4th meal slot** — deferred, low priority. *Needs:* a small hot/cold tea-time item pool; most is store-bought namkeen/toast so payoff is low until justified.
- **GUEST / SPECIAL-OCCASION mode** — later. *Needs:* a "scale-up + impress" plate logic and portion/guest-count input.
- **NEED-BASED MODES (recovery/convalescent + weaning/baby-food)** — later; this is the stated **secondary segment**. *Needs:* condition-appropriate dish sets + a clinical/nutrition reference and safety review.
- **FESTIVE-POSITIVE proactive recommendations** (beyond the toggle) — later. *Needs:* the panchang/calendar service deliberately omitted in v1, plus a regional festival calendar by community.
- **SUBSTITUTION / VARIANT GRAPH** (butter chicken → butter paneer → Jain no-onion-garlic → vegan soya) — NOT researched now, but the **DB schema must be DESIGNED to carry dish variants/swaps** so it can be filled later. *Flag as a DB-schema-thinking item.*
- **PER-DISH MACRO/NUTRITION DATASET** — a **hard dependency for Q15 Protein-Calculator / Into-Fitness modes**. *Needs:* a per-dish macro data source to be identified and the DB modified during codification.
- **ALLERGEN HIDDEN-DERIVATIVE TABLE** — safety-critical lookup to build/verify (e.g., **hing → wheat**). This, plus **Jain restrictions**, are **HARD FILTERS**. *Needs:* a verified ingredient→hidden-allergen mapping.
- **SEASONAL-PRODUCE / AVAILABILITY feed** — deferred. *Needs:* a regional produce calendar or produce API, gated behind a quick-commerce metro check.
- **REAL-TIME PRICING feed** — deferred. *Needs:* mandi / quick-commerce price APIs.
- **PANCHANG / CALENDAR auto-service** — deliberately NOT connected in v1 (replaced by the Modes above). *Needs:* a panchang API + observance inference if ever revived.
- **HEALTH CONDITIONS research — BP / diabetes / kidney / liver** — PARKED. Q11 still flows as a **secondary demotion** but has **no dish-implication research** behind it yet. *Needs:* condition→dish-implication research + clinical review.
- **PREMIUM-PROMOTION hook** (identify well-off households via **D1 income band**, surface premium items like parmesan/exotic products) — deferred but **design-for via a static premium-tier tag** on dishes/ingredients gated by D1; **no live pricing feed needed.**
- **COLD-START calibration (the 3×5 like-tap matrix)** — referenced but its exact definition is **pending the founder's own specification** before codification.
- **VARIABILITY, REPETITION & EXPLORATION — [DEFERRED → v2/v3].** v1 ships **only a trivial no-duplicate guard** across the 7 plates (the same hero/dish does not appear twice in one set). The full machinery is deliberately deferred because it requires **user history (v2)** and **cohort data (v3)** to calibrate — hard-coding it in cold-start would be guessing. Deferred components:
  - **(a) Role-aware recency decay** — `recency_penalty = f(days_since_shown, hero_role)`: *support recurs freely* (no penalty — you want rice/roti daily), *everyday dry/liquid heroes rotate* (mild penalty), *single/special heroes get spaced out* (strong penalty — no butter chicken twice in a week). Repetition is NOT uniformly bad; staples *should* recur.
  - **(b) Per-axis variety** — diversity enforced *within* the dry pool, *within* the liquid pool, and *across* cuisines/bases — not merely "7 different plates" (which could still be seven tomato-onion gravies).
  - **(c) Exploration policy** — deliberately surfacing a small number of lower-ranked / unseen dishes to generate the like/dislike training signal. **This is a *prerequisite* for v2 learning: without exploration there is no feedback on un-shown dishes, so the model can never learn what the user dislikes among things it never offered.** Exploration rate is a tunable parameter.
  - **(d) Comfort↔variety dial** — the strength of (b) and (c) tied to **D3 adventurousness** and **D5 variety-fatigue**: adventurous/young households get more roam, comfort-seeking households get more familiar repetition. v1 default lean = **familiar-leaning** (suits indulgence-first + a cold catalogue); the dial opens as D3/D5 and v2 learning mature.
  - *Needs:* logged per-element history (the `feedback_event` / `recommendation_event` substrate already designed in the schema) before any of (a)–(d) can be calibrated.

---

## Recommendations

1. **Build Strand 1 as a soft transient layer keyed to the regional palette first.** Before wiring the weather API, ensure every state palette carries tagged rainy-day / summer / winter hero sets (the region tables above). The weather signal is only as good as the regional hero mapping it resolves to. Threshold to revisit: if user edits frequently override the weather boost (>~30% override rate once telemetry exists), reduce boost magnitude.
2. **Codify the six negative pairing guardrails + standalone flag now; instrument every plate for v2 affinity learning.** Log accept/edit/swap events from day one so v2 has training data for positive affinities on the same scoring function.
3. **Ship the region×hero-type carb defaults as editable, with poori gated to festive/specific pairings.** Track edit rates per region to calibrate the North-India roti-vs-rice tie-break.
4. **Implement Fasting/Festival/Veg-Egg/Weather as the four live modes; keep Mood and observance-inference explicitly out of v1.** Add the "Shall we turn on Fasting Mode?" prompt only in v2.
5. **Treat the Deferred register as a schema-design checklist now, build-later.** Two items demand schema foresight even though they aren't built: the **variant/substitution graph** and the **per-dish macro dataset** (hard dependency for Q15 fitness modes). Design columns/relations for both now. Build the **allergen hidden-derivative table** and **Jain restrictions as hard filters** before any public launch — these are safety-critical.
6. **Get the founder's 3×5 cold-start like-tap matrix definition before codifying cold-start.** It is a known blocking dependency.

### Version roadmap (restate)
- **v1:** rule-based cold-start (this document).
- **v2:** per-user learning on the **same scoring function** (positive pairing affinities, carb preference, observance prompts, mood).
- **v3:** cross-user cohort clustering.
- (Never use the label "v1.5".)

## Caveats
- **Weather quantification is thin** (see Key Findings) — directionally strong, numerically weak; this is why weather is a soft boost, never a filter.
- **Humid-vs-dry heat distinction is Ayurvedic/qualitative** — implement only if the weather API exposes humidity, else skip.
- **Positive pairing affinities are deliberately un-researched** — they are a v2 learning target, not a v1 gap to fill by desk research.
- **Health-condition dish implications (Q11) are parked** — Q11 demotes secondarily but has no dish-level research behind it yet; do not over-promise health behaviour in v1.
- **Allergen/Jain hard filters and the hidden-derivative table are safety-critical and unbuilt** — must be completed and verified before launch.
- **Cold-start matrix is undefined** pending founder input.
- **Variability/repetition/exploration is deferred to v2/v3** — v1 has only a no-duplicate guard; the real machinery (role-aware recency, per-axis variety, exploration, the comfort↔variety dial) needs user/cohort data to calibrate, and exploration is itself a prerequisite for v2 learning.
- This document is research-only: **no codification, weights, schema, or scoring tables** are specified here by design.

## DERIVE-now vs LEARN-in-v2 vs MODE vs DEFERRED (consolidated)
- **DERIVE now:** weather transient boost (from API + Q4 + regional palette); the six negative pairing guardrails + standalone-dish flag; region×hero-type carb defaults (editable).
- **LEARN in v2:** positive pairing affinities; per-user carb preference; observance-inference prompts; mood.
- **Handled by MODE (v1):** Fasting, Festival, Veg/Egg filters, Weather (Mood = future).
- **DEFERRED/PARKED:** tea-time 4th slot; guest mode; need-based modes; festive-positive proactive; variant/substitution graph (schema-design now); per-dish macro dataset (Q15 dependency); allergen hidden-derivative table + Jain hard filters (safety-critical, pre-launch); seasonal-produce feed; real-time pricing; panchang auto-service; health-condition research; premium-promotion hook (static tag, design-for); cold-start 3×5 matrix (pending founder spec); **variability/repetition/exploration** (role-aware recency, per-axis variety, exploration policy, comfort↔variety dial — v1 ships only a no-duplicate guard; exploration is a prerequisite for v2 learning).


---

## Future / Deferred / RFC Register  *(this document)*
*Quick-reference index of this document's forward-looking items. Convention: `[ID] [TAG] Title — trigger/what-it-needs — STATUS`. Tags: [v2]/[v3]/[KB]/[SAFETY]/[DATA]/[DB]/[later]/[parked]. Status: OPEN / RFC-DRAFTED / DONE(vX.Y). When this file is edited, update the relevant line so the freeze lineage stays in-place. Detailed rationale for each item is in the sections above.*

| ID | Tag | Item | Trigger / needs | Status |
|---|---|---|---|---|
| RES-F1 | later | Snack / tea-time 4th meal slot | small tea-time pool | OPEN |
| RES-F2 | later | Guest / special-occasion mode | scale-up plate logic + guest count | OPEN |
| RES-F3 | later | Need-based modes (recovery + weaning/baby-food) | dish sets + clinical review | OPEN |
| RES-F4 | later | Festive-positive proactive recommendations | panchang/calendar + festival map | OPEN |
| RES-F5 | DB | Substitution / variant graph | schema designed; populate later | OPEN |
| RES-F6 | DATA | Per-dish macro/nutrition dataset | identify source + DB mod | OPEN |
| RES-F7 | SAFETY | Allergen hidden-derivative table + Jain hard filters | verified mapping | **OPEN — PRE-LAUNCH** |
| RES-F8 | later | Seasonal-produce / availability feed | produce calendar/API | OPEN |
| RES-F9 | later | Real-time pricing feed | mandi/quick-commerce API | OPEN |
| RES-F10 | later | Panchang / calendar auto-service | panchang API (replaced by modes in v1) | OPEN |
| RES-F11 | parked | Health conditions (BP/diabetes/kidney/liver) | clinical research | PARKED |
| RES-F12 | later | Premium-promotion hook | D1 income + static premium tag | OPEN |
| RES-F13 | — | Cold-start 3×5 calibration matrix | founder spec | **DONE (locked; folds into feedback model)** |
| RES-F14 | v2/v3 | Variability/repetition/exploration (recency, per-axis variety, exploration, comfort↔variety dial) | user/cohort data | OPEN |

