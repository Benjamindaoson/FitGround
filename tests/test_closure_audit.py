"""Closure audit tests on eval manifest."""

from pathlib import Path

import pandas as pd

from fitground.closure.audit import (
    duplicate_leakage_audit,
    quality_audit,
    validate_manifest,
)
from fitground.config import EVAL_MANIFEST_PATH


def test_validate_eval_manifest() -> None:
    if not EVAL_MANIFEST_PATH.exists():
        return
    df = pd.read_parquet(EVAL_MANIFEST_PATH)
    v = validate_manifest(df)
    assert v["total_rows"] == 5000
    assert v["eval_rows"] == 5000
    assert v["duplicate_sample_id"] == 0


def test_quality_sums_to_total() -> None:
    if not EVAL_MANIFEST_PATH.exists():
        return
    df = pd.read_parquet(EVAL_MANIFEST_PATH)
    q = quality_audit(df)["ALL"]
    assert q["VALID"] + q["SUSPICIOUS"] + q["INVALID"] == q["total"]
