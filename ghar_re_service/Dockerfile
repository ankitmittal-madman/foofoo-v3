# Ghar RE v1.0 — production image (Phase F Task 2, RE-DOC-10 §13).
#
# Build context is the REPO ROOT, not this directory, because the image needs three things that
# live above it: ghar_re_core/ (the math package), pyproject.toml (its build metadata), and
# contracts/ (the shared request/response schema). Build with:
#     docker build -f ghar_re_service/Dockerfile -t ghar-re:<engine_version> .
#
# Multi-stage on purpose: the builder installs into a virtualenv and keeps pip, setuptools, wheel
# and any transient build tooling out of the runtime layer. Only the finished venv is copied
# forward, so the shipped image contains the dependency tree and nothing that produced it.
#
# PINNING (per the architecture review's "pin everything, no silent minor-version drift"): the base
# image is pinned to an exact patch tag and every runtime dependency to an exact ==version below,
# rather than the >= ranges in pyproject.toml. Ranges are right for a library consumed by others;
# an image is a build artefact and must be reproducible. To upgrade, change a version here
# deliberately and rebuild — never let a rebuild silently pick up something new.
# The multi-platform registry digest was resolved from Docker Hub on 2026-08-04. Keeping the tag
# alongside it preserves readability while the digest makes rebuilds immutable.

# ---------------------------------------------------------------------------
# Stage 1 — builder
# ---------------------------------------------------------------------------
FROM python:3.11.15-slim-bookworm@sha256:b18992999dbe963a45a8a4da40ac2b1975be1a776d939d098c647482bcad5cba AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /build

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Runtime dependencies, pinned exactly. Installed BEFORE the source is copied so this layer is
# cached and only re-runs when a version here actually changes.
RUN pip install --no-cache-dir \
      "fastapi==0.139.2" \
      "uvicorn==0.51.0" \
      "jsonschema==4.26.0" \
      "PyYAML==6.0.1" \
      "joblib==1.5.3" \
      "numpy==2.4.6" \
      "scipy==1.17.1" \
      "scikit-learn==1.9.0" \
      "threadpoolctl==3.6.0"

# Now the two first-party packages. --no-deps because every dependency is already pinned and
# installed above; without it, pip would be free to resolve the >= ranges in pyproject.toml and
# quietly upgrade something the line above deliberately pinned.
COPY pyproject.toml /build/pyproject.toml
COPY ghar_re_core /build/ghar_re_core
RUN pip install --no-cache-dir --no-deps /build

COPY ghar_re_service /build/ghar_re_service
RUN pip install --no-cache-dir --no-deps /build/ghar_re_service

# ---------------------------------------------------------------------------
# Stage 2 — runtime
# ---------------------------------------------------------------------------
FROM python:3.11.15-slim-bookworm@sha256:b18992999dbe963a45a8a4da40ac2b1975be1a776d939d098c647482bcad5cba AS runtime

# Unbuffered stdout so the structured JSON log lines (RE-DOC-10 §10) reach the platform's log
# collector as they happen, instead of sitting in a buffer until the process exits.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

COPY --from=builder /opt/venv /opt/venv

# The immutable snapshot (RE-DOC-10 §8) and the shared contract. Both are given EXPLICIT paths and
# env vars rather than relying on relative walks from the installed package — those walks resolve
# against site-packages in a container and are exactly what would break at startup otherwise.
COPY ghar_re_service/data/bundle /srv/ghar-re/bundle
COPY ghar_re_service/runtime-publication /srv/ghar-re/publication
COPY contracts/ghar-re-v1.schema.json /srv/ghar-re/contracts/ghar-re-v1.schema.json

# GHAR_RE_CONFIG_DIR is set here, not left to the provider at startup, because
# ghar_re_core.catalogue reads ingredients_v5.csv at IMPORT time — earlier than any provider runs.
# Both it and config.py resolve against this variable, so the process is pointed at the bundle from
# the very first import.
ENV GHAR_RE_BUNDLE_DIR=/srv/ghar-re/bundle \
    GHAR_RE_CONFIG_DIR=/srv/ghar-re/bundle/config \
    GHAR_RE_CONTRACT_PATH=/srv/ghar-re/contracts/ghar-re-v1.schema.json \
    FOOFOO_ENV=production

# Fail the BUILD if the bundle didn't make it in, rather than shipping an image that only fails
# once it is deployed and taking traffic.
RUN test -f /srv/ghar-re/bundle/manifest.json \
      && test -f /srv/ghar-re/bundle/catalogue.json \
      && test -f /srv/ghar-re/contracts/ghar-re-v1.schema.json \
      || (echo "FATAL: bundle or contract missing from image" && exit 1)

# Modernized deployments inject one immutable DB publication into the build context and set this
# argument. Ordinary/local builds retain the 810-row fallback and do not pretend a publication is
# present. Runtime still verifies the SQLite checksum before becoming ready.
ARG GHAR_RE_PUBLICATION_REQUIRED=false
RUN if [ "$GHAR_RE_PUBLICATION_REQUIRED" = "true" ]; then \
      test -f /srv/ghar-re/publication/manifest.json \
      && test -f /srv/ghar-re/publication/catalogue.jsonl \
      && test -f /srv/ghar-re/publication/catalogue.sqlite3; \
    fi

# Non-root. The service writes nothing to disk — it loads its snapshot into memory at startup and
# serves from there — so it has no reason to run with write access to anything.
RUN useradd --system --create-home --uid 10001 ghar && \
    chown -R ghar:ghar /srv/ghar-re
USER ghar

EXPOSE 8080

# One worker on purpose. The counters in lifecycle.py are per-process (Phase D), so multiple
# workers would each keep a partial count and /v1/meta would report whichever process answered.
# Scale with more machines (fly.toml), not more workers, until there is a real metrics backend.
CMD ["uvicorn", "ghar_re_service.main:app", \
     "--host", "0.0.0.0", "--port", "8080", \
     "--workers", "1", "--no-access-log"]
