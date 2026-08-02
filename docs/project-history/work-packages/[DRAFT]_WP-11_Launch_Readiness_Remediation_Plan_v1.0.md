# [DRAFT]_WP-11_Launch_Readiness_Remediation_Plan_v1.0

**Status:** DRAFT — remediation plan reconciling THREE sources: an external (GPT) live-audit report, an earlier same-repo Claude self-audit (Aug 1, claude.ai/code/artifact/3b18615d-28d1-4dbe-86d5-a80799c072f7), and this session's own independent Supabase MCP verification. No remediation work has been executed yet; this document is the plan, not the fix.
**Version:** v1.0
**Date:** 2026-08-02
**Placement:** docs/project-history/work-packages/[DRAFT]_WP-11_Launch_Readiness_Remediation_Plan_v1.0.md
**Builds on:** WP-9 Independent Engineering Due Diligence Audit, WP-9 Validation Audit, WP-8B/8C/8D/8E backend foundation, S47 (cron auth + CORS fix, prior session), S49–S54 onboarding FK/state-code fixes (this session, KNOWLEDGE.html).
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

## 0. Third source reconciled: the Aug 1 Claude self-audit

The Founder also surfaced an earlier Claude-authored audit of this same repo (dated Aug 1, one day before this session), which independently ran its own live Supabase queries at the time. Cross-checking it against today's (Aug 2) verified state shows several of its P0/P1 findings are now **closed** — useful signal that real progress happened between the two audits, not just more findings piling up:

| Aug 1 Claude audit finding | Today's (Aug 2) verified state | Status |
|---|---|---|
| P0: `auth.users`=2, `public.profiles`=0 — nobody has ever completed onboarding | `profiles`=2 rows now exist (this session's S49–S54 test signups, after fixing the onboarding_sessions/household_answers FK bugs and the home_state code-mapping bug) | **Closed since Aug 1** — directly caused by this session's own fixes; worth naming so it isn't re-flagged as still-open |
| P0: cron endpoints (`cron-hard-delete`/`cron-retention-purge`) `verify_jwt=false`, no app-level check, publicly triggerable | `list_edge_functions` today: both show `verify_jwt: true`; `config.toml`'s own comment documents this was fixed in a prior session (S47, "two P0 launch blockers fixed") alongside `requireServiceRole()` | **Closed since S47** — the *auth* gap is fixed; what remains (confirmed independently by both this audit and GPT's) is that **no jobs are actually scheduled** (`cron.job` empty) — a different, narrower gap than "unauthenticated" |
| P3: `ghar_re` schema — 28 tables, RLS disabled, flagged by Supabase's own advisor | Today: all 28 `ghar_re` tables have RLS **enabled**, via a migration (`ghar_re_private_schema_rls`) applied live with no matching repo file | **Closed, but undocumented** — the fix landed as an untracked live migration; folded into this plan's P0 #2 (migration ledger reconciliation) below |
| Dead code: `onboarding` Edge Function + its whole dependency tree unreachable from the app | Confirmed still true — `onboarding` remains undeployed (§1 below) and its dependency tree (`_shared/services/re/*`, `re-engine-full-adapters.ts`, `services/onboarding/orchestrator.ts`, etc.) is still unimported by any live handler | **Still open** — folded into P0 #3 below |
| P0: DPDP export/delete built but zero mobile callers, unreachable by users | Confirmed still true — `user-export`/`user-delete` remain undeployed and have no mobile UI | **Still open** — folded into P0 #3 below |
| P1: no feedback loop, no profile/settings/history screens, no CD, no monitoring, no mobile tests | All confirmed still true today, unchanged | **Still open** — folded into §2 P1/P2 below, consistent with GPT's independent inventory of the same gaps |

This reconciliation matters for the plan below: it means "no user has ever completed onboarding" is **not** still a P0 (it's the one blocker actually resolved between the two audits, by this session's own bug-fixing work) — GPT's audit ran after that fix landed and correctly did not re-flag it. The remaining P0s below are the ones **confirmed still open by both external audits and this session's own live queries.**

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
3. **Deploy the missing lifecycle functions, or formally retire the dead one.** Two different things bundled under "3 undeployed functions," per the Aug 1 Claude audit's more precise split:
   - `user-export`/`user-delete`: real DPDP-required logic, zero mobile callers, zero deployment. This is a **legal exposure** (India DPDP Act data-subject rights), not just drift — both audits independently rank this P0/P1. Deploy both, then build the mobile entry points (buttons) in the P1 product workstream below.
   - `onboarding`: confirmed genuine dead code — the Aug 1 audit traced the full import graph (`_shared/services/re/*`, `re-engine-full-adapters.ts`, `services/onboarding/orchestrator.ts`, `services/recommendations/service.ts`, `services/planning/persistence.ts`, `services/scheduler/nightly-plan.ts`) and found nothing live imports any of it — the recommendations screen calls the RE directly via `re-client.ts`, not this pipeline. Needs a decision, not an engineering task: formally archive/retire it (matches this repo's own "no silently-forked local copy" governance principle already applied to the contract schema) or explain why it's being kept.
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

- This plan corrects three specific claims in the GPT audit using live queries run in this same session — but it does not re-verify GPT's GitHub/Fly.io/EAS claims, which remain provisional pending equivalent direct verification.
- The Aug 1 Claude audit's own claims were treated with the same skepticism as GPT's, not given a free pass for sharing a model family — its live-data claims (row counts, cron `verify_jwt`, `ghar_re` RLS) were checked against today's actual state, not assumed still accurate a day later. Two of its three main P0s turned out to already be closed.
- The CORS 401 root cause (gateway intercepting OPTIONS before function code) is a plausible, well-documented Supabase behavior consistent with the observed log evidence, but has not been proven with a fresh, controlled reproduction in this session — flagged as needing further investigation, not stated as certain. Notably, neither the Aug 1 Claude audit's inventory nor GPT's mentioned this as a P0 in the same terms — GPT observed the actual 401s; the Aug 1 audit only noted "no CORS headers found... relies on platform default" without catching the preflight failure. Treat this as the newest, least-corroborated finding of the three.
- No effort/timeline estimates are given; the source audits' "1-2 weeks" style estimates were not independently validated and are omitted here rather than repeated without basis.

## 5. Versioning & Placement

v1.0 — initial draft, reconciling an external GPT audit, an earlier same-repo Claude self-audit (Aug 1), and this session's own independent Supabase MCP verification (Aug 2). Supersedes nothing; complements WP-8G (recommendation variety, separately drafted this session).

## Founder Sign-off

