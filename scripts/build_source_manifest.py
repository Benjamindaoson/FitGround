#!/usr/bin/env python3
"""Build artifacts/source_manifest.json from HF API + local observations."""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fitground.config import (
    ARTIFACTS_DIR,
    HF_REPO_ID,
    HF_SOURCE_REVISION,
    RAW_FIT_DIR,
)
from fitground.data.hf_env import configure_hf_cache
from huggingface_hub import dataset_info


def _shard_entry(path: Path | None, hf_name: str, hf_size: int | None) -> dict:
    entry: dict = {"filename": hf_name, "hf_size_bytes": hf_size}
    if path and path.exists():
        entry["observed_bytes"] = path.stat().st_size
        try:
            entry["row_count"] = pq.ParquetFile(path).metadata.num_rows
        except Exception as exc:
            entry["row_count_error"] = str(exc)
    return entry


def main() -> None:
    configure_hf_cache()
    info = dataset_info(HF_REPO_ID)
    shards = {s.rfilename: s.size for s in info.siblings if s.rfilename.endswith(".parquet")}

    train_entries = []
    for name in sorted(k for k in shards if "/train-" in k):
        local = RAW_FIT_DIR / name if (RAW_FIT_DIR / name).exists() else RAW_FIT_DIR / "data" / Path(name).name
        train_entries.append(_shard_entry(local if local.exists() else None, name, shards[name]))

    eval_entries = []
    for name in sorted(k for k in shards if "/eval-" in k):
        local = RAW_FIT_DIR / "data" / Path(name).name
        eval_entries.append(_shard_entry(local if local.exists() else None, name, shards[name]))

    manifest = {
        "generated_at": datetime.now(UTC).isoformat(),
        "dataset_identifier": HF_REPO_ID,
        "dataset_revision": info.sha or HF_SOURCE_REVISION,
        "dataset_revision_pinned": HF_SOURCE_REVISION,
        "license": "cc-by-nc-nd-4.0",
        "train_shard_count": len(train_entries),
        "eval_shard_count": len(eval_entries),
        "train_shards": train_entries,
        "eval_shards": eval_entries,
    }
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    out = ARTIFACTS_DIR / "source_manifest.json"
    out.write_text(json.dumps(manifest, indent=2))
    print(f"Wrote {out} ({len(train_entries)} train, {len(eval_entries)} eval shards)")


if __name__ == "__main__":
    main()
