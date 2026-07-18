# [ACTIVE]_WP-13_Household_Members_Conditions_Vocabulary_v1.0

**Status:** ACTIVE — migration + code + tests authored and verified locally; **NOT yet applied to the live database** (blocked by the harness's own permission classifier pending explicit Founder confirmation of that specific step — see §5). Not committed, not pushed.
**Version:** v1.0
**Date:** 2026-07-18
**Placement:** docs/project-history/work-packages/[ACTIVE]_WP-13_Household_Members_Conditions_Vocabulary_v1.0.md
**Builds on:** FD-15 (Founder Decision Register), `[ACTIVE]_SER-004_household_members_conditions_vocabulary_v1.0.md` (Founder-approved as finalized, 2026-07-18), the independent Architecture Challenge Review that preceded SER-004's finalization.
**Governance basis:** SER-004 (this WP's sole implementation authority — no engineering judgment beyond what SER-004 already ratified was exercised here).

---

## Executive Summary

Implements SER-004 exactly as finalized: `household_members.segment` (scalar `text`, 8-value CHECK) becomes `household_members.conditions` (`text[]`, 15-value CHECK), via migration `033` (+ rollback), with the three dependent TypeScript files and two test files updated to match. `deno task verify`: **71 tests, 0 failures**, `fmt`/`lint`/`check` all clean. **The migration has been authored and locally verified for correctness but has not been executed against the live database** — an explicit permission gate in this session's tooling blocked direct execution pending your confirmation, and this WP respects that gate rather than working around it.

## 1. Pre-implementation verification (this session, live introspection — not assumed)

Before writing migration `033`, re-verified every schema assumption SER-004 depends on, directly against the live database:
- Exact constraint name confirmed: `household_members_segment_check` (not guessed from the ERD).
- `household_members` confirmed at **0 live rows** — no data-loss scenario exists for the type conversion.
- No view, rule, or function body anywhere in the live database references `household_members.segment` (checked via `pg_depend`/`pg_proc.prosrc`, not grep alone).
- `addon_slots.household_member_id` FK confirmed live and structurally unaffected (references `household_members.id` only).
- The target vocabulary re-derived **directly from a live query** (`SELECT DISTINCT segment FROM re_engine.re_addon_classes UNION SELECT DISTINCT segment FROM re_engine.re_household_addon_plans`) — confirmed exactly 20 distinct values, matching SER-004's audit with zero drift.

**No discrepancy found between the live schema and SER-004's assumptions.** Proceeded as authorized.

## 2. Vocabulary — single authoritative derivation, not hand-retyped

The 15-value CHECK-constraint vocabulary embedded in migration `033` was generated programmatically: the live-queried 20-value list piped through a small script applying exactly SER-004 §6's five exclusion/collapse rules (`allergy_member`, `cook_needs_instruction`, `working_kitchen_manager` excluded; `child_or_picky_child`→`picky_child` and `postpartum_mother`→`lactating_or_postpartum_mother` collapsed). Output: 15 values. **Arithmetic disclosed:** an earlier task message estimated "~17-18" remaining values; the actual computed result from the stated rules is 15 — used as authoritative, not force-fit to the estimate.

## 3. What was built

- **`database/migrations/033_household_members_conditions_vocabulary.sql`** — forward migration, follows the `025`/`026` precedent exactly (`ALTER COLUMN ... TYPE text[] USING ARRAY[segment]`, rename, new default, drop/add CHECK).
- **`database/rollback/033_household_members_conditions_vocabulary_rollback.sql`** — companion rollback. **A real ordering bug was caught and fixed during authoring** (an early draft added the old scalar CHECK constraint before converting the column back to scalar type, which does not type-check against an array-typed column) — corrected to the right sequence (drop new CHECK → drop default → convert type → rename → restore NOT NULL → restore old CHECK), with both lossiness caveats (multi-tag rows; vocabulary value mismatch) documented inline, not silently glossed over.
- **`supabase/functions/_shared/services/onboarding/orchestrator.ts`** — `OnboardingAnswers.members[].segment: string` → `conditions: string[]`; `HouseholdMemberRow.segment` → `conditions: string[]`; both persistence call sites and the RE-engine member-mapping call site updated; new `assertNoConflictingLifeStageTags()` function + call added (§4).
- **`supabase/functions/_shared/services/adapters/supabase-stores.ts`** — `persistHouseholdMembers` insert payload updated (`segment` → `conditions`).
- **`supabase/functions/_shared/services/re/types.ts`** — `HouseholdMember.segment: string` → `conditions: string[]`.
- **`supabase/functions/_tests/re_core.test.ts`, `re_integration.test.ts`** — fixtures updated to the new array shape and lowercase vocabulary (`segment: "TODDLER"` → `conditions: ["toddler"]`, etc.).
- **Full codebase sweep confirmed** (`grep -rn "segment" supabase/functions/ --include="*.ts"`) — zero remaining functional references; only two explanatory code comments mention the old name for context.

## 4. Application-layer validation added (per SER-004 §11)

`assertNoConflictingLifeStageTags()` in `orchestrator.ts` enforces that a member cannot carry more than one of a narrowly-scoped, sequential age-band set (`baby_6_18m`, `toddler`, `school_child`, `teen_high_appetite`) simultaneously — deliberately **not** applied to `picky_child`, `elderly_member`, `recovery_member`, `pregnant_member`, or `lactating_or_postpartum_mother`, since the Canonical Planning Model's own stress test (§7, "Elderly couple + Recovery") shows those legitimately co-occurring with an age band or with each other on the same member. Enforced in application code (throwing the existing `ERR_VALIDATION_FAILED`), not as a DB constraint — consistent with this repository's existing pattern of keeping business-rule validation in code rather than DB triggers.

## 5. What was NOT done, and why (explicit gate, not an oversight)

**The migration was not executed against the live database.** This session's tooling classified direct execution of `033` against the connected Supabase project as a production-schema-modifying action requiring explicit confirmation beyond the general "write and run" task framing, given the earlier "Do NOT modify the database" instruction in this same engineering track and the standing instruction to get confirmation before hard-to-reverse, shared-system actions. Rather than retrying or working around that block, this WP stops here and asks for your explicit go-ahead on that one step. Everything else the tasking requested — writing the migration, writing the rollback, updating all dependent code, updating tests, and running the full local test suite — is complete and verified.

**Consequently, `900_structural_validation.sql` and any live-DB-dependent check were not run** (they require the migration to have been applied first). `deno task verify` (fmt/lint/check/test, all against local fake stores — no live DB) was run in full and is the verification available at this stage.

**Not touched, per explicit instruction:** `DOC-P3-04`, `DOC-P3-06`, `DOC-P3-03` §LF-A09/§LF-C01 (flagged for a separate documentation realignment pass, SER-004 §13). No LF-C/add-on generation logic built (Phase 3, out of scope).

## Critical Self-Review

- **Anything invented?** No — every schema and vocabulary decision traces directly to SER-004's finalized §§4-8; the one implementation-only addition (`assertNoConflictingLifeStageTags`) was explicitly requested by the task and scoped narrowly, with its exclusions justified by evidence already in the ratified Planning Model, not invented judgment.
- **Frozen artifacts touched?** No — `DOC-P3-04`/`DOC-P3-06`/`DOC-P3-03` untouched, per instruction.
- **Live database touched?** No — confirmed unchanged; live introspection performed was read-only (`SELECT`/`\d`), no DDL executed.
- **Honest completeness:** this WP is migration-authored-and-verified, not migration-applied. The distinction is stated plainly in the Status line, not blurred.

## Versioning & Placement

v1.0, `docs/project-history/work-packages/` per the Placement Rule; naming per WP-5AA (`WP-13`, next sequential number after `WP-12`). Companion certificate: REPO-CERT-024.

## Founder Sign-off

Founder acceptance of WP-13 as authored, and explicit authorization to execute migration `033` against the live database: _______________________ Date: ___________
