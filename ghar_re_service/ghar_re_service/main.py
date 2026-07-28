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

from ghar_re_service import auth, engine, schemas
from ghar_re_service.lifecycle import AppState, log_event, startup
from ghar_re_service.version import API_VERSION, ENGINE_VERSION

state = AppState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    startup(state)  # load auth → config → catalogue → indices → registry → ready
    yield


app = FastAPI(title="Ghar RE", version=ENGINE_VERSION, lifespan=lifespan)


# Paths requiring a valid service-to-service signature (RE-DOC-10 §4: "All compute calls").
# /healthz and /readyz stay open on purpose — the deploy platform's probes call them before any
# secret is necessarily wired, and gating liveness on auth is how a rollout deadlocks itself.
# /v1/meta also stays open per RE-DOC-10 §4 ("no auth data"); it exposes versions + counters only.
SIGNED_PATHS = frozenset({"/v1/recommendations"})


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


@app.get("/healthz")
def healthz():
    # Liveness: 200 as soon as the process is up, regardless of load state (RE-DOC-10 §12).
    return {"status": "alive"}


@app.get("/readyz")
def readyz():
    # Readiness: 200 only once catalogue + config are loaded (traffic gate).
    if state.ready:
        return {"status": "ready"}
    return JSONResponse(status_code=503, content={"status": "loading"})


@app.get("/v1/meta")
def meta():
    # Versions plus lightweight process-local counters (Phase D Task 3) — no metrics backend,
    # cheap and replaceable wholesale once Phase F picks real monitoring.
    body = {
        "api_version": API_VERSION,
        "engine_version": ENGINE_VERSION,
        "config_version": state.config.versions["config"] if state.config else "unloaded",
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
