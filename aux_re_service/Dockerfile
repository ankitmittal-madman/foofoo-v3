FROM python:3.11.15-slim-bookworm@sha256:d29f48a31a8b408ed19272ca1e7b10ebae13b240a27e862d3d4217c528e2e0c3 AS builder

ENV PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /build
RUN apt-get update \
    && apt-get install --yes --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir "setuptools==79.0.1" "wheel==0.45.1"
RUN pip install --no-cache-dir \
    "joblib==1.5.3" \
    "lightfm==1.17" \
    "numpy==2.4.6" \
    "scipy==1.17.1"

RUN pip install --no-cache-dir \
    "annotated-doc==0.0.5" \
    "annotated-types==0.8.0" \
    "anyio==4.14.2" \
    "certifi==2026.7.22" \
    "charset-normalizer==3.4.9" \
    "click==8.4.2" \
    "fastapi==0.141.1" \
    "h11==0.16.0" \
    "idna==3.18" \
    "narwhals==2.24.0" \
    "pydantic==2.13.4" \
    "pydantic-core==2.46.4" \
    "requests==2.34.2" \
    "scikit-learn==1.9.0" \
    "starlette==1.4.1" \
    "threadpoolctl==3.6.0" \
    "typing-extensions==4.16.0" \
    "typing-inspection==0.4.2" \
    "urllib3==2.7.0" \
    "uvicorn==0.52.1"

COPY aux_re_service/pyproject.toml ./pyproject.toml
COPY aux_re_service/aux_re_service ./aux_re_service
RUN pip install --no-cache-dir --no-deps .

FROM python:3.11.15-slim-bookworm@sha256:d29f48a31a8b408ed19272ca1e7b10ebae13b240a27e862d3d4217c528e2e0c3

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH="/opt/venv/bin:$PATH"
WORKDIR /srv/aux-re
COPY --from=builder /opt/venv /opt/venv
RUN apt-get update \
    && apt-get install --yes --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --no-create-home --uid 10002 auxrec \
    && mkdir -p /srv/aux-re/state \
    && chown auxrec:auxrec /srv/aux-re/state
COPY aux_re_service/data/models /srv/aux-re/models
COPY aux_re_service/data/retrieval/v1 /srv/aux-re/retrieval
ENV AUX_REC_MODEL_ARTIFACT_DIR=/srv/aux-re/models \
    AUX_REC_LIGHTFM_ARTIFACT_PATH=/srv/aux-re/models/lightfm_v2.joblib \
    AUX_REC_CANDIDATE_POOL_PATH=/srv/aux-re/retrieval/candidates.json \
    AUX_REC_KNOWLEDGE_GRAPH_PATH=/srv/aux-re/retrieval/knowledge_graph.json
USER auxrec
EXPOSE 8081
CMD ["uvicorn", "aux_re_service.main:app", "--host", "0.0.0.0", "--port", "8081", "--workers", "1", "--no-access-log"]
