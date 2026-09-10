#!/usr/bin/env python3
"""Validate FIT-Clean manifest row counts and consistency."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fitground.closure.audit import load_manifest, validate_manifest
from fitground.config import EVAL_SHARD_COUNT, MANIFEST_PATH, TRAIN_SHARD_COUNT


def main() -> None:
    if not MANIFEST_PATH.exists():
        print(json.dumps({"error": "manifest not found"}, indent=2))
        sys.exit(1)
    df = load_manifest(MANIFEST_PATH)
    v = validate_manifest(df)
    expected_train = 100_000
    expected_eval = 5_000
    v["expected_train"] = expected_train
    v["expected_eval"] = expected_eval
    v["train_match"] = v["train_rows"] == expected_train
    v["eval_match"] = v["eval_rows"] == expected_eval
    v["total_match"] = v["total_rows"] == expected_train + expected_eval
    ok = v["train_match"] and v["eval_match"] and v["duplicate_sample_id"] == 0
    v["status"] = "PASS" if ok else "FAIL"
    print(json.dumps(v, indent=2))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
