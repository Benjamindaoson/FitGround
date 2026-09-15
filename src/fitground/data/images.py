"""Image audit utilities — decode/hash with immediate release."""

from __future__ import annotations

import hashlib
import io
from typing import Any

import imagehash
from PIL import Image

from fitground.data.schema import ImageAuditResult


def _extract_bytes(image_field: Any) -> bytes | None:
    if image_field is None:
        return None
    if isinstance(image_field, dict):
        return image_field.get("bytes")
    if isinstance(image_field, bytes):
        return image_field
    return None


def _extract_path(image_field: Any) -> str | None:
    if image_field is None:
        return None
    if isinstance(image_field, dict):
        return image_field.get("path")
    return None


def audit_image_bytes(
    raw_bytes: bytes | None,
    path: str | None = None,
    compute_phash: bool = True,
) -> ImageAuditResult:
    """
    Audit raw image bytes: decode → validate → hash → release PIL immediately.
    """
    if raw_bytes is None:
        return ImageAuditResult(
            present=False,
            decodable=False,
            width=None,
            height=None,
            mode=None,
            format=None,
            sha256=None,
            phash=None,
            path=path,
            error="missing_bytes",
        )

    sha256 = hashlib.sha256(raw_bytes).hexdigest()
    img: Image.Image | None = None
    buf: io.BytesIO | None = None
    try:
        buf = io.BytesIO(raw_bytes)
        img = Image.open(buf)
        img.load()
        phash_val = str(imagehash.phash(img)) if compute_phash else None
        result = ImageAuditResult(
            present=True,
            decodable=True,
            width=img.width,
            height=img.height,
            mode=img.mode,
            format=img.format,
            sha256=sha256,
            phash=phash_val,
            path=path,
            error=None,
        )
    except Exception as exc:
        result = ImageAuditResult(
            present=True,
            decodable=False,
            width=None,
            height=None,
            mode=None,
            format=None,
            sha256=sha256,
            phash=None,
            path=path,
            error=f"decode_failed:{exc}",
        )
    finally:
        if img is not None:
            img.close()
        del img, buf, raw_bytes

    return result


def audit_image(image_field: Any, compute_phash: bool = True) -> ImageAuditResult:
    """Audit embedded HF Image struct(bytes, path)."""
    raw_bytes = _extract_bytes(image_field)
    path = _extract_path(image_field)
    if raw_bytes is None:
        return audit_image_bytes(None, path, compute_phash)
    # Copy bytes reference then pass to audit_image_bytes which deletes local ref.
    data = bytes(raw_bytes)
    del raw_bytes, image_field
    return audit_image_bytes(data, path, compute_phash)


def image_ref(split: str, shard_id: str, row_id: int, modality: str, path: str | None) -> str:
    inner = path or "embedded"
    return f"fitvto-100k/{split}/{shard_id}/{row_id:04d}/{modality}:{inner}"
