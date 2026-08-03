---
name: quality-gate
description: How to run the production quality gate and where it lives
metadata:
  type: project
---

The production quality gate lives in `ops/quality/` (placed there, not a new top-level tree, to
respect CLAUDE.md's frozen-architecture rule — Founder chose this on 2026-08-03).

Run it: `ops/quality/run_full_quality_suite.sh` (add `--quick` to skip the perf benchmark). Reports
land in `ops/quality/reports/<timestamp>/` (summary.txt/md/html + JSON + JUnit + artifacts).
Triage/re-run failures: `python3 ops/quality/runner/report_reader.py [--rerun-failed]`.

What runs here vs gated: Python unit/contract/security/recsys/planning/perf/chaos all run
(needs `PYTHONPATH=<repo>:<repo>/ghar_re_service`). Database, edge functions, and mobile UI are
gated behind env vars but ARE runnable in this sandbox as of 2026-08-03 — none of these require
touching production:
- database: `supabase start` (local docker stack, images already pulled) then apply
  `database/migrations/*.sql` in order via psql against `postgresql://postgres:postgres@127.0.0.1:54322/postgres`,
  export as `DATABASE_URL`. One statement in migration 041 (`REVOKE EXECUTE ON FUNCTION
  public.rls_auto_enable()`) will error locally by design — that function is a production-only
  manual artifact per migration 029's own comment, not a bug; harmless to skip locally.
- edge functions: `curl -fsSL https://deno.land/install.sh | sh`, add `~/.deno/bin` to PATH —
  installs cleanly, all 65 Deno tests then pass.
- mobile UI: `cd mobile && npx expo start --web --port 8081` (uses `mobile/.env`, which points at
  the live prod Supabase project — fine, screens only render, no writes happen from a screenshot
  crawl), export `GHAR_WEB_URL=http://localhost:8081`. `ops/quality/ui/run_ui.mjs` now
  auto-discovers every screen from `mobile/app`'s own expo-router file tree (no hardcoded route
  list) and screenshots each one, not just the home screen — needs `npm install playwright` +
  `npx playwright install chromium` inside `ops/quality/ui/` first (that's now its own
  package.json there, gitignored node_modules).

With all three unlocked, the suite hits 100.0/READY instead of 95.0/NOT-CERTIFIABLE.

Verdict rule: launch is NOT certified while any P0 surface is unverified, even at 100% pass — an
unverified DB/edge/UI is a launch risk, not a green light. The RE is tested black-box (behaviour,
exclusions, contract), never its scoring formula.
