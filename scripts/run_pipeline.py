#!/usr/bin/env python3
"""Run the full FitGround FIT data engineering pipeline."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

# Ensure src is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fitground.audit.eda import run_eda
from fitground.audit.readiness import readiness_decision
from fitground.config import DATASET_EVAL_BYTES, MANIFEST_PATH, RAW_FIT_DIR
from fitground.data.pipeline import run_pipeline


def _raw_data_bytes() -> int:
    total = 0
    if RAW_FIT_DIR.exists():
        for f in RAW_FIT_DIR.rglob("*"):
            if f.is_file():
                total += f.stat().st_size
    return total


def main() -> None:
    parser = argparse.ArgumentParser(description="FitGround FIT pipeline")
    parser.add_argument("--skip-train", action="store_true")
    parser.add_argument("--skip-eval-download", action="store_true")
    parser.add_argument("--max-train-shards", type=int, default=None)
    args = parser.parse_args()

    print("=== FitGround FIT Pipeline ===")
    pipeline_result = run_pipeline(
        skip_train=args.skip_train,
        skip_eval_download=args.skip_eval_download,
        max_train_shards=args.max_train_shards,
    )

    if "error" in pipeline_result:
        print(f"Pipeline error: {pipeline_result}")
        sys.exit(1)

    print("=== EDA ===")
    eda_report = run_eda(MANIFEST_PATH)

    raw_bytes = _raw_data_bytes()
    available = shutil.disk_usage("/workspace").free
    raw_present = raw_bytes >= DATASET_EVAL_BYTES * 0.8

    readiness = readiness_decision(
        pipeline_result, eda_report, raw_present, raw_bytes
    )

    print(f"\nDecision: {readiness['decision']}")
    print(f"Manifest: {MANIFEST_PATH}")
    print(f"Raw bytes: {raw_bytes / 1e9:.2f} GB")
    print(f"Available: {available / 1e9:.2f} GB")


if __name__ == "__main__":
    main()
