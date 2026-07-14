# [ACTIVE]_DOC-P4-00_Backend_Foundation_Architecture_v1.0

**Status:** ACTIVE — Backend Foundation Architecture (design only; no code, no endpoints, no schema/DB change).
**Version:** v1.0
**Date:** 2026-07-14
**Placement:** docs/architecture/[ACTIVE]_DOC-P4-00_Backend_Foundation_Architecture_v1.0.md
**Work Package:** WP-8A (Backend Foundation Architecture).
**Supersedes:** None (first backend-foundation document; the umbrella beneath the referenced DOC-P4-01 Frontend Spec and DOC-P4-02 Service/Edge-Function Specs).
**Governance basis (frozen, authoritative, NOT redesigned here):** DOC-P3-02 (CDM), DOC-P3-03/03A (Business Logic + Logic Governance), DOC-P3-04 v1.3 (Schema/ERD), DOC-P3-05 (Migration Strategy), DOC-P3-06 v1.2 (API Contract), DOC-P3-07 v1.2 (Security), DOC-P3-08 v1.1 (Integration & Infrastructure), RE-DOC-01–05 (Recommendation Engine), SER-001 (city_tier), REPO-CERT-006 (GREEN), REPO-CERT-007 (Data Gate ICD-1).

> **Scope discipline.** This document defines *how the backend code is organized and built* on top of the already-frozen platform, API contract, security model, and RE design. It introduces **no new endpoint, table, schema element, or business rule.** Every architectural choice either cites a frozen artifact or is explicitly flagged as an implementation-layer convention (DCR-class), never a silent change to frozen architecture.

---

## Executive Summary

FooFoo's backend is **not a monolith server** — the frozen architecture (DOC-P3-06 §01, DOC-P3-08) defines it as **Supabase Edge Functions (Deno/TypeScript) over PostgreSQL**, split into two surfaces: **Surface A** (mobile app → Supabase PostgREST directly, guarded by RLS) and **Surface B** (custom Edge Functions for everything touching the `re_engine` schema, which is service-role-only). The Recommendation Engine is an **isolated module** (RE-DOC-01) whose only boundary is the versioned `/v1` HTTP contract. This document formalizes the **code architecture** for Surface B and the RE runtime: a layered `functions → services → repositories → database` structure with dependency injection, explicit in-function authorization (because RLS does not protect service-role calls), a shared RE core reused by both the live endpoint and the nightly CRON, and a deploy pipeline (Supabase CLI + GitHub Actions) that runs the `900–905` validation and safety gates as release blockers.

**Backend readiness: HIGH for design, GREEN data baseline in place (ICD-1).** The schema, seeds, RE data (2,952 cohorts / 20,664 weekly plans), triggers, and safety gates are all proven (REPO-CERT-007). What remains is implementation of the 10 frozen endpoints against this baseline.

---

## 1. Overall Backend Architecture

```
┌────────────────────────── Mobile App / Admin Portal ──────────────────────────┐
│                                                                                │
│   Surface A (direct)                         Surface B (RE / privileged)       │
│   Supabase JS SDK ───► PostgREST ──► RLS      HTTPS /v1/* ───► Edge Functions   │
│   (profiles, week_plans, plan_slots,          (Deno/TS, service_role)          │
│    interaction_events, dishes read…)                 │                         │
└──────────────────────────────────────────────────────┼─────────────────────────┘
                                                        ▼
                        ┌──────────────── Edge Function runtime ────────────────┐
                        │  API layer (handler)  →  Service layer  →  Repository  │
                        │      auth/validate         RE core / domain   pg access │
                        └───────────────────────────────┬────────────────────────┘
                                                         ▼
        PostgreSQL (ap-south-1)  ── public schema (RLS) ── re_engine schema (service_role only)
                                          ▲                         ▲
             triggers (derive/derive-vector/propagate)   nightly CRON (23:30 UTC / 05:00 IST, LF-L01)
                                                         │
        External (server-side): OpenWeatherMap (weather_cache 12h) · OneSignal · Cloudinary · PostHog · Sentry
```

- **Platform:** Supabase — PostgreSQL, Auth, Edge Functions, Storage (DOC-P3-08 §Tech-Stack, item 1). Region **`ap-south-1`** (fixed, DOC-P3-08 §Environment).
- **Two surfaces (DOC-P3-06 §01):** A = direct PostgREST+RLS for `public` tables with client RLS policies; B = Edge Functions for the RE / `re_engine` (locked `service_role`, DOC-P3-04 §03.26).
- **RE isolation (RE-DOC-01 §01–02):** the RE reads the app event stream and knowledge layer, never writes app user tables; the HTTP contract is its only in/out boundary — enabling future microservice extraction with zero app change.

## 2. Folder Structure (Edge Functions monorepo, under `supabase/`)

Deno-based; each deployable Edge Function is a folder under `supabase/functions/`. Shared code lives in `_shared/` (Deno convention: leading underscore = not independently deployable).

```
supabase/
  functions/
    _shared/
      api/            # handler helpers: router, request parsing, response envelope
      auth/           # JWT verification, claims extraction, in-function authorization
      middleware/     # compose(): auth → validate → rate-limit → handler → error/log
      validation/     # zod schemas per endpoint (request/response), CHECK-mirroring
      services/       # domain/service layer (business orchestration)
        re/           # Recommendation Engine core (the shared module — §14)
          candidate/  # class-first candidate generation (LF-D01..D07)
          scoring/    # FinalScore, weight ladder, MMR (LF-E01..E08, F01..F03)
          coldstart/  # confidence ladder, bandit (RE-DOC-04)
          safety/     # 4 safety gates (LF-H01..H04) — last line before serve
        onboarding/   # persona/cohort resolution (LF-A01..A09)
        planning/     # week plan / class plan assembly (LF-B01..B02, C01..C02)
        content/      # dish/ingredient/tag read models
      repositories/   # data-access layer: one repo per aggregate; only place raw SQL lives
      db/             # pg client factory (service_role), transaction helper
      config/         # typed env/config loader (§13)
      logging/        # structured logger (§12)
      errors/         # error catalogue + typed AppError (§11, DOC-P3-06 §21)
      types/          # generated DB types (supabase gen types) + domain types
    consent/          # POST /v1/consent           (thin handler → service)
    onboarding/       # POST /v1/onboarding
    recommendations/  # POST /v1/recommendations
    events/           # POST /v1/events
    plan/             # GET  /v1/plan/{user}/{week}
    health/           # GET  /v1/health
    ...               # remaining endpoints from DOC-P3-06 §03 (10 total)
    _cron/
      nightly-plan/   # LF-L01 scheduled generation (reuses services/re — DCR-P3-06-007)
      daily-features/ # dish feature snapshot (LF-J09), acceptance-rate refresh
  migrations/         # SYMLINK/mirror of repo database/migrations (source of truth stays in repo)
  tests/              # deno test: unit (services), integration (against local supabase)
```

**Rule:** endpoint folders are **thin** — parse → delegate to a service → format response. No business logic in handlers. All SQL lives only in `repositories/`.

## 3. Module Boundaries

| Module | Owns | May depend on | May NOT depend on |
|---|---|---|---|
| `api`/handlers | HTTP shape, status codes | services, middleware, validation | repositories, db (directly) |
| `services` (domain) | business orchestration per DOC-P3-03 LFs | repositories, other services, re core | api/handlers, HTTP |
| `services/re` (RE core) | candidate→score→MMR→safety | repositories (read-only knowledge), config | app user-table writes (RE-DOC-01 §02) |
| `repositories` | all SQL, mapping rows↔domain | db client, types | services logic, HTTP |
| `db` | pg connection, transactions | config | everything above |

The **RE core is the strictest boundary**: it reads `re_engine.*` + `dishes`/`dish_ingredients` and writes only RE-owned tables (`suggestion_logs`, `plan_slots` slate fields, `never_list`, `not_today_suppression`) — never `profiles`/user tables (RE-DOC-01 §02; DOC-P3-06 §13 read/write matrix).

## 4. Repository Pattern

- One repository per aggregate root: `DishRepository`, `CohortRepository`, `WeeklyPlanRepository`, `PersonaRepository`, `InteractionEventRepository`, `SuggestionLogRepository`, `ConfigRepository`, etc.
- Repositories expose **intention-revealing methods** (`findClassDishOptions(classCode)`, `resolveCohort(personaId, stateCode, dietMode, cityTier)`), never leak SQL upward.
- Read models are **typed** from `supabase gen types` output (§21) so schema drift breaks the build.
- **Keyset pagination mandatory** on partitioned tables (`interaction_events`, `suggestion_logs`) on `(occurred_at, id)` per DOC-P3-06 §09 — no OFFSET.
- Repositories are the **only** layer that references `re_engine` (which is service-role-only) — reinforcing the isolation boundary in code.

## 5. Service Layer

- Services implement the DOC-P3-03 Logical Functions (LFs) as orchestration, delegating I/O to repositories. Each service method maps to one or more `LF-*` and cites it in a docstring (coding standard §24).
- The **recommendation service** is the shared core invoked by both `POST /v1/recommendations` (live) and `_cron/nightly-plan` (scheduled) — a single implementation, per **DCR-P3-06-007** (scheduled jobs never call the public HTTP endpoint).
- Services are **stateless**; per-request state is passed explicitly (request context object). No module-level mutable state (safe for serverless concurrency).

## 6. API Layer

- Implements **only** the 10 frozen Surface-B endpoints (DOC-P3-06 §03): `/v1/consent`, `/v1/onboarding`, `/v1/recommendations`, `/v1/events`, `/v1/plan/{user}/{week}`, `/v1/health`, + the remainder in §03; `/v2/recommendations` is **reserved, not implemented** (RE-DOC-01 §04).
- Uniform **response envelope** and **error catalogue** per DOC-P3-06 §20–21, including `trace_id` for audit join-back to `suggestion_logs`/`context_log`/`interaction_events` (DOC-P3-06 §07).
- Pipeline latency budgets are contractual: `/v1/recommendations` ≤ 800 ms total (DOC-P3-06 §03), onboarding steps < 200 ms.
- **Surface A is not re-implemented** — the app uses the Supabase SDK directly for `public` tables with RLS (DOC-P3-06 §01.1/§02). Backend work is Surface B only.

## 7. Authentication Flow

- Supabase Auth issues JWTs; the client sends `Authorization: Bearer <jwt>`.
- Every Edge Function **verifies the JWT first** (shared `auth/verifyJwt`), extracting `sub` (user id) and `role` claim. Unauthenticated → `401` per DOC-P3-06 §05.1 auth-failure matrix.
- `/v1/health` is the only unauthenticated endpoint (reads `re_engine.re_engine_versions.is_active`, DOC-P3-06 §13).

## 8. Authorization Strategy

- **Critical rule (DOC-P3-06 §01.2 / §05):** Edge Functions run under `service_role`, which **bypasses RLS** — so RLS provides *zero* protection at this layer. **Every ownership/authorization check must be coded explicitly in the function.**
- Pattern: after JWT verify, the service asserts the authenticated `sub` owns the target rows (e.g., `week_plan.profile_id == sub`) before any read/write. Centralized `auth/assertOwns(...)` helper.
- `re_engine` is never exposed to `anon`/`authenticated` (DOC-P3-04 §03.26) — only reachable via service-role Edge Functions, and only through the authorized service methods.
- Admin Portal uses a distinct role/claim; admin-only endpoints assert it. (Content-ops writes are a "manual gate" per DOC-P3-06 §03 LF-K04 — not a public API.)

## 9. Middleware

`compose(handler)` wraps every endpoint with, in order: **request-id/trace-id → JWT auth → input validation → rate-limit check → handler → response envelope → error handler → structured log/metrics flush.** Cross-cutting concerns live here, never in handlers.

## 10. Validation Framework

- **Zod** schemas per endpoint for request and response, colocated in `_shared/validation/`.
- Enum/format validators **mirror the database CHECK constraints** (DOC-P3-07 §26: DB CHECKs are the source of truth for valid enum values) — validation fails fast before hitting the DB.
- Response schemas are validated in non-prod (contract self-test) to catch drift from DOC-P3-06 shapes.

## 11. Error Handling

- Single typed `AppError { code, httpStatus, message, retriable, traceId }`; codes come from the **API Error Catalogue (DOC-P3-06 §21)**.
- Handlers never leak stack traces or DB errors to clients; internal detail goes to logs + Sentry with the `trace_id`.
- Safety-gate violations and derivation conflicts are **P0** (DOC-P3-07 §02, §34) — surfaced as hard failures, never swallowed.

## 12. Logging

- Structured JSON logger (org standard); every log carries `trace_id`, endpoint, user (hashed), latency, outcome.
- No PII in logs (DOC-P3-07 §16 data classification; DPDP). No secrets ever logged (`/hygiene-secrets` discipline).
- Errors → **Sentry** (server-side); product analytics → **PostHog** (DOC-P3-08 §09). Both are server-side for anything touching secrets.

## 13. Configuration

- Typed config loader reads Edge Function env secrets (DOC-P3-08 §Env-Vars): `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_DB_URL`, `OPENWEATHERMAP_API_KEY`, `ONESIGNAL_REST_API_KEY`, `CLOUDINARY_CLOUD_NAME`, etc.
- **Secrets are server-side only, rotatable without code/schema change** (DOC-P3-07 §14.1). Config is **not** schema-dependent (DOC-P3-08 §17). Fail-fast on missing required secret at cold start.

## 14. Recommendation Engine Runtime Integration

- The RE core (`services/re`) is the runtime realization of RE-DOC-01–05 and DOC-P3-03 §06–10, executed as the class-first pipeline: **cohort/context → class plan → candidate pool → hard constraints → scoring (weight ladder) → MMR variety → suppression → 4 safety gates → slate**.
- Reads: `re_class_dish_options`, `re_cohorts` (now tier-aware, SER-001), `re_weekly_class_plans`, `dishes`, `dish_ingredients`, `dish_tags`/`genome_vector`, config tables. Writes: `plan_slots` slate fields, `suggestion_logs`, `context_log` (DOC-P3-06 §13).
- **Engine versioning** via `re_engine.re_engine_versions` (`classfirst_v1` active) — enables shadow/A-B without app change (DOC-P3-06 §17.1: `classfirst_v1 → v2 → ltr_v1 → ml_v1`).
- Cold-start uses the confidence ladder + bandit exploration (RE-DOC-04); config already seeded (weight ladder 5 tiers, scoring/confidence/variety configs — verified live).
- **Same core, two callers:** live endpoint + nightly CRON (DCR-P3-06-007).

## 15. Supabase Interaction Model

- Edge Functions connect with the **service-role** key (server secret) → full DB access, RLS bypassed (hence §8's explicit authz).
- Prefer the **pg client (`SUPABASE_DB_URL`)** for RE/transactional work (transactions, `SELECT … FOR UPDATE`); use PostREST/SDK only where convenient for simple reads.
- Derived columns (`diet_type`, `is_jain`, `allergen_flags`, `genome_vector`) are **never written by the backend** — they are trigger-owned (CDM Invariant 6; proven in REPO-CERT-007). Content-ops writes ingredients/tags/`dish_ingredients`/`dish_tags`; triggers derive the rest.
- `tags.vector_position` assignment and re-derivation are DB functions (migrations 010/023) — the backend calls them, never reimplements the logic.

## 16. Transaction Strategy

- Recommendation generation runs read-mostly; the **slate write + suggestion_log + context_log commit atomically** per request (one transaction) so a slate is never half-recorded (auditability, DOC-P3-03A §08).
- Onboarding writes (profile/persona/cohort resolution) are transactional per step.
- Never/Not-Today sync writes to `re_engine` are transactional (DOC-P3-06 §06.3).
- Retry only on serialization failures; user-facing hard-constraint/safety failures are never retried.

## 17. Caching Strategy

- **Server-side:** only `weather_cache` (12h TTL, DOC-P3-04 §03.18 / DOC-P3-08 §19) — OpenWeatherMap results cached to stay within 1,000 calls/day.
- **Dish feature snapshot** (`re_engine.dish_features`, LF-J09) is a daily-materialized read model (a cache of genome/popularity) refreshed by `_cron/daily-features`.
- **Client-side:** app caches plan/dish data (TanStack Query + MMKV, stale-while-revalidate) — a frontend concern, noted for contract awareness (DOC-P3-08 §19). No Redis at MVP.

## 18. Background Jobs

- Scheduler: **`pg_cron`** (available; DOC-P3-08) and/or Supabase scheduled functions. Jobs:
  - **Nightly plan generation** — 23:30 UTC / 05:00 IST (LF-L01, DOC-P3-08 §CRON) via `_cron/nightly-plan` reusing the RE core.
  - **Daily dish-feature snapshot / acceptance-rate refresh** (LF-J09).
  - Weather cache warmups, notification scheduling (OneSignal server leg).
- Jobs invoke the **shared service layer**, not HTTP endpoints (DCR-P3-06-007). Each job is idempotent and logs to operational audit tables (`etl_job_runs`, `safety_gate_log`, `coverage_gap_log`).

## 19. Event Flow

- App emits interactions → `POST /v1/events` → append-only `interaction_events` (partitioned) + Never/Not-Today sync to `re_engine` (DOC-P3-06 §06.3).
- RE reads the event stream read-only (RE-DOC-01) to evolve user taste vectors (LF-J03) — **eventually**, via the nightly job / next request, not synchronously in the event write path.
- Reason tags recorded at slate generation are **immutable** (CDM Invariant 14).

## 20. Dependency Injection

- Lightweight **constructor/factory DI** (no heavy framework, Deno-appropriate): a per-request `Container` builds `db → repositories → services → handler`. Enables swapping real repos for fakes in unit tests, and swapping RE versions.
- No global singletons for stateful deps; the pg pool is the only process-level singleton (created at cold start).

## 21. Testing Strategy

- **Unit** (`deno test`): services + RE core with in-memory/fake repositories — deterministic scoring, constraint, and safety-gate logic. The RE's determinism is testable (proven in the WP-6E clean-room).
- **Integration:** run against a **local Supabase / disposable Postgres** (the exact WP-6E clean-room pattern) — apply migrations 001–030 + seeds, then exercise endpoints; assert the `900–905` validation + 4 safety gates return 0 violations.
- **Contract tests:** validate live responses against the DOC-P3-06 zod response schemas.
- **Safety-gate tests are release-blocking** (see §23). Target: the frozen NFRs (DOC-P3-06 §18) and RE quality metrics.

## 22. Environment Strategy

- **Locked map (DOC-P3-08 §Env; DOC-P3-07 §31):** Local dev + **`foofoo-staging`** (same schema, separate secrets) + Production **`foofoo-mvp`**. No new environment without Founder approval.
- **Canonical execution project going forward:** `cmkswalqpmmqojwdmqbv` (per Founder, WP-6E.1) — treat as the staging/canonical target; production promotion remains Founder-gated.
- Backend developed and tested locally/staging; **production deploys are never automatic** (DOC-P3-08 §Env rule 3).

## 23. Deployment Strategy

- **Edge Functions deploy via Supabase CLI**, alongside migrations, under the **same numbered-migration discipline** as the frozen schema (DOC-P3-08 §14; DOC-P3-05 Part a). Every forward migration keeps its paired `_rollback.sql`.
- **CI = GitHub Actions** (DOC-P3-08 §Tech-Stack item 8): typecheck → lint → unit tests → **RE safety-gate SQL (diet/allergen/Jain = 0 rows) against staging, P0 release blocker** (DOC-P3-08 §CI; DOC-P3-07 §34) → build.
- Promotion staging→prod is a **separate, explicitly Founder-approved** step; Claude Code never pushes to `main`/`develop` without approval.

## 24. Coding Standards

- Org `coding-standards-enforcer`: JSDoc/inline docs on every function/handler citing the `LF-*` it implements; **structured logger only, never `console.*`**; changelog entries for non-trivial changes.
- TypeScript strict mode; no `any` at module boundaries; DB types generated, not hand-written.
- One responsibility per file; handlers thin; SQL only in repositories.

## 25. API Versioning

- Path-based (`/v1/*`), per DOC-P3-06 §17. `/v2/recommendations` reserved for future LTR/ML (RE-DOC-01 §04) behind the unchanged `/v1` contract.
- RE algorithm versions (`classfirst_v1 → v2 → ltr_v1 → ml_v1`) evolve **behind** the stable contract via `re_engine_versions` (shadow/canary) — no client change.
- Contract stability statement (DOC-P3-06 §16.4) governs additive-only changes.

## 26. Rate Limiting

- Per DOC-P3-06 §10 (authoritative). Enforced in middleware (per-user/JWT `sub`), keyed appropriately; `/v1/recommendations` and `/v1/events` are the hot paths. Free-tier ceiling: 500K Edge Function invocations/month (DOC-P3-08 §07) — a capacity-planning input, not a design blocker.

## 27. Observability

- Per DOC-P3-06 §22: structured logs + `trace_id` correlation; latency histograms per endpoint against the §18 budgets; error rates → Sentry; product events → PostHog.
- **Safety-gate dashboards**: continuous 0-violation assertion on diet/allergen/Jain (any non-zero = P0). Coverage-gap logging when a class yields < 3 candidates (LF-D07).
- Health endpoint + engine-version surfaced for ops.

## 28. Future AI Integration

- The frozen baseline is a **classical (non-neural) RE** — there is **no `pgvector`/embedding/LLM infra today** (confirmed across DOC-P3-06/07/08). `pgvector` extension is *available* on the platform (17.6) but unused.
- Future AI (`ltr_v1`, `ml_v1`, embeddings, LLM explanations) enters **only** via: (a) a new RE version behind the stable contract, and (b) a governed **AGR/SER** (adding vector search touches the `re_engine` schema and is net-new infra — DOC-P3-08 §39C). The RE module isolation (RE-DOC-01) makes this a scoring-stage swap, not an app refactor.
- Design hooks now: keep the scoring stage pluggable (strategy interface), keep `genome_vector` available, keep feature snapshots materialized.

## 29. Scalability Roadmap

- **MVP (Supabase free/pro, <1K DAU):** Edge Functions + PostgreSQL; RE "Research Mode" (RE-DOC-05 State A). Free-tier ceilings honored (§26).
- **Growth (5K+ DAU):** RE "Cluster Mode" (State C); read replicas / connection pooling (Supavisor); partition maintenance (`pg_partman`, present).
- **Microservice extraction:** the RE module can be lifted out behind its HTTP contract with zero app change (RE-DOC-01 §01) when scoring cost/latency warrants — the boundary is designed for it.
- Region stays `ap-south-1`; CDN (Cloudinary) fronts images.

## 30. Developer Workflow

1. Branch off `main` (never commit to `main`/`develop` without approval).
2. Local: `supabase start`; apply migrations 001–030 + seeds; write service + repo + handler; `deno test`.
3. Run the `900–905` validation + safety gates locally (the WP-6E procedure).
4. PR → GitHub Actions (typecheck/lint/test/safety-gates) → review.
5. Deploy to `foofoo-staging` via Supabase CLI; re-run validation on staging.
6. Founder-approved promotion to `foofoo-mvp`.

---

## Backend Readiness Score

| Dimension | Score | Basis |
|---|---|---|
| Data baseline | **9/10** | ICD-1 Data Gate PASSED (REPO-CERT-007); schema/seeds/triggers/safety gates proven |
| API contract clarity | **9/10** | 10 endpoints frozen + fully specified (DOC-P3-06 v1.2) |
| Security model clarity | **8/10** | RLS + service-role model frozen (DOC-P3-07); in-function authz rule explicit; SECURITY DEFINER RPC hardening open |
| Infra/deploy clarity | **8/10** | Supabase + CLI + GH Actions + env map locked (DOC-P3-08) |
| RE runtime readiness | **8/10** | Data + config + versioning in place; runtime code not yet built |
| **Overall backend readiness** | **8.5/10** | Design-complete foundation; implementation not started |

## Risks

1. **Service-role authz omissions** — since RLS doesn't protect Edge Functions, a missed in-function ownership check = data exposure. *Mitigation:* centralized `assertOwns`, mandatory in the middleware pattern, contract-tested.
2. **Latency budget** (`/v1/recommendations` ≤ 800 ms) with cohort/plan joins at scale. *Mitigation:* indexes present (134); materialized dish features; keyset pagination.
3. **SECURITY DEFINER RPC exposure** (from WP-6E.1 read-only review) — trigger functions callable by anon/authenticated via RPC. *Mitigation:* revoke EXECUTE / move out of exposed schema — a hardening item, recommendation only.
4. **Free-tier ceilings** (500K invocations, 500MB DB). *Mitigation:* capacity planning at growth; caching.
5. **AGR-P3-07-001 (DPDP under-13 age gate)** remains OPEN and launch-blocking (Security §06/§19/§38) — not a backend-arch blocker, but gates production.
6. **ICD-1 scope** — S-08/S-10 dish-linked options are partial + S-15 deferred; RE candidate coverage is ICD-1-bounded until content expands (Deferred Knowledge Register).

## Recommended Implementation Order

1. `_shared` foundation (config, db client, logger, errors, auth, middleware, validation, DI).
2. `/v1/health` (thinnest; proves the deploy pipeline + CI safety gates end-to-end).
3. `/v1/consent` + `/v1/onboarding` (persona/cohort resolution — reads the seeded RE reference layer).
4. **RE core** (`services/re`: candidate → scoring → MMR → safety) with unit tests.
5. `/v1/recommendations` (live) + `_cron/nightly-plan` (shared core).
6. `/v1/events` + Never/Not-Today sync; `/v1/plan`.
7. Remaining §03 endpoints; observability + rate limiting hardening.

## Estimated Implementation Work Packages (Phase 8)

| WP | Scope | Depends on |
|---|---|---|
| **WP-8B** | Backend scaffolding + `_shared` + CI pipeline + `/v1/health` | this doc |
| **WP-8C** | Auth/authz framework + onboarding + consent | 8B |
| **WP-8D** | RE runtime core (candidate/scoring/MMR/coldstart) + unit tests | 8B |
| **WP-8E** | `/v1/recommendations` + nightly CRON (shared core) + safety-gate CI | 8C, 8D |
| **WP-8F** | events + plan + suppression + taste-vector evolution | 8E |
| **WP-8G** | Observability, rate limiting, load/latency validation vs NFRs | 8E |
| **WP-8H** | Admin/content-ops endpoints; security hardening (RPC EXECUTE, DPDP gate coordination) | 8C |

## Suggested Phase 8 Roadmap

**Phase 8 = Backend Engineering.** WP-8A (this) → 8B (scaffold) → 8C (auth/onboarding) → 8D (RE core) → 8E (recommendations+CRON) → 8F (events/plan) → 8G (observability/perf) → 8H (admin/hardening) → **API Gate** (Edge Functions pass behavioral validation against the frozen DOC-P3-06 contract) → then Frontend (DOC-P4-01) → **Release Gate** (DPDP AGR-P3-07-001 resolved, launch criteria).

---

## Critical Self-Review
- **No redesign, no code, no schema/DB/migration/seed change.** Every architectural choice cites a frozen artifact (DOC-P3-06/07/08, RE-DOC-01, CDM invariants) or is flagged as an implementation-layer convention.
- **Consistency check:** two surfaces, 10 endpoints, service-role+in-function authz, RE isolation, shared core for live+CRON, numbered-migration deploy, locked env — all match the frozen documents; nothing contradicts DOC-P3-06/07/08.
- **Honest limits:** DOC-10 (Technical Architecture, .docx) was consulted via its formalization in DOC-P3-08, not re-read byte-for-byte; where DOC-10 and frozen P3 differ, P3 wins (DOC-P3-08 §40). Runtime performance against the 800 ms budget is a design intent to be validated in WP-8G, not yet measured.

## Versioning & Placement
First issue (v1.0), placed in `docs/architecture/` as the DOC-P4 backend-foundation umbrella beneath DOC-P4-01/02. Naming per WP-5AA standard. No frozen P3 document altered.

---

Founder Sign-off: _______________________ Date: ___________
