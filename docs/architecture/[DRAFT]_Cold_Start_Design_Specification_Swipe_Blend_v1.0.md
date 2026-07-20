# Cold Start Design Specification — Day-1 Swipe Blend

**Status:** DRAFT — pending Founder sign-off
**Version:** v1.0
**Date:** 2026-07-17
**Origin:** FD-07 (ratified: interim neutral-prior fallback, refine fast via real usage), OB-07 (onboarding swipe capture)
**Purpose:** Define, precisely, how the ~10 dish swipes a user makes during onboarding affect their very first generated weekly plan — before this gets built, not after.

## 1. The core design decision: no new mechanism

The temptation is to invent a new "blend formula" combining cohort priors and swipe signals. This spec deliberately does **not** do that. Instead:

**OB-07 swipes are just early interactions.** They get written to `interaction_events` the moment they happen (already decided). The existing weight ladder (RE-DOC-03, ratified FD-02) already knows how to shift weight from cohort-based to history-based scoring as `interaction_count` rises. A user who completes ~10 swipes during onboarding has, by the time their first plan is generated, already crossed from the "0 interactions" tier into the "1–10 interactions" tier — with no new code, just by the existing mechanism counting what already happened.

This means: **swipes don't need a bespoke blend rule — they need to correctly count as history**, and the existing formula does the rest.

| Tier | Interaction count | Cohort | Content | History | Context | Explore |
|---|---|---|---|---|---|---|
| Day 0 (before any swipe) | 0 | 55% | 20% | 0% | 15% | 10% |
| Right after onboarding (~10 swipes) | 1–10 | 35% | 25% | 15% | 15% | 10% |

The first plan a user ever sees is generated at the *second* row, not the first — it already carries a real, if small, personal signal.

## 2. What "history" means with only ~10 data points

`PersonalHistory` already computes a cosine similarity between the user's accumulated taste vector and a candidate dish's genome vector (RE-DOC-02/03). This spec makes one thing explicit: **this same computation runs unmodified at n=10 as at n=200.** No special-case sparse-data math is introduced. The weight ladder already accounts for low confidence at low interaction counts by giving history only 15% weight at this tier — the *safety* against over-trusting 10 data points is the weight, not the formula.

## 3. Edge cases (addressed explicitly, not left implicit)

- **Fewer than ~10 swipes (user skipped most of OB-07):** interaction count stays lower, naturally keeping the user closer to the Day-0 weights. No separate handling needed — the ladder already degrades gracefully.
- **Contradictory swipes** (liked and disliked very similar dishes): produces a low-magnitude, noisy taste vector. `ContentMatch` naturally returns near-neutral scores for a noisy vector — this is treated as correct behavior, not a bug to special-case. Worth monitoring once real usage exists, not solving speculatively now.
- **Swipes concentrated in one meal class** (e.g. user only swiped on breakfast dishes shown): history signal exists for breakfast-class scoring but is genuinely absent for lunch/dinner slots in the same first plan. The blend must be applied **per class, not globally** — a user's first breakfast slot may already show personal signal while their first dinner slot still runs close to pure cohort. This is stated explicitly here so it isn't accidentally implemented as one global weight applied everywhere.

## 4. Confidence

No new confidence formula. FD-03's approved clamp (Day-0 max 0.65) and the existing confidence bands (0.55–0.72 for the 1–10 interaction tier) apply unmodified — confidence rises because the tier changed, not because of a new calculation.

## 5. Success metric and validation

No new metric. This uses the same Day-0/Day-90 acceptance rate already named in DOC-01 §07 as the MVP's go/no-go measure. Concretely: once real users exist, compare first-plan acceptance for swipe-informed users against a hypothetical neutral-only baseline, as evidence for whether the interim fallback (FD-07 Option b) is working — this becomes the trigger for revisiting FD-07, not a fixed timeline.

## 6. Future considerations — event weighting (explicitly deferred, not decided)

> **CORRECTION (2026-07-18):** This section's conclusion — "MVP treats all events
> equally, differentiated weighting deferred" — is **superseded**. It re-decided
> something already settled: DOC-P3-03 §16/LF-E04 already specifies a
> differentiated, `[CONFIRMED]`, founder-approved event-weight model, ratified in
> the original June 2026 business logic specification, matching the live
> `re_event_weights` table exactly:
>
> | event_type | weight |
> |---|---|
> | dish_cooked | +0.80 |
> | dish_locked | +0.60 |
> | dish_rated_5star | +0.60 |
> | dish_accepted | +0.40 |
> | dish_rated_3star | +0.00 |
> | dish_rated_1star | −0.30 |
> | dish_swiped_past | −0.10 |
> | dish_not_today | −0.10 |
>
> Differentiated event weighting is not a future consideration — it already
> exists and should be trusted as-is. Source: `[ACTIVE]_Canonical_RE_Architecture_
> Final_Review_v1.0.md` §5. Per GOV-02, this section is left below unedited as
> the historical record — it is superseded, not deleted.

MVP treats every interaction event type — swipe like, swipe dislike, cooked, skipped, repeated, saved, shared, favourite, removed, never-again — as contributing equally to `interaction_count` and to the taste vector. A "cooked" signal and a single onboarding swipe currently count the same.

This is a known simplification, not an oversight. Differentiating event types by weight (e.g. "cooked" should probably count for more than "swiped left once") is a reasonable future direction, but assigning specific weights now — with zero real usage data to justify any particular number — would be inventing a value rather than deriving one, which this project's own governance explicitly avoids (AI-01: no assumptions, config not hardcoded without basis).

Interaction count and taste vector contribution are conceptually separate. MVP intentionally treats them identically for simplicity. A future version may independently weight event influence on the taste vector without changing interaction-count progression.

**Decision for MVP:** all events weighted equally. **Explicitly left open for later:** a differentiated event-weighting model, to be designed once real interaction data exists to inform what the weights should actually be — not before. This should become its own small spec when that time comes, not a retrofit into this one.

## 7. What this spec deliberately does not do

- Does not introduce a new database table, column, or algorithm.
- Does not attempt to make cold start "smarter than the data supports" — 10 swipes remain 10 swipes, weighted accordingly.
- Does not resolve FD-07's longer-term question (whether to eventually source real cohort-prior research) — that stays open, tracked separately.
- Does not implement differentiated event-type weighting (see §6) — deferred by design.

## Founder Sign-off

Approve this specification as the standard for implementing the swipe-blend step of the cold-start plumbing task: _______________________ Date: ___________
