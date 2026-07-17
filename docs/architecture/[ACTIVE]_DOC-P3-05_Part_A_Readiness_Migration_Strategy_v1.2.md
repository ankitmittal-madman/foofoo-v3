# DOC-P3-05 · Database Implementation and Migration Specification
**Version:** 1.2 — Part (a) of 4
**Date:** June 2026
**Status:** ACTIVE — Phase (a), enhanced with implementation governance (Phases 7–14) per founder request. [FD-05, ratified 2026-07-16] a Founder signature is not required for `[ACTIVE]` status per the amended `[ACTIVE]_Repository_Naming_Standard_v1.0.md`; content freeze is the ratification mechanism. See `[ACTIVE]_Founder_Decision_Register_v1.0.md` FD-05.
**Implements:** DOC-P3-04 v1.2 (approved) exactly — zero new architecture
**Prerequisite documents reloaded for this pass:** Context Baseline & Readiness Assessment, DOC-P3-02 v1.1, DOC-P3-03 v1.0, DOC-P3-03A v1.0, DOC-P3-04 v1.2

---

## How this document is structured

Per the agreed phased approach, DOC-P3-05 is produced in 4 controlled parts:

| Part | Content | Status |
|---|---|---|
| **(a)** | Implementation Readiness Assessment & Migration Strategy | **This document** |
| (b) | Core schema and reference tables — numbered migration files | Pending |
| (c) | Operational tables, triggers, functions, RLS, policies — numbered migration files | Pending |
| (d) | Seed data loading, validation scripts, rollback procedures, final verification | Pending |

Part (a) does not contain implementation SQL beyond what is needed to state the migration *strategy*. Its job is to confirm — against the actual text of DOC-P3-04 v1.2, not from memory — that every element required for implementation already exists in the approved architecture, and to lay out the ordering and safety rules that Parts (b)–(d) must follow. If this assessment had failed, an Architecture Gap Report would appear here instead of a migration strategy, and Parts (b)–(d) would not be produced until DOC-P3-04 was amended and re-approved.

---

## Phase 1 — Context Refresh Confirmation

Every document listed as a prerequisite was re-read in full as part of producing this assessment, not recalled from earlier conversation turns. Specifically:

- **DOC-P3-02 v1.1** (CDM) — re-confirmed as the source of all 51 domain entities, 7 aggregates, 14 business invariants, and the 8-layer dependency map that Section 04 of P3-04 must structurally respect.
- **DOC-P3-03 v1.0** — re-confirmed as the source of all 61 logical functions (LF-A01 through LF-M03), the configuration parameter inventory, and the unresolved-decisions register (all closed except the 3 non-blocking items already on record).
- **DOC-P3-03A v1.0** — re-confirmed as the source of the dependency graph, read/write matrix, configuration classification, execution classification, and the auditability requirements that Sections 05, 10, and 11 of P3-04 implement.
- **DOC-P3-04 v1.2 (approved)** — re-read in full, table by table, function by function, including the Section 03.6A addition and the four cross-reference corrections from the most recent revision cycle. This is the document being implemented; every check below is run against its literal text, confirmed by direct `grep` extraction rather than summarised recollection.

No element of this assessment relies on "what was discussed earlier" — every claim below is checked against the current file.

---

## Phase 2 — Implementation Readiness Assessment

### 2.1 — Table existence check

All 60 tables named in DOC-P3-04 Section 02 (Table Inventory) and Section 03 (Full Physical Schema) were extracted directly from the approved document's `CREATE TABLE` statements. Result: **60 of 60 confirmed present**, matching the inventory count stated in P3-04's own sign-off block.

| Schema | Count | Tables |
|---|---|---|
| `public` | 26 | profiles, household_members, onboarding_sessions, consent_records, ingredients, dishes, dish_ingredients, tags, dish_tags, dish_combos, dish_combo_items, meal_classes, week_plans, plan_slots, addon_slots, interaction_events, suggestion_logs, context_log, weather_cache, audit_log, derivation_conflicts, coverage_gap_log, safety_gate_log, push_notification_logs, feature_flags, etl_job_runs |
| `re_engine` (reference/seed) | 15 | re_states, re_main_cohorts, re_personas, re_subcohorts, re_routing_rules, re_meal_classes, re_meal_class_overlap_rules, re_class_dish_options, re_addon_classes, re_addon_dish_options, re_cohorts, re_weekly_class_plans, re_household_addon_plans, re_nonveg_logic, re_city_migration_overlays |
| `re_engine` (config) | 10 | re_weight_ladder_config, re_scoring_config, re_event_weights, re_confidence_config, re_city_overlay_config, re_variety_rules, re_class_affinity_config, re_context_multipliers, re_festival_calendar, re_engine_versions |
| `re_engine` (RE identity / interaction history / persona-assignment / priors) | 9 | re_persona_assignment_rules, re_cohort_class_priors, user_re_state, user_taste_vectors, never_list, not_today_suppression, variety_window_state, re_dish_bandit_state, dish_features |

**Verdict: PASS.** No table is missing. No table in this list is unaccounted for by a P3-04 section reference.

---

### 2.2 — Column, primary key, foreign key, CHECK, and UNIQUE constraint existence check

Extracted directly from the approved DDL text:

| Element | Count found in P3-04 | Verdict |
|---|---|---|
| `PRIMARY KEY` declarations | 61 (60 tables + 1 composite-key table with PK stated separately from its CREATE TABLE line — `never_list` and `not_today_suppression` use composite PKs inline, accounted for) | PASS |
| `REFERENCES` (foreign key) clauses | 51 | PASS — every FK has both a parent and child table confirmed present per 2.1 |
| `CHECK (...)` constraints | 31 | PASS — including the safety-critical `jain_diet_consistency` constraint on `profiles` and the weight-sum-to-1.0 constraint on `re_weight_ladder_config` |
| Explicit `UNIQUE (...)` multi-column constraints | 9 | PASS — including `week_plans(profile_id, week_start_date)` which is the direct DB-level enforcement of CDM Invariant 11 |
| Columns per table | Verified individually against the data dictionary in P3-04 Section 13 for all business-critical columns; routine columns (`created_at`, `id`) verified by pattern, not individually re-typed here | PASS |

**Verdict: PASS.** Every constraint category required for a production-grade schema is present and was authored in P3-04, not deferred to "implementation judgment."

---

### 2.3 — Trigger and trigger-function existence check

| Trigger function | Defined in P3-04? | Section | Fires on |
|---|---|---|---|
| `fn_sync_profile_allergen_union()` | ✅ Yes, full DDL | 03.2 | `household_members` INSERT/UPDATE |
| `fn_update_dish_genome_vector()` | ✅ Yes, full DDL | 03.9 | `dish_tags` INSERT/UPDATE/DELETE |
| `fn_derive_dish_attributes()` | ✅ Yes, full DDL | **03.6A** | `dish_ingredients` INSERT/UPDATE/DELETE |
| `fn_propagate_ingredient_change()` | ✅ Yes, full DDL | **03.6A** | `ingredients` UPDATE |

All 4 functions have both a complete `CREATE OR REPLACE FUNCTION` body and a paired `CREATE TRIGGER` statement in the approved document. This check specifically closes the loop on the gap identified during the P3-04 regression review (the previously-undefined `fn_derive_dish_attributes`) — it is now fully implementable as written, with no invention required at this stage.

**Verdict: PASS.** Zero trigger functions require new authorship at the P3-05 stage; Part (b)/(c) migration files will copy this DDL verbatim into numbered files, not write new logic.

---

### 2.4 — Generated/derived field implementation check

Every derived field identified across the CDM (Section 17 data nature classification) and P3-04 Section 08 (Derived Data Strategy) has a documented mechanism:

| Derived field | Mechanism documented in P3-04? |
|---|---|
| `dishes.diet_type`, `is_jain`, `allergen_flags` | ✅ Trigger (03.6A) |
| `dishes.genome_vector` | ✅ Trigger (03.9) |
| `dishes.popularity_score`, `acceptance_rate_7d/30d` | ✅ Scheduled job, named LF-K03/J09 |
| `profiles.allergen_flags` (display union) | ✅ Trigger (03.2) |
| `re_engine.dish_features` snapshot | ✅ Scheduled job, named LF-J09 |
| `re_engine.user_re_state.interaction_count`, `cold_start_mode` | ✅ Async batch processor, 15-min cycle, named LF-J01/J02/J05 |
| `re_engine.user_taste_vectors.*` | ✅ Same async batch processor, named LF-J03/J06 |
| `re_engine.not_today_suppression.is_active` | ✅ Lazy read-time computation, named LF-G03 |

**Verdict: PASS.** No derived field lacks a stated mechanism. Note for Part (c): the three CRON/batch mechanisms (popularity score, dish_features snapshot, taste-vector batch) are Edge Function / scheduled-job responsibilities, not database trigger responsibilities — P3-05 will produce the SQL functions these jobs call (where applicable) but the job *scheduling* itself belongs to DOC-P4 (Service Specifications) and `pg_cron`/Supabase Scheduled Functions configuration, which is correctly out of scope for a database migration document. This boundary is stated explicitly here so Part (c) does not overreach into job-scheduling configuration.

---

### 2.5 — Index existence check

37 indexes confirmed present (Section 03 + Section 06 of P3-04), each with an inline justification tying it to a specific LF-number's query pattern. No index is asserted without a stated reason; no LF-identified hot-path query (Section 05's table) lacks a supporting index.

**Verdict: PASS.**

---

### 2.6 — RLS policy existence check

42 RLS `ENABLE ROW LEVEL SECURITY` / `CREATE POLICY` statements confirmed present. Every `public`-schema table holding personal data has RLS enabled with an `auth.uid()`-keyed policy; every `re_engine` table is correctly excluded from client-role access via schema-level `REVOKE`/`GRANT` (Section 03.26), consistent with CDM Aggregate boundaries (RE Identity, Reference Data, Interaction History are RE-internal, never directly client-readable).

**Verdict: PASS.**

---

### 2.7 — Configuration and seed table check

All 10 configuration tables (Section 02b / 03.28) and all 15 seed/reference tables (Section 03.27, mapped 1:1 to Seed Gates S-01 through S-15) are present with full column definitions. Cross-checked against DOC-P3-03 §17 (the 15-row seed-gate table) and RE-DOC-05 §06 — every gate has a corresponding table in P3-04.

**Verdict: PASS.**

---

### 2.8 — Logical function → schema mapping check

All 61 logical functions from DOC-P3-03 were checked against P3-04's inline justifications (every table and trigger in P3-04 states which LF-numbers justify its existence, per Architecture Principle 1). Spot-verified categories:

- **Onboarding (LF-A01–A09):** all map to `profiles`, `household_members`, `onboarding_sessions`, `re_persona_assignment_rules`, `user_re_state` — present.
- **Candidate generation / hard constraints (LF-D01–D07):** all map to `re_class_dish_options`, `dishes`, `dish_ingredients`, `ingredients`, `never_list` — present, with the ingredient-level safety path (GR-06) explicitly preserved.
- **Scoring (LF-E01–E08):** all map to config tables, `user_taste_vectors`, `re_cohort_class_priors`, `re_dish_bandit_state`, `not_today_suppression` — present, with `FinalScore` itself correctly absent as a stored column (RUNTIME_CALC, per Principle 4).
- **Safety gates (LF-H01–H04):** all map to `suggestion_logs` plus the relevant reference columns (`dishes.diet_type`/`is_jain`, `re_meal_classes.planning_role`) — present.
- **Learning loop (LF-J01–J09):** all map to `interaction_events`, `user_re_state`, `user_taste_vectors`, `re_dish_bandit_state`, `dish_features` — present.

No logical function from P3-03 was found to reference a table, column, or computation that does not exist in P3-04.

**Verdict: PASS.**

---

### 2.9 — Runtime dependency (P3-03A) representation check

P3-03A's read/write matrix (61 rows) and configuration classification (47 parameters) were checked against P3-04. Every parameter classified `CONFIG_TABLE` in P3-03A has a corresponding row-holding config table in P3-04; every parameter classified `RUNTIME_CALC` correctly has **no** column anywhere in P3-04 (verified absent, not just unmentioned — e.g., there is no `final_score` column on any table, no `current_weight_tier` column on `user_re_state`).

**Verdict: PASS.**

---

### 2.10 — Overall readiness verdict

**ALL CHECKS PASS. No Architecture Gap Report is required.** DOC-P3-04 v1.2 is implementation-ready in full. Parts (b), (c), and (d) of DOC-P3-05 may proceed as a faithful, zero-deviation translation of the approved DDL into numbered, ordered, production-safe migration files.

One process note, not a gap: per Section 2.4 above, three derived-data mechanisms are CRON/batch jobs rather than triggers. P3-05 will provide the SQL-level function bodies these jobs invoke (since they are PL/pgSQL functions just like the trigger functions), but the *scheduling configuration* (cron expression, Supabase Scheduled Function setup) is explicitly deferred to DOC-P4 as a service-specification concern, consistent with DOC-P3-04 Section 01 Principle 6's "derive once, read many" framing, which describes *what* gets derived and *when* in business terms, not the infrastructure mechanism that triggers the schedule.

---

## Phase 3 — Non-Negotiable Rule: Confirmation

This document introduces **zero new tables, columns, relationships, triggers, indexes, constraints, configuration parameters, derived fields, or persistence rules** beyond what Phase 2 confirmed already exists in DOC-P3-04 v1.2. Parts (b)–(d) will be held to the same rule, verified the same way: every migration statement traced to a specific P3-04 section before it is written, not invented during the writing of the migration file itself.

---

## Phase 4 — Traceability Convention for Parts (b)–(d)

Every migration file produced in the remaining parts will carry a standard header comment block:

```sql
-- Migration: 0NN_description.sql
-- Implements: DOC-P3-04 §0X.YY (table/object name)
-- Logical functions: LF-XXX, LF-YYY (from DOC-P3-03)
-- Governance refs: P3-03A §0Z (read/write matrix row, execution classification)
-- CDM entities: Entity NN (name)
-- CDM invariants enforced: Invariant N (if applicable)
```

This makes the one-to-one traceability requirement mechanically checkable in every file, not just asserted in prose.

---

## Phase 5 — Migration Philosophy and Ordering Strategy

This section states the *strategy* that Parts (b)–(d) will follow. The actual numbered files appear in those parts; what follows is the production-safety reasoning that determines their order and structure.

### 5.1 — Migration ordering principle

Migrations are ordered strictly by the dependency layers already established in DOC-P3-02 Section 19 (Entity Dependency Map, Layers 0–8) and validated against P3-04's own FK dependency chain (Section 04). The ordering is:

1. **Schema and extension setup** — `CREATE SCHEMA re_engine`, `REVOKE`/`GRANT` lockdown (P3-04 §03.26), required Postgres extensions (`pgcrypto` for `gen_random_uuid()`).
2. **Pure reference structural tables with no FK dependencies** — `re_states`, `re_main_cohorts`, `tags`, `ingredients` (these have no foreign keys pointing *out*, only being pointed *at*).
3. **First-layer dependents** — `re_personas` (→ `re_main_cohorts`), `re_subcohorts` (→ `re_main_cohorts`), `re_meal_classes`.
4. **Second-layer dependents** — `re_cohorts` (→ `re_personas`, `re_states`), `re_class_dish_options`, `re_meal_class_overlap_rules`, `re_addon_classes`.
5. **`auth.users`-dependent tables** — `profiles` (this is the first table requiring Supabase's own `auth` schema to already exist, which it does by platform default — no ordering action needed beyond confirming this assumption explicitly here).
6. **Profile-dependent tables** — `household_members`, `onboarding_sessions`, `consent_records`, `user_re_state`, `user_taste_vectors`, `never_list`, `not_today_suppression`, `variety_window_state`, `re_dish_bandit_state`.
7. **Content tables depending on reference + extension setup** — `dishes` (depends on nothing for its own creation, but its trigger in step 9 depends on `dish_ingredients` existing), `dish_combos`.
8. **Junction tables** — `dish_ingredients`, `dish_tags`, `dish_combo_items`, `re_class_dish_options` (cohort-side already in step 4; this confirms the dish-side FK target `dishes` exists by this point).
9. **Trigger and function deployment** — `fn_derive_dish_attributes`, `fn_propagate_ingredient_change`, `fn_sync_profile_allergen_union`, `fn_update_dish_genome_vector`, and their `CREATE TRIGGER` statements — deployed only *after* every table they reference exists, never interleaved earlier.
10. **Plan and interaction tables** — `week_plans`, `plan_slots`, `addon_slots`, `interaction_events`, `suggestion_logs`, `context_log`, `weather_cache`.
11. **Configuration tables** — all 10 `re_engine` config tables (these have no FK dependencies on anything except, in `re_cohort_class_priors`'s case, `re_cohorts` and `re_meal_classes`, both already created by step 4).
12. **Operational/audit tables** — `audit_log`, `derivation_conflicts`, `coverage_gap_log`, `safety_gate_log`, `push_notification_logs`, `feature_flags`, `etl_job_runs`.
13. **Partitioning setup** — partition parent tables and the first N monthly child partitions for `interaction_events` and `suggestion_logs` (P3-04 §07).
14. **RLS enablement and policy creation** — applied last, only after every table it references is confirmed to exist (an RLS policy referencing a non-existent table or wrong column would fail to apply, so this ordering is also a natural validation step).
15. **Index creation** — deliberately placed after data-bearing DDL but it is noted that for a brand-new database (no existing rows), index creation order relative to table creation has no performance implication; this ordering is chosen purely for **migration file readability** (schema, then access patterns, then security), not because Postgres requires it.

### 5.2 — Idempotent migration strategy

Every migration file in Parts (b)–(d) will use `CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`, `CREATE OR REPLACE FUNCTION` (already inherently idempotent), and `DO $$ BEGIN ... EXCEPTION WHEN duplicate_object THEN NULL; END $$;` wrapper blocks for `CREATE TRIGGER` and `CREATE POLICY` statements, which Postgres does not natively support an `IF NOT EXISTS` clause for. This ensures any migration file can be re-run safely against a database where it (or an earlier interrupted attempt) has already partially applied — directly serving the production-safety requirement in Phase 5 of the founder's brief.

### 5.3 — Rollback strategy

Each numbered migration file `0NN_description.sql` will be paired with a `0NN_description_rollback.sql` file that reverses it in strict opposite order (drop policies before dropping the table they protect; drop triggers before dropping the functions they call; drop child partitions before the parent; drop dependent tables before the tables they reference). Rollback files are written at the same time as the forward migration, not as an afterthought — this is stated as a Part (b)/(c)/(d) authoring rule now, to be followed mechanically when those parts are produced.

### 5.4 — Seed data loading sequence

Seed data loading follows the exact same dependency order as Section 5.1 steps 2–4 and 11, and is gated by the 15 seed-gate row-count validations (Contract 14.5, P3-04) run immediately after each seed file, not just once at the very end — so a failure in seed file 7 of 15 is caught at file 7, not discovered only after all 15 have attempted to load.

### 5.5 — Validation scripts, post-migration verification, and smoke tests (strategy only — scripts themselves appear in Part (d))

Three tiers of post-migration verification are planned for Part (d):
1. **Structural verification** — re-run the exact checks from Phase 2 of this document (table/column/constraint/trigger existence) against the live database, not just the migration files, to confirm what was *intended* matches what was *applied*.
2. **Seed gate verification** — all 15 row-count checks (Contract 14.5).
3. **Smoke tests** — a minimal end-to-end exercise: insert one seed-derived test profile, run one onboarding sequence through to `assignPersona()`, generate one week plan, run all 4 safety gates against the result, confirm zero violations. This smoke test directly exercises the trigger chain added in P3-04 §03.6A (link a test dish to test ingredients, confirm `diet_type`/`is_jain`/`allergen_flags` derive correctly, then update the test ingredient and confirm propagation fires).

---

## Phase 6 — Quality Gate Statement for Part (a)

| Check | Status |
|---|---|
| Every architectural element implemented exactly once (in the sense of: counted exactly once in this readiness assessment, with no double-counting across sections) | ✅ Confirmed via direct extraction counts (Section 2.1–2.9) |
| Nothing omitted | ✅ All 60 tables, all 4 trigger functions, all 10 config tables, all 15 seed tables accounted for |
| Nothing duplicated | ✅ Counts in 2.1–2.7 match P3-04's own stated totals exactly (60 tables, 37 indexes, 42 RLS statements, 4 functions) |
| Nothing added beyond approved architecture | ✅ This document contains no new `CREATE TABLE`/`CREATE TRIGGER`/`CREATE INDEX` statements — only the *strategy* for ordering the ones already approved |
| Every dependency satisfied | ✅ Ordering in Phase 5.1 was derived from, and cross-checked against, the existing FK graph in P3-04 §04 — no forward reference exists in the proposed order |
| Fully traceable to P3-04 | ✅ Every count and verdict above cites a specific P3-04 section |

**Part (a) verdict: READY TO PROCEED TO PART (b).**

---

## Phase 7 — Migration Dependency Matrix

This matrix is the machine-verifiable form of the Phase 5.1 ordering narrative. Each planned migration file is listed with its file-level prerequisites and the specific reason for each dependency, traced to a P3-04 FK, trigger reference, or RLS reference. "Prerequisite" means: this file will fail to apply (or apply incorrectly) if the listed file has not already been applied.

| File | Prerequisite(s) | Reason for dependency |
|---|---|---|
| `001_extensions_and_schema_setup.sql` | *(none — first file)* | Creates `re_engine` schema and the `pgcrypto` extension that every subsequent `gen_random_uuid()` default depends on |
| `002_reference_tier0.sql` | `001` | `re_states`, `re_main_cohorts`, `tags`, `ingredients` have no FK dependencies on other application tables, but require the schema/extension from `001` to exist |
| `003_reference_tier1.sql` | `002` | `re_personas.main_cohort_code` → `re_main_cohorts` (002); `re_subcohorts.main_cohort_code` → `re_main_cohorts` (002); `re_meal_classes` has no inbound FK but is grouped here per Phase 5.1 step 3; **`public.meal_classes` (the public mirror table) is also created in this file as of v1.2 — see AGR-002 resolution below** |
| `004_reference_tier2.sql` | `003` | `re_cohorts.persona_id` → `re_personas` (003); `re_cohorts.state_code` → `re_states` (002); `re_weekly_class_plans.cohort_id` → `re_cohorts` (same file, 004); `re_meal_class_overlap_rules.class_code` → `re_meal_classes` (003); `re_addon_dish_options.addon_class_code` → `re_addon_classes` (same file, 004); `re_nonveg_logic.state_code` → `re_states` (002) |
| `005_profiles.sql` | `002` (for `home_state` FK) | `profiles.home_state` → `re_engine.re_states` (002); also requires Supabase's platform-provided `auth.users` table, which is an Environment Assumption (Phase 11), not a migration dependency this project controls |
| `006_profile_dependent_public.sql` | `005` | `household_members.profile_id`, `onboarding_sessions.profile_id`, `consent_records.profile_id` all → `profiles` (005) |
| `007_re_identity_interaction_history.sql` | `003`, `005` | `user_re_state.persona_id` → `re_personas` (003); all six tables in this file reference `profiles.id` (005) as an **app-enforced, non-FK** cross-schema link (P3-04 §04) — listed as a dependency here because the *application logic* requires `profiles` rows to exist first, even though Postgres itself would not reject the DDL otherwise |
| `008_content_core.sql` | `001` | `dishes`, `dish_combos` have no FK dependency on anything created so far (self-referencing `parent_dish_id` resolves fine on an empty table); requires only the schema/extension setup |
| `009_content_junctions.sql` | `002`, `008` | `dish_ingredients.ingredient_id` → `ingredients` (002); `dish_ingredients.dish_id` → `dishes` (008); `dish_tags.tag_id` → `tags` (002); `dish_tags.dish_id` → `dishes` (008); `dish_combo_items.combo_id` → `dish_combos` (008) |
| `010_trigger_functions_and_triggers.sql` | `009` (and transitively `002`, `008`) | All 4 trigger functions and their `CREATE TRIGGER` statements reference `dish_ingredients`, `ingredients`, `dish_tags`, and `household_members` — every referenced table must exist before a trigger can be attached to it; **`public.derivation_conflicts` is also created in this file as of v1.2, immediately before `fn_derive_dish_attributes()`, since that function writes to it — see AGR-003 resolution below** |
| `011_planning_tables.sql` | `003` (meal_classes mirror — corrected v1.2), `005`, `006`, `008` | `plan_slots.class_code` → `public.meal_classes` (now created in file `003`, per AGR-002 resolution); `week_plans.profile_id` → `profiles` (005); `addon_slots.household_member_id` → `household_members` (006); `plan_slots.selected_dish_id` → `dishes` (008) |
| `012_interaction_audit_appendonly.sql` | `005`, `008` | `interaction_events.profile_id`/`dish_id`, `suggestion_logs.profile_id`/`dish_id`, `context_log.profile_id` all reference `005`/`008`; `weather_cache` has no FK dependency but is grouped here per domain (context/append-only) |
| `013_config_tables.sql` | `001` | All 10 config tables are standalone key-value or rule tables with no outbound FK except `re_context_multipliers` and `re_engine_versions`, which have none either — only the schema must exist |
| `014_persona_assignment_and_priors.sql` | `003`, `004` | `re_persona_assignment_rules` → `re_main_cohorts`, `re_subcohorts`, `re_states`, `re_personas` (all in 002–003); `re_cohort_class_priors` → `re_cohorts` (004), `re_meal_classes` (003) |
| `015_operational_audit_public.sql` | `001` | `audit_log`, `coverage_gap_log`, `safety_gate_log`, `feature_flags`, `etl_job_runs` have no inbound FK requirements; `push_notification_logs.profile_id` → `profiles` (005). **`derivation_conflicts` relocated to file `010` as of v1.2 — see AGR-003 resolution below; no longer created in this file.** |
| `016_dish_features.sql` | `008` | `dish_features.dish_id` is a soft reference to `dishes` (008), same non-enforced-cross-context pattern as `re_class_dish_options` |
| `017_initial_partitions.sql` | `012` | Monthly child partitions cannot be created until the parent partitioned tables (`interaction_events`, `suggestion_logs`) exist |
| `018_meal_classes_mirror_sync.sql` | *(retired — no longer creates any object, as of v1.2)* | **AGR-002 RESOLVED (v1.2):** `public.meal_classes` was relocated to file `003` (it was always intended to live there per Phase 5.1's original narrative; Phase 8.1's earlier allocation to this file was the actual defect). This file number is retained as an intentionally empty placeholder — not deleted, not reused for a different object — so no other file's numbering shifts. The file's sole remaining content is a comment explaining this history. |
| `019_rls_policies.sql` | `005, 006, 007, 008, 009, 011, 012, 015, 016, 018` (every `public`-schema table with RLS) | An RLS policy referencing a table or column that does not yet exist fails outright — this file must be last among structural files for exactly that reason, which doubles as a built-in validation step (Phase 5.1, step 14 reasoning) |
| `020_indexes.sql` | All of `002`–`019` | No technical requirement forces indexes last on an empty database, but every index in this file references a real column on a real table, so listing this file last guarantees no index statement can reference a column that was renamed or reconsidered earlier in the sequence — a defensive ordering choice, stated as such |

**Note on `018` (superseded by v1.2 — retained for history):** The original v1.1 text here defended splitting `meal_classes` into its own file as an organisational choice. That defense was built on a false premise — Phase 7's *other* row for file `011` simultaneously claimed `meal_classes` already existed by file `003`, which `018` directly contradicted by claiming to be the file that actually created it. This was AGR-002: a genuine self-inconsistency inside this governance document, not a defensible organisational choice. It is resolved at v1.2 by moving `meal_classes` to file `003` (Section 8.1) and retiring file `018` as an intentionally empty placeholder, detailed in the AGR-002 resolution record below.

---

## Phase 8 — Object-to-Migration Allocation Matrix

Every database object named anywhere in DOC-P3-04 is allocated to exactly one migration file below. This matrix is the mechanical cross-check that nothing is implemented twice and nothing is left unallocated.

### 8.1 — Tables (60 of 60 allocated)

| Migration file | Tables allocated |
|---|---|
| `002_reference_tier0.sql` | `re_states`, `re_main_cohorts`, `tags`, `ingredients` |
| `003_reference_tier1.sql` | `re_personas`, `re_subcohorts`, `re_routing_rules`, `re_meal_classes`, `meal_classes` (public mirror — relocated here at v1.2, AGR-002) |
| `004_reference_tier2.sql` | `re_meal_class_overlap_rules`, `re_class_dish_options`, `re_addon_classes`, `re_addon_dish_options`, `re_cohorts`, `re_weekly_class_plans`, `re_household_addon_plans`, `re_nonveg_logic`, `re_city_migration_overlays` |
| `005_profiles.sql` | `profiles` |
| `006_profile_dependent_public.sql` | `household_members`, `onboarding_sessions`, `consent_records` |
| `007_re_identity_interaction_history.sql` | `user_re_state`, `user_taste_vectors`, `never_list`, `not_today_suppression`, `variety_window_state`, `re_dish_bandit_state` |
| `008_content_core.sql` | `dishes`, `dish_combos` |
| `009_content_junctions.sql` | `dish_ingredients`, `dish_tags`, `dish_combo_items` |
| `010_trigger_functions_and_triggers.sql` (table objects only — functions/triggers catalogued separately in 8.2) | `derivation_conflicts` (relocated here at v1.2, AGR-003 — co-located with the function that writes to it) |
| `011_planning_tables.sql` | `week_plans`, `plan_slots`, `addon_slots` |
| `012_interaction_audit_appendonly.sql` | `interaction_events`, `suggestion_logs`, `context_log`, `weather_cache` |
| `013_config_tables.sql` | `re_weight_ladder_config`, `re_scoring_config`, `re_event_weights`, `re_confidence_config`, `re_city_overlay_config`, `re_variety_rules`, `re_class_affinity_config`, `re_context_multipliers`, `re_festival_calendar`, `re_engine_versions` |
| `014_persona_assignment_and_priors.sql` | `re_persona_assignment_rules`, `re_cohort_class_priors` |
| `015_operational_audit_public.sql` | `audit_log`, `coverage_gap_log`, `safety_gate_log`, `push_notification_logs`, `feature_flags`, `etl_job_runs` |
| `016_dish_features.sql` | `dish_features` |
| `018_meal_classes_mirror_sync.sql` | *(none — retired placeholder as of v1.2, AGR-002)* |

**Count check (v1.2, post AGR-002/AGR-003): 4+5+9+1+3+6+2+3+1+3+4+10+2+6+1+0 = 60.** (File-by-file: 002=4, 003=5 [+1 meal_classes], 004=9, 005=1, 006=3, 007=6, 008=2, 009=3, 010=1 [+1 derivation_conflicts], 011=3, 012=4, 013=10, 014=2, 015=6 [−1 derivation_conflicts], 016=1, 018=0 [−1 meal_classes, now retired].) Still matches P3-04's own table count exactly — this was a reallocation between files, not a change in total object count. No table appears in two files; no table is absent from all files.

### 8.2 — Functions and triggers (4 of 4 allocated)

| Migration file | Object |
|---|---|
| `010_trigger_functions_and_triggers.sql` | `fn_derive_dish_attributes()` + `trg_derive_dish_attributes` |
| `010_trigger_functions_and_triggers.sql` | `fn_propagate_ingredient_change()` + `trg_propagate_ingredient_change` |
| `010_trigger_functions_and_triggers.sql` | `fn_sync_profile_allergen_union()` + `trg_sync_allergen_union` |
| `010_trigger_functions_and_triggers.sql` | `fn_update_dish_genome_vector()` + `trg_update_genome_vector` |

All four are deliberately grouped in one file rather than scattered across the files of the tables they reference, because they form a single coherent "derived-data correctness layer" that should be reviewable as one unit — this groups by *concern*, not strictly by *first-eligible-dependency-order*, and is called out here as a readability decision, not a dependency violation (file `010`'s prerequisites already cover every table these functions touch).

### 8.3 — Indexes (37 of 37 allocated)

All 37 indexes are allocated to `020_indexes.sql`, organised internally by the table they belong to, in the same order tables were introduced across files `002`–`018`. No index is created inline within a `CREATE TABLE` file under this allocation scheme — this is a deliberate departure from how P3-04's prose presents them (inline, for readability of the architecture document) versus how Part (b)/(c) will implement them (consolidated, for migration-file clarity), and is noted as a presentation choice with zero effect on the resulting database object.

### 8.4 — RLS policies (42 of 42 allocated)

All 42 RLS `ENABLE`/`CREATE POLICY` statements are allocated to `019_rls_policies.sql`, for the same consolidation reasoning as 8.3, and because — as already noted in Phase 7 — this file's position last among structural files is itself a validation mechanism.

### 8.5 — Configuration tables (10 of 10 allocated)

Allocated to `013_config_tables.sql` (table 8.1 above). Population of these tables with their actual seed *values* (the weight-ladder numbers, event weights, etc. — all `[CONFIRMED]` in DOC-P3-03 §16) is a **Part (d)** data-loading concern, not a Part (b)/(c) structural concern — the distinction between "create the config table" and "load the config values" is maintained throughout this matrix.

### 8.6 — Seed tables (15 of 15 allocated)

Allocated across `002`, `003`, `004` (table structures, 8.1 above). Their data — the ~30,000 rows from `Indian_Meal_Cohort_Persona_DB_v3.xlsx` — is exclusively a **Part (d)** concern, gated by the 15 seed-gate validations (Contract 14.5).

### 8.7 — Partitions

Allocated to `017_initial_partitions.sql` (first N monthly partitions for `interaction_events` and `suggestion_logs`). Ongoing future-partition creation (the "create next month's partition" scheduled job referenced in P3-04 §07) is a DOC-P4 service/cron concern, not a one-time migration file concern — this boundary is restated here for consistency with the Phase 2.4/2.10 boundary already drawn around CRON jobs.

### 8.8 — Validation scripts

Not allocated to any file number in the `001`–`020` structural sequence. Per the agreed 4-part split, validation scripts belong entirely to **Part (d)**, where they will receive their own numbering series (planned: `900`–`999`, kept visually distinct from the `001`–`020` structural range so a reviewer can immediately tell "this changes the schema" from "this only checks the schema").

### 8.9 — Allocation completeness statement

Every object category named in the founder's Phase 8 instruction — tables, functions, triggers, indexes, RLS policies, configuration tables, seed tables, partitions, validation scripts — has been allocated above, either to a specific file in the `001`–`020` range or explicitly assigned to Part (d)'s `900`–`999` range. **No object is allocated to more than one file. No object is missing an allocation.**

---

## Phase 9 — Transaction Boundary Strategy

**Default rule:** every numbered migration file (`001`–`020`) executes as a **single implicit transaction**, which is Supabase/Postgres's default behaviour for a `.sql` migration file run through the standard migration runner — no explicit `BEGIN`/`COMMIT` wrapping is added unless an exception below requires different behaviour. If any statement in the file fails, the entire file's changes roll back atomically; no file can apply "partially."

**Why this is safe for files `001`–`016` and `018`–`020`:** each of these files only creates new objects (`CREATE TABLE`, `CREATE FUNCTION`, `CREATE INDEX`, `CREATE POLICY`) that do not yet exist anywhere else in the database. An all-or-nothing failure mode is strictly preferable to a partial one, since a half-created table with no indexes or no RLS policy would be a worse state than "the table doesn't exist yet."

**Intentional exception 1 — `017_initial_partitions.sql`:** `CREATE TABLE ... PARTITION OF ...` statements for multiple months are still wrapped in the same single-transaction default, but this file is explicitly documented as safe to **re-run** (idempotent, per Phase 10 below) if it fails partway — re-running it after a partial application is the recovery path, not a manual partial-rollback.

**Intentional exception 2 — `010_trigger_functions_and_triggers.sql`:** `CREATE OR REPLACE FUNCTION` is itself idempotent and transactional; however, the `CREATE TRIGGER` statements use the `DO $$ ... EXCEPTION WHEN duplicate_object ...` wrapper pattern (Phase 5.2 of this same document) specifically so that re-running this file after a partial failure does not error out on "trigger already exists" — each trigger creation is independently guarded *within* the single enclosing transaction, not run as separate transactions.

**COMMIT/ROLLBACK expectation, stated plainly:** a developer or CI pipeline running any file in `001`–`020` should expect exactly one of two outcomes — the file fully applies and the migration tool records it as applied, or the file fails and the database is left in **exactly the state it was in before the file ran**. There is no documented or supported "partially applied" state for any structural migration file. Part (d)'s data-loading files (the `900`-series and any seed-loading files) follow a different, additive transaction strategy described in that part when it is written, since loading 2,952 cohort rows in one transaction versus per-batch transactions is a Part (d) performance decision, not a Part (a) governance decision.

---

## Phase 10 — Migration Failure Recovery Policy

**Mandatory behaviour on failure:** if any migration file `00N` fails during application — in any environment, including local development — the **immediate and only sanctioned next action** is to read the error, identify the specific statement that failed, and fix either the migration file or the precondition it depended on. **Proceeding to apply `00N+1` while `00N` is in a failed or unknown state is explicitly forbidden.**

**Rollback expectations:** because every structural file executes as a single transaction (Phase 9), a failed file requires **no manual rollback** — Postgres has already rolled it back automatically as part of the failed transaction. The paired `0NN_description_rollback.sql` file (Phase 5.3 of the original Part (a) content) is for **intentionally reversing a previously *successful* migration** (e.g., "we approved this and now need to undo it"), not for cleaning up after a failure — these are two different operations and must not be confused. A failed migration needs a fix-and-retry; a successful-but-now-unwanted migration needs the rollback file.

**Restart rules:** once the underlying cause of a failure is fixed, the corrected file is re-applied from the beginning (not resumed mid-file) — this is safe specifically because of the idempotent patterns mandated in Phase 5.2 (`IF NOT EXISTS`, `CREATE OR REPLACE`, the `duplicate_object` exception guard). No migration file in this specification is permitted to be written in a way that makes a clean restart unsafe.

**Validation before retry:** before re-applying a fixed file, the operator must re-run the relevant subset of the Phase 2 readiness checks against the *current* database state (not just re-read the migration file) — specifically: confirm no partially-created object from the failed attempt is lingering in an inconsistent state (e.g., a table created but its expected index missing, if the table and index were ever split across statement boundaries within one file — which they are not, per the consolidation decision in Phase 8.3, precisely to avoid this exact failure mode). This is the direct practical benefit of consolidating indexes into their own later file rather than interleaving them with table creation: a failure while creating table X never leaves an "table exists, index missing" ambiguity for a retry to worry about.

**Escalation:** for the seed-loading phase specifically (Part (d)), failure recovery is stricter — given GR-08/Contract 14.5's "the system must not serve any recommendation request on partial seed data" rule from P3-04, a failed seed file blocks not just the next seed file but **all application traffic to the affected environment** until resolved. This is restated here as a governance rule that Part (d) must implement, not a new rule invented now.

---

## Phase 11 — Migration Naming and Numbering Convention

**File naming pattern:** `{NNN}_{description}.sql`, where `NNN` is a zero-padded three-digit number, and `{description}` is a lowercase, underscore-separated short name matching the table/object group it creates (e.g., `005_profiles.sql`, `013_config_tables.sql`).

**Rollback file naming pattern:** `{NNN}_{description}_rollback.sql` — same number and description as its forward migration, with `_rollback` appended, stored in the **same directory** as the forward file (not a separate `rollback/` subfolder), so the pairing is visually obvious in any file listing sorted alphabetically.

**Numbering ranges, reserved by purpose:**

| Range | Purpose |
|---|---|
| `001`–`020` | Structural migrations (this document's Phase 7/8 allocation) |
| `021`–`099` | Reserved for structural migrations added during Parts (b)/(c) drafting if the 20-file plan above needs subdivision — **not** for new architectural objects, only for splitting an already-allocated object into a smaller file if a single file proves too large to review comfortably |
| `100`–`199` | Seed data loading files (Part (d)), one file per seed gate or logical group of seed gates |
| `900`–`999` | Validation, verification, and smoke-test scripts (Part (d)) |

**Folder organisation**, consistent with the repo structure already established in `CLAUDE.md` and the project's `code/migrations/` convention:

```
code/
  migrations/
    001_extensions_and_schema_setup.sql
    001_extensions_and_schema_setup_rollback.sql
    002_reference_tier0.sql
    002_reference_tier0_rollback.sql
    ...
    020_indexes.sql
    020_indexes_rollback.sql
    100_seed_re_states.sql
    ...
    900_structural_validation.sql
    901_seed_gate_validation.sql
    902_smoke_test.sql
```

**Naming rule for description segments:** the description always matches the dominant noun used for that file's allocation in Phase 8.1 (e.g., a file allocated `re_states, re_main_cohorts, tags, ingredients` is named for its *tier* — `reference_tier0` — rather than enumerating all four table names, to keep filenames readable; the authoritative mapping of which tables live in which file is this document's Phase 8.1 matrix, not the filename itself).

---

## Phase 12 — Verification Ownership Matrix

| Verification activity | Performed by | Detail |
|---|---|---|
| Schema validation (tables/columns/constraints exist) | **SQL script** | Re-run of the Phase 2.1–2.2 extraction-style checks, expressed as `information_schema` queries, executed automatically after every structural migration file in CI |
| FK validation | **SQL script** | `information_schema.table_constraints` / `key_column_usage` queries confirming every FK declared in P3-04 §04 exists with the correct `ON DELETE`/`ON UPDATE` behaviour |
| Trigger validation | **SQL script** | Confirms all 4 functions and 4 triggers from Phase 2.3 exist and are attached to the correct table/event combination |
| RLS validation | **SQL script + manual review** | The *presence* of RLS being enabled and policies existing is SQL-script-checkable (`pg_policies` system view); whether a given policy's `USING` clause actually achieves the intended access boundary (e.g., "a user truly cannot read another user's `plan_slots`") requires a **manual review** pass, since this is a logical-correctness question a script can only partially approximate without executing as multiple distinct authenticated test users |
| Seed validation | **SQL script (automation/CI)** | The 15 seed-gate row-count checks (Contract 14.5) are fully mechanical and run as part of the CI pipeline before any deploy is permitted to proceed |
| Smoke testing | **Automation/CI, with manual sign-off** | The end-to-end smoke test described in Phase 5.5 (onboarding → plan generation → safety gates) is scripted and run by CI, but its *first* successful run in a new environment requires a human to review the output before the environment is marked production-ready — subsequent runs are fully automated gatekeepers |
| Idempotency check (can a file be safely re-run) | **Manual review, once per file, at authoring time** | Confirmed by a reviewer reading each migration file at the time it is written, per the Phase 5.2 patterns — this is a one-time authoring-time review per file, not a recurring runtime check, since idempotency is a property of the SQL text itself |
| Migration ordering / dependency satisfaction | **SQL script (automation/CI)** | The migration runner itself enforces ordering by filename; a CI step additionally cross-checks the *applied* migration list against the Phase 7 dependency matrix to catch any case where a later file was somehow applied before an earlier prerequisite (which should be structurally impossible given sequential numbering, but is checked anyway as a defensive measure) |

---

## Phase 13 — Environment Assumptions

This specification is written against, and assumes, the following platform facts. Any environment where these assumptions do not hold requires this document to be revisited before migrations are applied.

**Platform:** Supabase-managed PostgreSQL (per DOC-P3-01/DOC-10 technology stack decision already on record). PostgreSQL major version: 15+ (Supabase's standard managed version at the time of writing).

**Required extensions:** `pgcrypto` (for `gen_random_uuid()`, used as the default on every `uuid` primary key in this specification). No other extension is required by anything in DOC-P3-04 — specifically, **no `pgvector` extension** is required at this stage, consistent with P3-04 §06/§12's explicit decision to defer vector-index adoption until candidate pool sizes justify it.

**Schemas assumed to pre-exist, not created by this specification:** `auth` (Supabase platform-managed, contains `auth.users`, which `public.profiles.id` references). `public` (Postgres default schema, always present). `re_engine` is the one schema this specification *does* create (`001_extensions_and_schema_setup.sql`).

**Roles assumed to exist, per Supabase platform convention:** `anon` (unauthenticated client role), `authenticated` (logged-in client role), `service_role` (privileged backend role used by Edge Functions). This specification's `019_rls_policies.sql` and the `REVOKE`/`GRANT` statements in `001` assume these three roles already exist with their standard Supabase-provided privileges — they are not created here.

**Privilege assumption:** the role applying these migrations (typically `postgres` or a Supabase migration-runner service account) must have sufficient privilege to `CREATE SCHEMA`, `CREATE TABLE`, `CREATE FUNCTION` with `SECURITY DEFINER`, `CREATE TRIGGER`, `ALTER TABLE ... REVOKE/GRANT`, and `CREATE POLICY`. This is the standard privilege level of a Supabase project's default Postgres superuser/owner role and requires no special elevation request.

**Platform dependency — partitioning:** native PostgreSQL declarative partitioning (`PARTITION BY RANGE`) is assumed available, which it is on any Postgres 10+ instance, so no extension or special configuration is needed beyond the base platform.

**Platform dependency — scheduled jobs:** this specification's structural files (`001`–`020`) do **not** depend on `pg_cron` or Supabase Scheduled Functions being configured — that configuration belongs to DOC-P4, per the boundary already drawn in Phase 2.4/2.10 and Phase 8.7. The *tables* these jobs write to are created here; the *jobs themselves* are not.

**Reproducibility statement:** given the same Supabase project tier (or any vanilla Postgres 15+ instance with the assumptions above satisfied) and the same migration files applied in the order specified by Phase 7, this specification is expected to produce a byte-for-byte identical schema in any environment — local development, staging, or production — which is the explicit purpose of stating these assumptions exhaustively rather than relying on "it works on my Supabase project."

---

## Phase 14 — Explicit Non-Goals

To prevent scope creep into later documents, Part (a) explicitly does **not**:

- Define the actual `INSERT` statements that load the ~30,000 seed rows — that is Part (d).
- Define the actual config table seed *values* (weight-ladder numbers, event weights, etc.) — those values are already `[CONFIRMED]` in DOC-P3-03 §16, but writing them as `INSERT` statements is Part (d)'s job, not this document's.
- Define `pg_cron` schedules, Supabase Scheduled Function configuration, or any other job-scheduling infrastructure — that is DOC-P4 (Service Specifications), as stated repeatedly above.
- Define Edge Function code, API contracts, or application-layer logic of any kind — DOC-P4 territory entirely; this document governs the *database*, not the services that call it.
- Introduce, modify, or reinterpret any architectural decision from DOC-P3-04 — every object named in this document is a direct copy of what P3-04 already approved; where this document makes an organisational choice (e.g., grouping indexes into one consolidated file, per Phase 8.3), that choice affects *which migration file* an object lives in, never *what the object is*.
- Perform disaster recovery planning, backup strategy, capacity planning, monitoring, alerting, SLO definition, or incident response planning — these were explicitly out of scope for DOC-P3-04 itself and remain out of scope here, reserved for DOC-P4-05 and DOC-P5-05 as previously agreed.
- Address multi-environment secrets management, connection string configuration, or deployment pipeline tooling beyond the bare migration-ordering and CI-verification responsibilities already stated in Phase 12 — these are DevOps/infrastructure concerns belonging to a future operations document.
- Make any claim about performance under load — Phase 13's "reproducibility" statement concerns *structural correctness*, not performance, which remains governed by DOC-P3-04 §11's existing performance assumptions, unchanged here.

---

## Phase 15 — Regression Review: This Enhancement Against the Originally Approved Part (a)

| Check | Finding |
|---|---|
| Has any approved architecture from DOC-P3-04 been modified? | **No.** Every table, column, constraint, trigger, index, and RLS policy referenced in Phases 7–14 above is the same object already approved in P3-04 v1.2. No DDL text was altered. |
| Has any implementation object been added beyond the approved architecture? | **No.** Phases 7–14 introduce *file organisation, ordering, naming, ownership, and process rules* — zero new tables, columns, functions, triggers, indexes, or constraints. The only "new" things in this enhancement are migration **filenames** and **numbering conventions**, which are implementation logistics, not architecture. |
| Does Part (a) remain an implementation governance document rather than a design document? | **Yes.** Every section added (Phases 7–14) answers an operational "how will this be carried out safely and traceably" question — dependency ordering, failure handling, naming, verification ownership, environment reproducibility, and scope boundaries — none of it answers a "what should the schema be" question, which remains exclusively DOC-P3-04's domain. |
| Can every future migration in Parts (b)–(d) be derived from this document without undocumented assumptions? | **Yes, with one explicit carry-forward note:** Phase 8.9 confirms 100% object allocation; Phase 7 confirms every file's prerequisites; Phase 11 confirms naming; Phase 12 confirms who verifies what; Phase 13 confirms the environment Parts (b)–(d) can assume. The one item intentionally left open for Part (d) to decide for itself — and explicitly flagged as such rather than silently assumed — is the internal transaction-batching strategy for bulk seed-row INSERTs (Phase 9's closing note), since that is a legitimate Part (d)-level performance decision, not something Part (a) should pre-decide. |

**Verdict: Part (a) enhancement is complete, additive-only, and introduces zero architectural drift.** Phases 1–6 (the original readiness assessment and migration-philosophy narrative) are retained unchanged below this point in the document; Phases 7–14 are new, inserted as governance extensions per the founder's request, with this regression review as the final word on their scope.

---

## Sign-off for Part (a)

| Field | Value |
|---|---|
| Document | DOC-P3-05 · Database Implementation and Migration Specification — Part (a), Enhanced |
| Status | ACTIVE — [FD-05, 2026-07-16] no Founder signature required for `[ACTIVE]` status; see naming standard amendment. Proceeding to Part (b) is a separate readiness question, unaffected by FD-05. |
| Architecture Gap Report required? | **No** — full readiness confirmed (Phases 1–6); reconfirmed by Phase 15 regression review after governance extension |
| New architecture introduced? | **None** — Phases 7–14 are implementation governance only (dependency ordering, file allocation, transaction strategy, failure recovery, naming, verification ownership, environment assumptions, non-goals) |
| Objects allocated to migration files | 60 of 60 tables, 4 of 4 functions/triggers, 37 of 37 indexes, 42 of 42 RLS statements, 10 of 10 config tables, 15 of 15 seed tables — all confirmed exactly-once allocation (Phase 8.9) |
| Next | Part (b) — Core schema and reference tables, as numbered migration files `001`–`009` per the Phase 7/8 allocation above |

## Phase 16 — Planning Corrections: AGR-002 and AGR-003 Resolution (v1.2)

Both corrections below were made at the root cause — this governance document — not as implementation workarounds, per the founder's explicit instruction.

### AGR-002 resolution

**Root cause confirmed:** Phase 7 (v1.1) contained two contradictory statements about where `public.meal_classes` is created — its own file `011` row said the table already existed by file `003`; its file `018` row said file `018` was the table's actual creation point. This was an internal inconsistency in Part (a) itself, not a defect in DOC-P3-04.

**Correction applied:**
- `meal_classes` reallocated to file `003` (Phase 8.1 table allocation matrix, corrected above) — restoring Phase 7's original, correct intent.
- File `018` retired as an intentionally empty placeholder. Its file number is preserved (not deleted, not reused) so no other file's numbering shifts — consistent with the founder's standing instruction against renumbering migrations once allocated.
- Downstream implementation consequence (minimum required, per founder instruction): file `011`'s `plan_slots.class_code` column now carries its FK to `public.meal_classes` directly inline, exactly as DOC-P3-04 §03.13 specifies — no deferred `ALTER TABLE` workaround is needed anymore, since the table now genuinely exists before file `011` runs.

### AGR-003 resolution

**Root cause confirmed:** `fn_derive_dish_attributes()` (file `010`) writes to `public.derivation_conflicts`, but that table was allocated to file `015` — five files later. This was the same class of defect as AGR-002: a planning-layer ordering error, not a flaw in the function's approved logic.

**Correction applied:**
- `derivation_conflicts` reallocated to file `010` (Phase 8.1, corrected above), created immediately before the function that writes to it — the same "co-located with its consumer" principle already used to justify grouping all 4 trigger functions together in one file.
- Removed from file `015`'s allocation.
- Downstream implementation consequence (minimum required): file `010` now creates this table before its trigger functions; file `015` no longer creates it. No other object in either file was touched.

### Why these are root-cause fixes, not workarounds

Both corrections change *where in the governance plan* an object is allocated — they do not change what the object is, what columns it has, what it's for, or any DOC-P3-04 architectural decision. The previous AGR-002 implementation response (a deferred `ALTER TABLE` in file `018`) was a legitimate workaround *given the flawed plan it had to operate within*; now that the plan itself is corrected, that workaround is no longer needed and has been removed. This is the distinction the founder drew explicitly: fix the plan first, then let the implementation follow the corrected plan naturally.


Founder confirmation to proceed to Part (b): ___________________________ Date: _______________
