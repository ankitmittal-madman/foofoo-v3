# Canonical Recommendation Engine Architecture — Final Review

**Status:** Final architectural review, pre-LF-C
**Date:** 2026-07-18
**Method:** First-principles design (product outward, schema never consulted until Part 3), then compared against implementation. All primary sources read in full this session: RE-DOC-01 through 05 (`.docx`, decoded), the complete Founder Decision Register, the complete DOC-P3-03 Business Logic Specification. `KNOWLEDGE.html` (298KB) was **not** read in full — disclosed, not silently skipped.

---

## 1. Executive Summary

FooFoo's RE was designed, from the very first document (RE-DOC-01, June 2026), as a genuinely well-architected system: isolated module, versioned API, four concentric layers, a 4-state evolution model with a real ML upgrade path, and a feature store built from Day 1 specifically so nothing is lost when ML arrives later. The design documents are not the problem. **What happened between design and database is where things drifted — and it drifted in two different directions, one already caught, one newly found here.**

The newly found direction: **`re_event_weights` was never a rogue table.** It is `[CONFIRMED]`, founder-approved, fully specified in DOC-P3-03 §16, with the exact 10 values (`dish_cooked +0.80`, `dish_locked +0.60`, `dish_accepted +0.40`...) verified live in the database. The Canonical Planning Model's "treat all events equally for MVP, differentiated weighting deferred" decision — made in this same project, weeks later — **directly contradicts a decision that already existed and was already implemented.** This is the single most important correction in this review.

**Verdict: C — significant, precisely-scoped redesign**, unchanged in category from the prior pass. The precomputed-lookup pattern (`re_weekly_class_plans`, `re_household_addon_plans`) remains the core structural issue. What's new here is confirmation, from primary sources, of *why* it exists (spreadsheet import — RE-DOC-03/05 never describe it, it appears nowhere in the design docs) and a corrected, evidence-based answer on event weighting.

---

## 2. Canonical Recommendation Engine Vision (first principles, no schema consulted)

The RE exists to answer one question well: *what should this household eat right now, given who they are, what they've done before, and what moment they're in* — and to keep answering it better as it learns, without the app ever needing to know how. Three commitments follow from that: the RE is sovereign (a product, not a feature); it reasons in layers that build outward from food itself (genome) through safety (graph) through the household (composition + conditions) to the moment (context); and it evolves through swappable scoring stages, never a rewrite, so today's rule-based MVP and tomorrow's ML stack share one contract.

---

## 3. Canonical Architecture

```
Research (evidence, not truth)
   |
   v
Knowledge Extraction -> genome dimensions, class taxonomy, condition vocabulary
   |
   v
Reference Metadata Layer -> meal classes, addon classes, dish options, context
   multipliers, variety rules (small, stable, versioned; owns "what things ARE")
   |
   v
Composition + Planning Semantics Layer -> household facts (composition, region)
   + independently-firing conditions -> genome-space attributes (FD-15)
   |
   v
Candidate Generation -> class filter -> hard constraints (never bypassed)
   |
   v
Scoring -> FinalScore = weighted(CohortPrior, ContentMatch, PersonalHistory,
   ContextFit, ExplorationBonus) -> PenaltyTerms, weights from the interpolated
   ladder (owns "what things ARE WORTH, right now, for this user")
   |
   v
Variety Re-ranking (MMR) -> Safety Gates (run twice: pre-score hard filter,
   post-rank final check -> RE-06)
   |
   v
Runtime State -> per-user, write-heavy, correctly grained (taste vectors,
   bandit state, variety window, cold-start confidence)
   |
   v
Learning Loop -> feature store logging from Day 1, weekly cluster/recalibration
   CRONs (State C/D), version-gated promotion (shadow mode, 72h, offline eval)
```

Layer ownership, stated plainly: reference metadata owns *what things are*. The composition + semantics layer owns *who this household is and what they need*. Scoring owns *what's worth showing, right now*. Runtime state owns *what this specific user has actually done*. Nothing above should ever store the *output* of a planning decision as if it were one of these four kinds of fact — that collapse is exactly what happened to two tables (§8).

---

## 4. Persistence vs. Computation Philosophy — answered per artifact

| Artifact | Verdict | Why |
|---|---|---|
| **Weekly meal plans** | **Derive live** (currently: wrongly persisted) | RE-DOC-03/05 never describe a precomputed weekly plan — LF-B02's own query pattern reads `re_weekly_class_plans` as if it were metadata, but nothing in the design docs justifies storing the *output* of class assignment rather than the *rule* for deriving it |
| **Addon planning** | **Derive live** (currently: wrongly persisted) | Same reasoning — RE-DOC-02 §04's add-on table is a design *specification* (segment — addon class), not a precomputed *per-household plan*; `re_household_addon_plans` conflates the two |
| **Routing (absorb/swap/add)** | **Derive live** | Confirmed already in FD-15/SER-004 — a condition's channel varies per household by design; persisting it would be storing an answer that's supposed to change |
| **Scoring** | **Derive live, always** | This is a request-time computation by definition (RE-DOC-03 §02) — never a candidate for persistence |
| **Confidence** | **Derive live, cache the inputs** | The formula (LF-A08) is deterministic and cheap; only its *inputs* (interaction_count, onboarding completeness) need to persist, which they correctly do (`user_re_state`) |
| **Exploration (bandit)** | **Persist, but re-grained** | This is the one artifact that *should* persist state — Thompson Sampling requires α/β to accumulate over time. The problem isn't persistence, it's the grain (§8) |

**The general rule this produces:** persist facts and accumulating state (what happened, what a user's α/β currently are); derive plans and assignments (what should happen now). `re_weekly_class_plans`, `re_household_addon_plans`, and (differently) `re_persona_assignment_rules` violate this by persisting derived answers instead of the rules that produce them.

---

## 5. Event Learning Reassessment (revised finding)

**Ignoring the previous Founder Decision, from first principles: should these events carry equal learning value?** No — plainly no, and this project already answered this correctly once. `dish_cooked` (a household actually made the dish — the strongest possible signal) and `dish_swiped_past` (a half-second glance) cannot reasonably carry the same weight. DOC-P3-03 §16/LF-E04 already encodes this correctly: cooked +0.80, locked +0.60, rated-5★ +0.60, accepted +0.40, rated-3★ 0.00 (neutral), rated-1★ −0.30, swiped-past −0.10, not-today −0.10 (with its own separate decay). This is a well-designed, graduated signal hierarchy — not arbitrary, and not something that needs redesigning.

**What actually needs to happen: correct the record, not the architecture.** The Canonical Planning Model's §6 ("MVP treats all events equally... differentiated weighting explicitly deferred") should be marked superseded by DOC-P3-03's pre-existing, earlier, `[CONFIRMED]` event-weight table — not the other way around. **This is a documentation correction, not an engineering change.** `re_event_weights` should be trusted and used exactly as it stands.

---

## 6. Bandit Learning Reassessment

**Is per-user-per-dish the correct grain?** Evaluated on the six named criteria:

- **Accuracy:** highest possible at this grain — no information loss.
- **Learning quality:** poor in practice for a new dish or a lightly-shown one — each (user, dish) pair starts at Beta(1,1) and needs many exposures to become informative; with ~800 dishes and a typical user seeing maybe 20-30 unique dishes in early weeks, most cells stay uninformative for a long time.
- **Storage:** the real problem — combinatorial ceiling in the billions at 10M-user scale (unchanged finding from the prior pass, now confirmed against RE-DOC-05 §01, which specifies the bandit is meant to serve *cold-start exploration*, a per-class or per-cohort concern, not a per-dish one).
- **Future AI capability:** a coarser grain (per meal-class, or per genome-cluster) generalizes faster — exploring "has this user tried a fermented-South-Indian dish" is more informative early than "has this user tried Idli specifically."
- **Operational complexity:** per-dish requires no aggregation logic; per-class/cluster requires a small mapping layer, modest added complexity.
- **Cold-start behaviour:** RE-DOC-05 State A explicitly describes exploration as **class-level** cohort-adjusted priors, not dish-level — meaning the design intent was already coarser than what got implemented.

**Verdict: redesign justified, not just because it could grow large, but because the current grain learns slower than the documented cold-start design intends.** Recommend re-grain to per-(user, meal-class) as the primary bandit unit, with per-dish tracking only once a class has accumulated enough signal to matter — this can be revisited, not decided finally, in LF-C/Phase 3 design.

---

## 7. Weekly Planning Reassessment

**Why does `re_weekly_class_plans` exist?** Tested against all four candidate explanations: not runtime optimization (no design document describes a performance reason to precompute); not a deterministic planning cache in the sense of "compute once, reuse" (the underlying inputs — day-type fit scores, variety cooldowns, cuisine rotation — are static per class, meaning the *rule* could run in microseconds at request time; there's nothing to cache); not intentional architecture (RE-DOC-03/05, the authoritative design documents, never mention this table or a precompute step for weekly plans — LF-B02 in DOC-P3-03 is the only place it's described, and it reads the table as if it were reference data, not as a deliberate caching decision). **By elimination and by the row-count signature (2,952 × 7 = 20,664, an exact cross-product) this is a spreadsheet import** — the workbook's own `Weekly_Class_Plan_v3` sheet, loaded as-is.

**Answer: A — compute live.** The inputs already exist as real metadata (`re_meal_classes`' own `weekday_fit_1_5`/`weekend_fit_1_5`/`cuisine_family`/`variety_cooldown_days` columns) — this is not a case of missing information requiring precomputation to fill a gap; it's a case of the answer being stored when the question-answering rule was sitting right there in the schema the whole time.

---

## 8. Table Classification (all 35, complete)

| Table | Classification |
|---|---|
| `dish_features` | Operational Cache |
| `never_list` | Runtime State |
| `not_today_suppression` | Runtime State |
| `re_addon_classes` | Canonical Metadata (pending vocabulary rename/cleanup, SER-005) |
| `re_addon_dish_options` | Canonical Metadata |
| `re_city_migration_overlays` | Canonical Metadata (unpopulated — reconcile with next row) |
| `re_city_overlay_config` | Configuration |
| `re_class_affinity_config` | Configuration (should merge — §9) |
| `re_class_dish_options` | Canonical Metadata |
| `re_cohort_class_priors` | Knowledge Base (unseeded by ratified decision, FD-07) |
| `re_cohorts` | Canonical Metadata (content pending FD-15 Phase 4 shrink) |
| `re_confidence_config` | Configuration (should merge — §9) |
| `re_context_multipliers` | Configuration |
| `re_dish_bandit_state` | Runtime State (grain requires redesign, §6) |
| `re_dish_regional_affinity` | Canonical Metadata |
| `re_engine_versions` | Operational Cache |
| `re_event_weights` | Configuration — **confirmed correct and intentional (§5)** |
| `re_festival_calendar` | Canonical Metadata |
| `re_household_addon_plans` | **Derived Output, currently mis-stored as Research Provenance** — retire from runtime path |
| `re_main_cohorts` | Canonical Metadata — **already correctly sized (5 rows)** |
| `re_meal_class_overlap_rules` | Canonical Metadata |
| `re_meal_classes` | Canonical Metadata |
| `re_nonveg_logic` | Canonical Metadata (naming: should be `re_nonveg_pattern`) |
| `re_persona_assignment_rules` | **Derived Output wearing a "rules" name** — 1:1 with personas, not generalizable logic |
| `re_personas` | Canonical Metadata (content pending FD-15 Phase 4) |
| `re_routing_rules` | Canonical Metadata |
| `re_scoring_config` | Configuration (should merge — §9) |
| `re_states` | Canonical Metadata |
| `re_subcohorts` | Canonical Metadata (content pending FD-15 Phase 4) |
| `re_variety_rules` | Configuration — model example, no change |
| `re_weekly_class_plans` | **Derived Output, currently mis-stored as Research Provenance** — retire from runtime path |
| `re_weight_ladder_config` | Configuration — model example, no change |
| `user_re_state` | Runtime State |
| `user_taste_vectors` | Runtime State |
| `variety_window_state` | Runtime State |

No table classified as "Should Not Exist" — every table has a legitimate concept behind it; the debt is in *where* a few of them sit, not in whether they should exist at all.

---

## 9. Comparison — Already Excellent / Minor / Debt / Founder Decision / Future Evolution

**Already Excellent:** `never_list`, `not_today_suppression`, `variety_window_state`, `re_weight_ladder_config`, `re_variety_rules`, `re_engine_versions`, `re_main_cohorts` (confirmed right-sized against FD-15), the RE's own module isolation and API-versioning discipline (RE-DOC-01), the four-layer scoring design (RE-DOC-02/03), the 4-state evolution model with a real ML path (RE-DOC-05).

**Minor Improvements:** merge `re_class_affinity_config`/`re_confidence_config`/`re_scoring_config` into one `re_config` table; rename `re_nonveg_logic` — `re_nonveg_pattern`; reconcile `re_city_migration_overlays`/`re_city_overlay_config`.

**Architectural Debt:** `re_weekly_class_plans` and `re_household_addon_plans` (derive live, don't store); `re_persona_assignment_rules` (same pattern, one layer removed); `re_dish_bandit_state` grain.

**Requires Founder Decision:** whether to derive weekly plans as part of LF-C's design phase now, or as its own SER immediately after (recommendation: now — LF-C touches this exact derivation logic anyway); whether the config-table merge happens before or after LF-C (recommendation: after — zero consumers depend on the current shape, no urgency).

**Future Evolution (already correctly deferred, not debt):** `re_personas`/`re_subcohorts`/`re_cohorts` content shrink (FD-15 Phase 4); `re_cohort_class_priors` seeding (FD-07, a research gap, not an engineering one).

---

## 10. Ideal Recommendation Engine Architecture

Unchanged from the prior pass's conclusion, now with primary-source confirmation: three layers (canonical reference metadata, unified configuration, correctly-grained runtime state), with planning as computation over the first and third, never a fourth, stored-output layer. The RE-DOC set already describes this ideal — the gap is entirely in two tables' storage decisions, not in the documented design.

---

## 11. Gap Analysis

| Gap | Root cause (confirmed via primary source) | Severity |
|---|---|---|
| Weekly plans precomputed | Not described in any RE-DOC; spreadsheet import, confirmed by exact row-count signature and absence from design docs | High — primary plan, affects every user |
| Addon plans precomputed | Same pattern, already known | High |
| Event weights "equal" decision | **Contradicts a pre-existing, `[CONFIRMED]`, implemented decision** (DOC-P3-03 §16) — a documentation error in a later session, not a schema problem | Medium — needs correcting on record, zero engineering change |
| Bandit grain | RE-DOC-05 describes class-level cold-start exploration; implementation went to dish-level | Medium-High at scale |
| Config fragmentation | Spreadsheet-tab inheritance (unconfirmed against a specific source, but shape strongly implies it) | Low |

---

## 12. Recommended Future Architecture

Fold the weekly-plan derivation fix into LF-C's design phase (both are "stop storing an output, start deriving it live" fixes, and LF-C will touch the same class/addon derivation surface anyway). Correct the Canonical Planning Model's event-weighting section on the record. Schedule the bandit re-grain and config-table merge as near-term, non-blocking follow-ups.

---

## 13. Migration Roadmap

1. **Immediate, docs-only:** correct Canonical Planning Model §6 to reflect that differentiated event weighting is already ratified and implemented (DOC-P3-03, `[CONFIRMED]`) — supersede, don't delete, per GOV-02.
2. **Fold into LF-C design:** weekly-plan and addon-plan derivation logic (SER-005 already scopes the addon side; extend to weekly plans).
3. **Near-term, independent, non-blocking:** bandit re-grain; config-table merge; `re_city_overlay_config`/`re_city_migration_overlays` reconciliation.
4. **Already scheduled, no new roadmap needed:** FD-15 Phase 4 (persona/cohort content shrink); FD-07 (cohort-prior research, if ever commissioned).

---

## 14. Founder Decisions Required

1. Confirm the event-weighting correction (§5) — this is a documentation fix with zero engineering impact, recommend approving now.
2. Confirm weekly-plan derivation folds into LF-C design (recommended) vs. its own SER.
3. Confirm bandit re-grain target: per-(user, meal-class) as primary, per-dish only once class-level signal is rich (recommended), or a different grain.
4. Confirm config-table merge timing: after LF-C (recommended, zero urgency) or before.

---

## Final Verdict

**C — significant, precisely-scoped redesign**, with one important correction to how the finding is framed: the RE's *design* documents (RE-DOC-01–05) are excellent and internally consistent — genuinely strong architecture, read in full and confirmed. The debt is entirely in the gap between those documents and two tables that were loaded as spreadsheet mirrors without a design document ever describing them that way, plus one documentation contradiction (event weights) that resolves in favor of the *older*, already-correct decision. Nothing here should shake confidence in the RE's fundamental design — it should sharpen exactly where the next SERs need to point.

**Honest disclosure, restated:** `KNOWLEDGE.html` was not read in full this session. If it contains additional RE design history not captured in RE-DOC-01–05 or DOC-P3-03, this review's conclusions should be revisited against it before being treated as fully final.
