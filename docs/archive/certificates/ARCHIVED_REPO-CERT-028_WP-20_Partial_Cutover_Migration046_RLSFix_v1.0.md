# STATUS

ARCHIVED

## Reason

Implementation completed.

This document is retained for historical reference only.

It must not be used as the primary implementation guide.

Refer to the active documentation for the current source of truth.

---

# [ACTIVE]_REPO-CERT-028_WP-20_Partial_Cutover_Migration046_RLSFix_v1.0

**Status:** ACTIVE
**Version:** v1.0
**Date:** 2026-08-03
**Placement:** docs/archive/certificates/ARCHIVED_REPO-CERT-028_WP-20_Partial_Cutover_Migration046_RLSFix_v1.0.md
**Certifies:** WP-20 (Retire Legacy re_engine Schema) — PARTIAL execution only: migration 046 (re-home) and migration 048 (re_states RLS fix), both applied to production. Does NOT certify WP-20 as complete — migrations 047 (drop) and the edge-function redeploy are explicitly NOT covered.
**Supersedes:** N/A

---

## What this certifies

Two migrations were executed against the live Supabase project (`cmkswalqpmmqojwdmqbv`) on
2026-08-03, with the Founder's explicit in-conversation authorization to reuse the Supabase CLI's
existing stored login for the Management API. This is proof-of-execution for those two migrations
only — WP-20 as a whole remains DRAFT (see the work package's own §6 execution record for the full,
honest breakdown of what did and did not happen this session).

## Execution evidence

### 1. Migration 046 (re-home) — applied, verified
- `public.re_states` created and populated: **36/36 rows** match the `re_engine.re_states` source.
- `public.profiles.home_state`'s FK constraint (`profiles_home_state_fkey`) now targets
  `public.re_states`, confirmed via `pg_constraint`.
- The 5 per-user tables (`never_list`, `not_today_suppression`, `user_re_state`,
  `user_taste_vectors`, `re_dish_bandit_state`) created in `public`, 0 rows (matching source, which
  was 0 rows in every case).
- `database/validation/908_re_engine_decommission_validation.sql` run against production:
  **passed silently** (no exceptions raised).

### 2. `/audit-rls` run against the 6 re-homed tables — found and fixed a real bug
- **Finding (CRITICAL):** `public.re_states` had RLS enabled with **zero policies** immediately
  after 046 — silently unreadable by anon/authenticated, contradicting 046's own stated intent.
  Root cause: the project's `ensure_rls` platform event trigger auto-force-enables RLS on every new
  `public` table; `CREATE TABLE ... LIKE ... INCLUDING ALL` does not carry over the source table's
  RLS state, so the clone landed in the RLS-on/zero-policy configuration by default.
- **Fix:** migration `048_re_states_public_read_policy.sql` — one `CREATE POLICY ... FOR SELECT
  USING (true)`, matching the established `cuisines_public_read`/`meal_classes_public_read`
  convention exactly. Applied to production; verified `public.re_states` now shows exactly 1 policy
  (`re_states_public_read`, `cmd=SELECT`, `qual=true`).
- The 5 per-user tables' zero-policy state was confirmed **correct by design** (service-role-only,
  reproducing the old `re_engine` posture) — not a finding. Full report: `docs/archive/audits/ops/root-rls-audit/ARCHIVED_rls-audit.md` (formerly repo root).

### 3. What this certificate explicitly does NOT cover
- Migration 047 (`DROP SCHEMA re_engine CASCADE`) — **not applied**. Correctly gated: its own hard
  prerequisite (edge functions redeployed) is not met.
- Edge-function deployment (`cron-hard-delete`, `user-delete`, `user-export`) — **not done**. Both
  the Supabase CLI (`supabase functions deploy`) and an equivalent Management API call were blocked
  by the harness's own permission classifier as a production-mutating action; this was not routed
  around via a different tool, per the assisting agent's own operating instructions on respecting
  such a block. Needs a session with standing deploy permission, or a human running the deploy
  commands directly (see WP-20 doc §5 runbook / §6 execution record).
- `re_engine` schema itself: still exists in production, fully intact, alongside its `public`
  duplicates from 046. No data was lost or is at risk either way.

## Critical Self-Review

- **This is a partial certificate by design**, matching the pattern already established by
  REPO-CERT-027 (WP-19 batch-1). It exists so the two migrations that DID execute have a real,
  dated proof-of-execution record, without falsely implying WP-20 itself is complete.
- **No rollback was exercised in production** for either migration this session (only on the local
  Postgres 16 test cluster, in an earlier session). The rollback files exist and were tested
  locally; they have not been needed or run against the live project.
- **The blocked edge-function deploy is the load-bearing remaining risk** — until it happens, WP-20
  cannot proceed to 047, and `re_engine` (with its now-duplicated 6 tables) continues to exist
  as dead weight rather than being retired. This is a known, explicitly flagged gap, not an oversight.

## Versioning & Placement
v1.0, first issue. Companion: `docs/archive/implementation/work-packages/ARCHIVED_WP-20_Retire_Legacy_re_engine_Schema_v1.0.md` §6; `docs/archive/audits/ops/root-rls-audit/ARCHIVED_rls-audit.md`; `database/archive/re_engine_backup_20260803/` (the full pre-cutover backup, unaffected by this partial cutover).

## Founder Sign-off
