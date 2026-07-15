# REPO-CERT-016 — WP-8F Runtime Mapping Blocker (STOP) v1.0

**Status:** ACTIVE — Investigation Certificate (schema-mapping proof; **STOP** before implementation). No code, schema, migration, seed, validation-SQL, security, or frozen-document change; no live-DB write.
**Version:** v1.0
**Date:** 2026-07-15
**Placement:** docs/project-history/certificates/[ACTIVE]_REPO-CERT-016_WP-8F_Runtime_Mapping_Blocker_v1.0.md
**Attests:** [ACTIVE]_WP-8F_Runtime_Adapters_Blocker_Report_v1.0.md
**Dependencies:** REPO-CERT-015 (WP-8E), REPO-CERT-014 (WP-8D); DOC-P3-03 §06/§07/§08; migrations 002/003/008/009/011/012/021/022/024; seed 104.

---

## Certification

WP-8F began with the mandatory step: **prove every `CandidateRepository` mapping from the canonical
schema before writing code.** The proof was executed against the live migration + seed sources. It
**failed the gate**: four `DishCandidate` fields the WP-8D engine requires have **no provable
canonical source**, plus one read-adapter gap. Per the WP-8F rule ("If ANY schema mapping cannot be
proven, STOP … Do NOT continue past uncertainty") and repository governance (no invented mappings,
no fabricated defaults), implementation is **HALTED**. This certifies the investigation and the STOP.

## Blockers (evidence-backed; full detail in the work package)

1. **BLOCKER-8F-01 — variety dimensions `cuisine_family`, `main_ingredient_class` (LF-F01).** Canonical
   `tags.dimension` (seed 104): cooking_method ✓, texture ✓ — but **no cuisine_family** (only
   `cuisines.cuisine_group`/`parent_cuisine` via `dishes.cuisine_id`, ambiguous; `cuisine_family`
   column is on `re_meal_classes` (003:47), class-level) and **no main_ingredient_class** (nearest
   `dish_category`, semantically distinct).
2. **BLOCKER-8F-02 — religious meat markers halal/no_beef/no_pork (LF-D04, ingredient-level, safety).**
   `ingredients` (002) has is_veg/is_vegan/is_jain_excluded but **no beef/pork/halal marker**; no meat
   tag dimension. Only `jain` is supported.
3. **BLOCKER-8F-03 — dish `seasonal_affinity` (LF-E05).** No such column anywhere (008+022 confirmed);
   `weather_affinity` ≠ season; `ingredients.seasonal_peak[]` would need an undocumented aggregation.
4. **BLOCKER-8F-04 — cohort average taste vector (LF-E03 cold start).** `user_taste_vectors` is
   per-user; no cohort-level taste-vector table exists.

Each requires a Founder/architect decision (several imply schema evolution → SER, which is outside
WP-8F's "no migration change" scope). RE-DOC-02 (genome dimensions) might resolve 8F-01/8F-03 but is
`.docx`/binary and unreadable here — a ruling or Markdown excerpt is required; not guessed.

## Basis (executed this session)

- Read canonical schema: migrations 002 (tags/ingredients), 003 (re_meal_classes), 008 (dishes), 009
  (dish_tags/dish_ingredients), 011 (plan tables), 012 (interaction_events), 021 (cuisines +
  dishes.cuisine_id), 022 (dish attrs), 024 (regional affinity); seed 104 (canonical tag dimensions).
- Cross-checked against WP-8D `DishCandidate` and DOC-P3-03 LF-D04/E03/E05/F01/F02.
- Re-ran `deno task verify` → **62 passed / 0 failed** (no code changed).

## What was NOT done (blocked by rule)

`CandidateRepository`, remaining read adapters (taste/cohort-average is 8F-04-blocked), the
`/v1/onboarding` + `/v1/recommendations` endpoints (depend on the full engine), and all live-DB
validation. No runtime code was written — the mapping proof halted the work before implementation.

## Honest note on live-DB validation

Even without the mapping blockers, write-path validation must target a **disposable/staging** Supabase
(WP-6E clean-room pattern), never test writes into the canonical **production** dataset
(`profiles.id` FKs `auth.users`). Recommended for WP-8F once unblocked.

## Consequence

**WP-8F is BLOCKED.** The goal (make the backend executable against the real schema) cannot be met as
scoped until decisions 8F-01…8F-04 are made. The WP-8E orchestration layer, WP-8D engine, and
WP-8A–8C foundation remain intact and green (62 tests). Deploy discipline unchanged; DOC-P4-02 stays
DRAFT.

## Critical Self-Review

- **Guessed any mapping?** No — each gap has its exact absent/ambiguous schema location.
- **Read live schema, not memory?** Yes — migrations + seed 104 this session.
- **Safety honored?** Yes — refused to fabricate the LF-D04 religious markers or the LF-F01 variety
  dimensions that feed safety-critical filtering.
- **Existing system?** Untouched; verification still green.

## Versioning & Placement

v1.0, docs/project-history/certificates/ per the Placement Rule; naming per WP-5AA.

## Founder Countersignature (decisions 8F-01…8F-04)

Founder/architect rulings to unblock WP-8F: _______________________ Date: ___________
