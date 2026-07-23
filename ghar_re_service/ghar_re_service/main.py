"""
FastAPI app (RE-DOC-10 §4, RE-DOC-11 §4). Route handlers are TRANSLATION-ONLY:
parse → validate against the contract → call the engine → validate → serialize. No business logic
lives here; all recommendation math is in ghar_re_core, all composition in engine.py.
"""
from __future__ import annotations

import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Body
from fastapi.responses import JSONResponse

from ghar_re_service import schemas, engine
from ghar_re_service.lifecycle import AppState, startup, log_event
from ghar_re_service.version import API_VERSION, ENGINE_VERSION

state = AppState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    startup(state)          # load config → catalogue → indices → registry → ready
    yield


app = FastAPI(title="Ghar RE", version=ENGINE_VERSION, lifespan=lifespan)


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
    # Versions only — no request-specific data.
    body = {
        "api_version": API_VERSION,
        "engine_version": ENGINE_VERSION,
        "config_version": state.config.versions["config"] if state.config else "unloaded",
    }
    schemas.validate_meta(body)
    return body


@app.post("/v1/recommendations")
def recommendations(payload: dict = Body(...), request: Request = None):
    request_id = payload.get("request_id") or (request.headers.get("X-Request-Id") if request else None) or str(uuid.uuid4())
    payload.setdefault("request_id", request_id)

    # 503 if called before startup finished loading providers.
    if not state.ready:
        return JSONResponse(status_code=503, content={"error": "service_not_ready", "request_id": request_id})

    # parse/validate against the Phase A contract (additive/open — unknown fields ignored)
    try:
        schemas.validate_request(payload)
    except schemas.ContractError as e:
        log_event("request.invalid", request_id=request_id, error=str(e))
        return JSONResponse(status_code=422, content={"error": "invalid_request", "detail": str(e), "request_id": request_id})

    # call the engine (composition → ghar_re_core pipeline → response)
    response = engine.run(payload, state.catalogue, state.config, state.registry)

    # fail-closed: validate our OWN response before returning (RE-DOC-10 §15)
    schemas.validate_response(response)
    log_event("request.ok", request_id=request_id, plates=len(response["plates"]), warnings=len(response["warnings"]))
    return response
