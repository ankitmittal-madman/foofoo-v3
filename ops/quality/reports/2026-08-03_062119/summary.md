# Ghar Production Quality Report

_Generated 2026-08-03T06:21:19.311688+00:00 · git `aa841f5`_

| Quality score | Pass % | Passed | Failed | Skipped | Launch |
|---|---|---|---|---|---|
| **90.0** | 100.0 | 208 | 0 | 4 | ❌ NO |

**Launch readiness:** NOT CERTIFIABLE HERE — 0 failing tests, but P0 surfaces (DB, edge functions) are UNVERIFIED in this environment; certify them in CI/staging before launch

## Steps

| Step | Phase | Status | Priority | Detail |
|---|---|---|---|---|
| inventory | 1-2 | PASS | P3 | 66 components, 17 features |
| ruff-lint | 16 | PASS | P2 | clean |
| unit-core | 4 | PASS | P0 | 48 passed, 0 failed, 0 skipped |
| unit-service | 4 | PASS | P0 | 68 passed, 0 failed, 0 skipped |
| quality-contract | 6 | PASS | P0 | 5 passed, 0 failed, 0 skipped |
| quality-recsys | 8 | PASS | P0 | 63 passed, 0 failed, 4 skipped |
| quality-security | 13 | PASS | P0 | 12 passed, 0 failed, 0 skipped |
| quality-planning | 5 | PASS | P1 | 12 passed, 0 failed, 0 skipped |
| chaos | 14 | PASS | P1 | fail-safe behaviour held |
| performance | 12 | PASS | P2 | recommendations p50=43.48ms p99=96.69ms (threshold 1500.0ms, in-process) |
| secrets-scan | 13 | PASS | P1 | no hardcoded secret values detected |
| database | 7 | SKIP | P0 | no live database configured |
| edge-functions | 6 | BLOCKED | P0 | 5 Deno edge-function test file(s) present but not runnable |
| ui-playwright | 9-11 | SKIP | P1 | GHAR_WEB_URL not set. The frontend is an Expo/React-Native app with no committed web build; provide a running web target (e.g. `expo start --web`) to enable browser tests. |

## Unverified P0 surfaces (not certifiable in this environment)

- database: DATABASE_URL / SUPABASE_DB_URL not set — migrations, RLS, constraints, and data-integrity checks require a reachable Postgres with the Supabase auth.* bootstrap; not verifiable in this environment.
- edge-functions: Deno runtime is not installed in this environment; `deno test` cannot execute. Install Deno (or run in Supabase CI) to validate consent/feedback/household/recommendations/user-delete/user-export functions.