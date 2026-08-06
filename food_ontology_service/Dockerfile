FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 ONTOLOGY_ENV=production
WORKDIR /service
COPY food_ontology_service/pyproject.toml ./pyproject.toml
COPY food_ontology_service/food_ontology_service ./food_ontology_service
COPY food_ontology_service/migrations ./migrations
RUN pip install --no-cache-dir .
USER 65532:65532
EXPOSE 8080
CMD ["uvicorn", "food_ontology_service.main:app", "--host", "0.0.0.0", "--port", "8080"]
