#!/usr/bin/env python3
"""Generate data_engineering_v0.1_fingerprint.json when all gates pass."""

import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fitground.config import (
    ARTIFACTS_DIR,
    EVAL_SHARD_COUNT,
    HF_REPO_ID,
    HF_SOURCE_REVISION,
    MANIFEST_PATH,
    TRAIN_SHARD_COUNT,
)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _pytest_summary() -> dict[str, int]:
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--tb=no"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parents[1],
    )
    line = [ln for ln in r.stdout.splitlines() if "passed" in ln]
    collected = passed = failed = 0
    if line:
        import re

        m = re.search(r"(\d+) passed", line[-1])
        if m:
            passed = int(m.group(1))
        m2 = re.search(r"(\d+) failed", line[-1])
        if m2:
            failed = int(m2.group(1))
        m3 = re.search(r"(\d+) skipped", line[-1])
        collected = passed + failed + (int(m3.group(1)) if m3 else 0)
    return {"pytest_collected": collected, "pytest_passed": passed, "pytest_failed": failed}


def _git_commit() -> str | None:
    try:
        r = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).resolve().parents[1],
        )
        if r.returncode == 0:
            return r.stdout.strip()
    except OSError:
        pass
    return None


def main() -> None:
    import pyarrow.parquet as pq

    schema_path = ARTIFACTS_DIR / "fit_clean_schema_v0.1.json"
    quality_path = ARTIFACTS_DIR / "quality_rules_v0.1.yaml"
    source_path = ARTIFACTS_DIR / "source_manifest.json"
    lock_candidates = [
        ARTIFACTS_DIR / "uv.lock",
        Path(__file__).resolve().parents[1] / "uv.lock",
        ARTIFACTS_DIR / "requirements.lock.txt",
        Path(__file__).resolve().parents[1] / "requirements.lock.txt",
    ]
    lock_path = next((p for p in lock_candidates if p.exists()), None)

    if not MANIFEST_PATH.exists():
        print(json.dumps({"error": "manifest missing", "path": str(MANIFEST_PATH)}, indent=2))
        sys.exit(1)

    meta = pq.read_metadata(MANIFEST_PATH)
    train_rows = eval_rows = 0
    # Read split counts from parquet via pandas for accuracy
    import pandas as pd

    df = pd.read_parquet(MANIFEST_PATH, columns=["source_split"])
    train_rows = int((df["source_split"] == "train").sum())
    eval_rows = int((df["source_split"] == "eval").sum())
    total_rows = len(df)

    gates_ok = (
        train_rows == 100_000
        and eval_rows == 5_000
        and total_rows == 105_000
        and TRAIN_SHARD_COUNT == 406
        and EVAL_SHARD_COUNT == 20
    )

    pytest = _pytest_summary()
    status = "FROZEN" if gates_ok and pytest["pytest_failed"] == 0 else "PARTIAL"

    fp = {
        "dataset_id": HF_REPO_ID,
        "dataset_revision": HF_SOURCE_REVISION,
        "train_shards": TRAIN_SHARD_COUNT,
        "eval_shards": EVAL_SHARD_COUNT,
        "train_rows": train_rows,
        "eval_rows": eval_rows,
        "total_rows": total_rows,
        "fit_clean_path": str(MANIFEST_PATH.relative_to(MANIFEST_PATH.parents[2])),
        "fit_clean_size": MANIFEST_PATH.stat().st_size,
        "fit_clean_sha256": _sha256_file(MANIFEST_PATH),
        "schema_version": "v0.1",
        "schema_sha256": _sha256_file(schema_path) if schema_path.exists() else None,
        "quality_rules_version": "v0.1",
        "quality_rules_sha256": _sha256_file(quality_path) if quality_path.exists() else None,
        "source_manifest_sha256": _sha256_file(source_path) if source_path.exists() else None,
        "pipeline_git_commit": _git_commit(),
        "python_version": sys.version.split()[0],
        "dependency_lock_sha256": _sha256_file(lock_path) if lock_path else None,
        "dependency_lock_path": str(lock_path) if lock_path else None,
        **pytest,
        "data_engineering_status": status,
        "generated_at": datetime.now(UTC).isoformat(),
    }

    out = ARTIFACTS_DIR / "data_engineering_v0.1_fingerprint.json"
    out.write_text(json.dumps(fp, indent=2))
    print(json.dumps(fp, indent=2))
    if status != "FROZEN":
        sys.exit(2)


if __name__ == "__main__":
    main()
