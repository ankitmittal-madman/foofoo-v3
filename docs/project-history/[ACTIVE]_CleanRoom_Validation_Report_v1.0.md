# Clean-Room Repository Validation Report v1.0 (WP-5F)

**Status:** ACTIVE — Engineering validation report (repository-evidence simulation; no database executed)
**Version:** v1.0
**Date:** 2026-07-13
**Placement:** docs/project-history/[ACTIVE]_CleanRoom_Validation_Report_v1.0.md
**Supersedes:** None — first Clean-Room Validation Report
**Dependencies:** [ACTIVE]_Migration_Recovery_Report_v1.0 (WP-5B), [ACTIVE]_WP-5C_Rollback_Recovery_Report_v1.0 (WP-5C), [ACTIVE]_Repository_Completeness_Audit_v1.0, [ACTIVE]_Repository_Recovery_Backlog_v1.0, [ACTIVE]_Rollback_Dependency_Graph_v1.0, [ACTIVE]_Rollback_Confidence_Matrix_v1.0. Companion to [ACTIVE]_WP-5F_CleanRoom_Repository_Validation_v1.0 (work package) and its execution certificate.

---

## Executive Summary

WP-5F is a **validation-only** work package. It builds nothing and executes nothing against any database. It independently re-derives — from a full read of all 28 migrations, 28 rollbacks, 3 seed files and 6 validation scripts — whether the recovered FooFoo repository is internally consistent, reproducible and implementation-ready.

**Headline outcome: repository readiness = YELLOW.**

The **migration + rollback layer is sound and self-reconstructable**: numbering is contiguous 001–028, every forward migration resolves its foreign keys against earlier-numbered files, every migration has exactly one paired rollback (28/28), and the rollback set forms a clean reverse-order teardown to the empty pre-001 state. This is the property WP-5B/5C set out to restore, and this independent pass confirms it.

It is **not GREEN** because this pass surfaced two concrete, evidence-backed defects that the prior recovery reports did not capture, plus three carried gaps:

- **SEED-01 (new finding, HIGH):** seed file `101` inserts `re_meal_classes.slot` as scalar text using the value `'addon'`, but migration `025` converts that column to `text[]` and its new CHECK allows only `{breakfast,lunch,dinner,snack}` (legacy `'addon'` → `['snack']`). Applied in canonical order (001→028 then 100→102), the seed **fails**: wrong type *and* now-illegal value.
- **VALIDATION-01 (new finding, MEDIUM):** validation script `900` Check 1 hard-codes "expect 60 tables", but the recovered schema has **62** base tables (migrations `021` cuisines + `024` re_dish_regional_affinity added two after the DOC-P3-04 §02 "60" figure was written). Check 1 would report FAIL on a perfectly-built schema.
- Three carried gaps (not introduced here): no execution certificates with real output for WP-4B/4C/4DB; three migrations applied live but absent from the repo (`pf1_security_hardening`, `103_production_cuisines`, `103_production_ingredients`); and the unresolved `901` Test 5 privilege question (WP-04DC).

The clean-room cycle was performed as an **engineering simulation grounded in the repository files only.** No disposable development database was made available and no explicit approval to execute was given, so nothing was run. Every assumption is stated in §3.

---

## 1. Method & Authority

Per the WP-5F brief and the session-resume protocol: assume zero memory, repository is authoritative, evidence before conclusion, never infer execution. Every migration (001–028), every rollback (001–028), all seeds (100–102) and all validation scripts (900–904) were **read in full** (not searched, not sampled). Prior recovery reports were read as *claims to re-verify*, not as facts to inherit. Findings below cite file and line.

**No database was touched.** The `002`–`028` "live introspection" evidence relied on by WP-5B/5C is treated here as a prior read-only observation, not re-executed.

---

## 2. Migration Matrix (Step 3 / Step 7)

Legend: schema `p`=public, `re`=re_engine. "Deps" = lowest-numbered migration(s) whose objects this file references.

| # | File | Creates / Alters | Deps | Numbering | Verdict |
|---|---|---|---|---|---|
| 001 | extensions_and_schema_setup | pgcrypto ext; schema `re_engine`; grants + ALTER DEFAULT PRIVILEGES | — | ok | ✅ |
| 002 | reference_tier0 | `p.ingredients`(self-FK), `p.tags`, `re.re_states`, `re.re_main_cohorts` | 001 | ok | ✅ |
| 003 | reference_tier1 | `re.re_personas`,`re.re_subcohorts`,`re.re_routing_rules`,`re.re_meal_classes`,`p.meal_classes` | 002 | ok | ✅ |
| 004 | reference_tier2 | 9 `re_engine` reference tables (internal FK order correct) | 002,003 | ok | ✅ |
| 005 | profiles | `p.profiles` (FK→auth.users, →re_states) | 002 + auth.users | ok | ✅ |
| 006 | profile_dependent_public | `p.household_members`,`p.onboarding_sessions`,`p.consent_records` | 005 | ok | ✅ |
| 007 | re_identity_interaction_history | 6 `re_engine` per-user tables | 003 | ok | ✅ (profile_id FK intentionally absent, documented) |
| 008 | content_core | `p.dishes`(self-FK), REVOKE, `p.dish_combos` | 001 | ok | ✅ |
| 009 | content_junctions | `p.dish_ingredients`,`p.dish_tags`,`p.dish_combo_items` | 002,008 | ok | ✅ |
| 010 | trigger_functions_and_triggers | `p.derivation_conflicts`; 4 fns + 4 triggers | 002,006,008,009 | ok | ✅ (idempotent CREATE TRIGGER guards) |
| 011 | planning_tables | `p.week_plans`,`p.plan_slots`,`p.addon_slots` | 003,005,006,008 | ok | ✅ |
| 012 | interaction_audit_appendonly | `p.interaction_events`,`p.suggestion_logs` (partitioned parents),`p.context_log`,`p.weather_cache` | 005,008 | ok | ✅ (parents accept no rows until 017) |
| 013 | config_tables | 10 `re_engine` config tables (weight-sum CHECK) | 001 | ok | ✅ |
| 014 | persona_assignment_and_priors | `re.re_persona_assignment_rules`,`re.re_cohort_class_priors` | 002,003,004 | ok | ✅ |
| 015 | operational_audit_public | 6 operational/audit tables | 005 | ok | ✅ |
| 016 | dish_features | `re.dish_features` (soft dish ref, no FK) | 001 | ok | ✅ |
| 017 | initial_partitions | dynamic `DO` creates 3-month partitions of 012 parents | 012 | ok | ✅ (template dates from CURRENT_DATE) |
| 018 | meal_classes_mirror_sync | **empty retired placeholder** (AGR-002) | — | ok | ✅ (no-op by design) |
| 019 | rls_policies | ENABLE RLS + 23 policies on 19 public tables | 002,005,006,008,009,011,012 | ok | ✅ |
| 020 | indexes | **36** explicit indexes (public + re_engine) | 002–016 | ok | ✅ (header comment says "37"; only 36 authored — cosmetic) |
| 021 | cuisines_reference | `p.cuisines`; `cuisine_id` FK on dishes & dish_combos; RLS + policy | 008 | ok | ✅ RECONSTRUCTED |
| 022 | dish_display_attributes | +3 columns on `p.dishes` | 008 | ok | ✅ RECONSTRUCTED |
| 023 | tags_uniqueness_and_vector_positions | drop global UNIQUE→UNIQUE(dimension,tag_name); `fn_assign_tag_vector_positions()` | 002 | ok | ✅ RECONSTRUCTED (fn verbatim) |
| 024 | re_dish_regional_affinity | `re.re_dish_regional_affinity` (RR-01 table) | 002,008 | ok | ✅ RECONSTRUCTED |
| 025 | combo_component_type_and_slot_array | +`component_type` on dish_combo_items; `re_meal_classes.slot` scalar→`text[]` | 003,009 | ok | ✅ RECONSTRUCTED (USING expr reconstructed) — see SEED-01 |
| 026 | meal_classes_mirror_slot_array | `p.meal_classes.slot` scalar→`text[]` | 003 | ok | ✅ RECONSTRUCTED (USING expr reconstructed) |
| 027 | routing_rules_show_question_key_nullable | DROP NOT NULL + action CHECK | 003 | ok | ✅ (AGR-005) |
| 028 | weight_ladder_config_numeric_weights | weight cols real→numeric; re-add sum CHECK | 013 | ok | ✅ (AGR-006) |

**Numbering:** contiguous 001–028, no gaps, no duplicates (verified by directory listing).
**Reference integrity:** every FK / ALTER target is created in a strictly lower-numbered file. No forward references.
**Object uniqueness:** each table/function has exactly one CREATE across the set (e.g. `cuisines` only in 021, `re_dish_regional_affinity` only in 024).

## 3. Build Graph & Clean-Room Simulation (Step 5)

**Nature of this section: SIMULATION based on repository evidence.** No database was created or executed. A disposable dev DB was not available/approved; live execution is deferred to WP-5G per the WP-sequence reconciliation (see §9 and the companion IDR).

### 3.1 Forward build order (001 → 028)
```
001 (schema/ext) → 002 (tier0) → 003 (tier1) → 004 (tier2) → 005 (profiles)
 → 006 → 007 → 008 (content) → 009 (junctions) → 010 (triggers) → 011 (planning)
 → 012 (log parents) → 013 (config) → 014 → 015 → 016 → 017 (partitions)
 → 018 (no-op) → 019 (RLS) → 020 (indexes) → 021 (cuisines) → 022 → 023
 → 024 (regional affinity) → 025 (slot→array) → 026 (mirror slot→array)
 → 027 (routing null) → 028 (numeric weights)
```
Simulated result: **all 28 apply cleanly on a fresh database** — every dependency present before use; `auth.users` and `service_role`/`authenticated`/`anon` roles are the only external prerequisites (Supabase platform-provided, stated in 001/005 headers).

### 3.2 Seed layer (100 → 102) — **SEED-01 defect surfaces here**
- `100` config seeds: weight-ladder rows require the **numeric** column type from `028` to satisfy the exact-sum CHECK (the `'emerging'` tier sums to `0.999999940395355` under float4). ✅ compatible **because 028 is applied**.
- `101` reference seeds: `re_routing_rules` rows with NULL `show_question_key` require `027`. ✅ compatible. **BUT** `re_meal_classes` rows insert `slot` as **scalar text** with value **`'addon'`** (lines 84–85), which after `025` is a `text[]` column whose CHECK is `slot <@ {breakfast,lunch,dinner,snack}`. ❌ **fails on both type and value.** → **SEED-01.**
- `102` illustrative content: exercises the derive/propagate triggers; type-compatible with the migrated schema. ✅ (depends on `101` reference rows existing).

### 3.3 Validation layer (900 → 904) — **VALIDATION-01 defect surfaces here**
- `900` Check 1 expects **60** tables; schema has **62** (see §2 count) → ❌ **VALIDATION-01.** Other 900 checks (FKs, triggers, RLS-enabled=19, re_engine lockdown) are consistent with the migrated schema.
- `900` Check 7 seed gates are **expected to FAIL** by design (IDR-001 illustrative seeds) — not a defect.
- `901` Test 5 (privilege enforcement) is the **unresolved WP-04DC question** — see §6.
- `902`/`903`/`904` require auth.users fixtures; they self-skip when absent. Logic is sound against the migrated schema.

### 3.4 Teardown (028 → 001) → empty state
Applied in reverse order, the 28 rollbacks return the database to the pre-001 empty state (schema `re_engine` dropped last via `DROP SCHEMA … RESTRICT`; pgcrypto dropped `IF EXISTS`). Simulated result: **clean teardown to empty**, on an unseeded database. On a *seeded* database, five rollbacks fail loudly by design (see §4). This matches the Rollback Dependency Graph's clean-state property.

### 3.5 Assumptions (explicit)
1. External roles (`service_role`,`authenticated`,`anon`) and `auth.users` exist — Supabase platform-provided.
2. Auto-generated constraint names assumed by later ALTER/rollback statements match Postgres defaults: `tags_tag_name_key` (023), `re_meal_classes_slot_check` (025), `meal_classes_slot_check` (026), `re_weight_ladder_config_check` (028), `re_routing_rules_action_check` (027 rollback). These are the standard Postgres auto-names for the corresponding inline/table constraints; **not independently confirmed against a live catalog in this pass** (medium-confidence assumption, would be upgraded by WP-5G live apply).
3. Canonical apply order is all migrations (001–028) → seeds (100–102) → validation (900–904). SEED-01/VALIDATION-01 are stated under this order.

## 4. Rollback Matrix (Step 4 / Step 7)

| # | Reverses | Mechanism | Lossy / warned? | Confidence |
|---|---|---|---|---|
| 001 | schema/ext | REVOKE, DROP SCHEMA RESTRICT, DROP EXTENSION IF EXISTS | pgcrypto conditional | MEDIUM |
| 002–007 | reference/profile/identity | reverse-order DROP TABLE | no | HIGH |
| 008 | dishes/combos | DROP 2 tables (REVOKE moot) | no | HIGH |
| 009 | junctions | DROP 3 tables | no | HIGH |
| 010 | triggers/fns/table | DROP 4 triggers, 4 fns, derivation_conflicts | no | HIGH |
| 011 | planning | DROP addon_slots→plan_slots→week_plans | no | HIGH |
| 012 | log parents | DROP (warns: run 017 first) | no | HIGH |
| 013 | config | DROP 10 tables | no | HIGH |
| 014 | persona/priors | DROP 2 tables | no | HIGH |
| 015 | operational | DROP 6 tables | no | HIGH |
| 016 | dish_features | DROP 1 table | no | HIGH |
| 017 | partitions | `pg_inherits`-driven dynamic DROP | drops all current partitions (warned) | MEDIUM |
| 018 | no-op | `SELECT 1` | no | HIGH |
| 019 | RLS | DROP 23 policies + DISABLE RLS on 19 tables | no | HIGH |
| 020 | indexes | DROP **36** indexes | no | HIGH |
| 021 | cuisines | DROP policy, drop 2 FK cols, DROP table | no | HIGH |
| 022 | display attrs | DROP 3 cols | no | HIGH |
| 023 | tags uniqueness | DROP fn; restore global UNIQUE(tag_name) | **fails loudly on cross-dim dup names** | MEDIUM |
| 024 | regional affinity | DROP 1 table | no | HIGH |
| 025 | slot array | array→scalar `slot`; drop component_type | **lossy for multi-slot rows** | MEDIUM |
| 026 | mirror slot array | array→scalar `slot` | **lossy for multi-slot rows** | MEDIUM |
| 027 | routing null | drop action CHECK; SET NOT NULL | fails loudly on seeded skip-rules | MEDIUM |
| 028 | numeric weights | numeric→real; restore float4 sum CHECK | fails loudly on seeded 'emerging' row | MEDIUM |

**Coverage: 28/28.** Verified by basename pairing: `diff` of migration basenames vs rollback basenames (minus `_rollback`) is empty — **perfect 1:1**. No duplicate rollbacks. Index create/drop counts match exactly (36/36).

## 5. Dependency Graph (Step 7)

**Forward (build):** `001 → {002 → {003 → {004,014}, 005 → {006, 011, 012, 015}}, 008 → {009 → 010, 011, 012, 021, 022, 024, 025}, 013 → 028}`; `017` after `012`; `019`,`020` after all structural tables; `023` after `002`; `026`,`027` after `003`. No cycle exists (the only self-references — `ingredients.can_substitute_id`, `dishes.parent_dish_id` — are intra-table and satisfied within their own CREATE).

**Reverse (teardown):** strict `028 → 001`. Cross-migration forcing edges (from the Rollback Dependency Graph, re-verified): 017 partitions must drop before 012 parents (guaranteed by 017>012); 021 cuisine FKs before 008 tables (021>008); 010 triggers before 002/006/009 tables (010>...); 001 schema drop last. All satisfied by pure reverse order.

## 6. Validation Matrix (Step 7)

| Script | Purpose | Depends on | Clean-room verdict |
|---|---|---|---|
| 900 | structural (tables, FKs, triggers, RLS count, seed gates) | migrated schema | ⚠️ Check 1 stale (60 vs 62) → **VALIDATION-01**; Check 7 gate fails are expected (IDR-001) |
| 901 | trigger derivation behaviour + privilege Test 5 | seeded content (102) | ⚠️ Test 5 unresolved (WP-04DC); Tests 1–4 sound |
| 902 | safety gates 1–4 | fixture profile | ✅ logic sound; self-skips without auth fixtures |
| 903 | RLS cross-user isolation | ≥2 profile fixtures | ✅ logic sound; self-skips without fixtures |
| 904 | config CHECK + smoke path | config + reference seeds | ✅ logic sound (PARTIAL notices expected under IDR-001) |

## 7. Repository Integrity Report (Step 6)

| Check | Result | Evidence |
|---|---|---|
| No orphan migrations | ✅ PASS | 28 files, contiguous 001–028 |
| No duplicate rollback | ✅ PASS | 28 rollbacks, 1:1 basename pairing (empty diff) |
| No missing dependency | ✅ PASS | every FK/ALTER target in a lower-numbered file |
| No circular dependency | ✅ PASS | only intra-table self-FKs; no inter-file cycle |
| No broken references | ✅ PASS (schema) | all cross-file object references resolve |
| No undocumented object | ✅ PASS | every migration has a header citing its DOC-P3-04 §/AGR source |
| No inconsistent numbering | ✅ PASS | bands respected: structural 001–020, later 021–028, seeds 100–102, validation 900–904 |
| Seed ↔ migration consistency | ❌ FAIL | **SEED-01**: seed 101 slot scalar/`'addon'` vs 025 `text[]`/`snack` |
| Validation ↔ migration consistency | ⚠️ PARTIAL | **VALIDATION-01**: 900 Check 1 expects 60, schema has 62 |
| File hygiene | ✅ PASS | no stray/non-conforming files (one intentional `WP-3D_Check2_Fix_Reference.sql`) |

## 8. Risk Matrix (Step 7)

| ID | Risk | Sev | Likelihood if unaddressed | Evidence | Owner WP |
|---|---|---|---|---|---|
| SEED-01 | Illustrative seed 101 breaks against migrated schema (slot type+value) | HIGH | Certain (any build→seed run fails) | 101:84-85 vs 025:41-45 | WP-5E (execution/seed refresh) |
| VALIDATION-01 | 900 Check 1 reports FAIL on a correct schema (stale count) | MEDIUM | Certain (every 900 run) | 900:12-16 vs §2 count=62 | WP-5E |
| PROD-PARITY | 3 live-applied migrations absent from repo → repo build ≠ production | HIGH | Certain (repo cannot reproduce prod) | Migration_Recovery_Report §4 | WP-5D |
| EXEC-EVIDENCE | No real-output certificates for WP-4B/4C/4DB | MEDIUM | — (governance/audit gap) | Recovery Backlog RB-07/08/09 | WP-5E |
| SEC-901T5 | Privilege Test 5 (authenticated UPDATE derived col) never directly measured | MEDIUM | Unknown (default-deny likely holds) | WP-04DC diagnostic | WP-5D/5E |
| SIM-ONLY | Migration/rollback replay proven by reasoning, not live apply | MEDIUM | — (residual uncertainty on 5 auto-names) | §3.5 assumption 2 | WP-5G |
| DOC-020 | Migration 020 header says "37 indexes"; 36 exist | LOW | n/a (cosmetic) | 020:1 vs 36 CREATE | WP-5E errata |

## 9. Repository Readiness Report (Step 8)

| Question | Rating | Evidence |
|---|---|---|
| Can the repository rebuild its own schema? | 🟢 GREEN | 001–028 contiguous, all deps resolve, clean forward simulation (§2,§3.1) |
| Can the repository roll back? | 🟢 GREEN | 28/28 paired rollbacks, clean reverse teardown to empty (§4,§3.4) |
| Can it onboard a new engineer? | 🟡 YELLOW | Rich governance + migration headers exist; but README is 2 lines, no runbooks/templates yet (RB-11/12), and seed/validation layer misleads (SEED-01/VALIDATION-01) |
| Can it survive disaster recovery? | 🟡 YELLOW | Schema+rollback recoverable from repo; but 3 production migrations missing (PROD-PARITY) → a repo-only rebuild ≠ production, and no live replay yet proven |
| Can implementation begin? | 🟡 YELLOW | Schema baseline is implementation-ready; seed/validation must be corrected first and execution evidence produced before a launch gate |

**OVERALL: 🟡 YELLOW.** The Critical RR-01 risk is resolved (migration set now rebuilds the live schema shape, rollback layer complete). Promotion to GREEN is blocked by SEED-01, VALIDATION-01, PROD-PARITY, EXEC-EVIDENCE, SEC-901T5 and the absence of a live clean-room replay. None is a fabrication or an architecture defect; all are recovery-completion items.

## 10. Remaining Gaps (Step 9) — factual only

1. **SEED-01** — seed 101 incompatible with post-025 `slot` (type + value). *(new)*
2. **VALIDATION-01** — 900 Check 1 table count stale (60 vs 62). *(new)*
3. **PROD-PARITY** — `pf1_security_hardening`, `103_production_cuisines`, `103_production_ingredients` applied live, absent from repo (Migration_Recovery_Report §4; Recovery Backlog would need these added).
4. **EXEC-EVIDENCE** — WP-4B/4C/4DB have no companion certificates with real output (RB-07/08/09).
5. **SEC-901T5** — WP-04DC privilege question never directly measured.
6. **DOC-020** — cosmetic "37 vs 36" index header note.
7. Carried, out of recovery scope: 3 PIR architecture decisions (RB-16), DPDP age-gate (RB-17), IDR-001 master seed data ~30k rows (RB-18), 9 naming exceptions.

### Recommended follow-on work packages (do NOT execute — Founder approval required)

Per this session's WP-sequence reconciliation (see companion IDR), the live WP-5F brief re-sequences the committed Recovery Work Package Plan. Under the **brief's** numbering:

- **WP-5D — Production Migration Recovery:** recover/author repo files for the 3 live-only migrations (`pf1_security_hardening`, `103_production_cuisines`, `103_production_ingredients`) so a repo build reproduces production. Addresses PROD-PARITY. *(The committed WP Plan does not have a WP-5D of this name; this is a brief-defined package — see IDR.)*
- **WP-5E — Execution Evidence Recovery:** produce real-output certificates for WP-4B/4C/4DB; **correct SEED-01 and VALIDATION-01** (refresh illustrative seeds and 900 Check 1 against the 021–028 schema); resolve SEC-901T5. *(≈ the committed Plan's WP-5D "Execution Recovery" plus the two new findings.)*
- **WP-5G — Repository Green Certification:** perform a **live** clean-room apply+teardown on a disposable branch, confirm parity with production, then certify GREEN. *(≈ the committed Plan's WP-5F "Green Certification"; renamed to 5G because the brief reassigned "5F" to this validation.)*

## Critical Self-Review

- **Considered** inheriting WP-5B's "seed compatibility PASS" conclusion. **Rejected** — that check reasoned only about `component_type`/`cuisine_id` nullability and did not examine the `slot` scalar→array change; a full read of seed 101 against migration 025 surfaced SEED-01. This is exactly why WP-5F re-reads rather than trusts prior reports.
- **Considered** rating overall readiness GREEN because the migration/rollback layer is genuinely sound. **Rejected** — a repository whose own seed layer cannot load against its own migrations, and whose validation script fails on a correct schema, is not implementation-ready end-to-end. GREEN must mean the whole build→seed→validate→teardown cycle is clean.
- **Considered** executing a live apply on a Supabase preview branch (MCP is available). **Rejected** — no disposable dev DB was confirmed and no explicit execution approval was given; the brief mandates simulation unless both hold. Live replay is WP-5G.
- **Limitation:** five auto-generated constraint names assumed by ALTER/rollback statements (§3.5 assumption 2) are standard Postgres defaults but were not re-confirmed against a live catalog in this pass. This is the single residual that a WP-5G live apply would close.

## Versioning & Placement

`[ACTIVE]_CleanRoom_Validation_Report_v1.0.md` → `docs/project-history/`. New file; supersedes nothing.

## Founder Sign-off

Founder acceptance of the Clean-Room Validation Report: _______________________ Date: ___________
