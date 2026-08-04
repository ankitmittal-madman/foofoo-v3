# Phase 5 — Knowledge Base Audit (evidence-based)

Scope: `docs/architecture/ghar-re/ghar_re_v1_0_core_spine_FROZEN.md` (730 lines, read in
full), `ghar_re_core/config.py`, `ghar_re_core/knowledge.py`, `data/source/*`. All
line numbers cite the file as read during this audit.

## 1. Knowledge components named in the Core Spine + their own stated status

Core spine §"Future/Deferred/RFC Register" (lines 707-730) is the document's own tracker.
Quoting the table verbatim (Tag / Status):

| Component | Spine ref | Status (spine's own tag) |
|---|---|---|
| SP-F1 Personalization `S_pref` activation | line 712 | **OPEN** (v2) |
| SP-F2 Q15 behavioural override (κ-decay) | line 713 | **OPEN** (v2) |
| SP-F3 Per-signal confidence calibration (`conf_k`) | line 714 | **OPEN** (v2) |
| SP-F4 Familiarity→discovery ramp (`rho_disc`) | line 715 | **OPEN** (v2) |
| SP-F5 Diversity (4 axes) + recency + exploration policy | line 716 | **OPEN** (v2) |
| SP-F6 Learned ingredient embeddings (replace IDF) | line 717 | **OPEN** (v2) |
| SP-F7 Within-block tag similarity | line 718 | **OPEN** (v2) |
| SP-F8 Weather thermal inference (keep cultural tag) | line 719 | **OPEN** (v2) |
| SP-F9 Cohort term `S_cohort` activation | line 720 | **OPEN** (v3) |
| **SP-F10 Prior/KB doc (region×slot×season, comfort-heroes, graded signatures)** | line 721 | **OPEN** — the dedicated "Step 5" parameter-population pass, explicitly **not done** in v1.0 (also stated at §2 "D. Open items", line 396: "Full PRIOR population … is the dedicated parameter pass (Step 5)") |
| SP-F11 Nutrition Vector (`dish_macro`: protein/fibre/fat/carbs/sugar/sodium) | line 722 | **OPEN** (DATA/v2) |
| SP-F12 Ingredient aliases (4 unmatched tokens) + `ING` tokenization gaps | line 723 | **OPEN** (KB, "quick fix") |
| SP-F13 Allergen hidden-derivative table (hing→wheat) | line 724 | **OPEN — PRE-LAUNCH** (SAFETY) |
| SP-F14 Substitution/variant graph (butter chicken→paneer→jain→vegan) | line 725 | **OPEN** (DB-designed) |
| SP-F15/16/17 later features (snack slot, guest mode, festive, seasonal-produce, pricing, premium hook) | lines 726-728 | **OPEN** (later) |
| SP-F18 Health-condition dish implications (BP/diabetes/kidney/liver) | line 729 | **PARKED** (no clinical research behind it) |

Also explicitly called out inline: `sig(x)` (B4, line 331) — "v1 needs a graded signature score …
Authored in the parameter pass (Step 5 / Knowledge Base)" — i.e. the spine itself says signature
scores are NOT yet authored as of the spine's writing (superseded later by WP-21, see §3 below).
`PRIOR[zone][slot]` (B8, line 350) — "shape here; full population = Step 5" — i.e. the table
structure is frozen but the cells are illustrative/seed examples only (3 zones × 1 slot each shown,
lines 360-366), not a full region×slot×season population.

## 2. Per-source: loaded at runtime? populated or stub?

Grep evidence: `grep -rn "<filename>" ghar_re_core/*.py ghar_re_core/training/*.py`.

| File | Loaded by `ghar_re_core` at runtime? | Evidence | Populated / placeholder |
|---|---|---|---|
| `base_weights.yaml` | **Yes** | `config.py:50` `self.base = _load("base_weights.yaml")`; `config.py:65-76` `.W(key)` | Populated — concrete v1 defaults matching spine §B9 (e.g. `W_SIG: 0.30`, `data/source/base_weights.yaml:14`) |
| `distance_weights.yaml` | **Yes** | `config.py:51`; used in `ghar_re_core/pairing.py:55-57` | Populated |
| `q15_weights.yaml` | **Yes** | `config.py:52`, `.gamma()`/`.kappa_v1`/`.gain_bounds` (`config.py:85-111`) | Populated |
| `pairing_rules.yaml` | **Yes** | `config.py:53`; consumed in `ghar_re_core/pairing.py:73,89` | Populated |
| `weather_rules.yaml` | **Yes** | `config.py:54`; `ghar_re_core/scoring.py:452` thermal thresholds | Populated |
| `filters.yaml` | **Yes** | `config.py:55,144-149` (`T_CAP`) | Populated |
| `derivation_params.yaml` | **Yes** | `config.py:56,151-156`; `ghar_re_core/derivation.py:6` "All constants come from … never hardcoded" | Populated |
| `cohort_weights.yaml` | **Yes** | `config.py:57,158-199` (`w_cohort`, `w_cohort_effective`, `foreign_demote_effective`) | Populated, with an explicit self-flagged data-quality note at `data/source/cohort_weights.yaml:32`: "an inflated sig_score — Veg Burger is mis-tagged sig=0.75 … let 23% of the catalogue …" — i.e. the cohort layer itself documents a known curation defect upstream. |
| `bandit_weights.yaml` | **Yes** | `config.py:58,201-216` | Populated but code-level safety default is 0.0 (no-op) if the key is missing — `config.py:206-209` |
| `pref_model.yaml` | **Yes** | `config.py:59,218-257` | **Present but inert by design**: `pref_model_enabled` defaults False (`config.py:220-224`), no trained artifact configured (`ghar_re_core/model_provider.py:51`) — this is Phase-3 scaffolding, not a populated knowledge source |
| `community_priors.csv` | **Yes** | `config.py:262-273` `community_priors` property, opened directly with `csv.DictReader` | Populated (state→zone/diet_lean/cadence), cross-checked for conflicts by `ghar_re_core/knowledge.py:364-369` against the KB |
| `region_food_affinity.csv` (137 lines, `data/source/region_food_affinity.csv:1-4`) | **NOT loaded by `ghar_re_core`** — zero hits in `ghar_re_core/*.py` | grep returned nothing under `ghar_re_core/` | Populated with real curated affinity scores (state_code, dish_name, affinity_score 0-1), but it feeds the **offline seed/curation tooling only**: `data/source/generate_sig_scores_v1.py:92` reads it to derive `sig_scores_curation_template.csv`; `database/etl/generate_re_seeds.py:316-318` and `database/etl/generate_icd1_seeds.py:470` consume it for DB seed generation. It is a build-time input, not a live engine config file. |
| `sig_scores_curation_template.csv` | **NOT loaded by `ghar_re_core`** | no hits in `ghar_re_core/` | Populated — 63 dishes, each row explicitly marked `"RESOLVED (WP-21): <band>"` with `method` column stating **"AI-assigned via established Indian food-culture knowledge (not live-cited web sources) per Founder direction that per-dish Founder review isn't feasible at this volume; recommend a spot-check, not a full re-review"** (verbatim, every row, e.g. `sig_scores_curation_template.csv:2`). This is AI-generated curation input consumed by `ghar_re_service/ghar_re_service/scripts/build_catalogue.py` / DB seed builders, not read by the live scoring engine — the live engine reads `dish.sig_score` off the `Dish` object (`ghar_re_core/catalogue.py:57`), which for the golden sample comes from `ghar_re_core/fixtures.py`, not this CSV. |
| `term_synonyms_v2.csv` (122 lines) | **NOT loaded by `ghar_re_core`** | no hits | Populated (canonical_name/synonym/language, e.g. Pani Puri↔Gol Gappa/Puchka/Gupchup, `term_synonyms_v2.csv:1-5`); consumed only by `ghar_re_service/ghar_re_service/scripts/build_catalogue.py:128,217` (dish-name synonym resolution at catalogue-build time), not by any runtime `ghar_re_core` scoring path. |
| `ingredient_aliases_v2.csv` (169 lines) | **NOT loaded by `ghar_re_core`** | no hits | Populated (turmeric↔haldi etc., `ingredient_aliases_v2.csv:1-5`); consumed only by `build_catalogue.py:126,193` at build time. |
| `Indian_Meal_Cohort_Persona_DB_v3.xlsx` | **Indirectly, via transcription, not the raw file** | `ghar_re_core/knowledge.py:410` comment: "Wires data/source/Indian_Meal_Cohort_Persona_DB_v3.xlsx (41 personas, 131 meal classes, 2952 …)" | The xlsx itself is never opened by Python at runtime (no `openpyxl`/`pandas` read found in `ghar_re_core`); its content was manually transcribed into `knowledge.py`'s Python literals. This is a documentation/provenance comment, not a live file read — cannot verify 100% fidelity of the transcription against the workbook without opening it (not done in this audit; flagged as unverifiable). |

**Summary of the split:** `ghar_re_core/config.py`'s `Config` class loads exactly 9 YAML files + 1
CSV (`base_weights`, `distance_weights`, `q15_weights`, `pairing_rules`, `weather_rules`, `filters`,
`derivation_params`, `cohort_weights`, `bandit_weights`, `pref_model`, `community_priors.csv`) — this
is the complete live-engine config surface. `region_food_affinity.csv`, `sig_scores_curation_template.csv`,
`term_synonyms_v2.csv`, and `ingredient_aliases_v2.csv` are real, populated, curated files, but they sit
**one layer upstream** — build-time/seed-generation inputs for `database/etl/*` and
`ghar_re_service/.../build_catalogue.py`, not files the live Python RE (`ghar_re_core`) reads directly.
Whether that upstream pipeline's *output* actually reaches the live engine depends on whether the
810-dish catalogue cutover (still deferred, per prior audit) has happened — as of this audit, the
live RE runs on the 39-dish `ghar_re_core.fixtures` golden sample, which does not derive from these
CSVs at all.

## 3. Signature scores — spine vs actual state (important correction to the spine's own text)

The spine (§B4, line 331) states sig scores are not yet authored. In fact `sig_scores_curation_template.csv`
shows this partially happened **after** the spine was frozen, under a tracked work package (**WP-21**),
for 63 dishes flagged as national_icon/state_icon/regional_hero candidates (`sig_scores_curation_template.csv:1-63`
sample rows checked). But: (a) this is a curation *template* output, feeding seed generation, not a live
config the engine reads; (b) every one of the 63 rows carries the caveat quoted above — Medium
evidence-confidence, AI-assigned, explicitly "recommend a spot-check, not a full re-review" — so even
where signature scores exist, Founder-verified accuracy is not claimed. The 6-band calibration RULE
itself (`SIG_SCORE_BANDS`, `ghar_re_core/knowledge.py:238-248`) is transcribed from the KB and marked
`'real'` (i.e. the *scale* is authored/real), but which dishes land on which band beyond the golden
39-dish fixture set is only ~63-dish curated, not the full 810-dish catalogue.

## 4. Research → executable config traceability (3 concrete examples)

1. **Comfort-hero regional mapping** (research: rainy-day regional comfort dish per zone) →
   `ghar_re_core/knowledge.py:156-195` `COMFORT_HERO_MAP` — a Python literal transcribed
   "VERBATIM from ghar_knowledge_base_v0_2.md" (module docstring, `knowledge.py:2-3`), each row
   tagged real (✓, verified in catalogue) or stub (⚑, KB's own "needs refinement" marker) via the
   `_ch()` helper (`knowledge.py:151-155`). This **is** executable: `ghar_re_core/scoring.py:289-293`
   `_comfort_heroes_for(theta, wcond)` resolves it live inside `m_weather()`, and the KB's own gap
   note is preserved in code — `knowledge.py:206-216` documents that "Kanda Bhaji" (the KB-authored
   West-Maharashtra rain hero) does not exist under that name in the real 810-dish catalogue and had
   to be remapped to "Pakora (Mixed Veg)" as a **domain-owner-confirmed substitution**, not a silent
   fix. This is a genuine, traced, end-to-end path: doc → Python table → scoring function, with the
   provenance gap disclosed at each step rather than hidden.
2. **Regional dish affinity (state-level)** — `data/source/region_food_affinity.csv` (137 rows,
   state_code/dish_name/affinity_score, e.g. `PB,Butter Chicken,0.95,regional,...` at line 2) — this
   research/curation output feeds `data/source/generate_sig_scores_v1.py:62-64,92,193` (used to help
   derive the `sig_scores_curation_template.csv` band suggestions) and `database/etl/generate_re_seeds.py:316-318`
   / `generate_icd1_seeds.py:470` (DB seed generation). It does **not** feed `ghar_re_core` directly —
   no `region_food_affinity` string appears anywhere under `ghar_re_core/`. So this is a real trace,
   but it terminates at the seed-generation/DB layer, not the live scoring engine — it is documentation-
   → -build-tooling, not documentation-→-live-engine.
3. **Ingredient/dish-name synonym research** (Pani Puri / Gol Gappa / Puchka / Gupchup / Phulki
   regional naming, `data/source/term_synonyms_v2.csv:1-5`) → consumed only by
   `ghar_re_service/ghar_re_service/scripts/build_catalogue.py:128,217` for catalogue-build-time
   name resolution. Confirmed **not** read anywhere in `ghar_re_core/*.py` (empty grep). Same
   pattern as #2: real curated CSV, real downstream consumer, but the consumer is the catalogue
   build pipeline for the (still not cut over) 810-dish catalogue, not the live 39-dish engine.

**Conclusion on Phase 8 (research coverage):** where research became a KB-authored table transcribed
into `ghar_re_core/knowledge.py` (comfort heroes, zone map, sig-score bands, cuisine-group map), it IS
executable and live. Where research became a standalone curated CSV (region affinity, synonyms,
ingredient aliases, sig-score curation template), it is real and populated but sits in the
build/seed-generation layer, one hop short of the live `ghar_re_core` engine — it will only reach
production scoring once the deferred catalogue cutover consumes it.

## 5. Comfort heroes / signature scores — implemented or docs-only?

**Comfort heroes: implemented, not docs-only.** `grep -rn -i "comfort" ghar_re_core/*.py` shows a
full pipeline: KB table (`knowledge.py:156-195` `COMFORT_HERO_MAP`), a name→catalogue-dish resolver
(`knowledge.py:218-227` `COMFORT_HERO_TO_DISH`), a scoring-time lookup (`scoring.py:468-483`
`_comfort_heroes_for`), and a scoring-time decisive lift (`scoring.py:289-293`, "+0.5" when the dish
IS the household's own zone-specific hero) inside the live `m_weather()` BASE term. Also referenced
in `fixtures.py:11` ("Several dishes are named, BY NAME, after actual KB §R3 comfort heroes") and
`seedgen.py:168-172,322-332` (DB seed export of the same table). This is a real, wired concept, not
only RE-DOC-02's weather table.

**Signature scores: implemented as a scale + a golden-sample assignment, NOT a full-catalogue
authored set.** `SIG_SCORE_BANDS`/`BAND_TO_SCORE` (`knowledge.py:238-249`) is real and live
(`scoring.py:222-226` `sig()` reads `dish.sig_score` directly). But per-dish `sig_score` values
beyond the 39-dish fixture and the 63-dish WP-21 curation template are not established — the spine's
own B4 note (line 331) that authoring is a "Step 5 / Knowledge Base" task remains largely open for
the full catalogue.

## 6. Production knowledge-coverage estimate (config-layer, not raw dish counts)

| Component | Estimate | Evidence |
|---|---|---|
| Research Priors (docs/research → executable config) | **~25%** | 4 of the ~10+ candidate research artifacts (comfort heroes, zone map, sig bands, cuisine-group map) are transcribed into live `knowledge.py`; region-affinity/synonym/alias research (region_food_affinity.csv, term_synonyms_v2.csv, ingredient_aliases_v2.csv) is real but only reaches build-tooling (`generate_re_seeds.py`, `build_catalogue.py`), not `ghar_re_core` — see §4. |
| Weather (rules + comfort-hero resolution) | **~70%** for the 3 documented conditions (rain/hot/cold) × golden sample | `weather_rules.yaml` fully loaded (`config.py:54`), `m_weather` fully coded (`scoring.py:267-296`), comfort-hero map covers the golden 39-dish sample's named heroes; coverage against the full 810-dish catalogue is unverified/likely much lower since most catalogue dishes aren't in `COMFORT_HERO_TO_DISH` (only 10 name mappings, `knowledge.py:218-227`). |
| Pairings | **~90% of the frozen rule set, 0% learned** | `pairing_rules.yaml` fully loaded and consumed (`pairing.py:73,89`); all v1 hard gates/soft terms per spine §S4 are coded; this is a rule-authored feature with no data-population gap, so coverage is high relative to spec — the gap is only the deferred v2 richer machinery (recency/diversity, spine Appendix B). |
| Regional Intelligence (`PRIOR[zone][slot]`) | **~10-15%** | Spine itself states (line 396, line 350) the full region×slot×season cell population is the "dedicated parameter pass (Step 5)" and gives only 3 illustrative zone×slot examples (lines 360-366) out of a 6-zone × 3-slot (×season) matrix — the shape exists in code/config, the cells are largely unpopulated. |
| Safety (allergen filter completeness) | **~50%, explicitly not launch-ready** | Basic explicit-ingredient allergen filter is coded (spine §A3, line 240-244); the hidden-derivative table (hing→wheat) is `SP-F13`, tagged **"OPEN — PRE-LAUNCH"** (line 724) — the spine itself states allergen filtering "is not safe-complete" until this lands. |
| Seed Quality (as it bears on knowledge config, not raw dish count) | **Mixed / self-flagged** | `cohort_weights.yaml:32` documents a discovered defect (mis-tagged sig_score letting 23% of the catalogue through incorrectly) that had to be corrected — i.e. the seed/config layer has had at least one confirmed real quality bug, caught and noted in-repo rather than silently left. Sig-score curation beyond the golden sample is AI-generated, Medium-confidence, explicitly not Founder-reviewed (§3 above). |

All six estimates above are qualitative judgments grounded in the cited evidence, not measured
percentages from an actual count — flagged as such rather than presented as precise.
