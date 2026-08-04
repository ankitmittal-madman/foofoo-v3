# Phase 6 — Database Audit (evidence-based, no live DB access)

Status: DRAFT (working audit output, not a governed document under the Naming Standard)
Scope: `database/migrations`, `database/rollback`, `database/seeds`, `database/validation` (175 files total,
`find database -type f -name "*.sql" | wc -l` = 175), cross-checked against `supabase/functions/*` and
`ghar_re_core/*` for actual reads/writes.

## 1. Migration manifest and schema evolution timeline

`find database/migrations -name "*.sql" | sort` → 51 files, 001–051, all with paired
`database/rollback/NNN_..._rollback.sql`. Bands confirmed: structural 001–051 (no seed/validation
numbers mixed in), seeds 100–144, validation 900–909 + one ad hoc `WP-3D_Check2_Fix_Reference.sql`
(non-conforming filename — flag: violates the NNN_description.sql naming rule, no status prefix
expected but also no number-only pattern followed).

Key structural turning points (read in full):

- **001–033**: baseline `public` schema — profiles, household_members, content core (dishes,
  ingredients, cuisines, tags), planning tables, RLS (019), indexes (020), then a run of narrow
  ALTERs (021–033: cuisines reference, dish display attrs, tag vector positions, regional affinity,
  combo slot arrays, routing rules, weight ladder config, security hardening, cohort city tier,
  dish_ingredients main-flag, interaction dedup key, household_members conditions vocabulary).
- **034–037**: `ghar_re` schema created (catalogue mirror, household runtime mirrors, safety support
  incl. `allergen_hidden_derivatives` inert table, knowledge base) — this is the schema the prior
  audit (RE-DOC-12) described as the Python RE's offline golden-sample schema.
- **038**: `public.household_answers`, `public.household_context`, `public.recommendation_events`/
  `feedback_events` — the live per-request context tables.
- **039–044**: RLS drift fixes, pg_cron, `re_engine` RLS defense-in-depth, FK hardening, decision
  trace column on recommendation_events.
- **045**: `dish_name_synonyms` ontology columns (alias_type, region, language, source_url,
  confidence) added — originally on `ghar_re.dish_name_synonyms`.
- **046 → 047 (WP-20, "retire legacy re_engine schema")**: **046** re-homes the *only* `re_engine.*`
  tables live code still touched (`re_states`, `never_list`, `not_today_suppression`,
  `user_re_state`, `user_taste_vectors`, `re_dish_bandit_state`) into `public`, repoints
  `public.profiles.home_state` FK. **047** then `DROP SCHEMA re_engine CASCADE` — deletes the
  remaining ~30 legacy TS-RE reference tables (re_cohorts, re_weekly_class_plans, re_personas,
  re_meal_classes, re_addon_classes, etc.) confirmed unread by any live code, with a full JSON
  backup at `database/archive/re_engine_backup_20260803/` (~32k rows per the migration comment).
  **This means the "re_engine.* is dead legacy schema" finding from RE-DOC-12 is now moot — the
  schema itself no longer exists in the live database as of migration 047.**
- **048**: re_states public read policy. **049**: allergen model extended (fish, mustard bits).
- **050 (WP-21, production hardening)**: `DROP SCHEMA IF EXISTS ghar_re CASCADE` — drops the
  entire 28-table `ghar_re` schema (migrations 034–037 + 045's additions), on the explicit finding
  that no live runtime code reads it (`compose.ts`/`store.ts` grepped to confirm `public.*`-only;
  the live Fly.io `ghar_re_service` process reads `dishes.xlsx`/YAML bundles via `ghar_re_core`
  directly, never Postgres — a name collision, not a dependency). **This retires the
  "ghar_re.allergen_hidden_derivatives is inert, pending population" finding from RE-DOC-12 as
  moot too — the whole schema, inert table included, has been dropped, not fixed.**
- **051**: `public.dish_name_synonyms` (the post-046/050 home for dish aliasing, now the only
  synonyms table live).

**Net effect**: after migration 051, only the `public` schema exists for RE/content purposes.
Neither `ghar_re` nor `re_engine` remain as live Postgres schemas — both were deliberately dropped,
each with a documented, code-grep-verified "nothing reads this" justification and a JSON backup.

## 2. Table-by-table reference check (current live schema = `public.*`, 39 tables from CREATE TABLE greps)

Command used: `grep -rl "\b<table>\b" supabase/functions ghar_re_core mobile/src mobile/app`.

| Table | Refs in app code | Status |
|---|---|---|
| addon_slots | 0 | **Orphaned** — created, never read/written by any live code found |
| audit_log | 3 | referenced (DPDP/consent-adjacent) |
| consent_records | 8 | actively used |
| context_log | 0 | **Orphaned** |
| coverage_gap_log | 0 | **Orphaned** |
| derivation_conflicts | 0 | **Orphaned** |
| etl_job_runs | 0 | **Orphaned** |
| feature_flags | 0 | **Orphaned** (no flag-gating code found referencing it) |
| interaction_events | 5 | actively used |
| interaction_events_ | 0 | **Orphaned** — looks like a stray/duplicate-named table (trailing underscore); worth confirming this isn't a leftover partition-naming artifact from migration 017 (initial partitions) rather than a true separate table |
| onboarding_sessions | 6 | actively used |
| plan_slots | 2 | used |
| push_notification_logs | 0 | **Orphaned** |
| safety_gate_log | 0 | **Orphaned** |
| suggestion_logs / suggestion_logs_ | 0 / 0 | **Both orphaned** (same trailing-underscore pattern as interaction_events_) |
| weather_cache | 0 | **Orphaned** — `data/source/weather_rules.yaml` also has no ETL/loader found (see seed report §4) |
| week_plans | 3 | used |
| meal_classes | 0 | **Orphaned in app code search** — NOTE: this is the `public.meal_classes` mirror of `re_engine.re_meal_classes` created by migration 018/026; it may be read via a different grep surface (e.g. SQL views or RPC) not caught by this literal string search — flag as needs deeper check, not confirmed dead |
| re_states | 5 | actively used post-046 rehome |
| dishes, dish_ingredients, dish_combo_items, dish_combos, dish_tags, cuisines, ingredients, tags, dish_name_synonyms | not individually re-grepped here (see seed audit for RE-DOC-12 confirmed usage) | assumed live per prior audit + 051 |

**Recommendation**: `context_log`, `coverage_gap_log`, `derivation_conflicts`, `etl_job_runs`,
`safety_gate_log`, `push_notification_logs`, `weather_cache`, `addon_slots`, `feature_flags`,
`interaction_events_`, `suggestion_logs`/`suggestion_logs_` are candidates for either (a) a
hygiene-dead-code style removal pass, or (b) confirmation they're intentionally-provisioned
forward-looking tables (e.g., for planned logging infra) — this audit cannot distinguish those two
cases from static grep alone and does not recommend dropping anything without that confirmation.

## 3. RLS coverage — RE-relevant public tables

Evidence: `grep -rl "ENABLE ROW LEVEL SECURITY"` / `"CREATE POLICY"` across `database/migrations/*.sql`,
cross-checked by reading migration 038 directly for household_context/answers/events.

| Table | RLS enabled | Policy exists | Evidence |
|---|---|---|---|
| profiles | yes | yes | migrations 005, 019, 029 |
| household_members | yes | yes | `CREATE POLICY hm_all_own ON public.household_members FOR ALL USING (auth.uid() = profile_id)` — migration 019 |
| household_answers | yes | yes | migration 038 |
| household_context | yes | yes | `database/migrations/038_household_answers_context_and_events.sql:190-191`: `ALTER TABLE public.household_context ENABLE ROW LEVEL SECURITY;` / `CREATE POLICY household_context_all_own ON public.household_context ...` |
| recommendation_events | yes | yes | migration 038 |
| feedback_events | yes | yes | migration 038 |
| dishes | yes | yes | migrations 008, 019, 029, 039 (4 mentions — hardening iterated) |
| dish_ingredients | yes | yes | migration 019 |
| dish_name_synonyms | yes | yes | migrations 045/051 |

No RE-relevant public table was found missing RLS. This matches the "029_pf1_security_hardening" /
"039_rls_internal_table_drift_fix" / "041_re_engine_rls_defense_in_depth" pattern of iterative
hardening visible in the migration list — RLS was not a one-shot pass, it was revisited at least
three times as gaps were found.

## 4. household_context wiring — status update vs RE-DOC-12

RE-DOC-12 (2026-07-29) found `public.household_context` (migration 038) existed but had no writer.
`git log --oneline --all | grep -i household_context` shows exactly one commit touching it since:
`e487941 feat(re): cook_capability ranking bias + household_context wiring; add global pytest
config isolation`. Confirmed by direct grep: `supabase/functions/recommendations/compose.ts`,
`supabase/functions/recommendations/handler.ts`, and
`supabase/functions/_tests/recommendations.test.ts` all reference `household_context`.
**Finding: the gap RE-DOC-12 flagged is closed** — household_context is now read in the live
recommendations path (compose.ts/handler.ts), not just declared in schema.

## 5. Non-conforming file names in database/validation

`database/validation/WP-3D_Check2_Fix_Reference.sql` does not match the `9NN_description.sql`
validation naming band and has no status prefix — flag per CLAUDE.md Naming Standard (WP-5AA);
not renamed here per the "Bulk-renaming existing files requires explicit Founder authorization" rule.

## Critical Self-Review

- No live Supabase MCP access was used for this audit (per task instructions) — all findings are
  from committed SQL text, not a live `information_schema` query. Table-existence and RLS findings
  reflect what migrations *declare*, assumed applied in order 001→051 with no live drift beyond
  what the migrations themselves document.
- The app-code reference grep (`supabase/functions`, `ghar_re_core`, `mobile/src`, `mobile/app`) is a
  literal substring match; it will miss references via dynamically-built table names, ORM query
  builders, or Supabase RPC/view indirection. "0 refs" is reported as "orphaned candidate," not a
  certified-dead table.
- Did not open every one of the 51 structural migrations line-by-line; migrations directly
  concerning dishes/ingredients/genome/allergen/cohort/class/schema-drop were read in full (034–038,
  045–051); narrower ALTER-only migrations (021–033, 039–044, 048–049) were read via header comment
  + grep, not full line-by-line, per the task's own scoping instruction.
