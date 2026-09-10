"""Bounded-memory streaming tests."""

from pathlib import Path

import pytest

from fitground.data.eval_pipeline import (
    _eval_shard_paths,
    load_eval_measurements,
    process_shard_streaming,
)
from fitground.data.memory import MemoryTracker, current_rss_bytes


@pytest.fixture
def first_shard() -> Path:
    paths = _eval_shard_paths()
    return paths[0]


def test_measurements_load_without_images() -> None:
    m = load_eval_measurements()
    assert len(m) == 5000
    key = next(iter(m))
    assert "body_height_cm" in m[key]
    assert "bust_ease_ratio" in m[key]


def test_streaming_small_batch_memory_stable(first_shard: Path) -> None:
    measurements = load_eval_measurements()
    shard_id = first_shard.name.replace(".parquet", "")
    shard_meas = {k: v for k, v in measurements.items() if k[0] == shard_id}

    rss_before = current_rss_bytes()
    tracker = MemoryTracker()

    rows = process_shard_streaming(
        first_shard,
        shard_meas,
        batch_size=4,
        max_rows=8,
        tracker=tracker,
    )

    rss_after = current_rss_bytes()
    assert len(rows) == 8
    assert rows[0]["person_image_identity"].startswith("person:")
    # Allow modest growth but not hundreds of MB from a 8-row batch.
    assert rss_after - rss_before < 300 * 1024 * 1024
