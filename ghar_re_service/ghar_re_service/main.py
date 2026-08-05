"""
FastAPI app (RE-DOC-10 §4, RE-DOC-11 §4). Route handlers are TRANSLATION-ONLY:
parse → validate against the contract → call the engine → validate → serialize. No business logic
lives here; all recommendation math is in ghar_re_core, all composition in engine.py.
"""

from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager

from fastapi import Body, FastAPI, Request
from fastapi.responses import JSONResponse

from ghar_re_service import auth, engine, ratelimit, schemas
from ghar_re_service.lifecycle import AppState, log_event, startup
from ghar_re_service.version import API_VERSION, ENGINE_VERSION

state = AppState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan hook — runs the startup load sequence once before the app accepts traffic.

    Trigger: process boot (ASGI server startup), not a client-facing route.
    Reads/writes: populates the process-wide `state` (AppState) — auth, config, catalogue,
    indices, rate limiter, registry — via `startup()`. `/readyz` only returns 200 once this
    has completed.
    """
    startup(state)  # load auth → config → catalogue → indices → registry → ready
    yield


app = FastAPI(title="Ghar RE", version=ENGINE_VERSION, lifespan=lifespan)


# Paths requiring a valid service-to-service signature (RE-DOC-10 §4: "All compute calls").
# /healthz and /readyz stay open on purpose — the deploy platform's probes call them before any
# secret is necessarily wired, and gating liveness on auth is how a rollout deadlocks itself.
# /v1/meta also stays open per RE-DOC-10 §4 ("no auth data"); it exposes versions + counters only.
SIGNED_PATHS = frozenset(
    {
        "/v1/recommendations",
        # WP-18 planning surfaces — all compute calls, so all signed + rate-limited.
        "/v1/cold-start",
        "/v1/calibration",
        "/v1/meal-plan",
        "/v1/weekly-plan",
        "/v1/class-dishes",
        "/v1/recipe",
        "/v1/search",
        "/v1/meal-episodes",
    }
)


@app.middleware("http")
async def verify_signature(request: Request, call_next):
    """Reject unsigned/invalid/stale requests with 401 BEFORE any parsing or computation.

    Runs as middleware rather than a route dependency for one specific reason: the HMAC covers the
    RAW request bytes, and this is the only layer that still has them. By the time a route's
    `payload: dict = Body(...)` has run, FastAPI has already parsed and discarded the exact byte
    sequence the signature was computed over.
    """
    if request.url.path not in SIGNED_PATHS:
        return await call_next(request)

    raw_body = await request.body()

    # Starlette streams the body once; replay it so the downstream route can still read it.
    async def _receive():
        return {"type": "http.request", "body": raw_body, "more_body": False}

    request._receive = _receive  # noqa: SLF001 — documented Starlette body-replay pattern

    request_id = request.headers.get(auth.REQUEST_ID_HEADER)
    auth_cfg = state.auth
    if auth_cfg is None:
        # Startup hasn't loaded auth yet (or failed to). Fail CLOSED — never serve compute traffic
        # with verification silently disabled.
        state.counters.record("error")
        log_event(
            "request.unauthenticated",
            request_id=request_id,
            outcome="error",
            reason="auth_not_loaded",
        )
        return JSONResponse(
            status_code=503, content={"error": "service_not_ready", "request_id": request_id}
        )

    try:
        auth.verify_request(
            raw_body=raw_body,
            signature_header=request.headers.get(auth.SIGNATURE_HEADER),
            secret=auth_cfg.secret,
            now=time.time(),
            max_skew_seconds=auth_cfg.max_skew_seconds,
        )
    except auth.AuthError as e:
        state.counters.record("error")
        # `reason` is a fixed token (missing_signature / malformed_signature / stale_signature /
        # invalid_signature) — safe to log and return; it reveals nothing about the secret.
        log_event("request.unauthorized", request_id=request_id, outcome="error", reason=e.reason)
        return JSONResponse(
            status_code=401,
            content={"error": "unauthorized", "detail": e.reason, "request_id": request_id},
        )

    return await call_next(request)


# Paths the rate limiter guards. /v1/recommendations is the expensive one (HMAC + full pipeline);
# /v1/meta is included because public ingress made it internet-reachable too and it is unauthed by
# design (RE-DOC-10 §4).
#
# /healthz and /readyz are deliberately EXEMPT. Fly's proxy probes them on a fixed interval, and a
# limiter that shed a health check would make the platform believe the machine is unhealthy and
# restart it — a rate limit that causes the very outage it exists to prevent.
RATE_LIMITED_PATHS = frozenset(
    {
        "/v1/recommendations",
        "/v1/meta",
        "/v1/cold-start",
        "/v1/calibration",
        "/v1/meal-plan",
        "/v1/weekly-plan",
        "/v1/class-dishes",
        "/v1/recipe",
        "/v1/search",
        "/v1/meal-episodes",
    }
)


# REGISTERED SECOND, RUNS FIRST. Starlette builds its middleware stack so that the most recently
# added middleware is the OUTERMOST layer — so this one sees the request before verify_signature
# above does. That ordering is the whole point: a flood is shed before any HMAC is computed, which
# is what protects the signature check rather than merely sitting behind it. Moving this decorator
# above verify_signature would silently invert it and cost exactly the CPU this is meant to save.
# test_ratelimit.py pins the order: an unsigned over-limit request must return 429, not 401.
@app.middleware("http")
async def enforce_rate_limit(request: Request, call_next):
    """Shed requests from a client that exceeds the configured per-minute allowance, with 429."""
    if request.url.path not in RATE_LIMITED_PATHS:
        return await call_next(request)

    limiter = state.rate_limiter
    # FAILS OPEN, unlike the signature check next door — and the asymmetry is deliberate. A limiter
    # that is not loaded yet is a missing safety damper; refusing traffic over it would turn a
    # degraded defence into a self-inflicted outage. The boundary that must fail CLOSED is auth, and
    # it does (503 above when state.auth is None), independently of anything here.
    if limiter is None or not limiter.enabled:
        return await call_next(request)

    key = ratelimit.client_key(
        request.headers.get(ratelimit.CLIENT_IP_HEADER),
        request.client.host if request.client else None,
    )
    decision = limiter.check(key, time.time())
    if not decision.allowed:
        state.counters.record_rate_limited()
        # The client key (an IP) is NOT logged: it is personal data under DPDP, and the operational
        # question "are we shedding traffic?" is answered by the count alone.
        log_event(
            "request.rate_limited",
            request_id=request.headers.get(auth.REQUEST_ID_HEADER),
            outcome="rate_limited",
            path=request.url.path,
            retry_after=decision.retry_after,
        )
        return JSONResponse(
            status_code=429,
            content={
                "error": "rate_limited",
                "detail": "too many requests",
                "request_id": request.headers.get(auth.REQUEST_ID_HEADER),
            },
            headers={"Retry-After": str(decision.retry_after)},
        )

    return await call_next(request)


@app.get("/healthz")
def healthz():
    """Liveness probe.

    Trigger: GET /healthz — called by the deploy platform's health-check probe, unauthenticated
    and not rate-limited (see SIGNED_PATHS/RATE_LIMITED_PATHS above).
    Reads/writes: nothing — always 200 as soon as the process is up, regardless of load state
    (RE-DOC-10 §12), so it never reflects catalogue/config readiness.
    Error codes: none — this endpoint cannot fail while the process is running.
    """
    return {"status": "alive"}


@app.get("/readyz")
def readyz():
    """Readiness probe.

    Trigger: GET /readyz — called by the deploy platform to decide whether to route traffic to
    this instance, unauthenticated and not rate-limited.
    Reads/writes: reads `state.ready` only (set True once `startup()` finishes loading
    auth/config/catalogue/registry).
    Error codes: 503 (`{"status": "loading"}`) while startup hasn't finished; 200 once ready.
    """
    if state.ready:
        return {"status": "ready"}
    return JSONResponse(status_code=503, content={"status": "loading"})


@app.get("/v1/meta")
def meta():
    """Reports service/engine/config/bundle versions and lightweight in-process request counters.

    Trigger: GET /v1/meta — unauthenticated by design (RE-DOC-10 §4: "no auth data"), but IS
    rate-limited since public ingress made it internet-reachable.
    Reads/writes: reads `state.config`, `state.bundle`, `state.counters` only — no external I/O.
    Error codes: none directly; the response is validated against the MetaResponse contract
    before returning (raises internally if the service's own shape ever drifted from the schema).
    """
    # Versions plus lightweight process-local counters (Phase D Task 3) — no metrics backend,
    # cheap and replaceable wholesale once Phase F picks real monitoring.
    body = {
        "api_version": API_VERSION,
        "engine_version": ENGINE_VERSION,
        "config_version": state.config.versions["config"] if state.config else "unloaded",
        # Which immutable snapshot is actually serving (RE-DOC-10 §8). None when running from repo
        # files rather than a baked image — that distinction is exactly what this field is for.
        "bundle_version": (state.bundle or {}).get("bundle_version"),
        "metrics": state.counters.as_dict(),
    }
    schemas.validate_meta(body)
    return body


@app.post("/v1/recommendations")
def recommendations(
    request: Request,
    # noqa: B008 is the correct call here, not a workaround — FastAPI's dependency system is
    # *defined* in terms of call-in-default (`= Body(...)`), and moving the call into the body
    # would break request parsing entirely.
    payload: dict = Body(...),  # noqa: B008
):
    """Produce a household's recommended plates (the RE's one compute endpoint).

    Trigger: POST /v1/recommendations — the sole SIGNED_PATH and RATE_LIMITED_PATH; requires a
    valid HMAC signature (verify_signature middleware, checked before this handler runs) and is
    subject to the sliding-window rate limiter (enforce_rate_limit middleware).
    Reads/writes: reads `state.catalogue`/`state.config`/`state.registry` (loaded at startup,
    never mutated per-request) and calls `engine.run()` for the actual composition; writes only
    to `state.counters` (in-process, not persisted) and structured logs via `log_event`.
    Error codes: 503 `service_not_ready` if called before startup finishes; 422
    `invalid_request` if the payload fails the Phase A contract; 500 `internal_error` on any
    unhandled exception from the engine; 200 with the validated response otherwise (warnings[]
    non-empty is still a 200 "partial" outcome, never an error — see Task 4 note below).
    """
    # `request` is annotated as a bare Request (not Request | None) deliberately: FastAPI
    # special-cases that exact type to inject the live request object, and always supplies it for
    # a route — so it is never None. Annotating it Optional makes FastAPI try to treat it as a
    # Pydantic body field instead, which fails at import time.
    t0 = time.time()
    header_id = request.headers.get(auth.REQUEST_ID_HEADER)
    request_id = payload.get("request_id") or header_id or str(uuid.uuid4())
    payload.setdefault("request_id", request_id)
    log_event("request.received", request_id=request_id)

    def elapsed_ms() -> float:
        return round((time.time() - t0) * 1000, 1)

    # 503 if called before startup finished loading providers.
    if not state.ready:
        state.counters.record("error")
        log_event(
            "request.rejected",
            request_id=request_id,
            outcome="error",
            detail="service_not_ready",
            latency_ms=elapsed_ms(),
        )
        return JSONResponse(
            status_code=503,
            content={"error": "service_not_ready", "request_id": request_id},
        )

    # parse/validate against the Phase A contract (additive/open — unknown fields ignored)
    try:
        schemas.validate_request(payload)
    except schemas.ContractError as e:
        state.counters.record("error")
        log_event(
            "request.invalid",
            request_id=request_id,
            outcome="error",
            error=str(e),
            latency_ms=elapsed_ms(),
        )
        return JSONResponse(
            status_code=422,
            content={"error": "invalid_request", "detail": str(e), "request_id": request_id},
        )

    # call the engine (composition → ghar_re_core pipeline → response)
    try:
        response = engine.run(payload, state.catalogue, state.config, state.registry)
        # fail-closed: validate our OWN response before returning (RE-DOC-10 §15)
        schemas.validate_response(response)
    except Exception as e:
        state.counters.record("error")
        log_event(
            "request.error",
            request_id=request_id,
            outcome="error",
            error=str(e),
            latency_ms=elapsed_ms(),
        )
        return JSONResponse(
            status_code=500,
            content={"error": "internal_error", "request_id": request_id},
        )

    # Task 4: a household that legitimately can't reach 7 plates is a distinct "partial" outcome,
    # never lumped into "error" — warnings[] is populated by engine.run, not raised as an exception.
    outcome = "partial" if response["warnings"] else "success"
    state.counters.record(outcome)
    log_event(
        "request.ok",
        request_id=request_id,
        outcome=outcome,
        plates=len(response["plates"]),
        warnings=len(response["warnings"]),
        latency_ms=elapsed_ms(),
    )
    return response


# =====================================================================================
# WP-18 planning surfaces. Translation-only routes (parse → engine planner fn → serialize), each
# signed + rate-limited like /v1/recommendations. The math/reconciliation lives in
# ghar_re_core.meal_planner; media (Cloudinary/recipe) is attached in engine.py.
# =====================================================================================
def _planning_call(name, fn, payload, request, needs_household=True):
    """Shared translation wrapper: 503 if not ready, 422 if the required inputs are missing, 500 on
    an engine error, 200 with the planner result otherwise. `fn(payload, catalogue, config)` for the
    household surfaces; a plain `fn(payload)` for the recipe lookup (needs_household=False)."""
    request_id = (
        payload.get("request_id")
        or request.headers.get(auth.REQUEST_ID_HEADER)
        or str(uuid.uuid4())
    )
    if not state.ready:
        state.counters.record("error")
        return JSONResponse(
            status_code=503, content={"error": "service_not_ready", "request_id": request_id}
        )
    if needs_household and not isinstance(payload.get("household"), dict):
        state.counters.record("error")
        return JSONResponse(
            status_code=422,
            content={
                "error": "invalid_request",
                "detail": "household required",
                "request_id": request_id,
            },
        )
    try:
        result = fn(payload, state.catalogue, state.config) if needs_household else fn(payload)
    except KeyError as e:
        state.counters.record("error")
        return JSONResponse(
            status_code=422,
            content={
                "error": "invalid_request",
                "detail": f"missing {e}",
                "request_id": request_id,
            },
        )
    except Exception as e:
        state.counters.record("error")
        log_event(f"{name}.error", request_id=request_id, outcome="error", error=str(e))
        return JSONResponse(
            status_code=500, content={"error": "internal_error", "request_id": request_id}
        )
    state.counters.record("success")
    log_event(f"{name}.ok", request_id=request_id, outcome="success")
    result["request_id"] = request_id
    return result


@app.post("/v1/cold-start")
def cold_start(request: Request, payload: dict = Body(...)):  # noqa: B008
    """WP-18 surface 1: top-15 diverse dishes for the post-onboarding preference primer."""
    return _planning_call("cold_start", engine.plan_cold_start, payload, request)


@app.post("/v1/calibration")
def calibration(request: Request, payload: dict = Body(...)):  # noqa: B008
    """WP-18 dish-pick surface: 3 slots x 5 dishes (3 expected-positive + 2 planted-mismatch,
    cell_role never surfaced to the client) for the post-onboarding calibration grid."""
    return _planning_call("calibration", engine.plan_calibration, payload, request)


@app.post("/v1/meal-plan")
def meal_plan(request: Request, payload: dict = Body(...)):  # noqa: B008
    """WP-18 surface 2: a slot's 4–5 dish options (pass class_code to reconcile to one class)."""
    return _planning_call("meal_plan", engine.plan_slot, payload, request)


@app.post("/v1/meal-episodes")
def meal_episodes(request: Request, payload: dict = Body(...)):  # noqa: B008
    """Complete safe meal episodes ranked by predicted choose, execution and non-regret."""
    return _planning_call("meal_episodes", engine.plan_meal_episodes, payload, request)


@app.post("/v1/weekly-plan")
def weekly_plan(request: Request, payload: dict = Body(...)):  # noqa: B008
    """WP-18 surface 3: the weekly class plan (7 days × slots, top-3 dish-backed classes each)."""
    return _planning_call("weekly_plan", engine.plan_weekly, payload, request)


@app.post("/v1/class-dishes")
def class_dishes(request: Request, payload: dict = Body(...)):  # noqa: B008
    """WP-18 surface 4: RECONCILIATION — only dishes of a finalized class for that day/slot."""
    return _planning_call("class_dishes", engine.plan_class_dishes, payload, request)


@app.post("/v1/recipe")
def recipe(request: Request, payload: dict = Body(...)):  # noqa: B008
    """WP-18 surface 5: full recipe + image for one dish (the meal-detail screen)."""
    return _planning_call("recipe", engine.recipe_detail, payload, request, needs_household=False)


@app.post("/v1/search")
def search(request: Request, payload: dict = Body(...)):  # noqa: B008
    """Safety-aware dish search with cuisine, diet, slot and cook-time filters."""
    return _planning_call("search", engine.plan_search, payload, request)
