# [ACTIVE]_REPO-CERT-029_WP-20_Full_Cutover_Completion_v1.0

**Status:** ACTIVE
**Version:** v1.0
**Date:** 2026-08-03
**Placement:** docs/project-history/certificates/[ACTIVE]_REPO-CERT-029_WP-20_Full_Cutover_Completion_v1.0.md
**Certifies:** WP-20 (Retire Legacy re_engine Schema) — FULL execution. Completes the runbook steps REPO-CERT-028 left open: edge-function redeploy, live smoke test, re-run of validation 908, and migration 047 (`DROP SCHEMA re_engine CASCADE`), all applied to production.
**Supersedes:** N/A (companion to, not a replacement of, REPO-CERT-028 — that certificate's own scope, migrations 046/048, stands as-is)

---

## What this certifies

This session completed the three steps REPO-CERT-028 explicitly left open, in the exact gated order the WP-20 work package's runbook (§5) requires, against the live Supabase project (`cmkswalqpmmqojwdmqbv`).

### Pre-flight fixes required before any of this was possible
- `supabase/config.toml` had an invalid top-level `[functions]\nverify_jwt = true` table — the
  installed CLI (v1.226.4) only supports per-function `[functions.<name>]` tables (confirmed via
  that CLI's own `supabase init` template), so this bare table broke config parsing for every
  `supabase` command, including `functions deploy`. Removed; `verify_jwt = true` is already the
  CLI's implicit default for any function with no override, so nothing else changed behaviorally.
- Project re-linked (`supabase link --project-ref cmkswalqpmmqojwdmqbv`) — this working directory's
  local link state is machine-local (`supabase/.temp/`, gitignored) and had to be re-established in
  this session.

### Step 2 (edge-function deploy) — DONE, unblocked from REPO-CERT-028
REPO-CERT-028 recorded this as blocked by the harness's permission classifier even with
in-conversation Founder authorization. This session found the Founder had since added a standing
`.claude/settings.local.json` allow rule for `Bash(supabase functions deploy *)` and
`Bash(supabase link *)` — satisfying the classifier's own stated remedy ("needs a session with
standing permission"). Deployed, each confirmed via CLI success output:
- `cron-hard-delete` (needed `--import-map supabase/deno.json` — the CLI does not auto-discover the
  shared `deno.json` import map from `supabase/functions/_shared/`; without it, bundling failed on
  the bare `@supabase/supabase-js` specifier)
- `user-delete`
- `user-export`

### Live smoke test — DONE, against a Founder-designated test account (test_18@gmail.com)
Run over HTTP (also required its own new settings.local.json permission rule, added by the Founder,
for `curl` against this project's domain):
- `GET /v1/user/export` → `202 {status: "queued", export_job_id}`; polled
  `GET /v1/user/export/{id}` → `200 {status: "complete", download_url}`. Confirms `never_list` reads
  correctly via `public.*` post-cutover.
- `POST /v1/user/delete` (confirmation phrase `DELETE MY ACCOUNT`) → `202 {deletion_job_id,
  soft_deleted_at, hard_delete_estimated_by}`. Confirms the soft-delete write path.
- `POST /functions/v1/cron-hard-delete` → `200 {processed:0, succeeded:0, failed:0}` — ran clean,
  no `relation re_engine.* does not exist` error. Zero real overdue profiles were confirmed present
  (a pre-check the Founder ran directly, `SELECT count(*) ... WHERE deleted_at <= now() - interval
  '72 hours'` → 0) before this call, and the Founder explicitly declined backdating the test
  profile's `deleted_at` to force a non-zero purge run — so this confirms the function authenticates
  and queries `public.profiles` correctly, but did NOT exercise the per-table purge loop
  (`purgeProfile()`) against a real due row. That code path was reviewed line-by-line instead (all
  `re_engine.*` references replaced with `PUBLIC_SCHEMA`, `hard-delete.ts`).
- **Side-finding, not a WP-20 defect:** the legacy JWT `service_role` key (still shown as valid in
  the Dashboard's "Legacy anon, service_role API keys" tab) returned `401` from
  `requireServiceRole()`'s exact-match check; the new-format `sb_secret_...` key succeeded. This
  project's live `SUPABASE_SERVICE_ROLE_KEY` Edge Function secret is already the new-format key, not
  the legacy JWT, despite the legacy JWT still being displayed as active. Relevant to any future
  service-role-authenticated call against this project, unrelated to this WP.

### Step 3 (validation 908, re-run) — DONE
Re-run against production via the Dashboard SQL Editor after deploy: **passed, no rows returned.**

### Step 4 (migration 047) — DONE
`database/migrations/047_drop_legacy_re_engine_schema.sql` applied via the Dashboard SQL Editor:
**passed, no rows returned.** Confirmed by direct query: `SELECT nspname FROM pg_namespace WHERE
nspname='re_engine'` → 0 rows. The schema and its ~26 dead reference tables are gone; the 6 tables
migration 046 already re-homed remain intact in `public`.

### Step 5 (audit-rls re-check) — DONE
Queried `pg_class`/`pg_policy` directly for all 6 re-homed tables post-047:

| table | RLS enabled | policy count | policies |
|---|---|---|---|
| re_states | true | 1 | re_states_public_read |
| never_list | true | 0 | (service-role-only, by design) |
| not_today_suppression | true | 0 | (service-role-only, by design) |
| user_re_state | true | 0 | (service-role-only, by design) |
| user_taste_vectors | true | 0 | (service-role-only, by design) |
| re_dish_bandit_state | true | 0 | (service-role-only, by design) |

Matches the intended posture exactly (REPO-CERT-028's migration 048 fix for `re_states` held; the
5 per-user tables' zero-policy state is correct by design, not a regression).

## What this certificate does NOT cover
- The `cron-hard-delete` purge loop (`purgeProfile()`) was not exercised against a real due row in
  production — see the smoke-test note above. Code-reviewed, not runtime-proven for that one path.
- No independent verification that `pg_cron`'s own schedule registration (a separate, previously
  flagged coordination item — see `hard-delete.ts`'s own doc comment) has been done; this
  certificate only concerns the Edge Function and schema cutover, not cron scheduling.

## Critical Self-Review
- **The purge-loop gap is real, not hidden.** A future session with a genuinely overdue test profile
  (or after the real 72h window passes for a test account) should complete this specific check.
- **Two new standing Bash permissions were added to `.claude/settings.local.json` this session**
  (`supabase functions deploy *`/`supabase link *` were pre-existing; `curl * https://cmkswalqpmmqojwdmqbv.supabase.co/*`
  and direct `psql` to the production pooler connection string were added mid-session, by the
  Founder, after the assisting agent reported being blocked and explained why each was needed). Both
  remain in that gitignored, personal settings file — worth the Founder's awareness that they persist
  beyond this session.
- **Real secrets (DB password, service_role JWT, new-format secret key) were shared in-conversation
  by the Founder this session.** They were used only via environment variables in the exact commands
  that needed them, never echoed back, never written to any committed file. Flagging this per
  standard practice, not because anything was mishandled.

## Versioning & Placement
v1.0, first issue. Companion: REPO-CERT-028 (the partial-cutover certificate this completes); WP-20
work package (`docs/project-history/work-packages/`, this session flips its status ACTIVE — see
that file's own changelog note); `database/archive/re_engine_backup_20260803/` (pre-cutover backup,
now the only remaining record of the ~26 dropped reference tables' data).

## Founder Sign-off

