# Ghar — Knowledge Base (KB) v0.2

> **KB Structure: FROZEN (freeze-ready).**  **Knowledge Population: WORKING (living dataset).**
> These are two different things: the *organization, interfaces, and metadata schema* below are frozen (changes = RFC); the *cell values* are expected to evolve continuously via founder curation and (v2) behaviour. The engine's intelligence layer — authored priors, comfort-hero maps, signature scores, community defaults, season/weather maps, normalization, and negative priors the frozen spine reads. Grounded in `Final_RE` + `ghar_dishes_catalogue_v1_LOCKED`.

## Metadata standard (every knowledge section carries this header)
```
Owner               : who is accountable for the cell values   {Research | NFHS | Founder-authored | Catalogue-derived | Behaviour-learned(v2)}
Source              : where the knowledge came from
Evidence confidence : are these mappings culturally CORRECT?    {High | Medium | Low}
Coverage confidence : is the table COMPLETE / not sparse?       {High | Medium | Low}
Version             : KB version that authored/last-touched it
Last reviewed       : YYYY-MM
```
> Two confidences on purpose: *evidence* = correctness of what's there; *coverage* = completeness of what's missing. v2 behaviour preferentially overrides **low-evidence** cells (correct guesses) and **fills low-coverage** gaps — different actions, so they're stored separately.

## §0. How the engine reads the KB (interface — FROZEN)
```
PRIOR[zone][slot](x)         -> BASE additive prior boosts        (Regional KB §R2)
comfort_hero(zone, weather)  -> m_weather transient boost target  (Regional KB §R3)
sig(x) in [0,1]              -> W_SIG · sig(x) in BASE            (Signature KB §S1  + sig_scores_v1.csv)
community_prior[state]       -> D6 soft diet-default              (Community KB §C1)
season_window(date,region)   -> season/thermal context            (Seasonal KB §Z1)
negative_prior(plate,ctx)    -> authored discouragements          (Negative KB §N1)
```
The KB supplies **parameters and target sets only** — never hard filters, never the scoring *form*.

---

# NAMESPACE A — REGIONAL KNOWLEDGE
`Owner: Research/Founder · Source: Final_RE + catalogue · Evidence: High · Coverage: Medium · Version: KB0.2 · Last reviewed: 2026-06`

## §R1. Zone map  (cuisine_group -> zone)   [grounded: 810 dishes]
> **A zone is a RECOMMENDATION zone, not an administrative geography.** It groups culinary palettes, so a state can be palette-North but diet-West (e.g. Rajasthan).

| cuisine_group | zone | dishes |
|---|---|---|
| north_indian, mughlai_nawabi | North | 210 |
| south_indian | South | 141 |
| west_indian | West | 96 |
| east_indian | East | 68 |
| central_indian | Central | 22 |
| northeast_indian | Northeast | 31 |
| street_food | PanIndia | 55 |
| foreign/other | Global | 187 |

**State→zone:** North: Delhi,Punjab,Haryana,UP,Uttarakhand,HP,J&K · West: Maharashtra,Gujarat,Goa · South: TN,Kerala,Karnataka,AP,Telangana · East: WB,Odisha,Bihar,Jharkhand · Central: MP,Chhattisgarh · Northeast: Assam+NE. ⚑ Rajasthan = palette-North / diet-West; MP = Central.

## §R2. Region × Slot priors  PRIOR[zone][slot]   (usage_tags multi-valued)
Additive BASE boosts on dish categories/attributes. **`usage_tags`** are multi-valued (not one category): {Daily, Weekend, Festival, Weather, Comfort, Recovery}.

**Breakfast**
| zone | boost | usage_tags |
|---|---|---|
| North | paratha +0.4, poha +0.3, chila +0.3 | Daily; chole-bhature=Weekend |
| South | idli +0.5, dosa +0.5, upma +0.3, ven pongal +0.3 | Daily; pongal also Festival,Comfort |
| West | poha +0.5, thalipeeth +0.3, upma +0.3 | Daily; misal=Weekend |
| East | luchi-alur dom +0.4, bread-omelette +0.2 | Weekend / Daily ⚑ |
| Central | poha +0.5 | Daily; jalebi-poha=Weekend |

**Lunch**
| zone | boost | usage_tags |
|---|---|---|
| North | roti+sabzi+dal +0.4, rajma/chole-chawal +0.3 | Daily; rajma also Comfort |
| South | rice+sambar/rasam +0.5, poriyal +0.3, curd-rice close +0.3 | Daily; curd-rice also Weather(summer) |
| West | roti/bhakri+sabzi+dal +0.4, varan-bhaat +0.3 | Daily |
| East | rice+macher jhol +0.5, dal +0.3 | Daily |
| Central | roti+dal+sabzi +0.4, dal-bafla +0.3 | Daily; bafla=Weekend |

**Dinner**
| zone | boost | usage_tags |
|---|---|---|
| North | roti+light sabzi+dal +0.4, khichdi +0.2 | Daily; khichdi=Comfort,Recovery,Weather |
| South | rice+rasam/curd +0.3, dosa/idli dinner +0.3 | Daily |
| West | roti/bhakri+sabzi +0.4, khichdi +0.2 | Daily; khichdi=Comfort,Recovery |
| East | rice+light jhol +0.4 | Daily |

## §R2a. Carb-default rules (support attach)
Rajma/Chole/Kadhi/Dal-Makhani→Rice · everyday North dals & sabzi→Roti · South sambar/rasam→Rice · Bengali/Odia jhol→Rice · Gujarati/Rajasthani→Roti·Rice split ⚑ · festive(dal-baati/chole)→Poori (festive-gated). Millet roti→"Roti".

## §R3. Comfort-hero maps  (weather × zone)   [✓ = verified in catalogue]
`Owner: Research · Source: Final_RE Strand 1 · Evidence: High · Coverage: Medium (NE/Kerala sparse)`

**RAIN/MONSOON** (hot, fried, tangy, khichdi-comfort)
| zone | heroes |
|---|---|
| North | pakora ✓, samosa ✓, kadhi-pakora ✓, aloo paratha ✓ |
| West-MH | kanda/mixed bhaji ✓, vada pav ✓, pithla-bhakri ✓, sol kadhi ✓ |
| West-GJ | bhajiya, dal-dhokli, methi na gota ⚑ |
| South-TN | bajji/bonda, medu vada ✓, rasam-rice ✓ |
| South-KL | parippu vada, pazham pori ⚑ |
| East-WB | khichdi ✓ (+beguni/ilish ⚑), telebhaja |
| Central | poha ✓, pakora ✓ |
| NE | thukpa, momos ⚑ |

**SUMMER/HEATWAVE** (cooling, high-water, low-spice, curd/coconut)
| zone | heroes |
|---|---|
| North | curd/raita, chaas, aam panna, sattu ✓, thandai |
| West | aamras (seasonal), chaas, sol kadhi ✓, kokum |
| South | curd rice ✓, neer mor, mor kuzhambu, tender coconut |
| East | panta bhat ⚑, light macher jhol |

**WINTER/COLD** (warming, heavy, ghee, jaggery)
| zone | heroes |
|---|---|
| North | sarson ka saag ✓+makki roti, nihari ✓, paya, bajra roti, gond laddu, gajar halwa ⚑ |
| West-GJ | undhiyu ✓, bajra bhakri, methi thepla |
| West-MH | bajra bhakri+thecha ⚑, pithla ✓ |
| South | ven pongal ✓, ellu/sesame, rasam ✓ |
| East | nolen gur sweets, pithe ⚑ |
> Mechanism: transient BOOST on the zone's row; rain→comfort/fried, summer→cooling/light + demote fried, winter→warming/heavy + relax health-damp. Never a hard filter (W_WEATHER=0.40, signed).

---

# NAMESPACE B — SEASONAL KNOWLEDGE
`Owner: Research · Source: Final_RE + ritucharya · Evidence: Medium · Coverage: Medium · Version: KB0.2`

## §Z1. Season windows (India default; region-overridable)
| season | months | thermal lean |
|---|---|---|
| Summer | Mar–Jun | hot → cooling |
| Monsoon | Jun–Sep | wet → comfort/fried |
| Post-monsoon | Oct–Nov | mild → neutral |
| Winter | Dec–Feb | cold → warming |
⚑ Overrides: Chennai/coastal-South summer extends (muted winter); North/hills deeper winter; Rajasthan extreme both ways.

## §Z2. Weather-API → thermal tag (transient)
`temp ≥ 34°C → HOT (cooling)` · `rain flag → WET (comfort)` · `temp ≤ 15°C → COLD (warming)` · else NEUTRAL. Cultural comfort hero (§R3) is the *target*; not derivable from temperature alone.

---

# NAMESPACE C — COMMUNITY KNOWLEDGE
`Owner: NFHS · Source: NFHS-5 (approx) · Evidence: Medium · Coverage: Medium · Version: KB0.2`
> **Initialization priors ONLY.** These seed D6's soft diet-default and are ALWAYS overridden by explicit Q5–Q8. Once user behaviour exists (v2), community-prior influence decays toward the household's revealed pattern.

## §C1. State diet-default → non_veg_cadence
| lean | states | default cadence |
|---|---|---|
| Strongly veg | Rajasthan, Gujarat, Haryana, Punjab(veg-lean), MP | rare / weekend |
| Mixed | UP, Maharashtra, Karnataka, Delhi | weekend / frequent |
| Strongly non-veg | WB, Kerala, Telangana, AP, TN, Odisha, Bihar, Jharkhand, Goa, all NE | frequent / daily |
⚑ Replace lean-labels with exact NFHS-5 fish/meat % per state (KB-F3).

---

# NAMESPACE D — SIGNATURE KNOWLEDGE
`Owner: Founder/Research (curated) + Auto-derived (draft) · Source: Final_RE + catalogue heuristic · Evidence: High(curated 58)/Low(draft 744) · Coverage: High(all 810) · Version: KB0.2`

## §S1. Calibration rule (keeps scoring consistent)
| score | band | definition |
|---|---|---|
| 1.00 | national_icon | recognized/iconic across India (Butter Chicken, Hyderabadi Biryani, Masala Dosa) |
| 0.90 | state_icon | defining dish of a state (Dal Makhani, Undhiyu, Nihari, Litti Chokha) |
| 0.75 | regional_hero | strong regional standard (Bisi Bele Bath, Macher Jhol, Puran Poli) |
| 0.60 | very_common | well-known everyday-plus (Rajma Chawal, Poha, Aloo Paratha) |
| 0.40 | common | ordinary named dish (standard dals, upma, sabzi-with-name) |
| 0.20 | utility | plain staple (steamed rice, plain dal, roti, papad) |

## §S2. Data location
All 810 draft scores live in **`sig_scores_v1.csv`** (separate data file — keeps this doc clean and lets scores regenerate independently). Each row carries: sig_score, band, evidence_confidence, coverage_confidence, owner, method, version. **58 curated=High, 744 auto-draft=Low** → curate the Low ones over time; behaviour refines in v2.

---

# NAMESPACE E — INGREDIENT KNOWLEDGE (Normalization)
`Owner: Catalogue-derived · Source: catalogue join · Evidence: High · Coverage: Medium · Version: KB0.2`
> Broader than aliases: **normalization** = mapping any surface token to a canonical ingredient (aliases, synonyms, regional names, protein equivalences). Grows into an ingredient reference over time.

## §E1. Normalization map (starter)
| surface token | canonical | type |
|---|---|---|
| coriander_seeds | coriander | alias |
| cumin_powder | cumin | alias |
| basmati_rice | rice (basmati flag) | variety |
| mixed_vegetables | {potato,carrot,beans,peas,cauliflower} | expansion ⚑ |
| grated_coconut | coconut | form |
| fish_fillet | fish | form |
| dhaniya | coriander | synonym |
| palak | spinach | synonym |
| mutton | goat | equivalence |
> Applying → 100% ingredient join for IDF/similarity + allergen derivation.

---

# NAMESPACE F — NEGATIVE KNOWLEDGE (authored discouragements)
`Owner: Founder/Research · Source: Final_RE Strand 2 + culinary logic · Evidence: High · Coverage: Medium · Version: KB0.2`
> Knowledge isn't only positive. These are authored **discouragements** as *data* (editable here without touching the spine). The spine ENFORCES the structural ones as pairing penalties (S4); the KB is the editable source of what to discourage. Cross-ref: spine §S4 guardrails.

## §N1. Negative priors
| discouragement | context | action | in-spine? |
|---|---|---|---|
| two rich/creamy gravies together | any plate | penalty (S4 hard-gate) | yes |
| two same-base gravies (both tomato-onion / both coconut) | any plate | penalty | yes |
| two dry heroes as the pair | any plate | penalty | yes |
| cross-region pair (Bengali + Punjabi hero) | any plate | penalty (cuisine-dist gate) | yes |
| deep-fried / very-heavy | heatwave day | demote | via weather |
| heavy lunch → heavy dinner (same day) | slot sequence | demote (v2 needs history) | ⚑ v2 |
| three of the same vegetable base (e.g. 3 potato dishes) | across the 7 | demote (variety) | ⚑ v2 |
| raw salads / street-style | peak monsoon | mild demote | via weather |
⚑ The sequence/variety ones need logged history → activate in v2 (SP-F5).

---

## Future / Deferred / RFC Register  *(this document)*
| ID | Tag | Item | Trigger / needs | Status |
|---|---|---|---|---|
| KB-F1 | KB | Refine all ⚑ regional cells | Founder regional knowledge | OPEN |
| KB-F2 | KB | Curate the 744 auto-draft sig scores | over time (drafts live in sig_scores_v1.csv) | OPEN |
| KB-F3 | KB | Exact NFHS-5 veg/non-veg % per state | data pull | OPEN |
| KB-F4 | KB | Region × slot × **season** 3-D priors | after 2-D validated | OPEN |
| KB-F5 | v2 | Learn priors + decay community/low-evidence cells from behaviour | usage data | OPEN |
| KB-F6 | KB | Festival-day comfort/signature overlays | festival map | OPEN |
| KB-F7 | KB | Season = climate/agriculture/culture split (mango season, holidays) | when availability/festival modes built | DEFERRED |
| KB-F8 | v3+ | Evolve KB → Knowledge Graph (ingredient–dish–region–festival–season) | scale; keep human-authored until then | DEFERRED |
| KB-F9 | v2 | Activate sequence/variety negative priors (§N1 ⚑) | logged history | OPEN |

*Companion to: RE v1.0 Core Spine (FROZEN) + D1–D7 (FROZEN). Supplies their parameters. Structure frozen; data living. Data file: `sig_scores_v1.csv`.*
