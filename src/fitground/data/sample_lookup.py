"""Lookup FIT-Clean rows for on-demand image materialization."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

LOOKUP_COLUMNS = [
    "sample_id",
    "source_split",
    "source_shard_id",
    "source_row_id",
    "person_sha256",
    "garment_sha256",
    "target_sha256",
]


def locate_sample(manifest_path: Path, sample_id: str) -> dict[str, Any]:
    df = pd.read_parquet(manifest_path, columns=LOOKUP_COLUMNS)
    row = df[df["sample_id"] == sample_id]
    if row.empty:
        raise KeyError(f"sample_id not found: {sample_id}")
    return row.iloc[0].to_dict()


def locate_samples(manifest_path: Path, sample_ids: list[str]) -> pd.DataFrame:
    wanted = list(dict.fromkeys(sample_ids))
    df = pd.read_parquet(manifest_path, columns=LOOKUP_COLUMNS)
    out = df[df["sample_id"].isin(wanted)].copy()
    missing = [s for s in wanted if s not in set(out["sample_id"])]
    if missing:
        raise KeyError(f"sample_id not found: {missing[:5]}")
    return out.sort_values(["source_shard_id", "source_row_id"]).reset_index(drop=True)


def group_ids_by_shard(rows: pd.DataFrame) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for rec in rows.to_dict("records"):
        grouped.setdefault(str(rec["source_shard_id"]), []).append(rec)
    return grouped
