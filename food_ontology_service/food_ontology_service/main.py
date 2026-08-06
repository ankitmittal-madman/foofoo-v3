from __future__ import annotations

import hashlib
import hmac
import json
from typing import Annotated, Any
from uuid import UUID

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from . import __version__
from .models import DishCreate, DishPatch, EnrichmentRequest, FeedbackInput, ImageRef, SimilarityInput
from .repository import ConflictError, MemoryRepository, NotFoundError, Repository
from .settings import Principal, Settings


def create_app(settings: Settings | None = None, repository: Repository | None = None) -> FastAPI:
    cfg = settings or Settings.from_env()
    if repository is not None:
        repo = repository
    elif cfg.database_url:
        from .postgres_repository import PostgresRepository

        repo = PostgresRepository(cfg.database_url)
    else:
        repo = MemoryRepository()
    app = FastAPI(title="Foofoo Food Ontology Service", version=__version__)
    app.state.settings = cfg
    app.state.repository = repo

    @app.exception_handler(NotFoundError)
    async def not_found(_request: Request, exc: NotFoundError):
        return JSONResponse(status_code=404, content={"error": str(exc)})

    @app.exception_handler(ConflictError)
    async def conflict(_request: Request, exc: ConflictError):
        return JSONResponse(status_code=409, content={"error": str(exc)})

    def principal_for(authorization: Annotated[str | None, Header()] = None) -> Principal:
        token = authorization.removeprefix("Bearer ") if authorization else ""
        for principal in cfg.principals:
            if hmac.compare_digest(token, principal.token):
                return principal
        raise HTTPException(status_code=401, detail="unauthorized")

    def require(scope: str):
        def dependency(principal: Principal = Depends(principal_for)) -> Principal:
            if scope not in principal.scopes:
                raise HTTPException(status_code=403, detail="forbidden")
            return principal
        return dependency

    def response(payload: Any, *, status_code: int = 200, replayed: bool = False, cache: bool = False):
        encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode()
        headers = {"ETag": f'"{hashlib.sha256(encoded).hexdigest()}"'}
        headers["Cache-Control"] = f"private, max-age={cfg.default_cache_seconds}" if cache else "no-store"
        if replayed:
            headers["Idempotency-Replayed"] = "true"
        return JSONResponse(status_code=status_code, content=json.loads(encoded), headers=headers)

    def require_key(key: str | None) -> str:
        if not key or len(key) > 200:
            raise ConflictError("valid_idempotency_key_required")
        return key

    @app.get("/healthz")
    def healthz():
        return {"status": "alive"}

    @app.get("/readyz")
    def readyz():
        ping = getattr(repo, "ping", None)
        if ping:
            try:
                ping()
            except Exception:
                return JSONResponse(status_code=503, content={"status": "unready", "database": "unavailable"})
        return {"status": "ready", "database": "postgres" if cfg.database_url else "memory"}

    @app.post("/v1/dishes")
    def create_dish(data: DishCreate, principal: Principal = Depends(require("ontology:write")),
                    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None):
        result = repo.idempotent(principal.name, "create_dish", require_key(idempotency_key),
                                 data.model_dump(mode="json"),
                                 lambda: (201, repo.create_dish(data).model_dump(mode="json")))
        return response(result.payload, status_code=result.status_code, replayed=result.replayed)

    @app.patch("/v1/dishes/{dish_id}")
    def update_dish(dish_id: UUID, data: DishPatch,
                    _principal: Principal = Depends(require("ontology:write"))):
        return response(repo.update_dish(dish_id, data).model_dump(mode="json"))

    @app.get("/v1/dishes/{dish_id}")
    def get_dish(dish_id: UUID, _principal: Principal = Depends(require("ontology:read"))):
        return response(repo.get_dish(dish_id).model_dump(mode="json"), cache=True)

    @app.get("/v1/dishes:resolve")
    def resolve_dish(name: str, _principal: Principal = Depends(require("ontology:read"))):
        return response(repo.get_by_name(name).model_dump(mode="json"), cache=True)

    @app.get("/v1/meal-classes")
    def meal_classes(_principal: Principal = Depends(require("ontology:read"))):
        return response({"items": repo.list_classes()}, cache=True)

    @app.get("/v1/meal-classes/{class_code}/dishes")
    def class_dishes(class_code: str,
                     _principal: Principal = Depends(require("ontology:read")),
                     role: str = Query(default="primary", pattern="^(primary|addon|combo_component)$"),
                     limit: int = Query(default=25, ge=1, le=100)):
        items = [item.model_dump(mode="json") for item in repo.dishes_by_class(class_code, role, limit)]
        return response({"class_code": class_code, "role": role, "items": items}, cache=True)

    @app.post("/v1/dishes/{dish_id}/enrichment-jobs")
    def enrich(dish_id: UUID, data: EnrichmentRequest,
               principal: Principal = Depends(require("ontology:write")),
               idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None):
        result = repo.idempotent(principal.name, f"enrich:{dish_id}", require_key(idempotency_key),
                                 data.model_dump(mode="json"),
                                 lambda: (202, repo.enqueue(dish_id, "enrich", data.fields,
                                                            data.priority, data.force)))
        return response(result.payload, status_code=result.status_code, replayed=result.replayed)

    @app.post("/v1/dishes/{dish_id}/classification-jobs")
    def classify(dish_id: UUID, data: EnrichmentRequest,
                 principal: Principal = Depends(require("ontology:write")),
                 idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None):
        result = repo.idempotent(principal.name, f"classify:{dish_id}", require_key(idempotency_key),
                                 data.model_dump(mode="json"),
                                 lambda: (202, repo.enqueue(dish_id, "classify", data.fields,
                                                            data.priority, data.force)))
        return response(result.payload, status_code=result.status_code, replayed=result.replayed)

    @app.get("/v1/dishes/{dish_id}/enrichment-status")
    def enrichment_status(dish_id: UUID,
                          _principal: Principal = Depends(require("ontology:read"))):
        return response(repo.enrichment_status(dish_id))

    @app.get("/v1/jobs/{job_id}")
    def job_status(job_id: UUID, _principal: Principal = Depends(require("ontology:read"))):
        return response(repo.job_status(job_id))

    @app.post("/v1/dishes/{dish_id}/relationships")
    def relationship(dish_id: UUID, data: SimilarityInput,
                     _principal: Principal = Depends(require("ontology:admin"))):
        return response(repo.save_relationship(dish_id, data).model_dump(mode="json"), status_code=201)

    @app.get("/v1/dishes/{dish_id}/similar")
    def similar(dish_id: UUID, _principal: Principal = Depends(require("ontology:read"))):
        dish = repo.get_dish(dish_id)
        return response({"dish_id": dish_id, "items": [x.model_dump(mode="json") for x in dish.relationships]}, cache=True)

    @app.post("/v1/dishes/{dish_id}/feedback")
    def feedback(dish_id: UUID, data: FeedbackInput,
                 principal: Principal = Depends(require("ontology:write"))):
        return response(repo.submit_feedback(dish_id, data, principal.name), status_code=202)

    @app.post("/v1/dishes/{dish_id}/images")
    def image(dish_id: UUID, data: ImageRef,
              _principal: Principal = Depends(require("ontology:admin"))):
        return response(repo.add_image(dish_id, data).model_dump(mode="json"), status_code=201)

    @app.get("/v1/dishes/{dish_id}/images")
    def images(dish_id: UUID, _principal: Principal = Depends(require("ontology:read"))):
        items = [item.model_dump(mode="json") for item in repo.get_dish(dish_id).images
                 if item.review_status == "accepted"]
        return response({"dish_id": dish_id, "items": items}, cache=True)

    @app.get("/v1/dishes/{dish_id}/provenance")
    def provenance(dish_id: UUID, _principal: Principal = Depends(require("ontology:read"))):
        dish = repo.get_dish(dish_id)
        return response({"dish_id": dish_id, "description": dish.description,
                         "fields": dish.fields, "class_memberships": dish.class_memberships})

    return app


app = create_app()
