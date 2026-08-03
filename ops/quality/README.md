# Ghar Production Quality Program

A self-contained, executable quality gate for the Ghar / FooFoo repository. One command runs every
applicable validation suite, collects real artifacts into a timestamped report, and prints a launch
verdict. It lives under `ops/` (not a new top-level tree) to respect the frozen-architecture rule
in `CLAUDE.md`.

## Run it

```bash
ops/quality/run_full_quality_suite.sh          # full run (includes perf benchmark)
ops/quality/run_full_quality_suite.sh --quick  # skip perf benchmark
```

Reports land in `ops/quality/reports/<timestamp>/` and `reports/latest.txt` points at the newest.

### Triage an existing report / re-validate a fix

```bash
python3 ops/quality/runner/report_reader.py                 # ranked failure triage (latest report)
python3 ops/quality/runner/report_reader.py --rerun-failed  # re-run only the failing pytest targets
```

## What actually runs here vs. what is gated

| Phase(s) | Suite | Status in this environment |
|---|---|---|
| 1-2 | Repository inventory + feature matrix | ✅ auto-generated |
| 4 | Unit — `ghar_re_core` + `ghar_re_service` | ✅ runs (pytest) |
| 5 | Planning surfaces (`/v1/cold-start`…`/v1/recipe`) | ✅ runs |
| 6 | API contract at the HTTP boundary (jsonschema) | ✅ runs |
| 6 | Edge functions (`supabase/functions`) | ✅ runs — needs Deno installed |
| 7 | Database (migrations/RLS/constraints/integrity) | ✅ runs — needs `DATABASE_URL` (e.g. `supabase start` locally) |
| 8 | Recommendation black-box behaviour (15 personas) | ✅ runs |
| 12 | Performance (in-process latency p50/p95/p99) | ✅ runs |
| 13 | API security + secrets scan | ✅ runs |
| 14 | Chaos / fail-safe probes (in-process) | ✅ runs |
| 9-11 | Headless browser UI + accessibility, one screenshot/console/network capture per screen discovered from `mobile/app`'s own route tree | ✅ runs — needs `GHAR_WEB_URL` (e.g. `expo start --web`) |
| 16-19 | Orchestrator, reports, dashboard, one command | ✅ this module |

Gated suites are recorded as **skipped/blocked with the concrete reason**, never faked. Unlock them:

```bash
export DATABASE_URL=postgres://…      # enables Phase 7 database checks
export GHAR_WEB_URL=http://localhost:8081  # enables Phase 9-11 (expo start --web)
# install Deno                         # enables Phase 6 edge-function tests
```

## Honesty rules baked into the verdict

- No fabrication: every number comes from a real pytest/JUnit run or a real probe.
- A **P0 test failure** ⇒ `can_launch_today = NO`.
- An **entirely-unverified P0 surface** (DB, edge functions) also blocks certification — 0 failing
  tests over a partial surface is *not* a launch green-light.
- The RE is tested as a **black box** (behaviour, exclusions, contract) — no scoring formula is
  asserted, per the program brief.

## Layout

```
ops/quality/
  inventory/generate_inventory.py     # Phase 1-2
  personas/personas.py                # Phase 3 (7 golden + 8 derived personas)
  suites/                             # Phase 4-8,13 pytest suites + conftest
  ui/run_ui.mjs                       # Phase 9-11 Playwright driver (gated on GHAR_WEB_URL)
  runner/orchestrator.py              # Phase 16-19 orchestrator + dashboard
  runner/perf_benchmark.py            # Phase 12
  runner/report_reader.py             # Phase 17/20 triage + re-validate
  run_full_quality_suite.sh           # Phase 19 single command
  reports/<timestamp>/                # Phase 17 evidence (summary.*, *.json, junit, artifacts)
```
