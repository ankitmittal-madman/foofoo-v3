"""Independent FastAPI deployment surface."""

from __future__ import annotations

import time
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from . import __version__, auth
from .config import Settings
from .feedback import FeedbackStoreError, LocalFeedbackStore
from .observability import metrics, record_feedback
from .schemas import FeedbackEvent, FeedbackReceipt, RecommendationRequest, RecommendationResponse
from .service import run


async def require_service_signature(request: Request) -> None:
    """Verify the exact cached request body before endpoint recommendation work begins."""
    try:
        settings = Settings.from_env()
    except ValueError as exc:
        raise HTTPException(status_code=503, detail="invalid_configuration") from exc
    if not settings.service_secret:
        raise HTTPException(status_code=503, detail="service_auth_not_configured")
    try:
        auth.verify(
            await request.body(),
            request.headers.get(auth.SIGNATURE_HEADER),
            settings.service_secret,
            time.time(),
        )
    except auth.AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


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
        "catalogue_publication": {
            "version": settings.catalogue_publication_version,
            "qdrant_collection": (
                settings.qdrant_collection if settings.catalogue_publication_version else None
            ),
        },
        "metrics": metrics(),
    }


@app.get("/metrics", response_class=PlainTextResponse)
def prometheus_metrics() -> str:
    lines = []
    for name, value in sorted(metrics().items()):
        safe_name = "foofoo_aux_re_" + "".join(
            character if character.isalnum() or character == "_" else "_" for character in name
        )
        lines.append(f"{safe_name} {value}")
    return "\n".join(lines) + "\n"


@app.post(
    "/v1/recommendations",
    response_model=RecommendationResponse,
    dependencies=[Depends(require_service_signature)],
)
def recommendations(payload: RecommendationRequest) -> RecommendationResponse:
    return run(payload)


@app.post(
    "/v1/feedback",
    response_model=FeedbackReceipt,
    dependencies=[Depends(require_service_signature)],
)
def feedback(payload: FeedbackEvent) -> FeedbackReceipt:
    settings = Settings.from_env()
    if not settings.feedback_enabled:
        raise HTTPException(status_code=503, detail="feedback_disabled")
    if not settings.feedback_path:
        raise HTTPException(status_code=503, detail="feedback_path_not_configured")
    try:
        stored = LocalFeedbackStore(Path(settings.feedback_path)).append(payload)
    except (OSError, FeedbackStoreError) as exc:
        raise HTTPException(status_code=503, detail="feedback_store_unavailable") from exc
    record_feedback(stored=stored, event_type=payload.event_type)
    return FeedbackReceipt(accepted=True, stored=stored, event_id=payload.event_id)
