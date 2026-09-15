#!/usr/bin/env python3
"""Rehydrate person/cloth/target images for manifest sample_ids without full dataset."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fitground.config import HF_REPO_ID, INTERIM_DIR, MANIFEST_PATH
from fitground.data.hf_env import configure_hf_cache
from huggingface_hub import hf_hub_download

EPHEMERAL = INTERIM_DIR / "materialize_ephemeral"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _locate_row(manifest_path: Path, sample_id: str) -> dict:
    import pandas as pd

    df = pd.read_parquet(manifest_path, columns=[
        "sample_id", "source_split", "source_shard_id", "source_row_id",
        "person_sha256", "garment_sha256", "target_sha256",
    ])
    row = df[df["sample_id"] == sample_id]
    if row.empty:
        raise KeyError(f"sample_id not found: {sample_id}")
    return row.iloc[0].to_dict()


def _shard_hf_path(shard_id: str) -> str:
    return f"data/{shard_id}.parquet"


def _download_shard(shard_id: str, keep: bool) -> Path:
    configure_hf_cache()
    EPHEMERAL.mkdir(parents=True, exist_ok=True)
    hf_hub_download(
        HF_REPO_ID,
        _shard_hf_path(shard_id),
        repo_type="dataset",
        local_dir=str(EPHEMERAL),
    )
    path = EPHEMERAL / "data" / f"{shard_id}.parquet"
    if not path.exists():
        raise FileNotFoundError(path)
    return path


def materialize_one(
    manifest_path: Path,
    sample_id: str,
    output_dir: Path,
    *,
    verify_hash: bool = True,
    keep_shard: bool = False,
) -> dict:
    meta = _locate_row(manifest_path, sample_id)
    shard_id = meta["source_shard_id"]
    row_id = int(meta["source_row_id"])
    path = _download_shard(shard_id, keep_shard)
    table = pq.read_table(path, columns=["person", "cloth", "target"])
    if row_id >= table.num_rows:
        raise IndexError(f"row_id {row_id} out of range for {shard_id}")
    out_dir = output_dir / sample_id.replace("/", "_")
    out_dir.mkdir(parents=True, exist_ok=True)
    result: dict = {"sample_id": sample_id, "files": {}}
    expected = {
        "person": meta.get("person_sha256"),
        "cloth": meta.get("garment_sha256"),
        "target": meta.get("target_sha256"),
    }
    for col in ("person", "cloth", "target"):
        struct = table[col][row_id].as_py()
        raw = struct.get("bytes") if struct else None
        if raw is None:
            raise ValueError(f"missing bytes for {col} in {sample_id}")
        digest = _sha256(raw)
        if verify_hash and expected[col] and digest != expected[col]:
            raise ValueError(
                f"hash mismatch {col}: expected {expected[col]}, got {digest}"
            )
        out_path = out_dir / f"{col}.png"
        out_path.write_bytes(raw)
        result["files"][col] = str(out_path)
        result[f"{col}_sha256"] = digest
    (out_dir / "metadata.json").write_text(json.dumps(meta, indent=2, default=str))
    if not keep_shard:
        path.unlink(missing_ok=True)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Materialize FIT samples from manifest")
    parser.add_argument("--sample-id", action="append", default=[])
    parser.add_argument("--input-manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--keep-shard", action="store_true")
    parser.add_argument("--verify-hash", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()

    ids = list(args.sample_id)
    if not ids:
        parser.error("provide at least one --sample-id")
    results = []
    for sid in ids:
        results.append(
            materialize_one(
                args.input_manifest, sid, args.output_dir,
                verify_hash=args.verify_hash, keep_shard=args.keep_shard,
            )
        )
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
