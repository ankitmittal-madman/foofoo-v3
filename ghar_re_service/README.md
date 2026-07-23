# ghar_re_service — Ghar RE v1 HTTP service (thin hosting shell)

The production RE service (RE-DOC-10 Phase B). It **hosts** the `ghar_re_core` domain package over
HTTP — it contains **no recommendation math of its own** (RE-DOC-11 §3). All scoring/derivation/
pairing lives in `ghar_re_core`, the single tested implementation.

## Layers
| Module | Responsibility |
|---|---|
| `providers.py` | `CatalogueProvider` / `ConfigProvider` Protocols + one adapter each (`LocalSnapshotCatalogueProvider`, `YamlFileConfigProvider`). The seams for future data sources (RE-DOC-11 §1/§2). |
| `modules.py` | `ScoringModule` protocol + ordered registry wrapping each `ghar_re_core.scoring` BASE component; composes BASE and emits the open `contributions[]` (RE-DOC-11 §6/§7). |
| `schemas.py` | Validates requests/responses against `contracts/ghar-re-v1.schema.json` directly (zero FastAPI imports, no hand-duplicated rules). |
| `engine.py` | Composition/translation: request → `ghar_re_core.pipeline.recommend` → contract response. |
| `lifecycle.py` | Startup: load config → catalogue → indices → registry → ready. Structured JSON logs. |
| `main.py` | FastAPI routes — translation-only. `POST /v1/recommendations`, `GET /healthz`, `/readyz`, `/v1/meta`. |

## Run
```bash
pip install -e .            # installs ghar-re-core (from repo root) first, then this
pip install -e ghar_re_service
uvicorn ghar_re_service.main:app --reload      # serves on :8000
python3 -m pytest ghar_re_service/tests -q     # contract + e2e tests
```

## Contract
`contracts/ghar-re-v1.schema.json` is the single source of truth. The service validates its own
responses before returning them (fail-closed). Compatibility is additive/open — unknown fields are
ignored, new fields are optional, breaking changes bump to `/v2/` (RE-DOC-11 §5).

## Scope
Phase A + B only. No Edge Function (Phase C), no container/deploy (Phase F), no CI/CD (Phase E).
Weather is mocked (injected via the request). Catalogue = golden sample; the real 810-dish
cutover is Phase G.
