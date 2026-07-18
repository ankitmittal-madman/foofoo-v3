# [ACTIVE]_SER-004_household_members_conditions_vocabulary_v1.0 — Schema Evolution Request

**Status:** ACTIVE — APPROVED (Founder decision, 2026-07-18, approved as finalized — including the §6 vocabulary exclusions/collapses and §5's derive-don't-persist routing decision, approved as correct, not a compromise to revisit).
**Version:** v1.0
**Date:** 2026-07-18
**Placement:** docs/governance/[ACTIVE]_SER-004_household_members_conditions_vocabulary_v1.0.md
**Type:** Schema Evolution Request.
**Author:** Claude (Engineering session, Phase 2 of FD-15).
**Implements in:** `database/migrations/033_household_members_conditions_vocabulary.sql` (+ rollback).
**Governance basis:** `[ACTIVE]_Founder_Decision_Register_v1.0.md` FD-15; `[ACTIVE]_Canonical_Planning_Semantics_Architecture_v1.0.md` §5/§7; `[ACTIVE]_Phase1_Persona_Decomposition_Catalog_v1.0.md` §3; `[ACTIVE]_Canonical_Planning_Model_v1.0.md` §1/§5/§9b.
**Review chain:** initial draft SER + Impact Matrix (this session) → independent Architecture Challenge Review (`Architecture_Challenge_Review_SER-004_v1.0.md`, external input) → Founder final decisions (this document).

---

## 1. Problem Statement

`household_members.segment` is a scalar `text` column constrained to exactly 8 values, forcing each household member into a single classification bucket. FD-15 ratified a Planning Semantics Architecture requiring each member to carry *multiple independent condition tags* simultaneously (a household member can be elderly **and** diabetic **and** recovering, at once) — the current schema architecturally cannot express this, and every compound case today would require a hand-written combination row (exactly the anti-pattern FD-15 eliminated at the persona layer).

## 2. Current State (live-verified 2026-07-18, not assumed from documentation)

Direct database introspection (`psql`, this session) confirms `household_members`:
```
segment text NOT NULL   -- no default
CONSTRAINT household_members_segment_check
  CHECK (segment = ANY (ARRAY['INFANT','TODDLER','SCHOOL_CHILD','DIABETIC_ELDER',
                               'POSTPARTUM','FITNESS_OVERLAY','FASTING_MEMBER','ADULT_STANDARD']))
```
Exact constraint name confirmed as `household_members_segment_check` (not assumed). **0 live rows** in `household_members` — no data-migration risk. `addon_slots.household_member_id` FK confirmed live, referencing `household_members.id` only (unaffected by any change to `segment`). No views, rules, or function bodies anywhere in the live database reference `household_members.segment` (confirmed via `pg_depend`/`pg_proc` introspection, not grep alone). `resolvers.ts` (the RE's live scoring path) does not read `segment` — consistent with WP-9's M-03 finding (LF-C/overlay derivation is 0% implemented).

A separate, richer, already-seeded vocabulary lives in `re_engine.re_addon_classes.segment` and `re_engine.re_household_addon_plans.segment` (free-text, no FK, no CHECK) — confirmed live to hold **exactly 20 distinct values**, sourced from the original research workbook (`Indian_Meal_Cohort_Persona_DB_v3.xlsx`) via `generate_re_seeds.py`'s `target_member_segment` field. This is the real target vocabulary; Phase 2 aligns to it rather than inventing a third one.

## 3. Repository Impact Analysis

Full Impact Matrix delivered in the prior session (Phase 2A). Headline: small runtime blast radius (nothing in the scoring path consumes `segment` today), moderate documentation blast radius (`DOC-P3-04`, `DOC-P3-06`, `DOC-P3-03` §LF-A09/§LF-C01 — tracked as future work, §13), low code blast radius (three TypeScript files: `orchestrator.ts`, `supabase-stores.ts`, `re/types.ts`).

## 4. Chosen Architecture

Convert `household_members.segment` (scalar `text` + CHECK) to `household_members.conditions text[] NOT NULL DEFAULT '{}'`, with a CHECK constraint enforcing containment against the finalized canonical vocabulary (§6), following the exact precedent of migrations `025`/`026` (`re_meal_classes.slot`/`meal_classes.slot` scalar→array conversion).

**Rename `segment` → `conditions`: CONFIRMED.** Matches ratified terminology used consistently across all four Planning Semantics documents; the column's type is changing regardless, so a migration is already required — renaming now avoids a second rename pass later.

## 5. Alternative Designs Considered (final)

Five options evaluated in the original review: status quo (rejected — cannot express multiple tags), `text[]` + CHECK (chosen), JSONB (rejected — no repository precedent, weaker validation), full junction table (rejected as premature — nothing consumes per-condition metadata yet), hybrid array + reference table (rejected for the same reason).

**A sixth variant — `text[]` plus a minimal append-only condition-history/audit table — was raised in the independent Architecture Challenge Review** (temporal staleness in Family A: pregnancy, postpartum, recovery, and age-banded conditions all have natural expiries a flat array can't express). **On final Founder challenge, this was correctly downgraded from "new table" to "documentation note":** no current repository component (Planning Engine, LF-C, Learning Engine, analytics) consumes condition history; `household_members` holds 0 rows today, so no staleness is actually accruing; and migration `033` succeeds identically with or without an audit table. Building it now would be solving a real future problem against an imagined present timeline — inconsistent with this repository's own standing engineering guidance. **Resolution: no audit table. The finding is preserved as a required design input for the future LF-C/Planning Engine Routing Design SER (§13), not discarded.**

**Storage: `text[]` + CHECK containment. CONFIRMED — no audit/history table, no junction table, no JSONB.**

## 6. Canonical Vocabulary (finalized, single authoritative source)

Derived this session by direct live query (`SELECT DISTINCT segment FROM re_engine.re_addon_classes UNION SELECT DISTINCT segment FROM re_engine.re_household_addon_plans`), **not retyped from memory or from the prior session's grep output**, to guarantee the CHECK constraint and this document draw from one single source. Live query returned exactly 20 distinct values, confirming no drift from the original Impact Matrix.

**Founder-finalized exclusions/collapses (applied programmatically to the live-queried list):**

| Value removed | Reason |
|---|---|
| `allergy_member` | Redundant with the existing `household_members.allergen_flags` bitfield; zero live usage (present in `re_addon_classes`, absent from `re_household_addon_plans`) |
| `cook_needs_instruction` | Household-scoped (`profiles.cook_capability`), not member-scoped — flagged for a future re-homing SER (§13) |
| `working_kitchen_manager` | Same reasoning as above |
| `child_or_picky_child` | Duplicate pair 1 — collapsed into `picky_child` |
| `postpartum_mother` | Duplicate pair 2 — collapsed into `lactating_or_postpartum_mother` |

**Arithmetic disclosed, not silently reconciled:** an earlier task message estimated "~17-18 values" remaining after exclusions. Applying the five exclusion/collapse rules above to the confirmed 20-value live vocabulary yields **15**, computed directly and reproducibly (see migration header for the derivation script), not approximated. 15 is used as authoritative.

**Final vocabulary — 15 values, `household_members.conditions`:**

```
baby_6_18m, diabetic_member, elderly_member, fasting_member, gym_high_protein_member,
hypertension_heart_member, jain_member, lactating_or_postpartum_mother, picky_child,
pregnant_member, recovery_member, school_child, teen_high_appetite, toddler, weight_loss_member
```

Families D (cooking capability) and E (economic/behavioral) remain excluded per Phase 1 Catalog §3 — household-scoped, not member-scoped, and not created here (no `profiles` columns exist yet for Family E; that's a future SER, §13).

## 7. Schema Proposal

See `database/migrations/033_household_members_conditions_vocabulary.sql` for the exact DDL. Summary: `ALTER COLUMN segment TYPE text[] USING ARRAY[segment]` (lossless — 0 live rows, but correct even if rows existed), `RENAME COLUMN segment TO conditions`, drop `household_members_segment_check`, add `household_members_conditions_check CHECK (conditions <@ ARRAY[15 values] AND cardinality(conditions) >= 0)`, set `DEFAULT '{}'`.

**Default: empty array `'{}'` replaces `ADULT_STANDARD`. CONFIRMED.** Correctly makes "no condition" the common case rather than a placeholder enum value. **`cardinality(conditions) >= 0` (not `>= 1`, unlike the `slot` precedent) — CONFIRMED.** Zero conditions is the common, valid case for most household members, unlike a meal class which must always occupy at least one slot.

## 8. Compatibility Analysis

Confirmed compatible with all four FD-15 documents (Architectural Validation, prior session). Confirmed compatible with the live `re_addon_classes`/`re_household_addon_plans` vocabulary (this SER adopts, not duplicates, those tokens — verbatim spelling preserved for zero-friction future LF-C matching). Confirmed compatible with `addon_slots`' FK structure (live-verified unaffected — references `household_members.id`, not `conditions`).

**Routing (Absorb/Swap/Add): NOT persisted. CONFIRMED.** Derived dynamically by the future Planning Engine. Architecture §9b: *"the same condition can route differently in different households"* — a persisted per-condition default channel would contradict the ratified design directly. No schema surface for routing exists in this SER.

## 9. Migration Strategy (high level)

Single forward migration, next sequential number `033`, following the `025`/`026` precedent exactly. See migration file for full DDL and derivation provenance. Companion rollback: `ALTER COLUMN conditions TYPE text USING conditions[1]`, explicitly commented as lossless only if no row has more than one tag at rollback time — **re-verify row state before executing the rollback if this runs after real data has accumulated.**

## 10. Backward Compatibility

0 existing rows convert trivially (no data-loss scenario to test against, verified live). `HouseholdMemberRow.segment: string` / `HouseholdMember.segment: string` become `conditions: string[]` — a compile-time-enforced change. `DOC-P3-06`'s frozen wire contract changes shape (single string → array) but no client codebase exists in this repository (confirmed), so this is a documentation-version concern only, tracked in §13, not a live-breakage concern.

## 11. Implementation Risks

- **Cross-value business rules unenforced at the DB layer:** the CHECK constraint validates vocabulary membership, not mutual exclusivity (e.g., nothing stops a member being tagged both `toddler` and `teen_high_appetite`). Enforced at the application layer (`orchestrator.ts`), consistent with this repository's existing pattern of keeping business-rule validation in code, not DB triggers.
- **Frozen document drift** (`DOC-P3-04`, `DOC-P3-06`, `DOC-P3-03` §LF-A09/§LF-C01) — explicitly out of scope for this SER, tracked in §13.
- **Vocabulary "closed-ness" is an assumption to watch, not a settled fact** (raised in the independent Architecture Challenge Review): real, common Indian-household conditions not yet in the vocabulary (celiac, lactose intolerance, thyroid, PCOS) exist. Not a defect in this design — the `text[]` + CHECK approach costs exactly one migration per future addition, which is an acceptable, proven-precedented cost, not a blocker.

## 12. Out-of-Scope Items

Food Genome, Recommendation Engine scoring, LF-C/add-on generation logic, the Planning Engine, the Learning Engine — none redesigned or touched. `profiles.cook_capability` and any future `cost_bias`/`novelty_bias` columns — not created here. Swap-channel schema (currently missing entirely) — not designed here. Routing logic itself — confirmed derived, not stored, no schema surface.

## 13. Future SERs Required

1. **Cook-capability & economic/behavioral re-homing SER** — move `cook_needs_instruction`/`working_kitchen_manager` add-on logic to key off `profiles.cook_capability`; add `cost_bias`/`novelty_bias` columns to `profiles` if/when Family E is activated.
2. **LF-C / Planning Engine Routing Design SER** — designs the Swap-channel's missing schema home and the runtime Absorb/Swap/Add decision logic; consumes this SER's vocabulary as an input. **Required design input, added by Founder amendment (2026-07-18):** six of the fifteen vocabulary values are temporally bounded by their own nature — `preconception`-adjacent (n/a, excluded — see below), `pregnant_member`, `lactating_or_postpartum_mother`, `baby_6_18m`, `toddler`, `recovery_member` each describe a state with a real, self-limiting endpoint (pregnancy ends, postpartum/recovery periods end, a baby ages out of a band whether or not anyone updates the record). This routing/Planning-Engine SER must treat these six values' natural expiry as a first-class design input — not because a new schema artifact is needed now (it explicitly is not — see §5's resolution), but because the finding must not be lost between this SER and the point where a real consumer and real household data both exist.
3. **Documentation realignment pass** — updates `DOC-P3-04` §03.2, `DOC-P3-06` §06.2, and `DOC-P3-03` §LF-A09/§LF-C01 to match the new vocabulary once implemented. Not performed here.
4. **Conditional: `re_conditions` reference table SER** — only if Phase 3 reveals a genuine need for DB-native per-condition metadata beyond documentation. Not triggered by this SER.

## 14. Founder Decision

**APPROVED as finalized** (Founder, 2026-07-18) — rename, storage model, vocabulary (15 values, both duplicate pairs collapsed, three exclusions), empty-array default with `cardinality >= 0`, and derived (not persisted) routing, all approved as correct, not a compromise to revisit. Migration `033` implements this SER exactly as specified.

## 15. Cross-references

- `[ACTIVE]_Founder_Decision_Register_v1.0.md` FD-15.
- `Architecture_Challenge_Review_SER-004_v1.0.md` (independent review; its Part 5 final verdict — audit table downgraded to documentation note — is incorporated verbatim into §5/§13 above).
- `database/migrations/025_combo_component_type_and_slot_array.sql`, `026_meal_classes_mirror_slot_array.sql` (schema precedent).
- `database/migrations/033_household_members_conditions_vocabulary.sql` (+ rollback) — implements this SER.
- `[ACTIVE]_SER-001_re_cohorts_city_tier_v1.0.md`, `[ACTIVE]_SER-002_...`, `[ACTIVE]_SER-003_...` (SER format precedent).

Founder Sign-off: Ankit Mittal — Date: 2026-07-18
