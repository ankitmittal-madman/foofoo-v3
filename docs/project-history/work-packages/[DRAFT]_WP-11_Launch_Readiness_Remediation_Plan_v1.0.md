# [DRAFT]_WP-11_Launch_Readiness_Remediation_Plan_v1.0

**Status:** DRAFT — remediation plan proposed from a combination of an external (GPT) live-audit report and this session's own independent Supabase MCP verification. No remediation work has been executed yet; this document is the plan, not the fix.
**Version:** v1.0
**Date:** 2026-08-02
**Placement:** docs/project-history/work-packages/[DRAFT]_WP-11_Launch_Readiness_Remediation_Plan_v1.0.md
**Builds on:** WP-9 Independent Engineering Due Diligence Audit, WP-9 Validation Audit, WP-8B/8C/8D/8E backend foundation, S49–S53 onboarding FK fixes (this session, unreleased KNOWLEDGE.html entries).
**Governance basis:** DOC-P3-08 (env map), the DPDP retention runbook (ops/audits/audit-dpdp/RUNBOOK_schedule-retention-jobs-2026-07-30.md), repo Naming Standard.

---

## Executive Summary

An external GPT-based audit assessed repository + live Supabase state and produced a P0–P3 launch-blocker list and a "35% repository-only readiness" verdict. Before turning that into an execution plan, this session independently re-verified the audit's live-state claims against the same Supabase project (`cmkswalqpmmqojwdmqbv`) via MCP, since a second AI's report is untrusted input until checked, not a finding on its own.

**Corrections found during independent verification (§1) — do not action the uncorrected version of these:**
- Row-count claims ("profiles/consent/recommendation_events/feedback_events = 0") are **stale**: this session's own test onboarding (S49–S54) has already put real rows into `profiles` (2), `consent_records` (12), and `recommendation_events` (18). `feedback_events` is genuinely 0 (no write path exists yet — separately confirmed).
- The "`ghar_re` has 28 tables with RLS disabled" finding is **contradicted**: all 28 `ghar_re` tables currently have RLS enabled, via a migration (`ghar_re_private_schema_rls`) applied live earlier today with **no matching file in this repo** — itself a new, more specific migration-ledger-drift finding than GPT's own.
- "Cron authentication is incompatible with the scheduler model" **mischaracterizes** a deliberate, already-documented decision: `supabase/config.toml`'s own comment explains `verify_jwt=true` is intentional because the service_role key is itself a validly-signed project JWT and passes gateway verification like any other caller. The real, confirmed gap is narrower: **no cron jobs are registered at all** (`cron.job` is empty), not that the auth model is wrong.

**Confirmed as real (no correction needed):**
- Zero rows in `cron.job` — retention/hard-delete will never run. **P0.**
- Deployed function set is incomplete: only `household`, `recommendations`, `consent`, `diag-re-check`, `cron-hard-delete`, `cron-retention-purge` are live; `onboarding`, `user-delete`, `user-export` are not deployed at all despite existing in the repo. **P1.**
- Browser CORS preflight (`OPTIONS`) to `household` returns 401 — confirmed independently from this session's own earlier log queries (not just GPT's report).
- Migration ledger drift: 3 live migrations have no corresponding repo file (`039_revert_rls_disable_grants_are_unsafe`, `039_revoke_excess_grants_internal_tables`, `ghar_re_private_schema_rls`).
- No EAS/mobile release configuration; no mobile test suite; no monitoring/alerting; no feedback UI; no profile/settings screen — all confirmed by direct repo inspection, unchanged from GPT's inventory.

**Not independently re-verified in this pass** (would need live GitHub/Fly.io checks this session doesn't have active credentials for at time of writing): Actions/deploy history, branch protections, Fly.io service health/deployment status, EAS build state. Treat GPT's findings on those as provisional until checked the same way the Supabase claims were.

---

## 1. Verification log (this session, via Supabase MCP against `cmkswalqpmmqojwdmqbv`)

| Check | Query/tool | Result |
|---|---|---|
| Deployed Edge Functions | `list_edge_functions` | `household`, `recommendations`, `consent`, `diag-re-check`, `cron-hard-delete`, `cron-retention-purge` — all ACTIVE. No `onboarding`, `user-delete`, `user-export`. |
| Registered cron jobs | `SELECT * FROM cron.job` | 0 rows. |
| Core table row counts | `SELECT count(*) FROM ...` | profiles=2, consent_records=12, recommendation_events=18, feedback_events=0, public.dishes=802, ghar_re.dishes=39. |
| RLS by schema | `pg_tables.rowsecurity` grouped by schema | public 37/37 on, re_engine 35/35 on, ghar_re 28/28 on. |
| Migration ledger | `list_migrations` | 3 live-only entries with no repo file: two `039_*` variants, one unnumbered `ghar_re_private_schema_rls`. |
| Gateway config | `supabase/config.toml` | `verify_jwt=true` globally, explicitly documented as intentional (service_role key is a valid JWT). |

## 2. Corrected launch blockers, in remediation order

**P0 — must fix before any real user traffic:**
1. **Register the two cron jobs.** `cron.job` is empty; retention purge and hard-delete (DPDP-required, per the existing runbook) will never run. Action: schedule both via `cron.schedule(...)` calling `net.http_post` with the service_role bearer, per the runbook already in the repo (`ops/audits/audit-dpdp/RUNBOOK_schedule-retention-jobs-2026-07-30.md`) — the runbook exists, it was just never executed.
2. **Reconcile the migration ledger.** Pull the exact SQL of the 3 live-only migrations (`039_revert_rls_disable_grants_are_unsafe`, `039_revoke_excess_grants_internal_tables`, `ghar_re_private_schema_rls`) from the live project and commit matching numbered files (044+) to `database/migrations/` + rollbacks, per this repo's naming standard. Until this is done, the repo cannot be trusted as a record of live schema state — directly contradicts CLAUDE.md's "live database matches repo" philosophy.
3. **Deploy the missing lifecycle functions** (`onboarding`, `user-delete`, `user-export`) or explicitly retire them from the repo if genuinely unused — shipping code that exists but was never deployed is itself a drift risk (GPT's P2 concern was under-severe here; an undeployed DPDP delete/export path is closer to P1 given regulatory exposure).
4. **Fix the CORS preflight 401.** Confirmed real. Likely cause: Supabase's gateway-level `verify_jwt` check intercepts `OPTIONS` before function code (including the existing `corsPreflight()` handler in `_shared/api/cors.ts`) ever runs, because browser preflight requests don't carry the apikey/Authorization header the gateway wants. Needs a per-function gateway-level exemption for `OPTIONS` (check current Supabase platform support for this) or confirmation that the mobile/web client already works around it another way — needs the live browser test GPT couldn't do and this session hasn't yet either.

**P1 — before wider testing/pilot:**
5. Reconcile catalogue counts: `public.dishes`=802 vs. the repo's deployed-service bundle (810) vs. `ghar_re.dishes`=39. Confirm which is the source of truth for live recommendations before more test households depend on cross-source dish IDs.
6. Verify Fly.io RE service is actually deployed/healthy (`/healthz`, `/readyz`) — not done this session; needs Fly credentials.
7. Verify GitHub Actions deploy history / branch protections — not done this session; needs GitHub MCP/`gh` auth (currently reconnecting).
8. Add feedback capture (table exists, no Edge Function or mobile UI), recommendation history, and a profile/settings screen — all confirmed absent.

**P2/P3 — as GPT's original list, unchanged by this verification pass:**
- Recommendation UI is intentionally Phase 1/debug-level (see already-drafted WP-8G on the separate "Refresh" determinism issue).
- No EAS config, mobile tests, monitoring/alerting, search, admin portal, feature-flag runtime.
- Unused index cleanup on `public.tags` (cosmetic).

## 3. Immediate next actions (recommended order)

1. Rotate any token pasted into the *other* session (GPT's) — outside this repo's control, action for the Founder directly.
2. Execute the DPDP cron-scheduling runbook against this project (P0 #1) — low-risk, additive, already documented.
3. Pull and commit the 3 missing migration files (P0 #2) — read-only pull, additive commit, no schema change.
4. Decide deploy-vs-retire for `onboarding`/`user-delete`/`user-export` (P0 #3) — needs a Founder decision, not just engineering.
5. Investigate and fix the CORS preflight 401 (P0 #4) — needs a live browser reproduction this session doesn't have tooling for yet.
6. Once P0s are closed, re-run this same verification methodology (live MCP queries, not narrative claims) against Fly.io and GitHub before declaring P1 items closed.

## 4. Critical Self-Review

- This plan corrects three specific claims in the source audit using live queries run in this same session — but it does not re-verify GPT's GitHub/Fly.io/EAS claims, which remain provisional pending equivalent direct verification.
- The CORS 401 root cause (gateway intercepting OPTIONS before function code) is a plausible, well-documented Supabase behavior consistent with the observed log evidence, but has not been proven with a fresh, controlled reproduction in this session — flagged as needing further investigation, not stated as certain.
- No effort/timeline estimates are given; GPT's "1-2 weeks" style estimates were not independently validated and are omitted here rather than repeated without basis.

## 5. Versioning & Placement

v1.0 — initial draft, combining external audit + this session's independent correction pass. Supersedes nothing; complements WP-8G (recommendation variety, separately drafted this session).

## Founder Sign-off

