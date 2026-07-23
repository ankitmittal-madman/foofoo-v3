# Ghar RE v1.0 — Core Scoring Spine Specification  *(FROZEN)*

> **Status: FROZEN as RE v1.0.** This is the version-controlled core specification of the Ghar recommendation engine. The equations, feature vector, similarity metric, scoring composition, and v1->v2->v3 evolution are **frozen**. From here, gains come from the **knowledge layer** (regional priors, signature scores, comfort-food maps, ingredient aliases, nutrition data) and **parameter tuning**, NOT from editing the spine. **Any change to the core is handled as a versioned RFC (RE v1.1 / v2), never as an in-place edit.** Forward-looking items are gathered in the **Future / Deferred Work** appendix and marked `[FUTURE]`, `[v2]`, `[v3]`, `[KB]`, `[SAFETY]`, or `[DATA]`.

---

## RE Design Principles (read first)
These eight principles govern every current and future decision in the engine. A change that violates one of these is a red flag.

1. **Taste before optimization.** Indulgence/flavour is the default; health, cost, and efficiency are secondary lenses the user opts into — never the engine's default agenda.
2. **Never surprise a cold-start user.** A new user gets familiar, recognizable, regionally-true plates. Discovery is *earned* as the engine gains confidence, not pushed on day one.
3. **Filters remove, scores rank.** Hard filters (diet, allergen, Jain, mode, weaning) decide *who is eligible*; scores only *order* the eligible. The two never blur.
4. **Behaviour overrides declarations.** Every stated input (Q15 objective, home state, income) is a *prior* whose authority decays as revealed behaviour accumulates. The user's taps are the truth.
5. **Diversity is introduced gradually.** Variety and exploration ramp up with data and confidence; they are not forced on a cold catalogue.
6. **Explainability over black-box in v1.** v1 is a transparent rule engine — every recommendation is traceable to weights and matches. ML *enhances* this later; it does not replace the explainable core.
7. **Rule engine first, ML enhances later.** v1 is hand-set rules. v2/v3 learn *parameters of the same equation* — they never restructure it.
8. **Every new feature plugs into the existing score, never replaces it.** New signals enter as new rule modules (`+ W_k·conf_k·m_k`) or as nudges on existing parameters. The master equation's *form* is invariant across versions.

## Score-magnitude convention (important for implementers)
**Scores are ordinal ranking values, not probabilities.** Only the *relative order* of dishes/plates within one candidate set matters. `plate_score = 9` vs `8` means "ranked higher", not "90% vs 80%" and not any absolute quantity. Do not threshold on absolute score; do not interpret as likelihood. Magnitudes are arbitrary and exist only to sort.

## The master score (the whole spine in one line)
```
score(x | theta) =  BASE(x, theta)                  [S2B - sum of rule modules: palette/slot/season/signature/age/household + weather]
                  x GAIN_Q15(x, theta)              [S3  - cooking-objective gain; kappa-decays to behaviour in v2]
                  + w_pref   * S_pref(x ; user)     [S1.4 - personalization; 0 in v1, learned v2]
                  + w_cohort * S_cohort(x ; cohort) [S1.4 - cohort; 0 in v1/v2, learned v3]
                  - PENALTY(x | chosen set)         [S4  - v1: trivial no-duplicate only; variety/recency deferred]
```
Pipeline: `onboarding+context -> filters (S2A) -> score each eligible dish -> form plates + pairing (S4) -> assemble-7 -> attach support -> 7 ranked plates`.

## Contents
- **Section 1** - Feature Space & Meal-Class Distance Metric
- **Section 2** - Hard Filters + the BASE Score (rule modules + weight tables)
- **Section 3** - The Q15 Cooking-Objective Gain (+ behavioural override)
- **Section 4** - Pairing Guardrails + Assemble-7 (the plate builder)
- **Appendix** - Future / Deferred Work (consolidated forward-notes)


---

## Section 1 (v1.1) — Feature Space & Meal-Class Distance Metric  *(revised)*

*Supersedes the first §1. This revision folds in five improvements: (1) the feature space is organized under **five semantic groups** (Sensory / Preparation / Nutrition / Structure / Identity); (2) a new **ingredient-overlap block** with rarity (IDF) weighting; (3) **rebalanced block weights** — taste up, cuisine down, texture up; (4) **calories moved out of "palate" into Nutrition**; (5) **graded diet distance**. Still math-not-code, still grounded in the real catalogue vocabulary, still linear-in-parameters so v2/v3 relearn the same quantities. Deferred refinements are logged in §7.*

---

## 0. The master score (unchanged in form)

```
score(x | θ) =  BASE(x, θ)  ×  GAIN_Q15(x, θ)
              + w_pref   · S_pref(x ; user)        [0 in v1, learned v2]
              + w_cohort · S_cohort(x ; cohort)    [0 in v1/v2, learned v3]
              − PENALTY(x | chosen set)            [v1: trivial no-duplicate only]
```
Section 1 defines `φ(x)` (the dish-intrinsic vector), the **meal-class distance** on it, and the personalization hook. `BASE`, `GAIN_Q15`, filters, pairing = later sections.

---

## 1. Feature space — organized as five semantic groups

Every feature lives in exactly one group. Future modules (Q15 gain, weather, personalization, diversity, health) operate on **groups**, never on raw dimensions — so the architecture stays clean as the engine grows.

### GROUP A — SENSORY  *(how it tastes/feels; the dominant family for a taste-first app)*
| Sub-block | Field | Encoding | Dim |
|---|---|---|---|
| taste-intensity | spice_level, sweetness | scalars to [0,1]: `(spice-1)/3`, `sweet/3` | 2 |
| `TA` taste | primary_taste | multi-hot | 7 |
| `TX` texture | texture | multi-hot | 15 |
| `RI` richness | richness | multi-hot | 7 |
| `MF` mouthfeel | mouthfeel | multi-hot | 7 |
| `AR` aroma | aroma_profile | multi-hot | 11 |
| `TH` thermal | serving_temp | scalar: frozen0 / chilled.2 / room.5 / warm.75 / hot1 | 1 |

### GROUP B — PREPARATION  *(how it's made / effort to make)*
| Sub-block | Field | Encoding | Dim |
|---|---|---|---|
| `CM` method | cooking_method | multi-hot | 16 |
| effort | total_minutes, difficulty | `clip(min/T_CAP,0,1)` (T_CAP=60), {easy0/med.5/hard1} | 2 |
| `FM` fermentation | fermentation | scalar none0/light.33/med.66/heavy1 | 1 |

### GROUP C — NUTRITION  *(satiety / energy / protein)*
| Sub-block | Field | Encoding | Dim |
|---|---|---|---|
| heaviness | heaviness | `(heavy-1)/2` | 1 |
| calories | calories | `clip((cal-30)/770,0,1)` | 1 |
| protein-proxy | diet + category | proxy now to **real grams in v2** (`dish_macro`) | 1 |

### GROUP D — STRUCTURE  *(role on the plate)*
| Sub-block | Field | Encoding | Dim |
|---|---|---|---|
| hero_role | hero_role | one-hot {liquid,dry,single,standalone,support,snack,accompaniment} | 7 |
| course | course | multi-hot {starter,main,support,accompaniment,dessert,beverage} | 6 |
| `DC` category | dish_category | multi-hot | ~22 |
| diet | diet | {veg,egg,non_veg} (used graded - §3.5) | - |

### GROUP E — IDENTITY  *(where it's from)*
| Sub-block | Field | Encoding |
|---|---|---|
| cuisine | cuisine + parent + group + region | hierarchical (§3.4) |
| `WE` weather-affinity | weather_affinity | multi-hot {all,cold,hot,rainy} - the **cultural** comfort tag |

### NEW BLOCK — INGREDIENT (`ING`)  *(semantic ingredient overlap)*
Each dish to an **IDF-weighted ingredient vector**. Rare/distinctive ingredients dominate; ubiquitous ones fade.
```
IDF(i) = ln( (N+1) / (df_i + 1) ) + 1          N = 810,  df_i = # dishes containing ingredient i
v(x)_i = IDF(i)  if ingredient i is in x, else 0
```
*Validated on the catalogue:* salt IDF~1.1 (ignored), onion/garlic/turmeric ~1.8-2.2 (low), but spinach~4.9, paneer~4.1, cream~4.0, mutton~3.6 (high). So **Palak Paneer drifts to Saag / Methi Malai / Hariyali via shared rare ingredients (spinach, cream)** - the generalization we want - while shared salt/onion adds nothing.

---

## 2. Functional groups for Q15 (views over the above)
Q15 re-weights these named index sets (defined now so the gain stays aligned):
- **`G_indulgence`** = RI in {buttery,creamy,ghee_rich,coconut_rich,oily} + CM in {deep_fried,shallow_fried} + heaviness + calories
- **`G_light`** = RI in {light,plain} + CM in {steamed,boiled,grilled,raw} + low calories
- **`G_protein`** = diet in {non_veg,egg} + DC in {dal_lentil,kebab,egg_dish} + protein-proxy *(to real grams v2)*
- **`G_comfort`** = thermal + WE + RI:ghee_rich + CM:tempered  *(the weather-interaction view)*

---

## 3. Meal-class distance `d(a,b)`
Soft neighborhoods, not hard buckets. Block-weighted composite (so 89 sparse tag-dims can't swamp the few scalars), `d` in [0,1]:
```
d(a,b) = sum_g  beta_g * delta_g(a,b)
```

### 3.1-3.3 Block distances
- **Scalar sub-blocks** (taste-intensity, effort, thermal, fermentation, heaviness, calories): `delta = mean(|diff|)` over the sub-block's normalized scalars.
- **Multi-hot sub-blocks** (`TA,TX,RI,MF,AR,CM,DC,WE`): **Jaccard distance** `1 - |A∩B|/|A∪B|` (=0 if both empty).
- **Ingredient `ING`**: `delta_ING = 1 - cosine( v(a), v(b) )` - IDF-weighted cosine; robust to differing ingredient counts.

### 3.4 Cuisine (Identity) - hierarchical, now **down-weighted**
`0` same cuisine · `0.25` same parent (chettinad-tamil) · `0.5` same group · `0.75` same broad region · `1.0` else. *(Its lowered beta below is the key change - taste, not origin, should decide what "eats alike". Regional logic is preserved in `BASE` palette-match and pairing coherence, not here.)*

### 3.5 Diet - **graded** (replaces binary)
```
        veg   egg  nonveg
veg     0.0   0.3   1.0
egg     0.3   0.0   0.7
nonveg  1.0   0.7   0.0
```
Structure delta = `mean( 1[role!=], 1[primary course!=], diet_grade )`.

### 3.6 Block weights `beta` - v1.1 defaults (sum = 1.00)
Taste-first rebalance: **Sensory family 0.46, cuisine down to 0.13, texture up to 0.08, ingredient 0.11.**

| Group | Block | beta |   | Group | Block | beta |
|---|---|---|---|---|---|---|
| Sensory | taste-intensity | 0.10 |   | Identity | cuisine | **0.13** |
| Sensory | `TX` texture | **0.08** |   | Identity | `WE` weather | 0.03 |
| Sensory | `RI` richness | 0.08 |   | **Ingredient** | `ING` | **0.11** |
| Sensory | `TA` taste | 0.07 |   | Nutrition | heaviness | 0.05 |
| Sensory | `MF` mouthfeel | 0.06 |   | Nutrition | calories | 0.05 |
| Sensory | `AR` aroma | 0.04 |   | Preparation | `CM` method | 0.07 |
| Sensory | `TH` thermal | 0.03 |   | Preparation | effort | 0.02 |
| Structure | role+course+diet | 0.04 |   | Preparation | `FM` ferment | 0.01 |
| Structure | `DC` category | 0.03 |   | | | |

`Sensory = 0.46 · Ingredient = 0.11 · Identity = 0.16 · Nutrition = 0.10 · Preparation = 0.10 · Structure = 0.07`  -> **sum = 1.00**

### 3.7 Similarity kernel
`sim(a,b) = exp(-d(a,b)/tau)`, `tau = 0.30`.

---

## 4. Personalization hook (inert v1 -> plugs in v2/v3)
Operates over the **Sensory + Ingredient** tag dims (accumulator `a_user`) and the **Sensory + Nutrition** scalars (preferred levels `mu_user`):
```
S_pref(x;user) = <a_user, taghot(x)>/Z - sum_s lambda_s*|scalar_s(x) - mu_user,s|
v1:  a_user = 0,  mu_user undefined  =>  S_pref = 0
v2 update (sketch; full rule = v2 spec):
  liked x:    a_user += eta*taghot(x);  mu_user <- running-mean(scalar(x))
  disliked x: a_user -= eta*taghot(x)
  calibration shown-not-tapped survivor: a_user -= eta_soft*taghot(x)   (eta_soft<eta)
```
Cohort term `S_cohort` = identical form per cluster, `w_cohort=0` until v3. **Form never changes across versions - only the learned vectors leave zero.**

---

## 5. Hard filters vs scoring (boundary)
Filters (diet/allergen/Jain/mode/weaning) remove dishes *before* scoring - they touch raw attributes, not `φ`. The graded diet distance (§3.5) is for *similarity*, not filtering; a vegetarian household still has non-veg **hard-filtered out** regardless of distance.

---

## 6. Open parameters (Section 1) - named, v1 defaults
| Param | Meaning | v1 default | Learn |
|---|---|---|---|
| `T_CAP` | effort time saturation | 60 min | tune (context via D2) |
| `beta_*` (16 blocks) | distance composition | §3.6 (sum=1) | tune / v2 |
| diet-grade matrix | §3.5 | as shown | tune |
| `IDF(i)` | ingredient rarity weight | from N=810 catalogue | recompute on catalogue change |
| `tau` | kernel bandwidth | 0.30 | tune |
| `w_pref / w_cohort` | personalization / cohort | 1.0 / 0.0 | v2 / v3 |
| `eta, eta_soft, lambda_s` | learning rates | - | v2 |

---

## 7. Deferred refinements (logged, not built - v2+)
- **Within-block tag similarity** (crispy-crunchy closer than crispy-smooth): needs hand-authored tag-distance or learned co-occurrence -> **v2**. *(Note: cross-block confusions like crispy-vs-smoky are already prevented by the block structure.)*
- **Learned ingredient embeddings** replacing IDF overlap -> **v2** (IDF is the solid v1 stand-in).
- **Real protein grams** replacing the protein-proxy in `G_protein` / Nutrition -> blocked on `dish_macro` dataset -> **v2**.
- **Weather thermal inference** (derive hot/cold-day fit from thermal+spice+heaviness instead of tags) -> **v2 efficiency**; v1 keeps the explicit `WE` tag because the *cultural* rainy-day comfort hero (kanda bhaji, khichuri) is **not** derivable from sensory features and our research flagged it as the most important weather behaviour.
- **Ingredient tokenization gaps**: a few category tokens (e.g. coconut/fish appear only as `grated_coconut`, `fish_fillet`) - the `ING` block must map to lexicon tokens; trivial alias pass (same 4-alias fix already noted for the diet join).

---

### Checkpoint
§1 is now taste-first, ingredient-aware, and cleanly grouped. Next: **Section 2 - hard filters (boolean predicates) + the `BASE` score and its weight tables** (state x slot x season palette priors, weather transient boost, signature boosts). Review the §3.6 beta rebalance and the new `ING` block if you want; otherwise I proceed to §2.

---

## Section 2 — Hard Filters + the BASE Score & Weight Tables

*Builds on §1 (v1.1). Two parts: (A) the **hard filters** — strict boolean predicates that remove dishes from the candidate set BEFORE any scoring (safety + diet + mode + the new calorie filter); (B) the **BASE score** — the rule-weighted match between a dish and the household's derived profile + today's context, with concrete v1 weight defaults and the region x slot x season prior-table SHAPE. All constants are named parameters with v1 defaults. Q15 gain (S3) multiplies BASE; pairing + assemble-7 + the discovery dial (S4) come after.*

---

## PART A — HARD FILTERS  (applied first; a dish survives only if ALL predicates are true)

Filters operate on **raw attributes**, never on `φ`/distance. They are the cheap first pass that shrinks 810 to the eligible pool; scoring runs only on survivors. Order is irrelevant (all must hold), but safety filters are listed first.

Let `H` = household profile, `x` = dish, `ctx` = today's context (slot, modes on/off, calorie target).

### A1. Diet filter (Q5/Q6) — SAFETY-ADJACENT
```
pass_diet(x,H) =
   if H.diet == 'veg'         : x.diet == 'veg'
   if H.diet == 'eggetarian'  : x.diet in {'veg','egg'}
   if H.diet == 'non_veg'     : TRUE, minus specific meat exclusions in Q6
                                (e.g. no_beef / no_pork / no_red_meat -> exclude those ingredient classes)
```

### A2. Jain filter (Q8) — HARD
```
pass_jain(x,H) = (not H.is_jain) OR (x.jain_compatible == 'Y')
```
*(jain_compatible already derived from ingredient flags: excludes onion, garlic, root vegetables.)*

### A3. Allergen filter (Q9/Q10) — SAFETY-CRITICAL
```
pass_allergen(x,H) = ( x.allergens INTERSECT H.allergens ) == empty
```
> **CAVEAT (carried):** this is the BASIC pass on explicit ingredient flags only. The hidden-derivative layer (e.g. hing -> wheat/gluten) is the deferred `allergen_hidden_derivative` table and MUST be folded in before public launch. Until then allergen filtering is not safe-complete.

### A4. Weaning filter (D5 age) — the ONE age HARD filter
Applies only to the plate intended for a weaning member (6mo-2yr) present in H:
```
pass_weaning(x) = (spice_level <= 1) AND (texture has soft/smooth/mashable) AND (no whole nuts/seeds/hard)
```

### A5. Mode filters (user-toggled, ctx)
```
FASTING on : pass_fast(x) = farali_compatible(x)
             = excludes grains, regular rice/wheat, pulses, onion, garlic;
               allows {sabudana, kuttu, singhara, rajgira, samak, makhana, potato, sendha namak}
             (needs a farali flag derived from ingredients — same join machinery)
VEG/EGG toggle : same predicate as A1 but session-scoped (manual), overrides standing diet upward in restriction only
```

### A6. Calorie filter (NEW — user opt-in, ctx)  *(your Point 4)*
Off by default. When the user sets a target and enables it:
```
per-dish view ("show calories")     : display only, no filtering
per-meal target  T_meal             : pass_cal(plate) = sum(calories of plate components) <= T_meal * (1 + epsilon)
per-day target   T_day              : allocate T_day across slots -> per-slot allowance -> same predicate
```
- Operates at **plate** level (dry + liquid/single + support), not single-dish, since the meal is the unit.
- v1 uses the existing `calories` column (present, 30-800). **Macro-accurate targeting (protein/carbs/fat) waits for the deferred `dish_macro` dataset (v2).**
- `epsilon` (tolerance) default 0.10.

> Note the boundary: A1-A5 are correctness/observance filters (always on per profile/mode); A6 is an optional user lens. Veg-day (Q7) is A1 applied for that day, with the meat->veg **substitution** handled at assemble-time (S4), not a blanked slot.

---

## PART B — THE BASE SCORE

For each surviving dish, `BASE(x | H, ctx)` measures fit to the household's derived profile and today's context. It is a weighted sum of **match features** (each normalized; weather is signed). This is distinct from `φ` (which is dish-intrinsic, for similarity); BASE is dish x user/context.

```
BASE(x | H, ctx) =  W_PALETTE  · m_palette(x,H)
                  + W_SLOT     · m_slot(x, ctx.slot)
                  + W_SEASON   · m_season(x, ctx.season)
                  + W_SIG      · sig(x)
                  + W_AGE      · m_age(x,H)
                  + W_HOUSE    · m_household(x,H)
                  + W_WEATHER  · m_weather(x, ctx.weather)        [TRANSIENT, signed]
                  + PRIOR[zone][slot](x)                          [authored prior boosts]
```

> **BASE is a sum of RULE MODULES (architectural contract).** Read the formula as `BASE = Σ_k W_k · conf_k · m_k(x | H, ctx)`. Each `m_k` is a **self-contained module** with the fixed signature `(dish, profile, context) → value in [0,1]` (weather signed [-1,1]). **New rules (festival, pantry, budget, freshness, leftovers, cook-availability, user-dislikes…) are added by registering a new module + its weight — never by editing existing modules or the equation.** This keeps BASE maintainable as it grows.
>
> **Confidence hook (`conf_k`).** Each module also returns a **confidence** in [0,1]; its effective weight is `W_k · conf_k`. This lets a low-trust signal (e.g. home-state palette for someone 20 years away) be down-weighted vs a high-trust one (user-selected mode, live weather). **v1: all `conf_k = 1.0`** (no basis to discriminate yet); confidence calibration is **[FUTURE → v2]**, data-driven. The hook is present now so it slots in without changing the equation.

### B1. `m_palette` — regional fit, D4-blended  *(the anchor term)*
```
cuis(x, S) = 1.00 if x.state_origin == S
           = 0.70 if same parent_cuisine
           = 0.40 if same cuisine_group / broad zone
           = 0.15 if adjacent zone
           = 0.00 otherwise
m_palette(x,H) = blend · cuis(x, H.home_state)  +  (1 - blend) · cuis(x, H.local_palette)
```
- `blend` = the D4 home<->local weight (0..1), from the derivation layer; elders/short-tenure raise `blend` (more home), long-tenure lowers it.
- **scope_tier gate:** `experimental` dishes get `m_palette · ρ_disc`, where `ρ_disc` is the discovery multiplier (near 0 in early v1 -> experimental stays hidden until the discovery dial opens, S4). `indianised_daily` is treated as `indian_core` for palette (full weight).

### B2. `m_slot` — meal-slot appropriateness
```
m_slot(x, slot) = 1 if slot in x.meal_type else 0      (meal_type multi-valued: breakfast/lunch/dinner/snacks)
```
A dish not tagged for the slot scores 0 here (heavy demote) but is not hard-excluded — allows the rare cross-slot dish.

### B3. `m_season` — standing seasonal thermal fit (macro, derived from month+location)
```
season in {summer, monsoon, winter, transitional}     (derived from ctx.date + Q4 location)
m_season(x, season):  summer  -> +1 hot_weather/cooling tags, -1 heavy/fried, 0 all_weather
                      winter  -> +1 cold_weather/warming,    -1 cooling
                      monsoon -> +1 rainy/comfort,           0 else
                      mapped to [0,1] (or signed small)
```
Reuses the `WE` weather_affinity tag (no separate season tag needed). This is the **standing** seasonal baseline; B7 weather is the **acute same-day delta** on top.

### B4. `sig` — signature / iconic boost  *(graded 0–1)*
```
sig(x) in [0,1] — a GRADED iconicity score, not boolean (smoother ranking):
   1.00  defining/iconic (e.g. Butter Chicken, Hyderabadi Biryani, Masala Dosa)
   0.90  flagship-classic (e.g. Dal Makhani)
   0.60  well-known standard (e.g. Rajma)
   0.20  everyday/ordinary (e.g. plain dal, simple sabzi)
```
> v1 needs a graded **signature score** on dishes (small curated authoring set). Proxy until authored: `tier`/`is_user_facing` mapped to the band above. Authored in the parameter pass (Step 5 / Knowledge Base).

### B5. `m_age` — age-band palate prior (from Q12 / D5)
Soft adjustments (not filters): kids present -> demote spice_level>=3 on shared heroes; elderly present -> boost soft-texture/light, demote heavy+hard-texture. Expressed as `m_age in [0,1]` fit to the most-restrictive shared floor.

### B6. `m_household` — household constraint soft-fit (D5)
Soft-fits the household structure: single -> repetition-tolerant, one-pot boost; couple+kids -> mild/familiar boost; joint family -> batch-friendly boost. `m_household in [0,1]`.

### B7. `m_weather` — TRANSIENT same-day boost/demote  *(Strand 1; signed, the critical weather term)*
Derived from the weather API on Q4 location. **Never a filter; resolves to the household's OWN regional comfort hero** (weather x region interaction):
```
rain today     : +  dishes that are (weather_affinity=rainy OR fried/comfort) AND in H.regional_comfort_set
                 -  raw/salad ; (coastal, peak monsoon) seafood
heatwave today : +  cooling/curd/light/hydrating ; - fried/rich/very-spicy/heavy
cold snap today: +  warming/ghee-rich/calorie-dense/millet/jaggery ; relax richness penalty
m_weather in [-1, +1]
```
The regional resolution uses `PRIOR[zone].comfort_heroes` (e.g. Maharashtra rain -> kanda bhaji; Bengal -> khichuri; TN -> rasam) — NOT a generic pan-India pakora.

### B8. `PRIOR[zone][slot]` — the authored prior-boost table  *(shape here; full population = Step 5)*
A compact, hand-authorable table keyed by **broad zone** x **slot**, returning small boosts on dish attributes (category / hero_role / specific cuisines / comfort_heroes). NOT per-dish weights — boosts on attributes the dishes already carry.

```
zones  = {North, South, East, West, Central, Northeast}        (from cuisine_group)
slots  = {breakfast, lunch, dinner}                            (snacks deferred)
PRIOR[zone][slot] = { (attribute_match -> boost), ... , comfort_heroes: [...] }
```
**Seed examples (illustrative; full set authored in the parameter pass):**
```
PRIOR[South][breakfast] = { dish_category:dosa_idli +0.5, cuisine~{tamil,kannada,telugu,kerala} +0.3,
                            serving: rice-led; comfort_heroes:[rasam (rain), neer_mor (heat)] }
PRIOR[North][lunch]     = { structure: dal + dry_sabzi + roti +0.4, hero_role:liquid(dal) +0.2,
                            comfort_heroes:[pakora (rain), sarson_saag (winter)] }
PRIOR[West][dinner]     = { Gujarat: rotli+shaak+dal +0.3 ; Maharashtra: bhakri+pithla / varan-bhaat +0.3,
                            comfort_heroes:[kanda_bhaji (rain), sol_kadhi (heat)] }
```

### B9. Weight defaults (v1) — named parameters
| Param | Term | v1 default | Rationale |
|---|---|---|---|
| `W_PALETTE` | regional fit | **1.00** | anchor — cold-start leans on regional/demographic prior |
| `W_SLOT` | slot fit | 0.60 | strong (don't serve dinner-only at breakfast) |
| `W_WEATHER` | transient weather | 0.40 | strong nudge, below palette ("critical" but not a filter) |
| `W_SIG` | signature boost | 0.30 | iconic dishes surface |
| `W_AGE` | age prior | 0.35 | mildness/texture floors |
| `W_HOUSE` | household fit | 0.35 | structure-appropriate |
| `W_SEASON` | standing season | 0.25 | macro baseline under acute weather |
| `ρ_disc` | discovery mult (experimental) | ~0.05 (floor) | familiarity-first; ramps in v2 (S4) |
| `epsilon` | calorie tolerance | 0.10 | A6 |

> Magnitudes are relative (BASE is a ranking score, not a probability). Palette anchored at 1.0; everything scaled against it. These are starting numbers to tune, not learned — v2 learns the per-user `S_pref` term (S1 §4) on top, never these rule weights directly (those stay the shared backbone).

---

## C. What BASE feeds
`score = BASE x GAIN_Q15 + w_pref·S_pref + ... - PENALTY`. Next:
- **S3 — Q15 GAIN:** the four cooking-objective profiles (Awesome Taste / Healthy Living / Into Fitness / Protein) as multiplier vectors over the §2 functional groups (G_indulgence, G_light, G_protein, G_comfort).
- **S4 — Pairing + Assemble-7:** dry+liquid pairing guardrails (predicates), the standalone/single handling, support attach, the **discovery dial `ρ_disc` ramp** (familiarity-first), and the trivial no-duplicate guard.

---

## D. Open items surfaced by Section 2
- **Signature flag** (B4) — small curated authoring task (Step 5); proxied by tier meanwhile.
- **Farali flag** (A5) — derive vrat-compatibility from ingredients (same join); needed when Fasting mode is built.
- **`local_palette` per city** (B1) — the D4 city palette targets (8 metros) feed `blend`; lives in the derivation layer.
- **Full PRIOR population** (B8) — the region x slot (x season) cells + comfort_hero sets — is the dedicated **parameter pass (Step 5)**, authored from the regional research.
- **Calorie filter** uses existing calories now; **macro targeting deferred** to `dish_macro` (v2).

### Checkpoint
§2 locks the filters (incl. the calorie filter) and the BASE score shape + weights + prior-table structure. Full prior-cell population is deliberately the later parameter pass. Next section S3 = Q15 gain.

---

## Section 3 — The Q15 Cooking-Objective Gain

*Builds on §1 (feature groups) + §2 (BASE). Q15 is the **master GAIN dial** — the cooking objective the user picks at onboarding. It RE-WEIGHTS the score by amplifying/damping whole feature groups; it is NEVER a filter (it cannot remove a dish, only move it up or down the ranking). Short section: the group-score functions, the gain table, the formula, and how it composes with BASE, weather, and the opt-in calorie filter.*

---

## 0. Where the gain sits
```
score(x|θ) = BASE(x,θ)  ×  GAIN_Q15(x | objective)  + w_pref·S_pref + ... - PENALTY
```
GAIN multiplies the already-computed BASE. Because it is multiplicative and bounded (~[0.7, 1.3]), it re-ranks without ever zeroing a dish — a rich dish is still *available* to a health-focused user, just ranked lower. Default on skip = **Awesome Taste**.

The four objectives (Q15):
`Awesome Taste` (default) · `Healthy Living` · `Into Fitness` · `Protein Calculator`.

---

## 1. Group-score functions  `gs_g(x)` in [0,1]
How strongly a dish expresses each functional group (groups defined in §1 §2). Each is an average of its member-signals, normalized to [0,1].

```
gs_indulgence(x) = mean(
      1[richness in {buttery,creamy,ghee_rich,coconut_rich,oily}],
      1[cooking_method in {deep_fried,shallow_fried,dum_cooked}],
      heaviness_n,
      cal_n )

gs_light(x) = mean(
      1[richness in {light,plain}],
      1[cooking_method in {steamed,boiled,grilled,raw,tempered}],
      (1 - cal_n),
      (1 - heaviness_n) )

gs_protein(x) = mean(
      1[diet in {non_veg,egg}],
      1[dish_category in {dal_lentil,kebab,egg_dish}],
      protein_proxy_n )          # proxy now -> REAL grams (dish_macro) in v2
```
> `protein_proxy_n` is a coarse [0,1] proxy from diet+category until `dish_macro` lands. This is exactly the "Paneer Butter Masala vs Moong Dal" risk the external review flagged — acknowledged; real grams replace the proxy in v2. (`G_comfort` is used by the weather term in §2, not by Q15.)

---

## 2. The gain table  `gamma[objective][group]`  (v1 defaults)
Coefficients are gentle (gain, not filter). Positive = amplify, negative = damp.

| Objective | G_indulgence | G_light | G_protein |
|---|---|---|---|
| **Awesome Taste** (default) | **+0.30** | 0.00 | 0.00 |
| **Healthy Living** | -0.20 | +0.30 | 0.00 |
| **Into Fitness** | -0.15 | +0.20 | +0.30 |
| **Protein Calculator** | -0.05 | +0.05 | +0.50 |

Reading it: Awesome Taste leans into flavour/richness (pure taste-first — fits the product's default identity). Healthy Living softly favours light, softly damps indulgence. Into Fitness favours protein + light, damps indulgence. Protein Calculator strongly favours protein (the one most dependent on real macros).

---

## 3. The gain formula
```
GAIN_Q15(x | obj) = 1 + Σ_g  gamma[obj][g] · gs_g(x)
```
With `gs_g in [0,1]` and the coefficients above, GAIN ranges roughly **[0.75, 1.30]**. Worked feel:
- Butter Chicken (`gs_indulgence~0.9`): Awesome Taste -> `1+0.30·0.9 = 1.27`; Healthy Living -> `1-0.20·0.9 = 0.82`. Same dish, ranked high for one objective, low for the other — never removed.
- Moong Dal (`gs_light~0.8, gs_protein~0.6`): Healthy Living -> `1+0.30·0.8 = 1.24`; Protein Calc -> `1+0.50·0.6 = 1.30`.

---

## 4. Composition with the rest of the spine
- **With BASE (multiplicative):** `score = BASE × GAIN`. Regional/context fit is decided first; the objective then tilts the ranking within what already fits. A health-focused South-Indian household still gets South-Indian food — just the lighter end of it.
- **With WEATHER (§2 B7) — a real interaction:** a cold-snap relaxes the richness penalty (boosts warming/rich) while Healthy Living damps indulgence. They compose multiplicatively, so a rich winter dish for a health user nets ~neutral — a mild cold-day allowance, not full indulgence. Sensible; no special-casing needed.
- **With the CALORIE FILTER (§2 A6) — soft vs hard:** Q15 is the always-on *soft* lean; the calorie filter is the *opt-in hard* cap. A Healthy-Living user gets lighter rankings automatically; if they additionally switch on a calorie target, over-target plates are removed outright. They stack cleanly (gain re-ranks survivors; filter sets who survives).

---

## 5. The stated objective is a PRIOR — behaviour overrides it (the aspiration problem)

Q15 is **self-reported, and may be aspirational** — a user picks "Healthy Living" then taps butter chicken all week. The engine must treat the stated objective as a *starting prior whose authority decays as revealed-preference evidence accumulates*. Behaviour is truth; the declaration is a claim.

**Mechanism — a confidence-decay multiplier on the gain, handing off to `S_pref`:**
```
gamma_effective[obj][g] = gamma_stated[obj][g] · kappa(confidence_user)
kappa: 1.0  (cold-start, no behavioural data — the stated objective is all we have)
   ->  kappa_floor ~0.3  as feedback confidence rises
```
As `kappa` falls, the Q15 lean weakens; simultaneously the learned personalization term `S_pref` (§1 §4) rises from zero to fill the gap. So authority transfers smoothly from *"what you said you want"* to *"what you keep choosing"*:
- stated Healthy-Living + actually eats rich -> `S_pref` accumulates rich preference **and** the Healthy-Living damp weakens -> engine stops fighting the user.
- stated objective matches behaviour -> `S_pref` simply reinforces it; no conflict.

This is the **same invariant** — still `score = BASE × GAIN + w_pref·S_pref`. Nothing restructures; `GAIN` becomes confidence-scaled and `S_pref` (already present, inert at zero) takes over. It mirrors the identical "stated/prior first, behaviour overrides" pattern used for income (D1) and familiarity->discovery (S4).

**v1 vs v2 (honest line):**
- **v1:** `kappa = 1.0` always — stated Q15 runs at full strength, because there is no behavioural data yet to override it with.
- **v2:** `kappa` decays on the confidence schedule and `S_pref` activates — this is where the override actually happens. The decay curve (how fast `kappa` falls) is calibrated on real history, like the rest of the v2 learning.

The v1 build only has to keep `gamma` **scalable** (not hard-baked) and `S_pref` **present at `w_pref`** (both already true) — so v2 slots in with no rework.

## 6. Defaults & other v2 notes
- **Skip default:** Awesome Taste (indulgence gain) — reinforces taste-first.
- **v2 also:** the `gamma` cells themselves can become per-user learned (beyond the global `kappa` decay); and `gs_protein` swaps its proxy for real `dish_macro` grams. Form unchanged.

---

## 7. Open parameters (Section 3)
| Param | Meaning | v1 default | Learn |
|---|---|---|---|
| `gamma[obj][g]` (12 cells) | objective gain table | §2 above | tune / v2 per-user |
| `kappa(confidence)` | stated-objective decay | 1.0 (v1) | v2 (decay curve) |
| `kappa_floor` | min objective authority | ~0.3 | v2 |
| `protein_proxy_n` | proxy protein score | diet+category coarse | replace w/ dish_macro (v2) |
| default objective | on Q15 skip | Awesome Taste | — |

### Checkpoint
§3 locks the Q15 gain — four objectives as multiplier vectors over the feature groups, bounded so it re-ranks but never filters, composing cleanly with BASE / weather / calorie filter. Final spine section next: **S4 — Pairing guardrails + Assemble-7** (build the actual 7 plates: dry+liquid pairing predicates, single/standalone handling, support attach, veg-day substitution, the familiarity->discovery dial, no-duplicate guard).

---

## Section 4 — Pairing Guardrails + Assemble-7 (the plate builder)

*The finish line. §1-§3 give every surviving dish a score. §4 turns scored dishes into the **7 ranked plates** the user sees: forms valid plates (dry+liquid pair / single alone / standalone alone), applies the pairing guardrails, attaches the support default, handles veg-day substitution, enforces the familiarity->discovery dial and the no-duplicate guard. Output: 7 plates, highest plate-score on top.*

---

## 0. Inputs to this stage
After §1-§3, each dish `x` in the eligible pool (post-filter) has:
- `score(x) = BASE(x) × GAIN_Q15(x) + w_pref·S_pref(x)`  (a scalar)
- `hero_role(x)` in {liquid, dry, single, standalone, support, snack, accompaniment}
- `scope_tier(x)`, cuisine, richness/base signals, diet.
The pools for the slot: **DRY pool**, **LIQUID pool**, **SINGLE pool**, **STANDALONE pool** (snacks/accompaniments excluded from B/L/D plates in v1). Support is not scored.

---

## 1. What a plate is
```
Plate ::=  (dry hero, liquid hero)        # the everyday pair  -> + support
        |  (single hero)                  # rich/special alone  -> + support
        |  (standalone complete)          # complete in itself  -> NO support
```
Support attaches to the first two forms by the default-carb rule (§4); standalone gets none.

---

## 2. Pairing guardrails (dry hero + liquid hero) — the six research rules as predicates
For a candidate pair `(d, l)`, split into HARD gates (pair not formed if violated) and SOFT terms (adjust compatibility).

### HARD gates — `allowed(d,l)`
```
allowed(d,l) =
   NOT both_rich(d,l)                 # G1: no two heavy/creamy gravies
   AND NOT same_base(d,l)             # G2: not two tomato-onion / two coconut / two same-dal
   AND cuisine_dist(d,l) <= theta_region   # G4: one-region coherence
```
- `both_rich`: both carry an indulgence-richness tag {buttery,creamy,ghee_rich,coconut_rich}. *(Largely pre-handled by the taxonomy — rich dishes are classified SINGLE, so they leave the liquid-pairing pool. This gate catches residue.)*
- `same_base`: shared defining base — derived from the §1 `ING` block on **base ingredients** (both coconut-dominant; both tomato+onion dominant; same primary dal). Use `cosine(base-ingredient vectors) > theta_base`.
- `cuisine_dist`: the §1 hierarchical cuisine distance; `theta_region` default **0.5** (same cuisine_group or closer) -> keeps the plate regionally coherent.
- *G3 (no two dry) is automatic* — we only ever pair one DRY with one LIQUID by construction.

### SOFT terms -> `compat(d,l)` in [-1,+1]
```
compat(d,l) =  b_balance · 1[ one rich/medium & one light ]        # G5: richness balance
             + b_protein · 1[ pulse/protein liquid & veg dry (or vice-versa) ]  # G6: protein-veg balance
             - p_sametaste · taste_overlap(d,l)                    # mild: avoid identical taste profiles
b_balance = 0.5 ,  b_protein = 0.3 ,  p_sametaste = 0.2   (params)
```

### Standalone flag
Dishes flagged `standalone` (biryani, khichdi, pulao, pav bhaji, masala dosa, + the global standalone set) **bypass pairing entirely** — they occupy a plate alone.

---

## 3. Plate score
Compatibility is applied **multiplicatively** so it has *proportional* influence regardless of the raw score scale (an additive `+0.5` would vanish against scores of ~100; a multiplier does not).
```
pair plate     P=(d,l):  plate_score(P) = ( score(d) + score(l) ) × ( 1 + lambda_pair · compat(d,l) )
single plate   P=(s):    plate_score(P) = score(s)
standalone     P=(t):    plate_score(P) = score(t)
lambda_pair = 0.5   (param — how strongly pairing quality scales the pair; compat in [-1,+1])
```
With `compat in [-1,+1]` and `lambda_pair=0.5`, a perfect pair is scaled ×1.5, a poor (but allowed) pair ×0.5 — proportional, scale-independent. Support is excluded from the score (it floats; §4).

---

## 4. Support (carb) default attach — DERIVE rule, editable
For non-standalone plates, attach a default from {Roti, Paratha, Poori, Rice} (millet roti -> "Roti"; naan excluded). Priority: **liquid-hero type first, else region.**
```
by hero type:  rajma->rice ; sambar/rasam->rice ; kadhi->rice ; chole->poori|rice ;
               most North dals/sabzis->roti ; aloo-sabzi(weekend)->poori ; shrikhand->poori
by region (fallback): South / Bengal-Odia / Goa-Konkan -> rice ;
               Punjab-North / Gujarat / Rajasthan / Maharashtra / Bihar -> roti (+rice) ;
poori: gated to weekend/festive or specific pairings only (never the everyday default)
```
User-editable; v2 learns per-user carb preference. (Plain noodles can act as support for gravy-mains — the §-earlier support set extension.)

---

## 5. Veg-day substitution (Q7) — substitute, don't blank
On a household veg-day, the diet filter (§2 A1) runs veg for that day. Rather than leaving a hole where a meat hero would rank:
```
v1: veg-day = veg filter ON for the day; the VEG pools simply refill the plates (no explicit 1:1 swap).
v2/deferred: explicit 1:1 substitution via the variant graph (butter chicken -> butter paneer),
             so the user sees the "same dish, veg version" rather than a different dish.
```
The variant/substitution graph is the deferred DB-designed feature; v1 just refills from the veg pool.

---

## 6. Assemble-7 — greedy selection with guards
```
1. CANDIDATES:
     pairs      = { (d,l) : d in DRY, l in LIQUID, allowed(d,l) }   with plate_score
     singles    = { (s)  : s in SINGLE }                            with plate_score
     standalones= { (t)  : t in STANDALONE }                        with plate_score
     ALL = pairs ∪ singles ∪ standalones
2. SORT ALL by plate_score descending.
3. GREEDY PICK top plates subject to:
     (a) NO-DUPLICATE GUARD: skip a plate if any of its heroes/dish already appears
         in an already-chosen plate of this set of 7.
     (b) DISCOVERY DIAL: cap the number of experimental/discovery plates at
         floor(rho_disc · 7).  v1 rho_disc ~0.05 -> ~0 experimental -> FAMILIARITY-FIRST.
   until 7 plates chosen.
4. ATTACH SUPPORT (§4) to non-standalone plates.
5. OUTPUT 7 plates, plate_score order (highest on top).
```

### What is DELIBERATELY minimal in v1 (deferred -> v2/v3, per the RE doc pointer)
The greedy step ships with **only the no-duplicate guard**. The richer machinery is parked because it needs user/cohort data to calibrate:
- **role-aware recency decay** (staples recur freely, specials spaced out)
- **per-axis variety** (diversity within dry pool, within liquid pool, across cuisines/bases — not just "7 different plates")
- **exploration policy** (surface unseen dishes to generate v2 training signal) — *prerequisite for v2 learning*
- **the familiarity->discovery ramp**: `rho_disc` is the dial; v1 pins it near floor (familiarity-first), v2 ramps it up on confidence x D3 x D5.

These all ride on the §1 distance `d(a,b)` / `sim(a,b)` already defined — no new machinery needed when they're turned on.

---

## 7. Open parameters (Section 4)
| Param | Meaning | v1 default | Learn |
|---|---|---|---|
| `theta_region` | max cuisine distance for a coherent pair | 0.5 | tune |
| `theta_base` | same-base exclusion threshold | 0.6 | tune |
| `b_balance, b_protein, p_sametaste` | soft pairing terms | 0.5 / 0.3 / 0.2 | tune / v2 |
| `lambda_pair` | weight of pairing quality in plate score | 0.5 | tune |
| `rho_disc` | discovery dial (familiarity->discovery) | ~0.05 floor | v2 ramp |
| support defaults | carb derive rule | §4 table | v2 per-user |

---

## 8. Spine complete
With §4, the core scoring spine is end-to-end:
```
onboarding+context -> [filters §2A] -> eligible pool
   -> score = BASE §2B × GAIN_Q15 §3 + w_pref·S_pref §1  (per dish)
   -> form plates + pairing guardrails §4.2 -> plate_score §4.3
   -> assemble-7 (no-dup + discovery dial) §4.6 -> attach support §4.4
   -> 7 ranked plates
```
Everything is a named parameter with a v1 default; the function is linear/multiplicative in those parameters so v2 (per-user `S_pref`, `kappa` decay, `rho_disc` ramp) and v3 (cohort) plug in without changing the form.

### Next (post-spine)
- **D1-D7 derivation formulas** — turn the reconciled derivation layer into explicit formulas producing the profile `H`/`theta` that §2 reads (blend, constraints, age/household priors, income proxy, time-route).
- **Step 5 parameter population** — author the full PRIOR[zone][slot][season] cells, comfort-hero sets, signature flags, and tune the weights above.
- **Schema -> code.**

---

# Appendix — Future / Deferred Work (consolidated forward-notes)

*Everything intentionally NOT built in v1.0, gathered in one place and tagged. The v1 spine is designed so each plugs in without changing the core equation.*

## A. v2 learning activations (the engine starts using behaviour)
- `[v2]` **Personalization `S_pref` activation** — like/dislike/swap + the closing-onboarding calibration (tap-to-like, planted-negative survivors) train the per-user tag accumulator `a_user` and scalar preferred-levels `mu_user`. Inert (=0) in v1. Full numeric update rule (rates, decay, scalar-confidence schedule) = the v2 spec.
- `[v2]` **Q15 behavioural override** — the `kappa(confidence)` decay curve that shifts authority from the stated objective to behaviour, plus optional per-user `gamma` cells. v1 pins `kappa=1.0`.
- `[v2]` **Per-signal confidence calibration** — learn each rule module's `conf_k` (e.g. trust home-state palette less after long tenure away; trust user-selected mode fully). v1 pins all `conf_k=1.0`.
- `[v2]` **Familiarity->discovery ramp** — `rho_disc` becomes `f(feedback_confidence x risk_appetite[D3] x household_type[D5])`: families-with-kids ramp slowly (very low exploration), single working professionals ramp faster. v1 pins `rho_disc` near floor (familiarity-first).

## B. v2/v3 model upgrades (same equation, richer parameters)
- `[v2]` **Variety / diversity machinery** across FOUR independent axes — **cuisine diversity, ingredient diversity, cooking-method diversity, taste diversity** (not a single "per-axis" lump). Plus **role-aware recency decay** (staples recur freely; specials spaced out) and an **exploration policy** (surface unseen dishes — a *prerequisite* for v2 learning, since you cannot learn dislikes for dishes never shown). All ride on the §1 distance `d(a,b)`; v1 ships only the no-duplicate guard.
- `[v2]` **Learned ingredient embeddings** replacing the IDF-weighted overlap block (IDF is the solid v1 stand-in).
- `[v2]` **Within-block tag similarity** — crispy↔crunchy closer than crispy↔smooth, via learned co-occurrence or authored tag-distance (weighted Jaccard). v1 uses vanilla Jaccard; the block structure already prevents cross-block confusions.
- `[v2]` **Weather thermal inference** — derive hot/cold-day fit from sensory features (thermal+spice+heaviness+water-content) instead of explicit tags, for scalability. v1 KEEPS explicit weather tags because the *cultural* rainy-day comfort hero (kanda bhaji, khichuri) is NOT derivable from sensory features and is the most important weather behaviour.
- `[v3]` **Cohort term `S_cohort`** activation — same inner-product form per cohort cluster; `w_cohort=0` until v3.

## C. Knowledge Base & data dependencies (separate, version-controlled apart from the spine)
- `[KB]` **Prior / Knowledge-Base document** — the region x slot x season PRIOR cells, comfort-hero maps, and graded signature scores will become one of Foo'Foo's largest knowledge bases. **Keep it as a separate, separately-versioned document**; the spine defines only the *interface* to it (B8/B4). This is the bulk of the parameter-population pass (Step 5).
- `[DATA][v2]` **Nutrition Vector** — replace the calorie-only Nutrition group + protein-proxy with a full per-dish vector: **calories, protein, fibre, fat, carbs, sugar, sodium** (the deferred `dish_macro` dataset). Unblocks the Q15 Protein Calculator and macro-accurate calorie/target filtering.
- `[KB]` **Ingredient aliases** — the 4 unmatched tokens (coriander_seeds, cumin_powder, basmati_rice, mixed_vegetables) + the `ING`-block tokenization gaps (grated_coconut, fish_fillet) -> 100% join.

## D. Safety — must complete BEFORE public launch
- `[SAFETY]` **Allergen hidden-derivative table** (e.g. hing -> wheat/gluten). v1 allergen filtering is the BASIC explicit-ingredient pass only and is NOT safe-complete until this lands. Jain restrictions + allergens are HARD filters.

## E. Deferred features (designed-for or parked; build later)
- `[DB-designed]` **Substitution / variant graph** (butter chicken -> butter paneer -> Jain -> vegan) — schema designed to carry it; powers the explicit veg-day 1:1 substitution (v1 just refills from the veg pool).
- `[later]` Snack / tea-time 4th meal slot · guest / special-occasion mode · need-based modes (recovery/convalescent + weaning/baby-food, the stated secondary segment) · festive-positive proactive recommendations.
- `[later]` Seasonal-produce / availability feed · real-time pricing feed · panchang / calendar auto-service (replaced in v1 by user-toggled modes).
- `[later]` **Premium-promotion hook** — surface premium items (e.g. parmesan, exotic produce) to well-off households via the D1 income band + a static premium-tier tag; no live pricing feed needed.

## F. Parked (not researched)
- `[parked]` **Health-condition dish implications** — BP / diabetes / kidney / liver. Q11 still flows as a secondary demotion, but there is no dish-implication research behind it. Needs condition->dish research + clinical review.

---
*End of RE v1.0 core specification. Companion document: **D1-D7 Derivation Formulas** (produces the profile `theta`/`H` this spine reads).*


---

## Future / Deferred / RFC Register  *(this document)*
*Quick-reference index of this document's forward-looking items. Convention: `[ID] [TAG] Title — trigger/what-it-needs — STATUS`. Tags: [v2]/[v3]/[KB]/[SAFETY]/[DATA]/[DB]/[later]/[parked]. Status: OPEN / RFC-DRAFTED / DONE(vX.Y). When this file is edited, update the relevant line so the freeze lineage stays in-place. Detailed rationale for each item is in the sections above.*

| ID | Tag | Item | Trigger / needs | Status |
|---|---|---|---|---|
| SP-F1 | v2 | Personalization S_pref activation (like/dislike/calibration) | feedback data | OPEN |
| SP-F2 | v2 | Q15 behavioural override (κ-decay + per-user γ) | user history | OPEN |
| SP-F3 | v2 | Per-signal confidence calibration (conf_k) | behaviour | OPEN |
| SP-F4 | v2 | Familiarity→discovery ramp (ρ_disc = f(conf × risk × household)) | history | OPEN |
| SP-F5 | v2 | Diversity: 4 axes (cuisine/ingredient/cooking/taste) + role-aware recency + exploration | history/cohort | OPEN |
| SP-F6 | v2 | Learned ingredient embeddings (replace IDF overlap) | data | OPEN |
| SP-F7 | v2 | Within-block tag similarity (crispy↔crunchy) | co-occurrence/authoring | OPEN |
| SP-F8 | v2 | Weather thermal inference (keep cultural comfort tag) | efficiency | OPEN |
| SP-F9 | v3 | Cohort term S_cohort activation | cohort data | OPEN |
| SP-F10 | KB | Prior/Knowledge-Base doc (region×slot×season, comfort-heroes, graded signatures) | authoring (Step 5) | OPEN |
| SP-F11 | DATA/v2 | Nutrition Vector (protein/fibre/fat/carbs/sugar/sodium) via dish_macro | macro data source | OPEN |
| SP-F12 | KB | Ingredient aliases (4) + ING tokenization gaps | quick fix | OPEN |
| SP-F13 | SAFETY | Allergen hidden-derivative table (hing→wheat) | verified mapping | **OPEN — PRE-LAUNCH** |
| SP-F14 | DB | Substitution/variant graph (butter chicken→paneer→jain→vegan) | powers veg-day 1:1 swap | OPEN |
| SP-F15 | later | snack/tea slot · guest mode · need-based modes · festive-positive | product decision | OPEN |
| SP-F16 | later | seasonal-produce feed · real-time pricing · panchang auto-service | integrations | OPEN |
| SP-F17 | later | premium-promotion hook (D1 income + static premium tag) | — | OPEN |
| SP-F18 | parked | health-condition dish implications (BP/diabetes/kidney/liver) | clinical research | PARKED |

