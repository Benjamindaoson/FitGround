"""Incremental checkpoint state for resumable eval processing."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from fitground.config import INTERIM_DIR
from fitground.data.schema import eval_manifest_arrow_schema

EVAL_CHECKPOINT_DIR = INTERIM_DIR / "eval_checkpoint"
STATE_FILE = EVAL_CHECKPOINT_DIR / "state.json"


class EvalCheckpointManager:
    def __init__(self, checkpoint_dir: Path = EVAL_CHECKPOINT_DIR) -> None:
        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.state = self._load_state()

    def _load_state(self) -> dict[str, Any]:
        if STATE_FILE.exists():
            return json.loads(STATE_FILE.read_text())
        return {
            "version": 1,
            "completed_shards": [],
            "shard_rss_peaks_bytes": {},
            "stopped_reason": None,
            "updated_at": None,
        }

    def save_state(self, stopped_reason: str | None = None) -> None:
        self.state["updated_at"] = datetime.now(UTC).isoformat()
        if stopped_reason is not None:
            self.state["stopped_reason"] = stopped_reason
        STATE_FILE.write_text(json.dumps(self.state, indent=2))

    def is_shard_done(self, shard_id: str) -> bool:
        ckpt = self.shard_path(shard_id)
        return shard_id in self.state.get("completed_shards", []) and ckpt.exists()

    def shard_path(self, shard_id: str) -> Path:
        return self.checkpoint_dir / f"{shard_id}.parquet"

    def write_shard_checkpoint(self, shard_id: str, rows: list[dict[str, Any]]) -> None:
        schema = eval_manifest_arrow_schema()
        table = pa.Table.from_pylist(rows, schema=schema)
        pq.write_table(table, self.shard_path(shard_id))
        completed = list(self.state.get("completed_shards", []))
        if shard_id not in completed:
            completed.append(shard_id)
        self.state["completed_shards"] = sorted(completed)
        self.save_state()

    def record_shard_rss_peak(self, shard_id: str, peak_bytes: int) -> None:
        peaks = self.state.setdefault("shard_rss_peaks_bytes", {})
        peaks[shard_id] = peak_bytes
        self.save_state()

    def list_checkpoint_tables(self) -> list[Path]:
        return sorted(self.checkpoint_dir.glob("eval-*.parquet"))
