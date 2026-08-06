FROM python:3.11.15-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /build
COPY aux_re_service/pyproject.toml ./pyproject.toml
COPY aux_re_service/aux_re_service ./aux_re_service
RUN pip install --no-cache-dir .
RUN useradd --system --uid 10002 auxrec
USER auxrec
EXPOSE 8081
CMD ["uvicorn", "aux_re_service.main:app", "--host", "0.0.0.0", "--port", "8081", "--workers", "1", "--no-access-log"]
