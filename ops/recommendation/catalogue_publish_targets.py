"""Clearly-separated publish adapters for Qdrant, Ghar, and Aux — all stamped with one version.

These adapters do not replace the existing, already-deployed GitHub Actions pipelines
(``.github/workflows/recommendation-catalogue-{publication,qdrant,ghar-deploy}.yml``) which
upload/deploy the file-based publication artifact for Qdrant and Ghar. They give the same
"one version id, three destinations" contract a direct, in-process, testable interface — so a
publish run can be verified as version-consistent across all destinations without depending on
CI infrastructure, and so Aux (which currently only has a *shadow* observation lineage, no
governed publish adapter of its own) gets one.

Every adapter takes the same ``publication_version`` string (``sha256:<hex>``, the exact value
produced by :func:`ops.recommendation.catalogue_db_publish.publish_to_db` /
:func:`ops.recommendation.catalogue_publication.publish`) and returns a small, uniform result
recording that stamp — callers can assert all three results carry an identical
``publication_version`` after a single publish.

None of these adapters flip live serving on their own. Whether a stamped version is actually
used to answer a real request is decided exclusively by ``public.catalogue_rollout_state``
(see catalogue_db_publish.read_rollout_state/set_rollout_state) — OFF (the default) means every
adapter below may run and record its result, but nothing serves it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class PublishTargetResult:
    """Uniform result shape returned by every adapter in this module."""

    target: str
    publication_version: str
    accepted: bool
    detail: str


class QdrantUploader(Protocol):
    """Minimal shape this module needs from a Qdrant client — swap in the real SDK client."""

    def upsert_collection(self, collection: str, points: list[dict[str, Any]]) -> int: ...


def publish_to_qdrant(
    uploader: QdrantUploader,
    *,
    publication_version: str,
    rows: list[dict[str, Any]],
) -> PublishTargetResult:
    """Upsert catalogue rows into a version-derived Qdrant collection.

    Collection name follows the same convention as the existing Qdrant workflow
    (``foofoo_recipes__<first 12 hex chars of the content hash>``) so a direct adapter call and
    the CI-driven upload always land in the identical collection for the same version.
    """
    digest_hex = publication_version.removeprefix("sha256:")
    collection = f"foofoo_recipes__{digest_hex[:12]}"
    points = [
        {"id": row["id"], "payload": row, "vector": row.get("genome_vector")} for row in rows
    ]
    accepted = uploader.upsert_collection(collection, points)
    return PublishTargetResult(
        target="qdrant",
        publication_version=publication_version,
        accepted=accepted == len(rows),
        detail=f"collection={collection} accepted={accepted} expected={len(rows)}",
    )


class GharDeployer(Protocol):
    """Minimal shape this module needs to hand a version to Ghar — swap in the real deploy call."""

    def deploy_published_catalogue(self, publication_version: str, rows: list[dict[str, Any]]) -> bool: ...


def publish_to_ghar(
    deployer: GharDeployer, *, publication_version: str, rows: list[dict[str, Any]]
) -> PublishTargetResult:
    """Hand a stamped catalogue snapshot to the Ghar deploy adapter. Never touches the 810-dish
    fallback bundle — Ghar's own runtime decides, via GHAR_RE_PUBLISHED_CATALOGUE_DIR and the
    rollout gate, whether to read this at all."""
    accepted = deployer.deploy_published_catalogue(publication_version, rows)
    return PublishTargetResult(
        target="ghar",
        publication_version=publication_version,
        accepted=bool(accepted),
        detail=f"dish_count={len(rows)}",
    )


class AuxRegistrar(Protocol):
    """Minimal shape this module needs to register a version with Aux's retrieval registry."""

    def register_catalogue_version(self, publication_version: str, dish_count: int) -> bool: ...


def publish_to_aux(
    registrar: AuxRegistrar, *, publication_version: str, rows: list[dict[str, Any]]
) -> PublishTargetResult:
    """Register a stamped catalogue version with Aux. Aux's own mode column
    (recommendation_events.aux_shadow_observation.mode: 'shadow'|'active', migration 099)
    already governs whether Aux serves from this version live; this adapter only makes the
    registration explicit and version-stamped."""
    accepted = registrar.register_catalogue_version(publication_version, len(rows))
    return PublishTargetResult(
        target="aux",
        publication_version=publication_version,
        accepted=bool(accepted),
        detail=f"dish_count={len(rows)}",
    )


def publish_to_all_targets(
    *,
    publication_version: str,
    rows: list[dict[str, Any]],
    qdrant: QdrantUploader,
    ghar: GharDeployer,
    aux: AuxRegistrar,
) -> list[PublishTargetResult]:
    """Publish the same stamped version to Qdrant, Ghar, and Aux. Returns one result per target,
    every one carrying the identical ``publication_version`` — callers should assert that."""
    return [
        publish_to_qdrant(qdrant, publication_version=publication_version, rows=rows),
        publish_to_ghar(ghar, publication_version=publication_version, rows=rows),
        publish_to_aux(aux, publication_version=publication_version, rows=rows),
    ]
