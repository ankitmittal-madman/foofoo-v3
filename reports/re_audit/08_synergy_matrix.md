# Phase 9 — Synergy Matrix (evidence-based)

Method: for each claimed cross-module interaction, grep for both concerns co-occurring in the same
function/module in `ghar_re_core/*.py`, then read the function to confirm it actually combines them
(not just each half implemented separately elsewhere). Spine reference: `docs/architecture/ghar-re/
ghar_re_v1_0_core_spine_FROZEN.md`.

| # | Claimed synergy | In code? | Evidence |
|---|---|---|---|
| 1 | weather × region | **Yes — real synergy** | `ghar_re_core/scoring.py:267-296` `m_weather(dish, theta, ctx)`: computes the generic weather signal, then at lines 289-293 calls `_comfort_heroes_for(theta, wcond)` (`scoring.py:468-483`) which resolves the household's *own* KB §R3 region-specific comfort hero (via `theta`'s derived zone/sub-zone) and adds a decisive +0.5 only if the candidate dish IS that region's hero — i.e. the weather boost is explicitly region-conditioned, not generic. Spine calls this out itself as "NOT a generic pan-India pakora" (spine line 348). |
| 2 | weather × household | **Partial — same BASE sum, not a joint function** | Weather (`m_weather`, `scoring.py:267`) and household fit (`m_household`, `scoring.py:250-264`) are separate BASE modules summed together in `base()` (spine formula, §S2 B; module list `scoring.py` — `m_palette`,`m_slot`,`m_season`,`sig`,`m_age`,`m_household`,`m_weather`,`prior_boost`). They compose additively via the shared `BASE` sum (architectural contract, spine line 291), but no single function reads both weather ctx AND household structure together to produce a joint term — e.g. household size doesn't change the weather boost magnitude. So the "interaction" is score-composition-level, not code-level fusion. |
| 3 | household × member (age/lifecycle) | **Yes — real synergy** | `ghar_re_core/derivation.py:180-215` (D5 block): a single function derives `spice_ceiling` (min over per-member age-band tolerance, line 187), `texture_floor` (has_weaning or has_senior, line 188), `heaviness_ceiling` (has_senior, line 189), `variety_pressure`/`batch_posture` keyed on `q1_household_type` (lines 190-191), AND `lifecycle_stage` (infant/toddler/pregnancy/elder/teen/school_child, lines 196-214) from member ages + roles + Q11 conditions together — genuinely fuses household composition and per-member age/condition data into one derived profile that `m_age`/`m_household` (`scoring.py:230-264`) then read. |
| 4 | cohort × class/genome | **Yes — real synergy** | `ghar_re_core/cohort_intel.py:216-260` `_class_affinity_uncached(theta, ctx)`: blends home-state affinity and current-city-lifestyle affinity per the household's own `City_Migration_Overlay` weights (`w_home`/`w_local`/`w_nat`, lines 245-247), keyed by `(home, destination_group(theta))` — a genuine home-state × migration-city × meal-class fusion, not two separate lookups. `config.py:158-186` (`w_cohort_effective`, `foreign_demote_effective`) further conditions the cohort weight itself on interaction_count (cold-start decay), so cohort × behavioural-confidence is also fused in one function. |
| 5 | pairing × context | **Partial** | `ghar_re_core/pairing.py:73-89` (`allowed()`/`compat()`) implements the hard gates/soft terms from the spine (§S4) purely from dish-pair attributes (richness, base ingredients, cuisine distance) — no `theta`/`ctx` (household/weather/season) argument is threaded into `pairing.py`'s functions per the grep; pairing coherence is dish-intrinsic, not household- or weather-conditioned in v1. This matches the spine's own scope (§S4 describes pairing guardrails as dish-pair predicates, not context-aware) — so "pairing × context" as a synergy is **not implemented and not actually claimed by the frozen spine** beyond veg-day substitution (§5, `ctx`-driven diet filter swap, spine lines 597-604), which IS real (diet filter A1 re-run per day, `derivation.py`/pairing pool refill logic). |
| 6 | cold-start × research priors | **Yes — real synergy** | `ghar_re_core/cohort_intel.py` docstring (line 4 area): "The 'make cold-start feel like the persona-DB plan, derived not copied' engine" — `class_affinity()` (item 4 above) IS the cold-start mechanism, directly built from the transcribed persona-DB/KB research (`Indian_Meal_Cohort_Persona_DB_v3.xlsx` → `knowledge.py` per `knowledge.py:410`). `config.py:173-185` `w_cohort_effective(interaction_count=0)` returns the strong cold-start weight at n=0 and decays with a configured half-life — i.e. cold-start state and the KB-authored cohort prior are fused in the same function, not independent systems. |
| 7 | ingredient × substitute | **No — not implemented** | `grep -rn -i "substitut" ghar_re_core/*.py` finds only: `ghar_re_core/knowledge.py:212` (a comment documenting a one-off comfort-hero name substitution, unrelated to ingredients), `ghar_re_core/seedgen.py:308-309` (a comment: "dish_variants (a couple, to exercise the substitution graph)" — i.e. only a couple of SEED rows exist to exercise the schema, no live substitution logic). The spine itself confirms this: SP-F14 "Substitution/variant graph (butter chicken→paneer→jain→vegan)" is tagged **OPEN** (spine line 725), and §5 (line 604) states "v1 just refills from the veg pool" rather than doing 1:1 ingredient substitution. **Docs-only / deferred, not built.** |
| 8 | region × comfort-hero | **Yes — real synergy (same code path as #1)** | Same evidence as #1 — `_comfort_heroes_for` (`scoring.py:468-483`) resolves region (via household's zone/sub-zone) to the KB §R3 comfort-hero table (`knowledge.py:156-195`), and `COMFORT_HERO_TO_DISH` (`knowledge.py:218-227`) maps the KB-authored hero name to an actual catalogue dish. This is arguably the most concretely-implemented synergy in the whole audit — see also the disclosed gap-fix at `knowledge.py:206-216` (Kanda Bhaji → Pakora (Mixed Veg) remap). |
| 9 | Q15 × gain (objective × BASE) | **Yes — real synergy (this is the spine's core composition, not incidental)** | `ghar_re_core/scoring.py:385-423` `gain_q15(dish, objective)` and the final `score()` function (line 423 area, "score = BASE × GAIN_Q15 + w_cohort(n)·S_cohort − foreign_demote(n)·S_foreign") multiply the BASE score (which already carries weather/region/household) by the Q15 gain — a literal multiplicative fusion per spine §S3 Part C (`scoring.py:327` "GAIN = 1 + Σ_g gamma[obj][g]·gs_g(x)"). This is the frozen spine's own master formula, implemented exactly as specified. |

## Additional cross-cutting observation

`ghar_re_core/scoring.py`'s final `score()` function is itself the single largest synergy point in
the codebase — it is where BASE (which already embeds weather×region, household×age, region×comfort-
hero), GAIN_Q15, cohort (with its own migration-overlay synergy), and foreign-demote all get combined
into one number. Most of the "real" synergies above are real precisely because they happen inside
BASE's constituent modules or inside `cohort_intel.py`/`derivation.py`, which then feed `score()` —
i.e. the architecture's "BASE is a sum of self-contained rule modules" contract (spine line 291) is
respected: modules that need cross-concern fusion (weather×region, household×age, cohort×migration)
do it internally before returning a plain `[0,1]`/`[-1,1]` value, rather than `score()` itself trying
to fuse raw concerns.

## Not-implemented / docs-only summary

- **Ingredient × substitute (variant graph)**: confirmed not built — spine explicitly defers it
  (SP-F14, `ghar_re_v1_0_core_spine_FROZEN.md:725`); only placeholder seed rows exist
  (`ghar_re_core/seedgen.py:308-309`).
- **Pairing × full context-awareness** (weather/season influencing pairing compatibility, beyond
  the veg-day diet-filter swap): not implemented in `pairing.py`, and not actually claimed as v1
  scope by the frozen spine — §S4 pairing guardrails operate on dish-pair attributes only.
- **Health-condition dish implications** (BP/diabetes/kidney/liver — part of the broader "member
  segment" claims in the original context): confirmed **PARKED** by the spine itself (SP-F18,
  `ghar_re_v1_0_core_spine_FROZEN.md:729`) — "Q11 still flows as a secondary demotion, but there is
  no dish-implication research behind it." Grep for `DIABETIC_ELDER`/`POSTPARTUM`/`FITNESS`/
  `FASTING` as explicit member-segment tokens in `ghar_re_core/*.py` and `data/source/*.yaml`
  returned no hits except `derivation.py:195` referencing "family-with-TODDLER" as a persona-DB
  sub-cohort code — the richer member-segment vocabulary described in the earlier spec generation
  (RE-DOC-01/02) does not appear to have a corresponding implementation under those exact tags in
  the live engine; `lifecycle_stage` (`derivation.py:196-214`) covers infant/toddler/pregnancy/
  elder/teen/school_child, which is a real but differently-named/scoped implementation of part of
  that idea.

All claims above are grounded in the cited file:line evidence; where evidence could not be found
(e.g. verifying the `Indian_Meal_Cohort_Persona_DB_v3.xlsx` transcription against the source
workbook, or measuring comfort-hero coverage against the full 810-dish catalogue rather than the
golden sample), this is stated explicitly rather than assumed.
