"""Stage 5: image handling plumbing.

IndianFoodDatasetCSV.csv has no image column, so for this dataset every row produces at most a
`not_applicable` image_assets placeholder — no download is attempted, no URL is fabricated. The
module is still exercised for every row so the plumbing (checksum computation, dish_images
linkage, primary-flag logic) is real and ready for a future source that does carry image URLs.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass
class ImageResult:
    source_url: str | None
    storage_path: str | None
    checksum_sha256: str | None
    fetch_status: str   # 'pending' | 'fetched' | 'failed' | 'not_applicable'
    alt_text: str | None
    is_primary: bool
    source_type: str     # 'csv_source' | 'external_api' | 'ai_generated' | 'human_upload'
    confidence: float | None


def resolve_image_for_row(dish_name: str, source_url_column: str | None) -> ImageResult:
    """Given a row, decide the image outcome. For this CSV, source_url_column is always None
    (no image column exists) so every row gets a not_applicable placeholder — expected and fine
    per the task brief.
    """
    if not source_url_column:
        return ImageResult(
            source_url=None, storage_path=None, checksum_sha256=None,
            fetch_status="not_applicable", alt_text=f"{dish_name} (no source image available)",
            is_primary=False, source_type="csv_source", confidence=None,
        )

    # Plumbing path for a future dataset that does carry an image URL column: no network
    # download is performed by the ETL itself (kept out of scope / no fabricated fetch), but the
    # checksum field is ready to be populated by whatever download step is wired in later.
    checksum = hashlib.sha256(source_url_column.encode("utf-8")).hexdigest()
    return ImageResult(
        source_url=source_url_column, storage_path=None, checksum_sha256=checksum,
        fetch_status="pending", alt_text=dish_name, is_primary=True,
        source_type="csv_source", confidence=0.9,
    )
