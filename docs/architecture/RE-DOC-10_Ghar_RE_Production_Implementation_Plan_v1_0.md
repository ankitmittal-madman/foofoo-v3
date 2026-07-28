# Ghar RE v1.0 — Production Implementation Plan
*(Companion to: Founder Decision — Architecture Frozen. Implements, does not revisit, that decision.)*

> **Status:** Architecture FROZEN per Founder Decision. This document is the concrete implementation plan against that decision — API contract, schemas, lifecycle, deployment, CI/CD, testing. Changes to the *architecture* require a new Founder Decision; changes to *this plan's details* (timeout values, endpoint names, etc.) are ordinary engineering iteration and don't require re-opening the frozen decision.

---

## 1. Architecture (restated for doc consistency)

```
Frontend
   │
   ▼
Supabase Edge Functions (TypeScript / Deno)   — auth, DB access, orchestration
   │  HTTP, service-to-service auth
   ▼
Python Recommendation Engine (stateless)      — ALL recommendation mathematics
   │
   ▼
Recommendation Response
```

RE owns zero DB connections, zero credentials, zero session state. Edge Functions own 100% of database access and all user identity. This single boundary is what makes every section below simple instead of ad hoc.

---

## 2. Implementation plan (phased)

| Phase | Deliverable | Depends on |
|---|---|---|
| A | Contract frozen: JSON Schema for request + response, versioned in a shared `contracts/` location | none |
| B | RE service skeleton: FastAPI app, startup catalogue/config loader, `/healthz` `/readyz`, `/v1/recommendations` returning the golden-sample pipeline's output through the new contract | A |
| C | Edge Function composition layer: household/context retrieval → payload build → signed call to RE → response handling → event logging | A |
| D | Observability: request ID propagation, structured logs, basic latency/error metrics on both sides | B, C |
| E | Contract tests: both sides validate against the shared schema in CI; golden-master regression test locked | A, B, C |
| F | Deployment: RE containerized and deployed with a warm-instance floor; Edge Functions deployed as today | B |
| G | Cutover: real 810-dish catalogue + KB parameter population replaces the golden sample inside the RE's startup bundle (Phase 1 of the product roadmap — separate from this document's scope) | B–F |

---

## 3. Project structure

```
ghar_re_service/                     # NEW — the production RE, distinct from the reference pipeline
├── app/
│   ├── main.py                      # FastAPI app, route registration
│   ├── lifecycle.py                 # startup/shutdown: load catalogue+config into memory
│   ├── schemas/                     # pydantic models mirroring contracts/ghar-re-v1.schema.json
│   ├── derivation/                  # D1-D7 (ported from ghar_re/derivation.py)
│   ├── scoring/                     # BASE, Q15 gain (ported from ghar_re/scoring.py)
│   ├── pairing/                     # pairing + assemble-7 (ported from ghar_re/pairing.py)
│   └── knowledge/                   # immutable catalogue/config loaders
├── data/                            # baked-in immutable snapshot (catalogue + config), versioned per build
├── tests/
│   ├── test_pipeline.py             # existing 16 tests, retargeted at the service layer
│   └── test_contract.py             # validates responses against the shared schema
├── Dockerfile
├── pyproject.toml
└── README.md

ghar_re/                             # DEMOTED — becomes offline tooling only:
                                      #   golden-master generation, experimentation, future v2/v3 training
contracts/
└── ghar-re-v1.schema.json           # single source of truth, read by both services' CI

supabase/functions/
└── recommendations/                 # NEW edge function: composes payload, calls RE, logs event
    └── index.ts
```

`ghar_re/` (the existing reference pipeline) is not deleted — it becomes the offline experimentation and training surface per point 10 (§15 below), decoupled entirely from the request path.

---

## 4. HTTP API contract

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/v1/recommendations` | The only compute endpoint |
| `GET` | `/healthz` | Liveness — 200 once the process is up |
| `GET` | `/readyz` | Readiness — 200 only after catalogue + config fully loaded |
| `GET` | `/v1/meta` | Returns current `engine_version` + `config_version` (for debugging/monitoring, no auth data) |

All compute calls require a service-to-service auth header (§9) and a `X-Request-Id` header (§10). No other endpoints exist — no direct data access, no admin routes, on this service.

---

## 5. JSON request schema

```json
{
  "request_id": "uuid",
  "household_profile": {
    "income_band": {"value": "mid", "confidence": 1.0, "source": "D1"},
    "time_route": {"value": "SIMPLIFY", "confidence": 1.0, "source": "D2"},
    "adventurousness": {"value": 0.42, "confidence": 1.0, "source": "D3"},
    "blend": {"value": 0.65, "confidence": 1.0, "source": "D4"},
    "constraints": { "diet": "veg", "is_jain": false, "allergens": [], "weaning_present": false },
    "variety_pressure": 0.5,
    "batch_posture": 0
  },
  "context": {
    "slot": "dinner",
    "date": "2026-07-23",
    "weekday": "thursday",
    "season": "monsoon",
    "weather": { "is_raining": true, "temp_c": 27 },
    "active_modes": ["fasting"],
    "calorie_target": null
  }
}
```

Notes:
- `household_profile` arrives **already derived** — D1–D7 run inside the RE per the frozen decision (point 2), so this shows the *shape* the RE emits internally and echoes in explainability, not what the Edge Function must compute. The Edge Function instead sends the **raw Q1–Q15 answers**; the schema above is what D1–D7 produces *from* that input, shown here for clarity on what the downstream scoring stage consumes.
- Full raw-input schema (Q1–Q15 + tenure context) lives in `contracts/ghar-re-v1.schema.json` alongside this derived shape — both are versioned together.

## 6. JSON response schema

```json
{
  "request_id": "uuid",
  "api_version": "v1",
  "engine_version": "1.2.0",
  "config_version": "2026.07.23",
  "plates": [
    {
      "plate_id": "uuid",
      "hero_dish_id": "...",
      "support_dish_id": "...",
      "plate_score": 8.42,
      "score_breakdown": {
        "base": 6.1, "gain_q15": 1.18, "pairing_compat": 0.35
      },
      "is_standalone": false
    }
  ],
  "warnings": []
}
```

`warnings` carries non-fatal notes (e.g. "only 5 of 7 plates could satisfy all constraints without repetition") — this is the mechanism for the "zero/partial eligible dishes" case in §11, returned as a valid response, not an error.

---

## 7. Startup lifecycle

```
process start
   → load contracts/schema (validate own request/response models against it — fail fast if drifted)
   → load immutable catalogue snapshot (baked into image, §8)
   → load YAML config layer (base_weights, distance_weights, q15_weights, pairing_rules,
     weather_rules, filters, derivation_params) + KB parameter tables
   → build in-memory indices (dishes by zone, by hero_role, by cuisine)
   → mark readyz = true
   → begin accepting /v1/recommendations traffic
```
`/healthz` returns 200 as soon as the process is listening, regardless of load state — `/readyz` is the one deployment orchestration should gate traffic on.

---

## 8. Immutable catalogue/config loading design

The RE never queries a database. Instead, a **build-time export step** (part of the CI pipeline, §14) pulls the current `dishes`, `dish_ingredients`, `cuisines`, and KB tables from Postgres and writes them to a versioned JSON/parquet bundle inside `ghar_re_service/data/`, committed into the Docker image at build time. A new catalogue or KB update requires a new image build + deploy — this is intentional per the frozen "immutable, loaded at startup" decision, and it also means catalogue changes are versioned and reviewable like code, not silently live.

---

## 9. Edge Function request composition

```
1. authenticate + authorize the request (existing Supabase auth)
2. fetch household + raw Q1-Q15 + household_context from Postgres
3. validate/normalize the payload against the shared request schema
4. generate request_id (§10)
5. call POST /v1/recommendations with a service-to-service signed header (§9 below)
6. on success: format response for the frontend, write feedback_event/recommendation_event row
7. on failure/timeout: apply fallback (§11), still log the event with a failure flag
```

## 10. Logging, tracing, request IDs

- `request_id` (UUIDv4) generated once at the Edge Function, sent as `X-Request-Id` header, echoed back in every RE response and in every log line on both sides.
- Structured JSON logs on both sides (not print/console text) — required specifically because debugging spans two languages.
- `traceparent` header propagated end-to-end if/when OpenTelemetry is added; not a Phase-1 requirement, but the request_id convention above is forward-compatible with it.

## 11. Timeout, retry, fallback

- Timeout: 2.5s on the Edge Function → RE call.
- Retry: at most one, network-level failures only (connection refused/reset) — never on timeout.
- Fallback: a small, pre-computed, cached-per-zone default plate set, served by the Edge Function directly when the RE is unreachable or times out, so the user sees familiar regional food instead of an error.
- Partial-success case (some but not 7 plates found): returned as a normal 200 with `warnings` populated (§6), not treated as a failure.

## 12. Health endpoints

- `/healthz`: process liveness only, always 200 once running.
- `/readyz`: 200 only once catalogue + config are fully loaded into memory; used by the deploy platform to gate traffic during rollout.

## 13. Deployment architecture

- RE containerized (Docker), deployed to a platform supporting a **minimum-instance floor** (e.g. Cloud Run `min-instances=1`, Fly.io) — not true scale-to-zero, since this sits on the critical path of every recommendation request and cold starts would be directly user-visible.
- Image tag = `engine_version`; deploys are rollback-able independently of the Edge Function deploy.
- RE reachable only from the Edge Function layer — private networking / IP allowlist, no public ingress.
- Secrets: only the shared service-to-service auth secret; no DB credentials of any kind (per §9/§10 of the frozen decision).

## 14. CI/CD strategy

- Two independent pipelines, one shared gate: **neither pipeline may deploy unless the contract tests (§15) pass against `contracts/ghar-re-v1.schema.json`.**
- RE pipeline: lint → type-check → pytest (existing 16 + contract tests) → golden-master diff (fails on unreviewed scoring changes) → catalogue/config export (§8) → build image → push → deploy.
- Edge Function pipeline: existing repo convention, with an added step that runs contract tests against a staging RE deployment before promoting.

## 15. Contract testing between Edge Functions and the Python RE

`contracts/ghar-re-v1.schema.json` is the single source of truth for both request and response shape. Both services validate against it independently in CI — the RE validates its own responses before returning them (fail closed rather than silently drifting), and the Edge Function validates its outgoing payloads. This is the mechanism that keeps "one executable implementation of the math" (Founder Decision, principle 1) from silently becoming "two slightly different understandings of the contract" over time.

---

## 16. Documents to update

- `docs/architecture/` — add this document as `RE-DOC-10`; supersede any prior draft architecture note that predates the frozen decision.
- `docs/governance/Founder Decision Register` — log the architecture-freeze decision with a pointer to this plan.
- `KNOWLEDGE.html` — update to reflect `ghar_re_service/` as the production path and `ghar_re/` as demoted to offline tooling, per §3.
- `ghar_re/README.md` — update in place to state its new scope explicitly (golden-master generation, v2/v3 experimentation only — not production).

---

*Next: Phase B (RE service skeleton) is the first buildable unit — it only depends on Phase A (the frozen schema), which this document defines.*
