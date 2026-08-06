"""Stage 5: real image generation (Pollinations.ai) + Cloudinary upload.

Replaces the earlier not_applicable-only stub. IndianFoodDatasetCSV.csv still has no image
column, so every image here is `source_type='ai_generated'`, never fabricated as if it came from
the CSV.

Generation mechanism ported from the Founder-supplied reference script
(`gemini_image_gen__Pollinations.py`): Pollinations.ai `flux-pro` model, 1024x1024, `nologo=true`,
random seed, GET request returning PNG bytes directly. Ported: the HTTP call shape, model,
dimensions, and retry/backoff pattern (`15 * attempt` seconds between retries, matching the
reference exactly). NOT ported: the reference's local-disk write + CSV status bookkeeping — no
local file write happens anywhere in this path; response bytes go straight from the HTTP response
into an in-memory upload to Cloudinary.

Cloudinary naming/upload follows the house convention already used by
`ghar_re_service/ghar_re_service/scripts/build_image_map.py` and
`ghar_re_service/ghar_re_service/media.py`:
  - public_id shape: `<dish_slug>_hero_01_<random-suffix>` (dish_slug = lowercase, every run of
    non-alphanumerics collapsed to a single underscore — identical `_slug()` logic).
  - credentials read from env only, never hardcoded: CLOUDINARY_CLOUD_NAME (default 'dzlqsobol'),
    CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET.
  - storage_path stores the Cloudinary public_id (not the full delivery URL) — the delivery URL is
    always derivable from public_id via `ghar_re_service.media.image_url()`'s existing formula, so
    storing the public_id keeps this ETL decoupled from the transform/cloud-name env choice at
    upload time. This choice is documented here and in the runbook.

Idempotency: the pipeline (see pipeline.py `_maybe_generate_image`) only calls into this module
for a dish that does not already have a dish_images row — this module itself does not query the
DB, it is a pure generate+upload function so it stays testable without a DB connection.
"""

from __future__ import annotations

import hashlib
import logging
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

logger = logging.getLogger("dish_ingestion.images")

IMAGE_WIDTH = 1024
IMAGE_HEIGHT = 1024
IMAGE_MODEL = "flux-pro"
POLLINATIONS_BASE = "https://image.pollinations.ai/prompt/"
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 15   # ported from reference: `time.sleep(15 * attempt)`
MIN_VALID_BYTES = 5000       # reference script's own sanity floor for "not an error page"

CLOUDINARY_UPLOAD_URL = "https://api.cloudinary.com/v1_1/{cloud}/image/upload"


@dataclass
class ImageResult:
    source_url: str | None
    storage_path: str | None          # Cloudinary public_id (see module docstring for why)
    checksum_sha256: str | None
    fetch_status: str                  # 'pending' | 'fetched' | 'failed' | 'not_applicable'
    alt_text: str | None
    is_primary: bool
    source_type: str                   # 'csv_source' | 'external_api' | 'ai_generated' | 'human_upload'
    confidence: float | None
    prompt_text: str | None = None
    prompt_backend: str | None = None      # 'groq_api' | 'hf_api' | 'heuristic'
    prompt_model_name: str | None = None
    image_gen_backend: str | None = None   # 'pollinations_flux_pro'
    image_gen_seed: int | None = None


def slugify(name: str) -> str:
    """Identical logic to build_image_map.py's `_slug()` — must match exactly so
    ghar_re_service.media's future asset discovery keeps working for these dishes too."""
    import re
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", name.lower())).strip("_")


def not_applicable(dish_name: str) -> ImageResult:
    """Generation disabled (--skip-images) or nothing to do — same placeholder shape as before."""
    return ImageResult(
        source_url=None, storage_path=None, checksum_sha256=None, fetch_status="not_applicable",
        alt_text=f"{dish_name} (image generation skipped)", is_primary=False, source_type="csv_source",
        confidence=None,
    )


def planned_dry_run(dish_name: str, prompt_text: str, prompt_backend: str, prompt_model_name: str | None) -> ImageResult:
    """Dry-run reporting only: describes what WOULD be generated, never calls Pollinations or
    Cloudinary (task brief rule 3 — dry-run must not touch either network)."""
    return ImageResult(
        source_url=None, storage_path=None, checksum_sha256=None, fetch_status="pending",
        alt_text=f"{dish_name} (planned: ai_generated, not executed in dry-run)", is_primary=True,
        source_type="ai_generated", confidence=0.7,
        prompt_text=prompt_text, prompt_backend=prompt_backend, prompt_model_name=prompt_model_name,
        image_gen_backend=None, image_gen_seed=None,
    )


class PollinationsClient:
    """Real generation call — Pollinations.ai flux-pro. No API key required (it's a free public
    endpoint), which is why this module's own env-var contract only concerns Cloudinary/prompt
    backends, not Pollinations itself.
    """

    def __init__(self, width: int = IMAGE_WIDTH, height: int = IMAGE_HEIGHT, model: str = IMAGE_MODEL,
                 max_retries: int = MAX_RETRIES, timeout: int = 60):
        self.width = width
        self.height = height
        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout

    def generate_png(self, prompt: str) -> tuple[bytes, str, int]:
        """Returns (png_bytes, request_url, seed). Raises on exhausted retries — caller decides
        whether that becomes a 'failed' image_assets row or an error log entry."""
        seed = random.randint(10000, 99999)
        encoded_prompt = urllib.parse.quote(prompt)
        url = (
            f"{POLLINATIONS_BASE}{encoded_prompt}"
            f"?width={self.width}&height={self.height}&nologo=true&model={self.model}&seed={seed}"
        )
        last_exc: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                req = urllib.request.Request(url, method="GET")
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    body = resp.read()
                if len(body) < MIN_VALID_BYTES:
                    raise ValueError(f"response too small to be a real image: {len(body)} bytes")
                return body, url, seed
            except Exception as exc:  # pragma: no cover - network
                last_exc = exc
                logger.warning("pollinations attempt %s/%s failed: %s", attempt, self.max_retries, exc)
                if attempt < self.max_retries:
                    time.sleep(RETRY_BACKOFF_SECONDS * attempt)
        raise RuntimeError(f"pollinations generation failed after {self.max_retries} attempts: {last_exc}")


class CloudinaryUploader:
    """Signed upload of in-memory bytes — no local disk write anywhere in this path."""

    def __init__(self, cloud_name: str | None = None, api_key: str | None = None, api_secret: str | None = None):
        import os
        self.cloud_name = cloud_name or os.environ.get("CLOUDINARY_CLOUD_NAME", "dzlqsobol")
        self.api_key = api_key if api_key is not None else os.environ.get("CLOUDINARY_API_KEY")
        self.api_secret = api_secret if api_secret is not None else os.environ.get("CLOUDINARY_API_SECRET")

    def configured(self) -> bool:
        return bool(self.api_key and self.api_secret)

    def upload_png(self, image_bytes: bytes, public_id: str, tags: str = "dish_ingestion,ai_generated") -> dict:
        if not self.configured():
            raise RuntimeError(
                "CLOUDINARY_API_KEY / CLOUDINARY_API_SECRET not set. This ETL will not fabricate an "
                "upload — set both before running with image generation enabled in --apply."
            )
        timestamp = str(int(time.time()))
        params_to_sign = {"public_id": public_id, "tags": tags, "timestamp": timestamp}
        signature = self._sign(params_to_sign)

        boundary = "----FooFooDishIngestionBoundary"
        fields = {
            "api_key": self.api_key,
            "timestamp": timestamp,
            "public_id": public_id,
            "tags": tags,
            "signature": signature,
        }
        body = _build_multipart(fields, "file", f"{public_id}.png", image_bytes, "image/png", boundary)

        url = CLOUDINARY_UPLOAD_URL.format(cloud=self.cloud_name)
        req = urllib.request.Request(
            url, data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:  # pragma: no cover - network
                import json
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:  # pragma: no cover - network
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"cloudinary upload failed: HTTP {exc.code}: {detail}") from exc

    def _sign(self, params: dict) -> str:
        # Cloudinary signature: sha1(sorted "key=value" pairs joined by '&', with the api_secret
        # appended directly — no separator — per Cloudinary's documented signing algorithm.
        to_sign = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        return hashlib.sha1((to_sign + self.api_secret).encode("utf-8")).hexdigest()  # noqa: S324 (Cloudinary's own documented scheme, not a security boundary here)


def _build_multipart(fields: dict, file_field: str, filename: str, file_bytes: bytes,
                      content_type: str, boundary: str) -> bytes:
    parts: list[bytes] = []
    for key, value in fields.items():
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{key}\"\r\n\r\n{value}\r\n".encode("utf-8"))
    parts.append(
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"{file_field}\"; filename=\"{filename}\"\r\n"
        f"Content-Type: {content_type}\r\n\r\n".encode("utf-8")
    )
    parts.append(file_bytes)
    parts.append(f"\r\n--{boundary}--\r\n".encode("utf-8"))
    return b"".join(parts)


def generate_and_upload(dish_name: str, prompt_text: str, prompt_backend: str, prompt_model_name: str | None,
                         pollinations: PollinationsClient, uploader: CloudinaryUploader) -> ImageResult:
    """Real generation + upload path — only ever called from apply mode for a dish that does not
    already have an image (idempotency check happens in pipeline.py, before this is called).
    """
    slug = slugify(dish_name)
    random_suffix = "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=6))
    public_id = f"{slug}_hero_01_{random_suffix}"

    try:
        png_bytes, request_url, seed = pollinations.generate_png(prompt_text)
    except Exception as exc:
        logger.error("image generation failed for %s: %s", dish_name, exc)
        return ImageResult(
            source_url=None, storage_path=None, checksum_sha256=None, fetch_status="failed",
            alt_text=f"{dish_name} (generation failed: {exc})", is_primary=False, source_type="ai_generated",
            confidence=None, prompt_text=prompt_text, prompt_backend=prompt_backend,
            prompt_model_name=prompt_model_name, image_gen_backend="pollinations_flux_pro", image_gen_seed=None,
        )

    checksum = hashlib.sha256(png_bytes).hexdigest()

    try:
        upload_response = uploader.upload_png(png_bytes, public_id)
    except Exception as exc:
        logger.error("cloudinary upload failed for %s (public_id=%s): %s", dish_name, public_id, exc)
        return ImageResult(
            source_url=request_url, storage_path=None, checksum_sha256=checksum, fetch_status="failed",
            alt_text=f"{dish_name} (upload failed: {exc})", is_primary=False, source_type="ai_generated",
            confidence=None, prompt_text=prompt_text, prompt_backend=prompt_backend,
            prompt_model_name=prompt_model_name, image_gen_backend="pollinations_flux_pro", image_gen_seed=seed,
        )

    stored_public_id = upload_response.get("public_id", public_id)
    return ImageResult(
        source_url=request_url, storage_path=stored_public_id, checksum_sha256=checksum, fetch_status="fetched",
        alt_text=f"{dish_name}, AI-generated professional food photograph", is_primary=True,
        source_type="ai_generated", confidence=0.75,
        prompt_text=prompt_text, prompt_backend=prompt_backend, prompt_model_name=prompt_model_name,
        image_gen_backend="pollinations_flux_pro", image_gen_seed=seed,
    )
