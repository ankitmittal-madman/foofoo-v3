STATUS: ARCHIVED
Reason: Superseded by docs/active/ (2026-08-04 documentation restructure). This audit remains the evidentiary source for docs/active/CURRENT_STATUS.md, OPEN_ITEMS.md, ROADMAP.md, and LAUNCH_BLOCKERS.md.

# Ghar RE — Clean-Room Production Audit (Audit vNext)

**Status:** ACTIVE — this audit supersedes every report under `reports/re_audit/archive/`.
**Date:** 2026-08-04
**Method:** Fresh, from-scratch evidence gathering. No prior audit report was read or cited as
evidence. Findings are grounded in: current repository code (read directly), live Supabase
queries (via MCP, executed this session), a live Fly.io health check (executed this session), and
direct test-suite runs (executed this session, not assumed). Where a live check could not be run
(e.g. mobile app in a real device/browser), that limitation is stated explicitly rather than
inferred.

---

## Headline finding

**FooFoo/Ghar RE is materially further along than a first read of its own architecture docs would
suggest, but has one structural problem that overshadows every scoring/ontology detail: the
actively-routed mobile app and the well-tested backend have diverged.** The backend (Edge
Functions + Python recommendation engine) is real, deployed, live-healthy, and extensively tested
(254+ automated tests across three layers, all passing, executed this session). But three
user-facing capabilities that the backend fully supports have **no reachable UI**:

1. **DPDP data-subject rights (export/delete) — built, deployed, legally required, zero mobile entry point.** A user in India cannot actually exercise their right to export or delete their data today, despite the Edge Functions existing and working.
2. **Recommendation explanation ("why this dish") — data flows end-to-end into the API response and gets persisted, but no screen ever renders it.**
3. **The screen that calls `/v1/recommendations` directly is dead code** (its own header comment says so) — the actively-routed home flow (`today.tsx` → `weekly-plan.tsx`) uses a different, newer `/v1/plan`-family surface instead, meaning feedback capture (like/dislike) is only reachable from one dead screen and one single-tap-only calibration screen. Most of a normal user's daily session captures **zero feedback**.

Separately, live database counts back this up: **126 `recommendation_events` exist, but 0 rows in `week_plans`, `plan_slots`, `household_context`, `interaction_events`.** Real recommendations are being generated and logged, but the plan-persistence and context-write paths are not actually firing for those users — a concrete, numbers-backed production gap, not a theoretical one.

## Second-order finding: the RE math is honest, tested, and mostly done — with one real wiring gap

The recommendation engine's core scoring/filtering/pairing/assembly pipeline is implemented,
tested (111 core + 69 service tests, all passing, run this session), and matches its own frozen
spec closely. The one genuine algorithmic gap: the frozen spec's IDF-weighted cosine distance
formula for pairing/meal-class similarity (`d(a,b)`) is implemented (`ghar_re_core/similarity.py`)
but **not actually wired into the scoring or pairing path that was supposed to use it** — pairing
still uses a cruder set-intersection proxy. Personalization (`s_pref`) and the feedback-training
loop are real code, confirmed still fully inert (0 real training runs, `enabled: false`), which is
an honest, self-documented choice given feedback volume (9 rows live), not a bug.

## Third-order finding: deployment is real, security posture is reasonable, mobile has zero test coverage

The RE service is live and healthy on Fly.io (verified this session: `/healthz`, `/readyz`,
`/v1/meta` all responding correctly). RLS is enabled on every user-data table with real ownership
policies; the internal-only tables with RLS-enabled-no-policy are a known, reviewed pattern (no
client grants exist). Supabase's leaked-password-protection is disabled (a real, one-click fix).
The **mobile app itself has zero automated tests of any kind** — no jest, no native E2E — which is
the single largest testing gap in the whole system, verified by direct search (zero `*.test.ts(x)`
files under `mobile/`).

## Scope of this audit

Every deliverable below (repository inventory, system topology, RE audit, food-knowledge audit,
database audit, E2E workflow audit, security audit, testing audit, deployment audit, readiness
scorecard, backlog, build sequence) was produced by direct evidence this session — see each file's
own citations. No conclusion here should be read as inherited from any prior audit; where a
finding happens to match something a prior audit also found, it was independently rediscovered.

## Reading order

1. `01_repository_inventory.md` — what exists
2. `02_system_topology.md` — how it fits together, by current-truth status
3. `03_recommendation_engine_audit.md`
4. `04_food_knowledge_audit.md`
5. `05_database_audit.md`
6. `06_e2e_workflow_audit.md`
7. `07_security_audit.md`
8. `08_testing_audit.md`
9. `09_deployment_audit.md`
10. `10_production_readiness_scorecard.md`
11. `11_prioritized_backlog.md`
12. `12_recommended_build_sequence.md`
</content>
