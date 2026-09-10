"""Determinism and idempotence tests."""

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from fitground.data.identity import make_sample_id
from fitground.data.stream_core import load_shard_measurements, process_shard_streaming


def test_sample_id_deterministic() -> None:
    a = make_sample_id("eval", "eval-00000-of-00020", 42)
    b = make_sample_id("eval", "eval-00000-of-00020", 42)
    assert a == b == "eval/eval-00000-of-00020/0042"


def test_same_shard_twice_identical_hashes(tmp_path: Path) -> None:
    """Process synthetic shard twice — sample_id and hashes must match."""
    import io

    from PIL import Image

    def _img_bytes() -> bytes:
        img = Image.new("RGB", (768, 1024), color=(1, 2, 3))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    b = _img_bytes()
    rows = []
    for i in range(2):
        rows.append({
            "person": {"bytes": b, "path": f"p{i}.png"},
            "cloth": {"bytes": b, "path": f"c{i}.png"},
            "target": {"bytes": b, "path": f"t{i}.png"},
            "body_height": 170.0, "body_bust": 90.0, "body_waist": 70.0,
            "body_hips": 95.0, "garment_bust": 100.0, "garment_length": 60.0,
            "garment_sleeve_length": 0.0,
        })
    table = pa.Table.from_pylist(rows)
    shard = tmp_path / "eval-00000-of-00020.parquet"
    pq.write_table(table, shard)
    shard_id = "eval-00000-of-00020"
    meas = load_shard_measurements(shard, shard_id)
    r1 = process_shard_streaming(shard, "eval", meas, batch_size=2)
    r2 = process_shard_streaming(shard, "eval", meas, batch_size=2)
    assert [x["sample_id"] for x in r1] == [x["sample_id"] for x in r2]
    assert [x["person_sha256"] for x in r1] == [x["person_sha256"] for x in r2]
    assert [x["quality_status"] for x in r1] == [x["quality_status"] for x in r2]
