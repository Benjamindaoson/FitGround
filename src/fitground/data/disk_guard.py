"""Disk space safety checks."""

from __future__ import annotations

import shutil
from pathlib import Path

DISK_RESERVE_BYTES = 20 * 1024**3  # 20 GiB safety margin


class DiskSpaceError(RuntimeError):
    pass


def free_bytes(path: Path = Path("/workspace")) -> int:
    return shutil.disk_usage(path).free


def require_disk_headroom(
    reserve_bytes: int = DISK_RESERVE_BYTES,
    path: Path = Path("/workspace"),
) -> int:
    free = free_bytes(path)
    if free < reserve_bytes:
        raise DiskSpaceError(
            f"Free disk {free / 1e9:.2f} GB < reserve {reserve_bytes / 1e9:.2f} GB"
        )
    return free


def disk_status(path: Path = Path("/workspace")) -> dict[str, int | float]:
    usage = shutil.disk_usage(path)
    return {
        "total_bytes": usage.total,
        "used_bytes": usage.used,
        "free_bytes": usage.free,
        "reserve_bytes": DISK_RESERVE_BYTES,
        "usable_bytes": max(0, usage.free - DISK_RESERVE_BYTES),
    }
