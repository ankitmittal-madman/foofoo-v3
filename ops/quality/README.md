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
Every completed run also produces `test-results.xlsx` and a dated `quality-report_*.zip`. The
workbook contains the run summary, every test case, errors, any persona journeys/recommendations
that ran, and source-workbook traceability. Excel/ZIP publication is mandatory: the orchestrator
returns a failure if it cannot build or validate them.

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
| WP-22 | Synthetic persona UI journeys — drives the real onboarding UI through all 100 personas, screenshots every answer/Continue, captures the resulting `/v1/recommendations` call, renders one HTML report per persona + an index grouped by outcome (200/422/warned) | ✅ wired into the orchestrator as the `ui-persona-journeys` step — needs `GHAR_WEB_URL`; each persona signs up its own fresh random-email account via the app's real sign-up flow (requires the target Supabase project to auto-confirm signups — no pre-provisioned test account needed); no RE scoring assertions. Report: `ops/quality/reports/<timestamp>/personas-ui/report/index.html`. Also runnable on demand via the `persona-journeys` GitHub Actions workflow (Actions tab → "Run workflow") — it deploys the checked-out commit to the public production-test Vercel target and uploads Excel plus a ZIP artifact. |
| 16-19 | Orchestrator, reports, dashboard, one command | ✅ this module |

Gated suites are recorded as **skipped/blocked with the concrete reason**, never faked. Unlock them:

```bash
export DATABASE_URL=postgres://…      # enables Phase 7 database checks
export GHAR_WEB_URL=http://localhost:8081  # enables Phase 9-11 (expo start --web) + WP-22
# WP-22 needs no pre-provisioned account — it signs up its own per-persona random-email account
# install Deno                         # enables Phase 6 edge-function tests
```

When `GHAR_UI_OUT` is omitted, standalone UI drivers write generated evidence to the system
temporary directory (`/tmp/foofoo-ui-artifacts` on Linux) instead of the repository. CI sets
`GHAR_UI_OUT` explicitly, packages the evidence into Excel/ZIP files, and retains the uploaded
GitHub Actions artifact for 90 days. Generated `ui-artifacts/` and repository-local `tmp/`
directories are ignored by Git.

## Run in GitHub Actions and download Excel

For the complete UI persona flow, open **GitHub → Actions → persona-journeys → Run workflow**.
Leave `persona_limit` blank for all personas or enter a small number such as `5` for a smoke run.
When the run finishes, its **Artifacts** section contains
`persona-journey-report-<run-id>-<attempt>` with:

- `test-results.xlsx` — one dated user journey, recommendation dish, final plan, and outcome row
  set per tested user; matching P01-P41 rows from the canonical source workbook are included for
  comparison.
- `persona-journey_*.zip` — the same workbook plus run metadata, errors, HTML, screenshots, and
  per-user JSON evidence under `ui-artifacts/`.

For all non-UI and conditionally available tests, run **GitHub → Actions → quality-gate → Run
workflow**. Download `ghar-quality-report-<run-id>-<attempt>` and open the newest timestamped
folder's `test-results.xlsx` or `quality-report_*.zip`. The workflow also runs automatically on
pushes and pull requests that touch the engine, contracts, or quality program.

Real-user test fixtures may be supplied to the persona driver through `GHAR_PERSONAS_JSON`, but
must set `user_type: "real"` and a pseudonymous `test_user_id`; credentials and access tokens are
never written to the workbook or logs.

## Signed network load and soak probes

`runner/network_load_test.py` can measure either Ghar or Aux with the service's raw-body HMAC.
It is measurement-only unless an operator supplies ratified gates; there are no repository-default
latency, error-rate, throughput or regression targets.

```bash
python3 ops/quality/runner/network_load_test.py \
  --service ghar --url http://127.0.0.1:8000/v1/recommendations \
  --secret "$GHAR_REC_SERVICE_SECRET" --payload ops/quality/fixtures/load_request.json

python3 ops/quality/runner/network_load_test.py \
  --service aux --url http://127.0.0.1:8001/v1/recommendations \
  --secret "$AUX_REC_SERVICE_SECRET" --payload /path/to/privacy-safe-aux-request.json \
  --baseline /path/to/approved-baseline-report.json --max-p95-regression-pct 10 \
  --max-error-rate 0.005 --min-throughput-rps 40
```

The JSON report contains only endpoint origin, status counts and aggregate timings. It never emits
the secret or request payload. A gated run exits non-zero when any supplied target fails; an
ungated run records `passed: null` so a measurement cannot be mistaken for launch approval.

## Aux promotion and kill-switch decision

`ops/recommendation/rollout_evidence.py` composes the decision input from five independent JSON
reports. It requires governed schemas, one publication hash, matching shadow/guardrail windows,
measured (not assumed) production guardrails, ratified targets with an approval reference, and a
gated load report whose successful Aux responses returned the same publication. The output embeds
SHA-256 lineage for every source and is written atomically without overwriting prior evidence.

```bash
python3 ops/recommendation/rollout_evidence.py \
  --current-mode shadow --offline /path/to/offline.json --load /path/to/load.json \
  --health /path/to/shadow-health.json --guardrails /path/to/guardrails.json \
  --targets /path/to/ratified-targets.json --output /path/to/rollout-evidence.json
```

`ops/recommendation/rollout_decision.py` consumes four privacy-minimized inputs: a passing governed
offline report, a passing gated Aux load report, rows from `re_engine.aux_shadow_health`, and zero
hard-guardrail counters. Its evidence document must also contain the full publication hash and all
product-ratified volume, availability, timeout, comparability, coverage and latency targets.

```bash
python3 ops/recommendation/rollout_decision.py /path/to/rollout-evidence.json \
  --output /path/to/rollout-decision.json
```

Exit code `0` means shadow is eligible for a controlled canary (or Aux is already safely off), `1`
means remain in shadow / continue collecting evidence, and `2` means an active canary breached an
operational or hard guardrail and automation must set `AUX_RE_MODE=off`. The evaluator does not
mutate deployment state; separation keeps evidence production and configuration authority audited.

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
  ui/run_persona_journeys.mjs         # WP-22 persona UI journey driver (gated on GHAR_WEB_URL)
  ui/personaToOnboardingAnswers.mjs   # WP-22 reverse mapper (persona q1..q15 -> OnboardingAnswers)
  personas/export_personas.py         # WP-22 persona JSON export for the Node driver
  runner/persona_journey_report.py    # WP-22 HTML report (per-persona pages + outcome index)
  runner/excel_report.py              # validated Excel + ZIP publisher for every test workflow
  runner/orchestrator.py              # Phase 16-19 orchestrator + dashboard
  runner/perf_benchmark.py            # Phase 12
  runner/network_load_test.py         # signed Ghar/Aux load measurement and ratified gates
  runner/report_reader.py             # Phase 17/20 triage + re-validate
  run_full_quality_suite.sh           # Phase 19 single command
  reports/<timestamp>/                # Phase 17 evidence (summary.*, *.json, junit, artifacts)
```
