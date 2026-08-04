STATUS: ARCHIVED
Reason: Superseded by docs/archive/audits/re_audit_v2/ (the 2026-08-04 clean-room re-audit), which is itself superseded by docs/active/. Kept for historical reference only.

# Phase 1 — Requirement Traceability Matrix

Status: DRAFT (working audit output, not a governed document under the Naming Standard)
Method: every requirement below is drawn from a canonical source document, then mapped to the
current repository state as verified in reports 02-09 of this audit (each row cites the source
report, not re-derived evidence — see those reports for file:line detail).

**Governing fact for this whole matrix:** the repository contains two spec generations and,
historically, two implementations.
- **Spec generation 1**: RE-DOC-01/02/03/04/05 (`docs/architecture/*.docx`, `docs/roadmaps/*.docx`) —
  "classfirst_v1": cohort matrix, 26 meal classes, MMR variety (λ=0.7), weight-ladder w_history,
  4-state (A/B/C/D) evolution model, Never/Not-Today exponential decay.
- **Spec generation 2**: RE-DOC-10/11/12/13 (`docs/architecture/*.md`) + the FROZEN Core Spine
  (`docs/architecture/ghar-re/ghar_re_v1_0_core_spine_FROZEN.md`) — D1-D7 derivation, BASE×GAIN_Q15
  scoring, pairing/assemble-7, HMAC/Fly.io deployment. **This is the generation actually built and
  live** (confirmed by RE-DOC-12's own as-built audit and re-confirmed by this audit's report 02).
- The **legacy TypeScript engine** (`re_engine.*` schema, `_shared/services/re/*.ts`) that spec
  generation 1 governed is now **formally gone**, not merely dormant: migration 047 dropped the
  `re_engine` schema outright (report 07 §1), with a JSON backup at
  `database/archive/re_engine_backup_20260803/`. Spec generation 1 therefore has **no live
  implementation to trace against** for most of its content — this is stated once here rather than
  repeated on every row.

Status legend: **Implemented** / **Partial** / **Stub** / **Missing** / **Deprecated** (spec existed,
superseded by a different mechanism, not present in any form) / **Deferred** (explicitly tracked as
future work by the canonical doc itself) / **Unknown** (not verifiable from repo evidence alone).

## A. Architecture & module boundary (RE-DOC-01, RE-DOC-10, RE-DOC-13)

| Requirement | Source | Status | Evidence |
|---|---|---|---|
| RE isolated as separate module/service, app never touches RE internals | RE-DOC-01 §1-2; RE-DOC-10 §1 | **Implemented** | `ghar_re_core`/`ghar_re_service` own zero DB connections/credentials; Edge Functions own 100% of DB access (RE-DOC-12 §1, re-confirmed report 02) |
| Versioned API contract (`contracts/ghar-re-v1.schema.json`), both sides validate | RE-DOC-01 §3; RE-DOC-10 §4-6,15 | **Implemented** | RE-DOC-12 §1 (single file, both sides reference it, CI gate) — not independently re-verified this session but no contradicting evidence found |
| Shadow-mode version promotion / rollback in <5 min | RE-DOC-01 §4 | **Unknown / likely Missing** | No shadow-mode or version-promotion machinery found in any of reports 02-09; nothing deployed at all (RE-DOC-13 Executive Summary — "PREPARED, NOT DEPLOYED") |
| Fallback: cached plan / static popular-8 on RE failure | RE-DOC-01 §5; RE-DOC-10 §11 | **Partial** | Edge Function `fallback.ts` returns one hardcoded pan-India plate, not a per-zone cached set (RE-DOC-12 §3 item 4, not re-verified this session — flagged unconfirmed in report 02) |
| HMAC service-to-service auth, rate limiting | RE-DOC-10 §9; RE-DOC-13 §2.3 | **Implemented** | `auth.py`/`ratelimit.py`, tested (`test_auth.py`, `test_ratelimit.py`) per RE-DOC-12/13 — not re-verified this session, no contradicting evidence |
| `requireOwnership` authorization on recommendations handler | RE-DOC-13 §2.2 (gap flagged by RE-DOC-12 §3 item 2) | **Implemented** (fixed since RE-DOC-12) | report 09 §5 — `handler.ts:107` |
| household_context read/write round-trip | migration 038; RE-DOC-12 §3 item 3 (gap) | **Implemented** (fixed since RE-DOC-12) | report 09 §4, report 07 §4 |
| Deployment to Fly.io, live traffic | RE-DOC-13 | **Missing** (not deployed) | RE-DOC-13 Executive Summary; not re-checked this session (out of scope — no infra access) |
| Two-engine ambiguity (legacy TS RE vs Python RE) | RE-DOC-12 Executive Summary (finding, not a requirement) | **Resolved** | report 07 §1 — `re_engine` schema dropped by migration 047, legacy engine has no schema to read even if code still exists on disk |

## B. Scoring algorithm (RE-DOC-03, RE-DOC-10, Core Spine)

| Requirement | Source | Status | Evidence |
|---|---|---|---|
| D1-D7 household derivation | Core Spine; RE-DOC-10 §3 | **Implemented** (D1-D6); **Stub** (D7) | report 02 — `derivation.py:52-241`; D7 = `field({}, "D7", ...)`, literally empty |
| Hard constraint pre-filter (diet/allergen/Jain/weaning/slot/class) | RE-DOC-03 §3; Core Spine §2 | **Implemented**, allergen filter explicitly basic-only | report 02 — `scoring.py:16-153`; hidden-derivative allergen layer out of scope by design (report 04) |
| 26 meal classes (cohort-matrix taxonomy) | RE-DOC-03 §1 | **Deprecated / reimplemented differently** | Actual system uses `hero_role`+`dish_category`+`meal_class_code` lookup with multi-class membership (report 02), not the literal 26-code cohort-matrix taxonomy |
| FinalScore formula (w_cohort·CohortPrior + w_content·ContentMatch + w_history·PersonalHistory + w_context·ContextFit + w_explore − Penalties) | RE-DOC-03 §2 | **Deprecated / reimplemented differently** | Actual formula is `score = BASE × GAIN_Q15 + w_cohort(n)·S_cohort − foreign_demote(n)·S_foreign` (report 08 item 9) — same spirit (cohort/context/history/explore terms), structurally different (multiplicative gain, not weighted sum) |
| Weight ladder (w_cohort/w_content/w_history/w_context/w_explore shifting by interaction count) | RE-DOC-03 §2 | **Partial** | `w_cohort_effective`/`foreign_demote_effective` decay with interaction_count (report 02, 08 item 4) — a real analogue for the cohort term; no equivalent ladder exists for `w_content`/`w_context`; `w_history` analogue (`s_pref`) exists but is pinned to 0.0 (report 09 §3) |
| BASE score = Σ W_k·conf_k·m_k(x) | Core Spine §S2B | **Implemented** | report 02 — `scoring.py:159-324`, 7 modules + prior_boost, `conf_k` pinned 1.0 v1 |
| Q15 gain | Core Spine §S3 | **Implemented** | report 02 — `scoring.py:326-398` |
| Pairing guardrails (G1-G6) | Core Spine §S4 | **Implemented, G6 partially buggy** | report 02, 09 §6 — G6 protein-check narrower than the code's own named categories, deliberate documented non-fix |
| Assemble-7 | RE-DOC-10 §3; Core Spine | **Implemented** | report 02 — `pairing.py:197-259` |
| Fallback dish-level (per-zone cached plate) | RE-DOC-10 §11 | **Partial / Unconfirmed** | report 02 — meal-planner-level class safeguard exists; service/edge-function-level per-zone fallback not re-verified this pass |
| Personal history learning (w_history term, scored) | RE-DOC-03 §2; RE-DOC-05 State B | **Deferred (built, inert by design)** | report 09 §3 — `s_pref` wired into registry, `enabled: false`, `w_pref: 0.0`, only `NullModelArtifactProvider` constructed; training pipeline real but never run against production data (FD-11 density gate) |
| Cold start (cohort/research-driven Day-0 plan) | RE-DOC-04 §1 | **Implemented**, differently-built | report 02 — `cold_start_top15()`, cook-capability bias, household-seeded diversify; cohort-prior mechanism is `cohort_intel.py`'s trained log-linear model, not a static persona lookup |
| 4-state evolution model (A/B/C/D) + confidence ladder | RE-DOC-05 §1 | **Missing / Deprecated** | report 02 — no state machinery found anywhere; confidence pinned to 1.0 everywhere in v1 |
| Exploration (Thompson Sampling bandit) | RE-DOC-03 §2; RE-DOC-05 | **Implemented as a different algorithm** (epsilon-greedy) | report 02, 09 §3 — real, live, `epsilon: 0.15` production default; no Thompson Sampling code exists anywhere |
| MMR variety guard (λ=0.7) | RE-DOC-04 §2 | **Deprecated / reimplemented differently** | report 02 — no MMR/λ mechanism found; variety achieved via no-duplicate-hero guard + per-class/cuisine caps + recent-window suppression, functionally similar goal, different algorithm |
| Never list (permanent, rare reactivation) | RE-DOC-04 §3 | **Missing** | report 02 — no persistent never-list/decaying-suppression state machinery found; closest analogue is a one-shot, session-scoped `exclude_dish_ids` filter |
| Not-Today exponential decay (P0·e^(-λt)) | RE-DOC-04 §3 | **Missing** | report 02 — same finding as above; no per-dish decaying suppression exists |
| ML upgrade path (classfirst_v2/v3, cluster_v1, ltr_v1, ml_v1) | RE-DOC-05 §2 | **Not started beyond Phase 3 scaffolding** | `s_pref` (report 09) is the only concrete step toward "classfirst_v2"-style personal learning, and it is inert; no clustering, LTR, or two-tower/CF code found in any report |

## C. Meal Genome (RE-DOC-02 §2) — see report 03 for full per-dimension table

| Requirement | Status | Evidence |
|---|---|---|
| 20-dimension genome, literal fields as specified | **Deprecated / restructured** | report 03 — none of the 20 dimensions is a literal 1:1 match; the actually-built Core Spine model uses ~89 tag dimensions across 5 semantic groups + ingredient block, a different (not necessarily worse) organizing scheme |
| Cross-cuisine discovery via cosine similarity on genome vectors | **Missing / spec-only** | report 03 — `delta_ING = 1-cosine(...)` is a frozen-doc formula, `pairing.py:39` explicitly implements only a "proxy," `genome_vector` column is a sparse tag-position array never compared via cosine anywhere |
| Per-dimension population (see report 03 for full count) | **~14/20 implemented in live golden-sample RE; ~15/20 have some schema home; only 6/20 confirmed bulk-populated for the real 802-dish catalogue; 5/20 have no real equivalent** | report 03 full table |

## D. Food Ontology / Graph (RE-DOC-02 §3) — see report 04 for full detail

| Requirement | Status | Evidence |
|---|---|---|
| Generic typed-edge graph (Dish/Ingredient/AllergenFlag/MealClass/UserProfile/MemberSegment nodes) | **Deprecated / reimplemented as flat FK tables** | report 04 §1 — every edge type is its own bespoke relational table or bitmask column; no traversable graph exists |
| Allergen propagation via graph traversal | **Reimplemented as bitwise-OR aggregation** | report 04 §1, §3 — functionally narrower than graph traversal (can't express arbitrary multi-hop derivation without new bit positions) |
| Allergen hidden-derivative folding (e.g. hing→gluten) | **Stub, PRE-LAUNCH blocking per the spec's own tag** | report 04 §3 — schema exists (now moot, table dropped with the rest of `ghar_re` schema per report 07 §1), zero seed rows ever existed, Core Spine's own register tags this `SP-F13, OPEN — PRE-LAUNCH` |
| Ingredient substitution (graph-based) | **Deferred, spec self-confirms not v1 scope** | report 04 §2 — schema existed (`ghar_re.dish_variants`, 2 rows, dropped with schema), Core Spine register SP-F14 explicitly states v1 uses pool-refill only |
| Religious compatibility (Jain/vegan/halal/no-beef) | **Partial** — Jain only | report 04 §4 — Jain is a real hard filter; vegan exists as a schema value absent from the live scoring engine's diet enum; halal not implemented anywhere; no-beef/no-pork is prose-only in the Core Spine |
| Member segment nodes (INFANT/TODDLER/DIABETIC_ELDER/POSTPARTUM/FITNESS/FASTING) | **Deprecated / reimplemented as `lifecycle_stage`** | report 08 "Not-implemented" summary — no `MemberSegment` node/table by that name; `lifecycle_stage` (derivation.py) covers a differently-scoped subset (infant/toddler/pregnancy/elder/teen/school_child); health-condition dish implications (BP/diabetes/kidney/liver) explicitly **PARKED** by the spine itself (SP-F18) |

## E. Knowledge Base (RE-DOC-02 §4-5, Core Spine) — see report 05 for full detail

| Requirement | Status | Evidence |
|---|---|---|
| Weather-to-food affinity mapping | **Implemented** for 3 conditions × golden sample; unverified at full-catalogue scale | report 05 §6 |
| Home-state vs current-city overlay | **Implemented** | report 08 item 4 — `cohort_intel.py`'s migration-overlay fusion |
| Comfort heroes | **Implemented, end-to-end** | report 05 §5 — KB table → resolver → scoring lookup, with a disclosed real-catalogue name-mismatch fix |
| Festival calendar boost | **Missing** | report 03 dim 16 — no field anywhere, only a boost-table usage-tag option with no confirmed seed rows |
| Region×slot×season PRIOR table (full population) | **Deferred, spec self-confirms** | report 05 §1 — Core Spine's own register: SP-F10, "OPEN," explicitly "not done in v1.0," only 3 illustrative cells shown |
| Signature scores (graded, full catalogue) | **Partial** | report 05 §3 — real 6-band scale + 63-dish WP-21 curation pass (AI-assigned, self-flagged "spot-check not full review"), not the full 802-810-dish catalogue |
| Research → executable config traceability | **Mixed** | report 05 §4 — KB-authored tables (comfort heroes, zone map, sig bands) ARE live; standalone curated CSVs (region affinity, synonyms, aliases) are real but terminate at the seed/build layer, one hop short of the live engine |

## F. Synergies (Phase 9) — see report 08 for full matrix

9 claimed cross-module interactions checked; **6 confirmed as real code-level fusion** (weather×region, household×member/lifecycle, cohort×class/migration, cold-start×research-priors, region×comfort-hero, Q15×gain), **1 partial/additive-only** (weather×household — same BASE sum, no joint function), **2 not implemented** (ingredient×substitute — spec self-defers as SP-F14; pairing×full-context — not implemented and not actually claimed as v1 scope by the frozen spine beyond the veg-day swap).

## G. Database & Seed Data (Phases 6-7) — see reports 06-07 for full detail

| Requirement | Status | Evidence |
|---|---|---|
| Real production dish/ingredient/cuisine/tag/combo catalogue | **Implemented, production-scale** | report 06 §1 — 802 dishes, 191 ingredients, 65 cuisines, 111 tags, 109 combo rows, ETL'd deterministically, ~99-100% coverage vs source |
| RLS on every RE-relevant public table | **Implemented** | report 07 §3 — all 8 checked tables have both `ENABLE ROW LEVEL SECURITY` and a `CREATE POLICY` |
| Dish-ontology alias seeding (WP-19, 23 batches) | **Partial / uncertified** | report 06 §4 — 786 rows committed, only 37 (batch 1, 4.7%) have a Founder-signed execution certificate (CERT-027); batches 2-22 are DESIGNED-not-CERTIFIED per the WP lifecycle rule |
| Legacy re_engine reference/cohort seeds | **Deprecated (schema dropped)** | report 06 §2 — ~3,000+ rows (incl. 2,952 cohorts), dead as of migration 047, historical record only |
| ghar_re golden-sample seeds | **Deprecated (schema dropped, was always disclosed-synthetic)** | report 06 §3 — 736 rows, `data_source='ai_generated'`, never claimed as production data, schema dropped by migration 050 |
| CSV research material → DB ETL | **Partial** | report 06 §5 — 4 files (`ingredient_aliases_v2.csv`, `term_synonyms_v2.csv`, `recipes_v1.json`, `dish_images_v1.json`, ~1,100+ rows/records combined) never reach any ETL path |
| Orphaned tables cleanup | **Not done** | report 07 §2 — ~11 tables with zero app-code references (`addon_slots`, `context_log`, `coverage_gap_log`, `derivation_conflicts`, `etl_job_runs`, `feature_flags`, `push_notification_logs`, `safety_gate_log`, `weather_cache`, `interaction_events_`, `suggestion_logs`/`suggestion_logs_`) |

## Traceability rollup (counts across all sections above, ~55 discrete requirements traced)

| Status | Approx. count | % of traced requirements |
|---|---|---|
| Implemented (fully or with minor caveats) | ~24 | ~44% |
| Partial | ~11 | ~20% |
| Deprecated / reimplemented differently (not a gap — a different, evidenced design choice) | ~10 | ~18% |
| Missing | ~6 | ~11% |
| Deferred (spec itself tags as future work) | ~4 | ~7% |
| Stub | ~2 | ~4% |
| Unknown (not verifiable from repo evidence) | ~2 | ~4% |

Note: rows can appear in more than one conceptual bucket (e.g. "deprecated" items are also, from
spec-generation-1's point of view, "missing" — they are counted once, under "deprecated," because a
verified replacement mechanism exists and doing the same job, which is a materially different finding
from a true gap). This rollup is a qualitative synthesis of reports 02-09, not an independently
re-counted database query — treat the percentages as directionally reliable, not exact.
