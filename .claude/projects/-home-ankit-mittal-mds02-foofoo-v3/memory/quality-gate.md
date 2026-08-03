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
(needs `PYTHONPATH=<repo>:<repo>/ghar_re_service`). Gated (recorded skipped/blocked, never faked):
database (needs `DATABASE_URL`), edge functions (needs Deno — not installed), mobile UI
(needs `GHAR_WEB_URL` against a running Expo web build).

Verdict rule: launch is NOT certified while any P0 surface is unverified, even at 100% pass — an
unverified DB/edge/UI is a launch risk, not a green light. The RE is tested black-box (behaviour,
exclusions, contract), never its scoring formula.
