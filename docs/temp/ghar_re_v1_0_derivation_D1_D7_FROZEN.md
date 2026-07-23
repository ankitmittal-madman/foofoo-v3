# Ghar RE v1.0 — Household Intelligence Layer — Formal Derivation Specification (D1–D7)  *(FROZEN)*

> **Status: FROZEN as RE v1.0** (companion to the frozen Core Spine). Logic, formulas, and the v1->v2->v3 evolution are frozen; changes are versioned RFCs, never in-place edits. This revision adds **presentation & interface** improvements only — no equation changed. Forward items are tagged `[v2]`/`[v3]`.

*Turns the 15 onboarding answers + context into the **Derived Household Profile `θ`** that the frozen Core Spine reads. `θ` is the single interface between onboarding and scoring.*

**Onboarding map:** Q1 household-type · Q2 #working-professionals · Q3 home-state · Q4 current-city · Q5 diet · Q6 non-veg-types · Q7 veg-days · Q8 Jain · Q9/Q10 allergies · Q11 conditions · Q12 age(s) · Q13 who-cooks · Q14 eat-out-freq · Q15 objective.

---

## §0. The onboarding -> θ pipeline (read first)
```
Onboarding raw answers (Q1–Q15)
        ↓  validation        (range/format checks, required-field guards)
        ↓  normalization     (units, city->tier, date->season/weekday, age->band)
        ↓  D1–D7 derivations (this document)
        ↓
   θ  =  Derived Household Profile        ← the interface object
        ↓
   RE Core Spine (filters -> score -> pair -> assemble-7)
```
Everything before `θ` is "household intelligence"; everything after is scoring. The two never blur.

---

## §1. The Derived Household Profile `θ`  (first-class object)
`θ` is the **named contract** between onboarding and the engine. Every field carries **provenance metadata** so any recommendation is traceable.

### 1.1 Per-field metadata schema (every derived field is a record, not a bare value)
```
field = {
   value      : the derived value
   confidence : [0,1]   — trust in this value          (v1: 1.0 for all; v2 learns)
   source     : which derivation produced it           (e.g. "D4")  or "explicit" / "context"
   kind       : explicit | derived | learned
   stability  : stable | dynamic
   version    : logic version that produced it          (e.g. "D-layer v1.0")
   timestamp  : when computed
}
```
> v1 pins `confidence=1.0` everywhere and `learned` fields are empty, but the **schema is present now** so confidence-learning, provenance/audit, and explainability slot in without rework. This metadata is what lets you later debug "why was this recommended?" down to the exact field and source.

### 1.2 θ classified by ROLE (not one long list)
| Class | Fields | Source |
|---|---|---|
| **Identity** | home_state, local_palette, region | Q3, Q4, D4 |
| **Constraints** (hard) | diet, meat_exclusions, is_jain, allergens, weaning_present, spice_ceiling, texture_floor, heaviness_ceiling | Q5–Q10/Q12, D5, D6 |
| **Preferences** (soft) | non_veg_cadence, community_prior, variety_pressure, batch_posture | Q3/Q6, D5, D6 |
| **Context** (today) | season, weekday, weather, active_modes, calorie_target | Q4+date, modes, user |
| **Derived Controls** | blend, blend_slot[], income_band, time_route(+reason), effort_ceiling, adventurousness, rho_disc | D1–D4 |
| **Behaviour / Latent** | latent.observance, latent.community_sub, S_pref state | D7, v2 learning |

### 1.3 θ classified by STABILITY (what to cache vs recompute)
- **STABLE** (compute once at onboarding; rarely change): home_state, region, diet, is_jain, allergens, age-bands, household structure, income_band, base blend.
- **DYNAMIC** (recompute per session/day): season, weekday, weather, active_modes, calorie_target, time_route (weekday vs weekend), blend_slot, rho_disc (as it ramps in v2), Q15 effective gain (as κ decays in v2).
> Implementation guidance: persist STABLE; recompute DYNAMIC each request.

---

## §2. Computation DAG + the universal (value, confidence) contract
**Every derivation emits `(value, confidence)`** — not only D1. `confidence=1.0` in v1; v2 calibrates from behaviour (e.g. blend_conf drops when a long-tenure migrant keeps picking home-region food, signalling the default tenure was wrong).
```
context(Q4->city,tier,climate; date->season,weekday) 
   -> D1, D4, D5, D6          (independent)
   -> D2 (needs D1),  D3 (needs D1,D4)
   -> D7 (v2, behavioural)
```

---

## §3. Interfaces — what feeds what (θ -> spine)  *(placed before the formulas on purpose)*
| Spine term | Fed by θ field(s) | From |
|---|---|---|
| `m_palette`, blend, local_palette, region | Identity + blend | D4 (+Q3/Q4) |
| hard filters A1–A3 (diet/jain/allergen), veg-day, non_veg_cadence | Constraints | D6 |
| weaning filter A4, `m_age`, variety_pressure | Constraints/Preferences | D5 |
| `m_household` | batch_posture | D5 |
| `m_effort` (BASE module) + effort_ceiling | time_route, effort_ceiling | D2 (needs D1) |
| `rho_disc`, experimental scope gate | adventurousness | D3 (needs D1,D4), bounded by D5 |
| weather comfort-hero resolution | region | D4 |
| `conf_k` per module `[v2]` | per-field confidence | all D (§1.1) |
| explainability output `[integration]` | source + reason metadata | all D |
| premium-promotion `[later]` | income_band | D1 |

---

## §4. The derivations D1–D7
*(Formulas unchanged from the reconciled layer. Each now annotated with what it emits, its confidence, and — for D2 — its reason.)*

### D1 — Disposable income / price-sensitivity  *(DERIVE proxy + confidence; ASK held)*
Inputs: Q2 earners, Q1 dependents/size, Q4 city-tier, Q12 age, Q13 hired-cook, Q14 eat-out.
```
earners_n    = clip(n_earners / 2, 0, 1)
depend_ratio = dependents / household_size
city_tier_n  = {tier1:1.0, tier2:0.6, tier3:0.3}[Q4.city_tier]
cook_hired   = 1 if Q13 == hired_cook else 0
eatout_n     = clip(eat_out_per_week / 4, 0, 1)
age_factor   = {<=24:0.5, 25-34:0.85, 35-50:1.0, 51-64:0.8, 65+:0.5}[age]

s_income = sigmoid( a0 + a_earn·earners_n + a_dep·(1-depend_ratio) + a_city·city_tier_n
                  + a_cook·cook_hired + a_eat·eatout_n + a_age·age_factor )
income_band = low if s_income<0.40 | mid if <0.70 | high otherwise

sub = [earners_n,(1-depend_ratio),city_tier_n,cook_hired,eatout_n]
income_conf = 1 - clip(2·stdev(sub),0,1)
if income_conf < conf_lo: pull s_income toward 0.45    # CONSERVATIVE when unsure
```
EMITS: `income_band (value, confidence=income_conf, kind=derived, stability=stable)`.
v1 defaults: a0=-1.5,a_earn=1.2,a_dep=0.8,a_city=1.0,a_cook=1.4,a_eat=0.7,a_age=0.5; cuts .40/.70; conf_lo=0.5.
> ASK held: no income question in v1; promote-to-ASK only if v2 shows D2 mis-routing beyond threshold.

### D2 — Time-pressure routing + effort ceiling  *(DERIVE; needs D1)*
```
effort_ceiling = family:1.0 | hired_cook:0.9·avail_discount | self weekday:0.40 / weekend:0.80 | order/tiffin:0.10
time_pressure  = clip(0.5·earners_n + 0.3·(Q13==self) - 0.2·eatout_n, 0, 1)
time_route, reason =
    (DELEGATE,  "hired cook present")        if Q13==hired_cook
    (OUTSOURCE, "dual-income / high time-pressure") if time_pressure high AND income_band==high
    (SIMPLIFY,  "low income / cook in-house")        otherwise
```
EMITS: `time_route (value, confidence, reason)` + `effort_ceiling`. The **reason** feeds explainability.
Registers BASE module: `m_effort(x|θ) = 1.0 if OUTSOURCE or dish_effort<=ceiling, else 1 - p_over·(dish_effort-ceiling)`; `+ W_EFFORT·m_effort`, W_EFFORT=0.40, p_over=1.0, avail_discount=0.9.

### D3 — Adventurousness  *(DERIVE start; LEARN; needs D1,D4)*
```
age_novelty = {<=24:1.0,25-34:0.8,35-50:0.5,51-64:0.35,65+:0.2}[age]
hh_novelty  = {single:0.9,couple:0.8,couple_kids:0.4,couple_kids_parents:0.3,joint:0.35,flatmates:0.85}[Q1]
migr_expo   = 1 - blend
A = clip(b0 + b_age·age_novelty + b_hh·hh_novelty + b_inc·s_income + b_migr·migr_expo + b_eat·eatout_n, 0,1)
v1: rho_disc = rho_floor + A·rho_span_v1   (0.05 + A·0.05 -> max ~0.10: FAMILIARITY-FIRST)
v2: rho_disc ramps on  A × feedback_confidence × (1 - kid_elder_cap)   [v2]
```
EMITS: `adventurousness A (value, confidence)`. Bounded by D5 (kids/elders cap novelty on SHARED heroes).
v1 defaults: b0=0,b_age=.35,b_hh=.25,b_inc=.15,b_migr=.15,b_eat=.10; rho_floor=.05,rho_span_v1=.05.

### D4 — Origin↔local blend  *(DERIVE start; LEARN tenure)*
```
is_migrant = region(Q3)!=region(Q4) ; elders = elders present ; tenure_n = 0.3 (v1 DEFAULT; v2 learns)
blend = 1.0 if not is_migrant else clip(c0 + c_elder·elders + c_age·age_factor - c_tenure·tenure_n, blend_min, 1.0)
blend_slot[breakfast]=max(blend,0.80) ; blend_slot[lunch]=blend-0.10 ; blend_slot[dinner]=blend
local_palette = 8-metro profile if Q4 in {Mumbai,Pune,Ahmedabad,Delhi-NCR,Bengaluru,Chennai,Hyderabad,Kolkata} else Q4 state
region = zone(Q4) blended with zone(Q3) by blend ; overrides: Ahmedabad(veg-pressure), Chennai(rice/tiffin)
```
EMITS: `blend (value, confidence=blend_conf; v1 1.0, v2 lower when tenure default proves wrong)`, local_palette, region.
v1 defaults: c0=.75,c_elder=.15,c_age=.10,c_tenure=.35,blend_min=.30.

### D5 — Household selection-constraint set  *(DERIVE; LEARN variety-fatigue)*
```
weaning_present = any member 6mo-2yr        -> A4 weaning HARD filter
spice_ceiling   = min over members of spice_tol  {weaning:1,toddler:1,child:2,teen:4,adult:4,senior:3}
texture_floor   = soft if (weaning or senior) else none
heaviness_ceiling = 2 if senior else 3
variety_pressure = {single:.2,couple:.5,couple_kids:.8,couple_kids_parents:.7,joint:.4,flatmates:.3}[Q1]
batch_posture    = 1 if Q1 in {joint,couple_kids_parents} else 0
m_age(x|θ)       = 1 - clip(max(0,spice_level(x)-spice_ceiling)·p_spice + texture_violation(x)·p_tex,0,1)
```
EMITS: the Constraints class + variety_pressure, batch_posture (each value+confidence). p_spice=.3,p_tex=.5.
*Most-restrictive-member floor applies to SHARED heroes; indulgent heroes still allowed elsewhere in the 7.*

### D6 — Tiered constraint profile  *(ASK core; DERIVE prior+conflicts; LEARN veg-day)*
```
diet, meat_exclusions, veg_days, is_jain, allergens   <- Q5/Q6/Q7/Q8/Q9/Q10   (HARD filters A1–A3)
non_veg_cadence = {daily,frequent,weekend,rare}  DERIVED from Q3 community prior, overridden by Q6
community_prior = NFHS state diet-default(Q3)     # SOFT prior only; explicit Q5–Q8 always win
condition_demotions = small soft demotes from Q11 # [PARKED] no dish-implication research
```
EMITS: Constraints (explicit, confidence=1.0 — they're asked) + Preferences (derived). Veg-day = scheduled substitution (refill from veg pool in v1; explicit 1:1 swap = deferred variant graph).

### D7 — Latent-attribute inference  *(LEARN only — v2/v3; never ASK)*
**Evidence-accumulation principle (no math in v1; the rule):**
```
single observation        -> WEAK evidence (do nothing)
repeated observations      -> evidence accumulates
crosses an activation threshold -> STRONG evidence -> PROMPT the user ("Turn on Fasting Mode?")
```
e.g. repeated Navratri farali picks -> likely observant-fasting; repeated Tuesday-veg -> likely veg-day; Eid sewai+mutton -> no-pork default. Inferred, never asked; activates only on accumulated evidence, always via a confirmable prompt (never silent).
v1: `latent = {}`. EMITS (v2): latent fields with confidence = accumulated-evidence strength. Activation thresholds = `[v2]`.

---

## §5. Calibration Parameters (chosen-and-tunable; not "open/undefined")
| Group | Params | v1 default |
|---|---|---|
| D1 | a0,a_earn,a_dep,a_city,a_cook,a_eat,a_age; band cuts; conf_lo | -1.5,1.2,0.8,1.0,1.4,0.7,0.5; .40/.70; 0.5 |
| D2 | effort_ceiling table; W_EFFORT; p_over; avail_discount | as above; 0.40; 1.0; 0.9 |
| D3 | b0,b_age,b_hh,b_inc,b_migr,b_eat; rho_floor,rho_span_v1 | 0,.35,.25,.15,.15,.10; .05,.05 |
| D4 | c0,c_elder,c_age,c_tenure,blend_min; tenure_n default; slot offsets | .75,.15,.10,.35,.30; 0.3 |
| D5 | spice_tol table; p_spice,p_tex; variety_pressure table | as above; .3,.5 |
| D6 | community_prior table (Q3) | NFHS state defaults [KB] |

---

## §6. Future / deferred (D-layer)
- `[v2]` **Confidence learning for ALL derivations** — the `(value, confidence)` framework is built; v2 calibrates the numbers from behaviour.
- `[v2]` **Provenance/audit tooling** — the per-field metadata (source/version/timestamp) is captured now; debugging/audit UI is v2.
- `[v2]` **Tenure** as a real learned input (v1 default 0.3) -> sharpens D4.
- `[v2]` **D7 activation** — evidence thresholds + the confirm-prompt flow.
- `[v2]` **Promote-to-ASK income** — only if proxy mis-routes D2 beyond threshold.
- `[KB]` **community_prior table** (NFHS state diet-defaults) lives in the Knowledge Base, not here.
- `[PARKED]` **Q11 condition->dish demotions** — placeholder; needs clinical research.

*Companion to: RE v1.0 Core Spine (FROZEN). Together = the complete v1 mathematical specification. Next: the Integration / Household Intelligence overview chapter, which leans on the formalized θ object + confidence/provenance contract defined here.*


---

## Future / Deferred / RFC Register  *(this document)*
*Quick-reference index of this document's forward-looking items. Convention: `[ID] [TAG] Title — trigger/what-it-needs — STATUS`. Tags: [v2]/[v3]/[KB]/[SAFETY]/[DATA]/[DB]/[later]/[parked]. Status: OPEN / RFC-DRAFTED / DONE(vX.Y). When this file is edited, update the relevant line so the freeze lineage stays in-place. Detailed rationale for each item is in the sections above.*

| ID | Tag | Item | Trigger / needs | Status |
|---|---|---|---|---|
| D-F1 | v2 | Confidence learning for all derivations | behaviour data (framework already built) | OPEN |
| D-F2 | v2 | Provenance / audit tooling | metadata captured now; UI/debug later | OPEN |
| D-F3 | v2 | Learn real tenure (v1 default 0.3) | user history → sharpens D4 | OPEN |
| D-F4 | v2 | D7 activation thresholds + confirm-prompt flow | accumulated behaviour | OPEN |
| D-F5 | v2 | Promote income to an ASK | only if proxy mis-routes D2 beyond threshold | OPEN |
| D-F6 | KB | community_prior table (NFHS state defaults) | lives in Knowledge Base | OPEN |
| D-F7 | parked | Q11 condition→dish demotions | clinical research + review | PARKED |

