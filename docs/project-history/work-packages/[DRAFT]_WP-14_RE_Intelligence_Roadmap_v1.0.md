# [DRAFT]_WP-14_RE_Intelligence_Roadmap_v1.0

**Status:** DRAFT — assessment and phased plan, grounded in RE-DOC-11/12 and this session's own direct findings. No ML code written; this is a proposal, not an implementation. A companion HTML visual is published alongside this document.
**Version:** v1.0
**Date:** 2026-08-02
**Placement:** docs/project-history/work-packages/[DRAFT]_WP-14_RE_Intelligence_Roadmap_v1.0.md
**Builds on:** RE-DOC-10 (Production Implementation Plan), RE-DOC-11 (Extensibility Review), RE-DOC-12 (Status and Roadmap, 2026-07-29 ground-truth audit), this session's S57 (decision-trace feature), S59 (legacy engine deletion), and today's Kanda Bhaji root-cause finding.
**Governance basis:** Core Spine FROZEN doc (`docs/architecture/ghar-re/ghar_re_v1_0_core_spine_FROZEN.md`) — consumed, not modified. RE-DOC-11's scope discipline applies here too: nothing below proposes moving the service boundary (Python RE, stateless, Edge Functions own DB/auth stays fixed).

---

## Executive Summary

Asked to assess the recommendation engine as a "lead product engineer from Zomato/Swiggy/Netflix" and propose class-based/ML changes to make it "really intelligent." The honest, evidence-grounded answer: **the architecture for this evolution is already designed — RE-DOC-11 §7/§8 specifies a formal `ScoringModule` protocol and an `ML integration` pattern where a learned module plugs into the exact same registry as a hand-authored one, with zero changes to the composition loop.** What's missing is not architecture vision, it's two concrete, sequenced things: (1) the class-based registry itself isn't implemented yet — today's scoring functions (`m_palette`, `m_weather`, `sig`, etc. in `ghar_re_core/scoring.py`) are ad hoc functions manually summed in `base()`, not yet the pluggable modules RE-DOC-11 calls for; (2) **there is zero feedback data to train anything on** — `public.feedback_events` has 0 rows (confirmed this session), no feedback UI exists, and the only signal captured today is "a plate was served," never "a user liked/rejected it."

**The single most important thing a real Zomato/Swiggy/Netflix engineer would say here: you cannot skip to ML.** Every one of those companies' recommendation systems started as rule/heuristic engines and only introduced learned ranking once real interaction logs existed in volume — Netflix's own public engineering writing is explicit that collaborative filtering needs interaction density, not just a catalogue. Proposing a model today would mean training on fabricated or synthetic labels, which directly violates this repo's own standing rule against inventing data (FD-11, cited elsewhere in this codebase) and would produce a model that's confidently wrong. The credible plan is sequenced: **formalize the class-based module registry first (cheap, no data needed, unlocks everything else) → instrument real feedback (cheap, unlocks the ability to ever justify ML) → THEN add a learned module using the same registry (RE-DOC-11 §8's own design) once there's something real to learn from.**

This WP proposes that sequence concretely, cites every claim to a document or a piece of code actually read this session, and flags (without silently fixing) the concrete data gaps found along the way.

---

## 1. What's actually implemented today (verified, not assumed)

| Layer | Status | Evidence |
|---|---|---|
| Hard filters (A1–A5: diet, jain, allergen, weaning, fasting) | Implemented, tested | `ghar_re_core/scoring.py::eligible()`, `ghar_re_core/tests/test_pipeline.py` |
| BASE scoring, `Σ W_k · conf_k · m_k(x)` | Implemented as hand-written functions, not a registry | `ghar_re_core/scoring.py` — `m_palette`, `m_weather`, `m_slot`, `m_season`, `m_age`, `m_household`, `sig`, `prior_boost` all called directly inside `base()`, not through any protocol/interface |
| Pairing guardrails + MMR-style Assemble-7 | Implemented, tested | `ghar_re_core/pairing.py::build_plates`/`assemble_7` — greedy best-score-first, no-duplicate guard, discovery-dial cap |
| Explainability (`contributions[]`) | Implemented per RE-DOC-11 §6's own recommendation | `recommendations/handler.ts` passes through `contributions[]` as-is; verified live in this session's own `recommendation_events` queries |
| Per-request decision trace (funnel + near-miss alternatives) | Implemented this session (WP-12), DB half live, RE half not yet deployed to Fly.io | See WP-12 |
| Real 810-dish catalogue | Implemented, migrated from the 39-dish sample (Phase G, prior session) | `ghar_re_service/data/bundle/catalogue.json` — 810 entries, confirmed by direct count today |
| Two engines / legacy TypeScript RE | **Resolved this session** — deleted as confirmed dead code (S59) | RE-DOC-12 §Executive-Summary flagged this as an undecided governance gap on 2026-07-29; this session independently found and removed the same dead cluster before reading RE-DOC-12, then confirmed the finding matches |
| Formal `ScoringModule` protocol + registry (RE-DOC-11 §7) | **Not implemented** | No `Protocol`/interface class exists in `scoring.py`; modules are plain functions, weights are read ad hoc from `CONFIG` inside `base()` |
| Feedback capture | **Not implemented** | `public.feedback_events` = 0 rows (this session's live query); no Edge Function writes to it; no mobile UI calls one |
| Learned/ML ranking of any kind | **Not implemented, and correctly so — no data exists yet** | See Executive Summary |

## 2. Why "class-based first, ML second" is the professionally correct order

- RE-DOC-11 §7 already specifies the target shape: `ScoringModule.score(dish, profile, context) -> ModuleResult`, a static registry BASE composition iterates over. Adding a signal becomes "append to the registry + a config weight," never touching the composition loop.
- RE-DOC-11 §8 already specifies exactly how ML plugs in: a learned module (embedding similarity, a preference model, a future ranker) **implements the identical protocol** — the registry doesn't know or care whether a module is a formula or a loaded model artifact. This is precisely the "class-based approach" the Founder asked for — it's already the documented design, just not yet built.
- RE-DOC-11's own "What NOT to over-build" section explicitly warns against speculative infrastructure nobody needs yet. Building an ML pipeline before the registry exists, and before feedback data exists, would be exactly that.

## 3. Concrete data/config gaps found this session (flagged, not silently fixed)

Recommendation quality today is bounded by data completeness, not just algorithm sophistication — worth fixing before any scoring changes, since a smarter algorithm over broken inputs is still broken:

1. **West-MH rain comfort hero ("Kanda Bhaji") doesn't exist in the real 810-dish catalogue** — confirmed by direct search; no close-name match. `ghar_re_core/knowledge.py::COMFORT_HERO_MAP`'s West-MH rain entry is a silent no-op in production. A second entry (`Pithla-Bhakri` vs. the real catalogue's `Pithla Bhakri`) has a hyphen/space mismatch with the same effect. Flagged with a comment at the data source this session (not fixed — picking a replacement dish is a domain call).
2. **`public.household_context` is provisioned but entirely unwired** (RE-DOC-12 §3.3) — every recommendation request still uses either the caller-supplied context or a hardcoded `DEFAULT_CONTEXT` (dinner/monsoon/Thursday), never "this household's actual recent context."
3. **Allergen hidden-derivative table is inert** (`ghar_re.allergen_hidden_derivatives`, `is_active=false`) — the Core Spine's own §D states allergen filtering is "not safe-complete" until this lands, and marks it pre-launch-blocking (SP-F13, `OPEN — PRE-LAUNCH`).
4. **Fallback plate is one hardcoded pan-India dish**, not the per-zone cached default set RE-DOC-10 §11 specifies (RE-DOC-12 §3.4) — every RE failure serves the same Moong Dal Khichdi regardless of region.
5. **"Refresh" is fully deterministic** — already drafted as WP-8G this session; directly relevant here because it's the single biggest "does this feel intelligent" lever a user actually experiences, and needs no ML, just the exclusion-list contract change WP-8G already proposed.

## 4. Proposed phased roadmap

**Phase 0 — Data foundation (no ML, no scoring changes; prerequisite for everything after).**
Wire `feedback_events` end-to-end: an Edge Function to write accept/reject/swap signals, and a minimal mobile UI to capture them (this is also WP-11's own flagged P1 gap — one build closes both). Wire `household_context` (item 2 above) so context reflects reality instead of a hardcoded default. Fix or explicitly resolve the two comfort-hero data gaps (item 1) with domain input.
*Done when:* real (accept/reject) signals exist in `feedback_events` for actual served recommendations, and context is read from real history for a returning user.

**Phase 1 — Formalize the class-based module registry (RE-DOC-11 §7, no ML yet).**
Introduce a `ScoringModule` protocol in `ghar_re_core`; migrate `m_palette`/`m_weather`/`m_slot`/`m_season`/`m_age`/`m_household`/`sig`/`prior_boost` into registered module instances with config-driven weights, composed by a registry loop instead of hand-written summation in `base()`. Golden-master tests (already in place) are the regression guard — this must be provably score-neutral, a refactor, not a rescoring, verified the same way this session's own `decision_trace` work proved `with_trace` never changes served plates.
*Done when:* `base()` is a registry iteration, not a hand-written sum, and every existing golden-master/pipeline test still passes unchanged.

**Phase 2 — Variety/exploration (no ML; needs only served/rejected counts, not labels).**
Implement WP-8G's `exclude_dish_ids` contract extension. Add a lightweight, non-learned exploration mechanism — e.g. epsilon-greedy rotation among near-tied top plates, or a simple Thompson-sampling-style class-level bandit seeded from cohort base rates (the legacy engine's old `RE-Visual-03` roadmap already sketched this shape; still directionally valid even though that specific engine was retired). This is the most user-visible "feels intelligent" improvement available before any ML — refresh stops being deterministic.
*Done when:* two consecutive "Refresh" calls for the same household/context can legitimately differ, and the mechanism is explainable via the existing `decision_trace`.

**Phase 3 — First learned module (ML, gated on Phase 0 producing real volume).**
Once `feedback_events` has meaningful density (a concrete threshold — e.g. a few thousand fleet-wide labeled events, or ~20+ per active household — should be set by whoever owns the data, not guessed here), add a `s_pref` `ScoringModule` — start with the simplest model that could work (logistic regression or a small gradient-boosted tree over structured features: cuisine, class, spice level, existing module scores; label = accepted/rejected). It plugs into the Phase 1 registry with **zero changes to the composition loop**, per RE-DOC-11 §8's own design. Treat the model artifact like catalogue/config — versioned, immutable, loaded at startup.
*Done when:* a real held-out evaluation (not a training-set metric) shows `s_pref` improves acceptance rate over the rule-only baseline, and it can be disabled via config with zero code change if it doesn't.

**Phase 4 — Collaborative signal, only once density justifies it.**
Two-tower retrieval or ALS-style collaborative filtering, gated on interaction density crossing a real threshold (the retired legacy engine's own roadmap visual estimated CF density > 1% as its trigger — a reasonable industry-standard bar, not something to hit before it's earned). Out of scope to plan in detail now; premature to design before Phase 3 even ships.

## 5. What this WP deliberately does NOT do

- Does not write any ML training code, model artifact, or scoring change — there is nothing to train on yet (Executive Summary).
- Does not touch the service boundary, the Python/Deno split, or the frozen contract's core shape — matches RE-DOC-11's own scope discipline.
- Does not silently fix the comfort-hero data gaps (§3.1) or pick exploration hyperparameters (§Phase 2/3 thresholds) — these are domain/product judgment calls, flagged for the Founder, not guessed.
- Does not repurpose the deleted legacy engine's cohort/bandit design wholesale — its `RE-Visual-03` roadmap is cited only where directionally still reasonable (Phase 2/4's shape), not adopted as-is, since it described a different, now-removed engine.

## 6. Critical Self-Review

- Every "not implemented" claim in §1 is backed by a direct read of `scoring.py`/`pairing.py`/a live DB query this session, not restated from a prior document.
- The Phase 3 density threshold is explicitly left unset rather than inventing a number — matching this repo's own standing rule against fabricated specifics.
- This plan leans heavily on RE-DOC-11, which is itself a review document, not a ratified Founder decision to build any of this — §1–§9 of RE-DOC-11 are recommendations the Founder has not yet signed off building. This WP does not treat RE-DOC-11 as authorization; it treats it as the best available design reference for HOW to build these things once someone decides to.
- No effort/timeline estimates are given for the same reason WP-11's didn't — not independently validated, omitted rather than guessed.

## 7. Versioning & Placement

v1.0 — initial draft. Companion visual: `docs/visuals/[ACTIVE]_RE-Visual-04_Live_Engine_Architecture_and_Roadmap_v1.0.html`, built for the current live Python engine specifically (the existing `RE-Visual-03_Evolution_Map.html` describes the now-deleted legacy TypeScript engine's roadmap and was left untouched, not silently repurposed, since it's a historical record of a different system).

## Founder Sign-off

