STATUS: ARCHIVED
Reason: Superseded by docs/active/ (2026-08-04 documentation restructure). This audit remains the evidentiary source for docs/active/CURRENT_STATUS.md, OPEN_ITEMS.md, ROADMAP.md, and LAUNCH_BLOCKERS.md.

# Repository Inventory (fresh, 2026-08-04)

Method: direct reading of current repo state. `reports/re_audit/archive/` excluded entirely.

## Top-level components

| Path | What it is |
|---|---|
| `mobile/` | Expo/React Native client (Expo Router, TypeScript). Expo `~52.0.0`, `expo-router ~4.0.0`, React Native `0.76.3`, `@supabase/supabase-js ^2.45.0`, `@tanstack/react-query ^5.59.0`. |
| `ghar_re_core/` | Pure-Python recommendation-engine domain package — scoring, derivation, pairing, similarity, substitution, preference, exploration, calibration, meal_planner, cohort_plan/intel, catalogue, knowledge, config, training pipeline. Golden-master-tested, frozen spec-bound. |
| `ghar_re_service/` | Thin FastAPI hosting shell over `ghar_re_core`. `main.py`, `auth.py`, `ratelimit.py`, `engine.py`, `providers.py`, `lifecycle.py`, `media.py`, `Dockerfile`, `fly.toml`, `data/bundle/` (baked catalogue+config). |
| `supabase/` | Deno Edge Functions (9 callable functions, listed below), `config.toml`, `deno.json`. |
| `database/` | 52 migrations, 43 seeds, 9 validation scripts, 72 rollback files, 2 ETL scripts, 2 dated archive backups (`ghar_re_backup_20260803`, `re_engine_backup_20260803`). |
| `docs/` | architecture, research, project-history (work-packages/certificates), governance, roadmaps, product, visuals. |
| `ops/` | `ops/quality/` — a real production quality-gate program (runner/suites/inventory/personas/ui), `ops/scripts/export-txn-logs.mjs`, `ops/audits/` (per-skill evidence files). |
| `scripts/` | `scripts/synthetic-users/` — Node synthetic-traffic generator. |
| `contracts/` | `contracts/ghar-re-v1.schema.json` — the one shared request/response schema, CI-enforced to have exactly one copy referenced by both sides. |
| `data/` | `sig_scores_v1.csv`, `dish_macro_v1.csv`, `dish_substitutions_v1.csv`, `data/source/` (raw CSVs/YAML/xlsx). |

## Every Supabase Edge Function (9 total)

| Function | Endpoint | Auth | Purpose |
|---|---|---|---|
| `plan` | `POST /v1/plan` | JWT + `authenticate()` | Multiplexes cold_start/calibration/meal_plan/weekly_plan/class_dishes/recipe surfaces to the RE service. |
| `recommendations` | `POST /v1/recommendations` | JWT + `authenticate()` | Core recommendation orchestration: ownership → context → compose → signed HMAC call to RE → passthrough or safe 503 fallback. |
| `feedback` | `POST /v1/feedback` | JWT + `authenticate()` | Records accept/edit/swap/like/dislike against the caller's own recommendation event. |
| `consent` | `POST /v1/consent` | JWT + `authenticate()` | Consent capture (LF-M01). |
| `user-export` | `GET /v1/user/export[/{job_id}]` | JWT + `authenticate()` | DPDP data export — computes synchronously, writes to a private per-user Storage prefix. **No mobile caller (see backlog P0).** |
| `user-delete` | `POST /v1/user/delete` | JWT + `authenticate()` | DPDP soft-delete + deletion-job handle. **No mobile caller (see backlog P0).** |
| `household` | `POST /v1/household` | JWT + `authenticate()` | Onboarding write path (sessions log, answers upsert, gated profile+members creation). |
| `cron-hard-delete` | pg_cron only | service_role | 72h hard-delete job. |
| `cron-retention-purge` | pg_cron only | service_role | Purges `interaction_events` (2yr) / `audit_log` (3yr). |

Auth model: gateway-level `verify_jwt=true` (default, no per-function override remaining) + in-function `authenticate()` re-verification as defense-in-depth on every non-cron function; both cron functions require the service_role key instead.

## CI/CD (`.github/workflows/`, 6 files)

| Workflow | Trigger | Does |
|---|---|---|
| `backend-ci.yml` | push/PR on `supabase/**`, `contracts/**` | Contract single-source-of-truth check + Deno fmt/lint/check/test. |
| `re-ci.yml` | push/PR on `ghar_re_core/**`, `ghar_re_service/**`, `contracts/**`, `data/source/**` | ruff + mypy both packages, bundle-drift check (`export_bundle.py --check`), `pytest` both packages. |
| `quality-gate.yml` | push/PR + manual | Runs the full `ops/quality` orchestrator (persona/recsys/contract/security/planning/perf/chaos), uploads report artifact even on failure. |
| `fly_deploy.yml` | push to `main` | Auto-deploys the RE service to Fly.io on every main push — **no staging/approval gate.** |
| `mirror.yml` | manual | Force-mirrors the repo to GitLab. |
| `drive-backup.yml` | manual | Zips repo, uploads to Google Drive. |

**Gap confirmed:** no workflow runs the mobile app's own `typecheck` script or any mobile test — because none exist (see testing audit).

## Deployment config (declared, cross-checked live in the deployment audit)

`ghar_re_service/fly.toml` + `Dockerfile`: app `ghar-re`, region `bom` (Mumbai), multi-stage Docker build (exact-pinned runtime deps, `--no-deps` installs, non-root user, build-time bundle-presence guard), `min_machines_running=1` (no scale-to-zero), rolling deploy strategy, HMAC-only trust boundary (public ingress is a documented, deliberate decision — Edge Functions can't join Fly's private mesh).

## Database footprint (fresh counts)

```
migrations: 52   seeds: 43   validation: 9   rollback: 72   etl: 2
```
Latest migration: `052_drop_unused_scaffolding_tables.sql` (drops `feature_flags` + 4 other confirmed-dead tables).

## Observability / monitoring

**Only real, executing observability code:** `supabase/functions/_shared/telemetry/telemetry.ts` — a structured-logger-backed shim (`captureError`/`recordMetric`/`withTiming`), not an external APM.

**Explicitly not wired** (per the code's own doc comments and `KNOWLEDGE.html`): Sentry, PostHog, OneSignal, OpenWeatherMap, Cloudinary — all "seams only, config slots exist, none wired." No Datadog, Prometheus, or Grafana anywhere in the repo (zero hits, not even a stub).

## Feature flags

**Removed, not active.** A `public.feature_flags` table was created (migration 015), never read/written by any application code, and dropped by the latest migration (052) as confirmed-dead scaffolding. No LaunchDarkly/GrowthBook integration exists. No flag-gating mechanism is live anywhere in the running system today.
</content>
