from __future__ import annotations

import importlib
import json
import logging
import os
import socket
import time
from collections.abc import Callable

from .postgres_repository import PostgresRepository
from .worker import JobHandler, OntologyWorker


def load_handlers(factory_path: str) -> dict[str, JobHandler]:
    """Load `module:function`; deployments own provider credentials and adapter composition."""
    if ":" not in factory_path:
        raise RuntimeError("ONTOLOGY_WORKER_HANDLER_FACTORY must be module:function")
    module_name, function_name = factory_path.rsplit(":", 1)
    factory: Callable[[], dict[str, JobHandler]] = getattr(
        importlib.import_module(module_name), function_name
    )
    handlers = factory()
    if not handlers or not set(handlers).issubset(
        {"enrich", "classify", "similarity", "image", "publish"}
    ):
        raise RuntimeError("worker handler factory returned invalid handlers")
    return handlers


def main() -> None:
    logging.basicConfig(level=os.getenv("ONTOLOGY_LOG_LEVEL", "INFO"))
    database_url = os.getenv("ONTOLOGY_DATABASE_URL")
    if not database_url:
        raise RuntimeError("ONTOLOGY_DATABASE_URL is required for workers")
    factory = os.getenv("ONTOLOGY_WORKER_HANDLER_FACTORY", "")
    handlers = load_handlers(factory)
    worker_id = os.getenv("ONTOLOGY_WORKER_ID") or f"{socket.gethostname()}:{os.getpid()}"
    batch_size = max(1, min(int(os.getenv("ONTOLOGY_WORKER_BATCH_SIZE", "20")), 100))
    poll_seconds = max(1, min(int(os.getenv("ONTOLOGY_WORKER_POLL_SECONDS", "5")), 60))
    once = os.getenv("ONTOLOGY_WORKER_ONCE", "false").lower() == "true"
    worker = OntologyWorker(PostgresRepository(database_url), worker_id, handlers, batch_size)
    while True:
        report = worker.run_once()
        print(json.dumps(report.__dict__, sort_keys=True))
        if once:
            return
        time.sleep(poll_seconds)


if __name__ == "__main__":
    main()
