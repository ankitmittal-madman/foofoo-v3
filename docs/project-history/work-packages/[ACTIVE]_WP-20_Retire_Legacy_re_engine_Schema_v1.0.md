# [ACTIVE]_WP-20_Retire_Legacy_re_engine_Schema_v1.0

**Status:** ACTIVE — cutover FULLY executed on production 2026-08-03. Migrations 046, 048, and 047
are all applied; edge functions (`cron-hard-delete`, `user-delete`, `user-export`) redeployed and
live-smoke-tested; validation 908 re-run post-deploy (passed); `re_engine` schema confirmed dropped;
RLS posture on the 6 re-homed tables re-confirmed post-drop. Full record: REPO-CERT-029
(`docs/project-history/certificates/[ACTIVE]_REPO-CERT-029_WP-20_Full_Cutover_Completion_v1.0.md`),
completing what REPO-CERT-028 (§6 below) left open.
**Version:** v1.0
**Date:** 2026-08-03
**Placement:** docs/project-history/work-packages/[ACTIVE]_WP-20_Retire_Legacy_re_engine_Schema_v1.0.md
**Supersedes:** N/A
**Dependencies:** none blocking; informs `audit-rls` (RLS posture of the re-homed tables) and `audit-rollback-readiness` (this WP's own rollback path) when either is next run.

---

## Executive Summary

The Founder asked for a schema audit: the live Supabase project carries three schemas
(`public`, `ghar_re`, `re_engine`) and asked which is used for what, with any data in an unused
schema migrated to the correct one before cleanup. Investigation (grounded in code — edge-function
imports, the Fly service's bundle-only startup, and `information_schema`/`pg_constraint` queries
against the live project) found:

- **`public`** — the live application schema (RLS-protected, client-facing). Active, authoritative.
- **`ghar_re`** — the current Python RE's offline knowledge/catalogue source, exported into the
  Fly service's baked bundle at build time. The Fly service never queries the DB at runtime. Active,
  authoritative for catalogue/knowledge.
- **`re_engine`** — the **legacy TypeScript RE's** schema (confirmed by its own code comments:
  `household/schema.ts` calls it "the LEGACY TypeScript RE's own onboarding flow ... retired and
  off the live request path"). ~32k rows across 26 populated tables, but only **3 tables** are still
  touched by live edge-function code: `re_states` (FK target of `public.profiles.home_state`),
  `never_list` and 4 other per-user RE-state tables (DPDP user-export/hard-delete). Everything else
  (`re_cohorts`, `re_weekly_class_plans`, `re_personas`, `re_meal_classes`, …) has zero code references.

So there was no single "unused schema" to sweep wholesale — `re_engine` is a **mix** of dead
reference data and a handful of still-live tables. This WP retires it correctly: preserve every row,
re-home the live tables into `public`, then drop the rest.

## 1. Evidence (how each schema's role was established)

| Claim | Evidence |
|---|---|
| `public` is the live schema | `supabase/functions/_shared/constants/schemas.ts`: "Public schema — client-facing content, RLS-protected"; `compose.ts`: "reads `public` — the LIVE application schema" |
| `ghar_re` is the RE's offline source, never queried live | Zero `ghar_re.*` references anywhere in `supabase/functions`; `ghar_re_service` startup (`lifecycle.py`) loads a `CatalogueProvider` from the **baked bundle**, never a DB connection |
| `re_engine` is the legacy TS-RE | `household/schema.ts:10`: "belong to `re_engine.re_routing_rules` — the LEGACY TypeScript RE's own onboarding flow ... confirmed by direct inspection (S40 ground-truth audit) to be retired" |
| Only 3 `re_engine` tables are still live | `grep -rn RE_ENGINE_SCHEMA supabase/functions` → exactly `hard-delete.ts` (5 per-user tables) and `user-export/store.ts` (`never_list`); `pg_constraint` shows `public.profiles.home_state → re_engine.re_states` as the only external FK into the schema |
| The rest is dead, not merely quiet | `pg_constraint` shows every other FK into `re_engine` is *internal to* `re_engine` (e.g. `re_weekly_class_plans → re_meal_classes`) — a self-contained legacy reference model with no external readers |

## 2. What was preserved (no record lost)

Every populated table in `re_engine` (26 tables, ~32,000 rows) was exported to JSON **before any
schema change**, committed at `database/archive/re_engine_backup_20260803/` (manifest + row counts
in that directory's `README.md`). This is independent of the re-homing below — even the ~30 tables
with zero live code references keep their data, permanently, in the repo.

## 3. The two-migration cutover

**Migration 046** (`database/migrations/046_rehome_re_engine_live_tables.sql`) — additive, safe to
run while `re_engine` still exists:
- Clones `re_engine.re_states` → `public.re_states` (structure + data), then repoints
  `public.profiles.home_state`'s FK from `re_engine.re_states` to `public.re_states`.
- Clones the 5 per-user RE-state tables (`never_list`, `not_today_suppression`, `user_re_state`,
  `user_taste_vectors`, `re_dish_bandit_state` — all 0 rows today) into `public`, RLS-enabled with
  no policies (service-role-only, matching the old posture), and `REVOKE`s `anon`/`authenticated`.
- **Found by testing:** the data-copy and the RLS/REVOKE steps are two separate `DO` blocks
  deliberately. `anon`/`authenticated` are Supabase-managed platform roles absent on a vanilla local
  Postgres; a `REVOKE ... FROM anon` failure must never be able to abort the data-copy loop and
  leave a table uncopied ahead of 047's drop. The REVOKE is wrapped in its own exception handler
  (`WHEN undefined_object`) and only warns.

**Validation 908** (`database/validation/908_re_engine_decommission_validation.sql`) — run after 046,
before 047: confirms every re-homed table has ≥ as many rows in `public` as its `re_engine` source,
confirms `profiles.home_state`'s FK no longer points at `re_engine`, and confirms no other FK
anywhere still points into `re_engine` (would make `047`'s `CASCADE` delete more than intended).

**Migration 047** (`database/migrations/047_drop_legacy_re_engine_schema.sql`) — `DROP SCHEMA
re_engine CASCADE`. Guarded: refuses to run if `public.re_states` doesn't exist yet (046 wasn't
applied). **Found by testing:** the guard and the drop must be **one `DO` block** (drop via
`EXECUTE`), not two separate top-level statements — confirmed on Postgres 16 that a client running
this script *without* `psql -v ON_ERROR_STOP=1` (the non-obvious default) would print the guard's
exception and then **still execute** a separate `DROP SCHEMA` statement that followed it. Folding
the drop into the same block means the `RAISE EXCEPTION` genuinely aborts before `EXECUTE` runs,
regardless of the calling client's error-stop setting.

Rollback files exist for both (`database/rollback/046_..._rollback.sql`,
`database/rollback/047_..._rollback.sql`); 047's rollback is a documented restore procedure (DDL
from the original migrations + data from the JSON backup) rather than a single inverse statement,
since undoing a `DROP SCHEMA CASCADE` of ~32k rows cannot be one SQL statement.

## 4. Edge-function code changes (committed, NOT yet deployed)

- `supabase/functions/_shared/constants/schemas.ts` — `RE_ENGINE_SCHEMA` export removed (replaced
  with a comment explaining the retirement and pointing at the re-homed tables/backup).
- `supabase/functions/_shared/mod.ts` — stops re-exporting `RE_ENGINE_SCHEMA`.
- `supabase/functions/_shared/services/scheduler/hard-delete.ts` — the 5 per-user tables now
  deleted via `PUBLIC_SCHEMA` instead of `RE_ENGINE_SCHEMA`.
- `supabase/functions/user-export/store.ts` — `never_list` now read via `PUBLIC_SCHEMA`.
- `supabase/functions/recommendations/compose.ts`, `supabase/functions/household/schema.ts` —
  comments updated to say `public.re_states` (was `re_engine.re_states`).
- No test file referenced `RE_ENGINE_SCHEMA` (checked — no test breakage); `supabase/functions` has
  no CI-runnable Deno available in this sandbox, so these edits are logic-reviewed but not
  typechecked here — **typecheck them (`deno task verify` per `supabase/README.md`) before deploy.**

## 5. Cutover runbook (the actual "how" for the next authorized session)

Execute strictly in this order — steps 1–2 can run any time; steps 3–5 are the hard cutover and
must not be reordered:

1. Apply `database/migrations/046_rehome_re_engine_live_tables.sql` to production (Management API
   or `supabase db push`). Safe: `re_engine` still exists, both copies coexist.
2. Run `database/validation/908_re_engine_decommission_validation.sql` against production. Must
   pass silently. If it raises, STOP — do not proceed to step 3.
3. Deploy the edited edge functions (`supabase functions deploy` for `hard-delete`'s scheduler
   consumer, `user-export`, and any function importing `_shared/mod.ts`/`constants/schemas.ts`).
   Confirm via a live smoke test: trigger (or dry-run) the hard-delete path and the user-export
   endpoint against a test profile and confirm both succeed reading/writing `public.*`.
4. Once step 3 is confirmed live and healthy, apply
   `database/migrations/047_drop_legacy_re_engine_schema.sql` to production.
5. Re-run `audit-rls` on the 6 re-homed `public` tables to confirm the RLS/REVOKE posture actually
   landed as intended on production (a REVOKE failure in step 1 only warns, per §3 — this step is
   the check that it didn't silently no-op on the real platform roles).

## 6. Execution record — 2026-08-03 (this session)

Steps 1 and 5 of the runbook above were executed against production this session, using the
Management API with the Founder's fresh in-conversation authorization to reuse the Supabase CLI's
existing stored login (`~/.supabase/access-token`):

- **Step 1 (migration 046) — DONE.** Applied to production. Verified: `public.re_states` holds all
  36 rows, `public.profiles.home_state`'s FK now points at `public.re_states`
  (`profiles_home_state_fkey`), and `database/validation/908_re_engine_decommission_validation.sql`
  passes silently against production.
- **Step 5 (audit-rls) — DONE, and it found a real bug.** `public.re_states` came up with RLS
  enabled and **zero policies** — silently unreadable by anon/authenticated, contradicting 046's own
  stated intent. Root cause: this project's `ensure_rls` platform event trigger auto-force-enables
  RLS on every new `public` table; `LIKE ... INCLUDING ALL` doesn't carry over a source table's RLS
  state, so the clone landed RLS-on-zero-policy by default. Fixed same-session by migration
  `048_re_states_public_read_policy.sql` (matching the `cuisines_public_read` /
  `meal_classes_public_read` convention exactly), applied to production and verified. Full findings:
  `rls-audit.md` (repo root). The 5 per-user tables re-homed alongside `re_states` correctly have
  zero policies by design (service-role-only, matching the old `re_engine` posture) — not a bug.
- **Step 2 (edge-function deploy) — BLOCKED, not attempted around.** Both `supabase functions
  deploy` (CLI) and an equivalent Management API call were refused by the harness's own permission
  classifier as a production-mutating action, even after the Founder's explicit in-conversation
  confirmation to proceed — chat-level authorization does not satisfy that gate. Per the assisting
  agent's own operating instructions, a blocked action must be reported, not routed around via a
  different tool that performs the same mutation. **This needs either a session with standing
  permission for `supabase functions deploy` (e.g. a permission rule in Claude Code settings), or a
  human running the three `supabase functions deploy` commands directly** (`cron-hard-delete`,
  `user-delete`, `user-export` — the only functions whose bundled code touches the edited files).
- **Step 3 (validate 908 again + apply 047) — NOT attempted, correctly gated.** 047's own hard
  prerequisite (step 2 confirmed live) is not met. Running it now would drop `re_engine` while the
  currently-deployed `hard-delete` and `user-export` functions still reference it, breaking DPDP
  hard-delete and user-export in production. This ordering was not relaxed even though the DB
  action itself was technically executable.
- **Step 4 (certificate + flip to ACTIVE) — NOT done**, per design: a certificate claiming
  completion requires the actual completion (steps 2–3) to have happened. This section IS the
  honest execution record for what *did* happen this session; the completion certificate is still
  pending steps 2–3.

## 7. Execution record — 2026-08-03 (later session, same day) — cutover completed

A later session the same day found a Founder-added standing permission for `supabase functions
deploy`/`supabase link` (satisfying §6's own stated remedy) and completed the remaining runbook
steps:

- Fixed a pre-existing, unrelated blocker first: `supabase/config.toml` had an invalid top-level
  `[functions]` table for the installed CLI version, breaking every `supabase` command. Removed it.
- **Step 2 (edge-function deploy) — DONE.** `cron-hard-delete`, `user-delete`, `user-export` all
  deployed via `supabase functions deploy` (needed `--import-map supabase/deno.json`, not
  auto-discovered by this CLI version).
- **Live smoke test — DONE**, against a Founder-designated test account: `user-export`
  (queued → complete, signed URL), `user-delete` (soft-deleted), `cron-hard-delete` (200, clean run
  against 0 real overdue profiles — confirmed no `re_engine` relation errors, but did not exercise
  the per-table purge loop against a real due row; that code was reviewed line-by-line instead).
- **Step 3 (validation 908 re-run) — DONE.** Passed, no rows, run against production post-deploy.
- **Step 4 (migration 047) — DONE.** `DROP SCHEMA re_engine CASCADE` applied to production;
  confirmed via `pg_namespace` that the schema no longer exists.
- **Step 5 (audit-rls re-check) — DONE.** All 6 re-homed tables confirmed: RLS enabled on every
  one; `re_states` has exactly its intended `re_states_public_read` policy; the 5 per-user tables
  correctly have zero policies (service-role-only, by design).
- **Certificate filed:** REPO-CERT-029 (full details, including two new standing Bash permissions
  added to `.claude/settings.local.json` this session for direct production `psql`/`curl` access).
  Status flipped DRAFT → ACTIVE accordingly.

## Critical Self-Review

- **The `cron-hard-delete` purge loop was not runtime-proven against a real due row** — see REPO-CERT-029.
  A future session with a genuinely overdue profile should close this specific residual gap.
- **The Founder's original framing ("migrate data from the unused schema") doesn't quite hold** —
  there wasn't one unused schema, there was one schema that's mostly dead but partly still live.
  This WP treats that nuance as the finding, not a reason to simplify the actual data.

## Versioning & Placement
v1.0, first issue. Companion backup: `database/archive/re_engine_backup_20260803/`. Companion
certificates: REPO-CERT-028 (partial cutover, migrations 046/048) and REPO-CERT-029 (full
completion, this WP's final status).

## Founder Sign-off

