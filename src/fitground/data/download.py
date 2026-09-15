"""Dataset download utilities with storage-aware strategy."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from huggingface_hub import hf_hub_download

from fitground.config import (
    DATASET_EVAL_BYTES,
    DATASET_TOTAL_BYTES,
    DATASET_TRAIN_BYTES,
    EVAL_SHARD_COUNT,
    HF_REPO_ID,
    INTERIM_DIR,
    RAW_FIT_DIR,
    TRAIN_SHARD_COUNT,
)


def storage_audit(available_bytes: int) -> dict:
    """Compute storage requirements vs availability."""
    return {
        "required_bytes_full": DATASET_TOTAL_BYTES,
        "required_bytes_train": DATASET_TRAIN_BYTES,
        "required_bytes_eval": DATASET_EVAL_BYTES,
        "available_bytes": available_bytes,
        "shortfall_bytes_full": max(0, DATASET_TOTAL_BYTES - available_bytes),
        "can_download_full": DATASET_TOTAL_BYTES <= available_bytes,
        "can_download_eval": DATASET_EVAL_BYTES <= available_bytes,
        "strategy": (
            "full_download"
            if DATASET_TOTAL_BYTES <= available_bytes
            else "eval_persistent_train_ephemeral"
        ),
    }


def shard_filename(split: str, index: int) -> str:
    if split == "train":
        return f"data/train-{index:05d}-of-{TRAIN_SHARD_COUNT:05d}.parquet"
    return f"data/eval-{index:05d}-of-{EVAL_SHARD_COUNT:05d}.parquet"


def download_shard(
    split: str,
    index: int,
    dest_dir: Path | None = None,
    ephemeral: bool = False,
) -> Path:
    """Download a single parquet shard."""
    filename = shard_filename(split, index)
    local_dir = INTERIM_DIR / "shards" if ephemeral else RAW_FIT_DIR
    if dest_dir is not None:
        local_dir = dest_dir
    local_dir.mkdir(parents=True, exist_ok=True)
    path = hf_hub_download(
        HF_REPO_ID,
        filename,
        repo_type="dataset",
        local_dir=str(local_dir),
    )
    return Path(path)


def download_eval_split() -> list[Path]:
    """Download all eval shards to raw directory."""
    paths = []
    for i in range(EVAL_SHARD_COUNT):
        paths.append(download_shard("eval", i, ephemeral=False))
    return paths


def cleanup_ephemeral_shard(path: Path) -> None:
    """Remove ephemeral shard after processing."""
    if path.exists():
        path.unlink()
    # Clean up empty cache artifacts in interim
    shard_dir = path.parent
    if shard_dir.name == "data" and shard_dir.parent == INTERIM_DIR / "shards":
        for f in shard_dir.glob("*.parquet"):
            if f != path and f.exists():
                pass  # keep others if any


def write_storage_report(report_path: Path, available_bytes: int) -> dict:
    audit = storage_audit(available_bytes)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(audit, indent=2))
    return audit
