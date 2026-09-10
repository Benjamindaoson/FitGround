"""Failure-injection tests on small fixtures."""

import io
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from PIL import Image

from fitground.data.disk_guard import DiskSpaceError, require_disk_headroom
from fitground.data.memory import MemoryLimitError, MemoryTracker
from fitground.data.stream_core import load_shard_measurements, process_shard_streaming


def _write_shard(tmp_path: Path, rows: list[dict]) -> Path:
    p = tmp_path / "eval-00000-of-00020.parquet"
    pq.write_table(pa.Table.from_pylist(rows), p)
    return p


def test_missing_image_bytes_invalid(tmp_path: Path) -> None:
    rows = [{
        "person": {"bytes": None, "path": "x.png"},
        "cloth": {"bytes": None, "path": "y.png"},
        "target": {"bytes": None, "path": "z.png"},
        "body_height": 170.0, "body_bust": 90.0, "body_waist": 70.0,
        "body_hips": 95.0, "garment_bust": 100.0, "garment_length": 60.0,
        "garment_sleeve_length": 10.0,
    }]
    shard = _write_shard(tmp_path, rows)
    meas = load_shard_measurements(shard, "eval-00000-of-00020")
    out = process_shard_streaming(shard, "eval", meas, batch_size=1)
    assert out[0]["quality_status"] == "INVALID"
    assert not out[0]["usable_for_fitground"]


def test_corrupt_bytes_invalid(tmp_path: Path) -> None:
    rows = [{
        "person": {"bytes": b"not-a-png", "path": "x.png"},
        "cloth": {"bytes": b"not-a-png", "path": "y.png"},
        "target": {"bytes": b"not-a-png", "path": "z.png"},
        "body_height": 170.0, "body_bust": 90.0, "body_waist": 70.0,
        "body_hips": 95.0, "garment_bust": 100.0, "garment_length": 60.0,
        "garment_sleeve_length": 10.0,
    }]
    shard = _write_shard(tmp_path, rows)
    meas = load_shard_measurements(shard, "eval-00000-of-00020")
    out = process_shard_streaming(shard, "eval", meas, batch_size=1)
    assert out[0]["quality_status"] == "INVALID"


def test_memory_limit_raises() -> None:
    tracker = MemoryTracker(limit_bytes=1)
    try:
        tracker.check_limit("test")
        raised = False
    except MemoryLimitError:
        raised = True
    assert raised


def test_disk_guard_passes_on_this_vps() -> None:
    free = require_disk_headroom(reserve_bytes=1024)  # 1KB reserve — should pass
    assert free > 0
