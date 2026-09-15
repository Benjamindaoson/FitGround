"""Deterministic sample and image identity."""

from __future__ import annotations

SPLIT_EVAL = "eval"
IMAGE_MODALITIES = ("person", "cloth", "target")


def make_sample_id(split: str, shard_id: str, row_id: int) -> str:
    """Deterministic ID: split/shard_id/row_id."""
    return f"{split}/{shard_id}/{row_id:04d}"


def make_image_identity(modality: str, sha256: str) -> str:
    """Image identity includes modality — path alone is not unique."""
    return f"{modality}:{sha256}"


def shard_id_from_filename(filename: str) -> str:
    """e.g. eval-00000-of-00020.parquet -> eval-00000-of-00020"""
    return filename.replace(".parquet", "")
