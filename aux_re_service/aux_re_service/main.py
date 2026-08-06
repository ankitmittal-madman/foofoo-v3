"""Independent FastAPI deployment surface."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from . import __version__
from .config import Settings
from .observability import metrics
from .schemas import RecommendationRequest, RecommendationResponse
from .service import run

app = FastAPI(title="FooFoo Auxiliary Recommender", version=__version__)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "alive"}


@app.get("/readyz")
def readyz():
    try:
        Settings.from_env()
    except ValueError:
        return JSONResponse(status_code=503, content={"status": "invalid_configuration"})
    return {"status": "ready"}


@app.get("/v1/meta")
def meta() -> dict[str, object]:
    settings = Settings.from_env()
    return {
        "version": __version__,
        "enabled": settings.enabled,
        "mode": settings.mode,
        "metrics": metrics(),
    }


@app.post("/v1/recommendations", response_model=RecommendationResponse)
def recommendations(payload: RecommendationRequest) -> RecommendationResponse:
    return run(payload)
