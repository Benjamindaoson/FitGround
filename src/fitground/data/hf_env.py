"""Hugging Face cache pinned under project data/cache."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from fitground.config import HF_CACHE_DIR

_CONFIGURED = False


def configure_hf_cache() -> Path:
    """Pin HF_HOME / hub cache to project directory."""
    global _CONFIGURED
    HF_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    os.environ["HF_HOME"] = str(HF_CACHE_DIR)
    os.environ["HF_HUB_CACHE"] = str(HF_CACHE_DIR / "hub")
    os.environ["HUGGINGFACE_HUB_CACHE"] = str(HF_CACHE_DIR / "hub")
    _CONFIGURED = True
    return HF_CACHE_DIR


def cache_size_bytes() -> int:
    cache = HF_CACHE_DIR
    if not cache.exists():
        return 0
    return sum(f.stat().st_size for f in cache.rglob("*") if f.is_file())


def prune_cache_except(keep_paths: set[Path], max_bytes: int | None = None) -> int:
    """Remove cache files not in keep_paths. Returns bytes freed."""
    freed = 0
    hub = HF_CACHE_DIR / "hub"
    if not hub.exists():
        return 0
    for f in hub.rglob("*"):
        if not f.is_file():
            continue
        if any(f == k or k in f.parents for k in keep_paths):
            continue
        try:
            sz = f.stat().st_size
            f.unlink()
            freed += sz
        except OSError:
            pass
    if max_bytes is not None and cache_size_bytes() > max_bytes:
        # Best-effort: remove oldest blobs if still over limit.
        blobs = sorted(
            (p for p in hub.rglob("*") if p.is_file()),
            key=lambda p: p.stat().st_mtime,
        )
        for f in blobs:
            if cache_size_bytes() <= max_bytes:
                break
            try:
                freed += f.stat().st_size
                f.unlink()
            except OSError:
                pass
    return freed
