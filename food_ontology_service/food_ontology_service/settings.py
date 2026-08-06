from __future__ import annotations

import json
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Principal:
    name: str
    token: str
    scopes: frozenset[str]


@dataclass(frozen=True)
class Settings:
    environment: str
    database_url: str | None
    principals: tuple[Principal, ...]
    default_cache_seconds: int = 300
    max_page_size: int = 100

    @classmethod
    def from_env(cls) -> Settings:
        environment = os.getenv("ONTOLOGY_ENV", "development").lower()
        raw = os.getenv("ONTOLOGY_SERVICE_TOKENS")
        principals: list[Principal] = []
        if raw:
            parsed = json.loads(raw)
            for name, value in parsed.items():
                principals.append(
                    Principal(name=name, token=value["token"], scopes=frozenset(value["scopes"]))
                )
        elif environment == "production":
            raise RuntimeError("ONTOLOGY_SERVICE_TOKENS is required in production")
        else:
            principals.append(
                Principal(
                    name="local-app",
                    token="local-ontology-token",
                    scopes=frozenset({"ontology:read", "ontology:write", "ontology:admin"}),
                )
            )
        database_url = os.getenv("ONTOLOGY_DATABASE_URL")
        if environment == "production" and not database_url:
            raise RuntimeError("ONTOLOGY_DATABASE_URL is required in production")
        return cls(
            environment=environment,
            database_url=database_url,
            principals=tuple(principals),
            default_cache_seconds=int(os.getenv("ONTOLOGY_CACHE_SECONDS", "300")),
        )
