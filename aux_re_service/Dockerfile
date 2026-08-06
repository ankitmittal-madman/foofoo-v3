FROM python:3.11.15-slim-bookworm@sha256:d29f48a31a8b408ed19272ca1e7b10ebae13b240a27e862d3d4217c528e2e0c3 AS builder

ENV PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /build
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir \
    "annotated-doc==0.0.5" \
    "annotated-types==0.8.0" \
    "anyio==4.14.2" \
    "click==8.4.2" \
    "fastapi==0.141.1" \
    "h11==0.16.0" \
    "idna==3.18" \
    "pydantic==2.13.4" \
    "pydantic-core==2.46.4" \
    "starlette==1.4.1" \
    "typing-extensions==4.16.0" \
    "typing-inspection==0.4.2" \
    "uvicorn==0.52.1"

COPY aux_re_service/pyproject.toml ./pyproject.toml
COPY aux_re_service/aux_re_service ./aux_re_service
RUN pip install --no-cache-dir --no-deps .

FROM python:3.11.15-slim-bookworm@sha256:d29f48a31a8b408ed19272ca1e7b10ebae13b240a27e862d3d4217c528e2e0c3

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH="/opt/venv/bin:$PATH"
WORKDIR /srv/aux-re
COPY --from=builder /opt/venv /opt/venv
RUN useradd --no-create-home --uid 10002 auxrec
USER auxrec
EXPOSE 8081
CMD ["uvicorn", "aux_re_service.main:app", "--host", "0.0.0.0", "--port", "8081", "--workers", "1", "--no-access-log"]
