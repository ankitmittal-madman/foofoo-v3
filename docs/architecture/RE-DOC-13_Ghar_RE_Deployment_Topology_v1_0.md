# Ghar RE v1.0 — Deployment Topology

**Status:** ACTIVE — verified directly against the repository at commit `db22b6b` (branch `main`), reflecting the state after signature verification (Phase C.5), real application tables (Phase C.5), and public ingress + rate limiting (the most recent commit).
**Version:** v1.0
**Date:** 2026-07-29
**Placement:** docs/architecture/
**Supersedes:** None. No prior Phase F topology review document exists in this repository as of this audit — searched by filename (`*topology*`) and by content; nothing found. This document is written fresh against RE-DOC-10 §13's deployment section and the current `fly.toml`/`Dockerfile`, not as a revision of an earlier document.
**Dependencies:** RE-DOC-10 (§13 Deployment Architecture), RE-DOC-12 (Status and Roadmap, companion document), `ghar_re_service/fly.toml`, `ghar_re_service/Dockerfile`, `ghar_re_service/README.md`.

---

## Executive Summary

Every component below is described by what was directly verified in the repository — a file read, a config parsed, a test run — with unverifiable claims (anything requiring a live Fly dashboard, real deployed secrets, or production traffic logs) marked explicitly rather than assumed to match what was configured. **Nothing described here is currently deployed.** `ghar_re_service/README.md`'s own banner states "PREPARED, NOT DEPLOYED," and this session confirmed why independently: no `flyctl` binary or Fly credentials exist in this environment, and the sandbox's outbound proxy returns 403 on both `fly.io` (blocks installing `flyctl` or validating config) and the Docker base-image registry (blocks building the image). This is a description of what *would* run if the prepared artifacts were deployed as-is, not a report on a live system.

---

## 1. Component map

```
┌─────────────┐
│  Frontend    │  Not present in this repository — no app/mobile/web directory exists here.
└──────┬───────┘  Out of scope for this document; treated as an external caller of the Edge Function API.
       │ HTTPS, user JWT
       ▼
┌─────────────────────────────┐
│  Supabase Edge Functions      │  Deno/TypeScript. Owns 100% of DB access and user identity
│  (recommendations, consent)   │  (RE-DOC-10 §1, verified — no DB driver imported by the RE).
└──────┬───────────────────────┘
       │ HTTPS, HMAC-signed          │ Supabase client (service-role, RLS bypassed)
       ▼                             ▼
┌─────────────────────┐      ┌─────────────────────────┐
│  Ghar RE (Fly.io)     │      │  Postgres (Supabase)     │
│  Python/FastAPI       │      │  public schema — real     │
│  stateless, no DB      │      │  application tables       │
└─────────────────────┘      └─────────────────────────┘
```

## 2. Component-by-component

### 2.1 Frontend

**Not present in this repository.** No `app/`, `mobile/`, or `web/` directory exists anywhere in the tree at the time of this audit (checked directly: `find . -maxdepth 2 -iname "*app*" -o -iname "*mobile*"` returns nothing outside `node_modules`/`.git`). RE-DOC-10 §1's architecture diagram names "Frontend" as the request originator; this document treats it as an external, out-of-repository caller of the Edge Function API and makes no claim about its runtime, deployment, or ownership.

### 2.2 Supabase Edge Functions (`supabase/functions/`)

- **Responsibility:** 100% of database access, all user authentication/authorization, request composition, response fallback, event logging (RE-DOC-10 §1, confirmed — the RE itself imports no database driver anywhere in `ghar_re_core/` or `ghar_re_service/ghar_re_service/`).
- **Runtime:** Deno, deployed as Supabase Edge Functions. Confirmed present: `recommendations/` (the RE-calling endpoint), `consent/` (a separate, unrelated endpoint for consent records), `_shared/` (common auth, DB client, logging, error-catalogue code used by both), `_tests/`.
- **Live functions, confirmed by directory listing:** exactly three deployable directories exist (`consent`, `recommendations`) plus `_tests` and `_shared` (not independently deployable). **No `onboarding` function exists** despite FD-04/DOC-P4-02 discussing a `/v1/onboarding` endpoint — this is consistent with RE-DOC-12 §1's finding that the household-answer-collection flow this repository actually implements is `household_answers`/`household_members` writes, not a dedicated onboarding endpoint.
- **Database access pattern:** `_shared/db/client.ts` constructs two client kinds — a service-role client (bypasses RLS; used for all reads/writes in `recommendations/compose.ts` and `events.ts`) and an authenticated client (RLS-scoped). The service-role client's use means **RLS provides zero protection on the Edge Function's own reads/writes** — every authorization decision must be coded explicitly. RE-DOC-12 §3 item 2 documents one place this was not done: the recommendations handler does not call the already-existing, already-tested `requireOwnership` before trusting a caller-supplied `household_id`.
- **Failure mode:** on any RE-call failure (timeout, network error, non-200, contract-invalid body), `fallback.ts` returns a valid HTTP 200 with a single hardcoded fallback plate (RE-DOC-12 §3 item 4 — this is a pan-India default, not the per-zone default RE-DOC-10 §11 specifies). The recommendation is still recorded via `events.ts` with an outcome other than `success`/`partial` (`timeout`/`network`/`http`/`bad_body`/`fallback`), so the failure is auditable even though the user experience degrades gracefully.
- **Scaling/ownership:** managed by Supabase's Edge Function platform — this document makes no claim about Supabase's own scaling behavior, since that is outside this repository and outside what was checked.
- **Cannot verify:** whether these functions are actually deployed to a live Supabase project, and if so, which project. RE-DOC-10's own environment map (FD-09, per the Founder Decision Register) was previously found stale on this exact point once already — this document does not repeat that check and takes no position on the current live project reference.

### 2.3 Ghar RE service (`ghar_re_service/`, intended for Fly.io)

- **Responsibility:** all recommendation mathematics (RE-DOC-10 §1). Stateless — holds an immutable, in-memory catalogue+config snapshot loaded at startup, computes, returns. Zero database connections, zero credentials beyond the one shared HMAC secret (confirmed: `providers.py`'s `EnvAuthConfigProvider` reads exactly one secret, `GHAR_RE_SERVICE_SECRET`, from the environment; no other credential is referenced anywhere in `ghar_re_service/`).
- **Runtime:** Python 3.11, FastAPI + uvicorn, single worker (`Dockerfile`'s `CMD` pins `--workers 1`, documented as necessary because `lifecycle.py`'s `Counters` and `ratelimit.py`'s `SlidingWindowRateLimiter` are both per-process in-memory state — a second worker would keep an independent, incomplete counter/rate-limit view).
- **Deployment boundary (as configured in `fly.toml`, not yet deployed):**
  - `min_machines_running = 1`, `auto_stop_machines = false` — a warm-instance floor, never scale-to-zero, because a cold start is directly user-visible on the critical recommendation path (RE-DOC-10 §13).
  - **Public ingress**, not private-only. This is the single most significant change since RE-DOC-10 §13 was written: that section specifies "private networking / IP allowlist, no public ingress," but the repository's most recent commit reverses this deliberately, because Supabase Edge Functions cannot join Fly's 6PN private mesh and cannot present a fixed egress IP range — verified directly in `ghar_re_service/fly.toml`'s own comment block and `README.md`'s "Public ingress and the trust boundary" section. **HMAC signature verification (§2.3 below) is now the sole trust boundary**, not a second layer behind network isolation.
  - `force_https = true` — plaintext HTTP is redirected; the household-composition data in request bodies (ages, dietary/allergy flags) must not cross the public internet unencrypted.
  - A concurrency backstop (`[http_service.concurrency]`, soft 200 / hard 250 in-flight requests) protects the 512MB `shared-cpu-1x` machine from being overwhelmed; this is separate from and complementary to the rate limiter below, which bounds *rate* rather than *concurrency*.
- **Trust boundary — verified in code and tests, not deployment:** every `/v1/recommendations` call must carry `X-Ghar-Signature: t=<unix>,v1=<hex>`, an HMAC-SHA256 over the raw request bytes. Verified via `ghar_re_service/ghar_re_service/auth.py` (pure verification logic, no FastAPI import) and `main.py`'s middleware, which runs the check before any body parsing. `test_auth.py` proves rejection of missing/malformed/tampered/wrong-secret/stale signatures, all returning 401.
- **Rate limiting** (`ratelimit.py`, new since the last RE-DOC): a sliding-window limiter keyed on the `Fly-Client-IP` header, registered to run **ahead of** HMAC verification in the ASGI middleware stack — confirmed by `test_ratelimit.py`'s ordering test, which sends an unsigned over-limit request and asserts a `429` (not `401`), proving no signature computation occurred for the shed request. Default: 300 requests/minute/IP, configurable via `GHAR_RE_RATE_LIMIT_PER_MINUTE` without a rebuild. Fails open (a missing limiter passes traffic through); the signature check fails closed (a missing secret returns 503) — this asymmetry is deliberate and documented in the module's own docstring.
- **Health/readiness:** `/healthz` (liveness, 200 once the process is listening) and `/readyz` (readiness, 200 only once the catalogue/config bundle is fully loaded) are distinct endpoints, both exempt from the rate limiter — verified in `main.py`'s `RATE_LIMITED_PATHS` set, which excludes both. This exemption exists specifically so a traffic spike cannot cause Fly's platform to misread a healthy machine as dead and restart it.
- **Startup data source:** an immutable bundle (`ghar_re_service/data/bundle/`), baked into the Docker image at build time by `scripts/export_bundle.py`, containing the 39-dish golden-sample catalogue plus the YAML config layer. Bundle version is a SHA256 content hash, surfaced at `/v1/meta`, so two deployed images' catalogues can be compared without inspecting either one directly. Verified: the bundle currently in the repo (`sha256:5bad97fad9a0f4a8` at last check) matches a fresh rebuild from `data/source/` (`export_bundle --check` passes).
- **Cannot verify:** whether the Docker image described by `Dockerfile` actually builds — the sandbox proxy blocks the base-image registry, so `docker build` has never been run in this environment, only simulated (a non-editable install into `site-packages`, run from outside the repo, reproducing the container's exact import-time conditions). Whether `fly config validate` accepts `fly.toml` — `flyctl` cannot be installed here. Whether the app, once deployed, is actually reachable at the intended public URL, and whether its live secret matches Supabase's copy.

### 2.4 Postgres (Supabase)

- **Two schemas relevant to the RE, kept deliberately separate:**
  - `public` — the live application schema. Holds `profiles` (the household root), `household_members`, `household_answers`, `household_context`, `recommendation_events`, `feedback_events` (RE-DOC-12 §1). Read/written exclusively by the Edge Functions' service-role client; the RE itself never connects.
  - `ghar_re` — the RE's own **offline golden-sample schema** (migrations 034–037), explicitly not the live application data (034's own header: "does NOT touch public.dishes / re_engine.* or the real 810-dish catalogue"). This schema exists for the RE's own reference/tooling use, is not queried by the Edge Functions, and is not queried by the deployed RE service either (the RE reads its baked bundle, never Postgres, at runtime).
  - `re_engine` — the legacy TypeScript RE's schema (referenced extensively throughout the Founder Decision Register, migrations 001–004 and others). Per RE-DOC-12's Executive Summary, this schema backs an engine that is not on the live recommendation path.
- **RLS:** enabled per-table on every `public`-schema table touched by this RE (verified: `household_answers`, `household_context`, `recommendation_events`, `feedback_events` each carry an own-row `auth.uid() = profile_id` policy in migration 038). This protects direct PostgREST access with a user JWT; it provides no protection against the Edge Function's own service-role client, which bypasses it entirely (§2.2 above).
- **Cannot verify:** the live Supabase project reference, whether these migrations have actually been applied to a live database (versus merely committed as SQL files), or current row counts in any live table.

## 3. Failure modes, by component

| Component | Failure | Observed behavior |
|---|---|---|
| Ghar RE unreachable/timeout | Edge Function's `re-client.ts` has a 2.5s timeout, at most one retry (network-level failures only, never on timeout — confirmed: `RE_TIMEOUT_MS = 2500` and the retry logic's own comment) | User still gets a valid 200 with a fallback plate (§2.2), recorded with outcome `timeout`/`network`/`http` |
| Ghar RE returns a contract-invalid body | `handler.ts` validates the RE's response against the shared contract before passing it through (fail-closed, RE-DOC-10 §15) | Fallback plate served, outcome `bad_body` |
| Ghar RE's rate limiter sheds a request | `429` with `Retry-After`, before HMAC verification runs | Not yet observed under real traffic — 300/min default is unmeasured (RE-DOC-12 §2) |
| Ghar RE's HMAC check rejects a request | `401` with a machine-readable `reason` token, before any parsing | Verified in tests; this is now the RE's sole trust boundary (§2.3) |
| Household has no `profiles` row (new user) | `compose.ts` returns a neutral-default household, `stubbed: true` | A real recommendation is still served; `events.ts` skips the DB write (no valid `profile_id`) but logs the outcome (RE-DOC-12 §1) |
| Ghar RE process crashes/restarts | In-memory counters and rate-limit state reset to zero (both are process-local, `--workers 1`, no external store) | Not user-visible on its own; `min_machines_running = 1` means a crash briefly reduces capacity to zero until Fly restarts the machine — this is a real single-point-of-failure risk inherent to the "not true scale-to-zero, but also not redundant" configuration RE-DOC-10 §13 chose |

## 4. Ownership and scaling — stated plainly where unverifiable

- **Edge Functions:** owned/scaled by Supabase's platform. Not independently verified this session.
- **Ghar RE:** intended to run as exactly one Fly.io machine (`min_machines_running = 1`) with a rolling-deploy strategy (bring up new, wait for `/readyz`, retire old — zero-downtime by design, per `fly.toml`'s `[deploy]` block). No horizontal scaling is configured; the concurrency backstop (§2.3) protects the single machine from overload, it does not add capacity.
- **Postgres:** owned/scaled by Supabase. Not independently verified.
- **None of the above ownership/scaling claims for Edge Functions or Postgres were checked against a live dashboard** — they are read directly off configuration files and code, consistent with this document's stated scope (repository state only).

## Critical Self-Review

This document's component map and failure-mode table are built entirely from configuration and code read during this session (`fly.toml`, `Dockerfile`, `main.py`, `auth.py`, `ratelimit.py`, `compose.ts`, `events.ts`, `handler.ts`, `fallback.ts`, `re-client.ts`, migrations 005/006/033–038) — no claim in §1–§3 restates an unverified prior summary. Every "cannot verify" statement names the specific blocker (missing `flyctl`, proxy 403 on `fly.io`/registry, no live Supabase access) rather than omitting the limitation silently. The absence of a prior Phase F topology document (stated in the header) was checked by both filename search and content grep before concluding this is a first version, not an update.

## Versioning & Placement

v1.0, filed under `docs/architecture/`, adjacent to RE-DOC-10/11/12 per the existing numbering convention for this document series. First version; nothing superseded.

Founder sign-off: _______________________ Date: ___________
