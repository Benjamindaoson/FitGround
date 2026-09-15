"""Unified incremental checkpoints for train + eval streaming."""

from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from fitground.config import EVAL_CHECKPOINT_DIR, FIT_CHECKPOINT_DIR, INTERIM_DIR
from fitground.data.schema import eval_manifest_arrow_schema


class FitCheckpointManager:
    def __init__(self, checkpoint_dir: Path = FIT_CHECKPOINT_DIR) -> None:
        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.state_path = self.checkpoint_dir / "state.json"
        self.state = self._load_state()
        self._import_legacy_eval_checkpoints()

    def _load_state(self) -> dict[str, Any]:
        if self.state_path.exists():
            return json.loads(self.state_path.read_text())
        return {
            "version": 2,
            "completed_shards": [],
            "shard_rss_peaks_bytes": {},
            "stopped_reason": None,
            "updated_at": None,
        }

    def _import_legacy_eval_checkpoints(self) -> None:
        legacy = EVAL_CHECKPOINT_DIR
        if not legacy.exists():
            return
        for src in legacy.glob("eval-*.parquet"):
            dst = self.checkpoint_dir / src.name
            if not dst.exists():
                shutil.copy2(src, dst)
        legacy_state = legacy / "state.json"
        if legacy_state.exists():
            old = json.loads(legacy_state.read_text())
            for sid in old.get("completed_shards", []):
                if sid not in self.state["completed_shards"]:
                    self.state["completed_shards"].append(sid)
            for k, v in old.get("shard_rss_peaks_bytes", {}).items():
                self.state.setdefault("shard_rss_peaks_bytes", {})[k] = v
            self.state["completed_shards"] = sorted(set(self.state["completed_shards"]))
            self.save_state()

    def save_state(self, stopped_reason: str | None = None) -> None:
        self.state["updated_at"] = datetime.now(UTC).isoformat()
        if stopped_reason is not None:
            self.state["stopped_reason"] = stopped_reason
        self.state_path.write_text(json.dumps(self.state, indent=2))

    def is_shard_done(self, shard_id: str) -> bool:
        return shard_id in self.state.get("completed_shards", []) and self.shard_path(shard_id).exists()

    def shard_path(self, shard_id: str) -> Path:
        return self.checkpoint_dir / f"{shard_id}.parquet"

    def write_shard_checkpoint(self, shard_id: str, rows: list[dict[str, Any]]) -> None:
        schema = eval_manifest_arrow_schema()
        table = pa.Table.from_pylist(rows, schema=schema)
        pq.write_table(table, self.shard_path(shard_id))
        completed = set(self.state.get("completed_shards", []))
        completed.add(shard_id)
        self.state["completed_shards"] = sorted(completed)
        self.save_state()

    def record_shard_rss_peak(self, shard_id: str, peak_bytes: int) -> None:
        self.state.setdefault("shard_rss_peaks_bytes", {})[shard_id] = peak_bytes
        self.save_state()

    def list_checkpoint_paths(self) -> list[Path]:
        return sorted(self.checkpoint_dir.glob("*.parquet"))

    def completed_count(self, split: str) -> int:
        prefix = "train-" if split == "train" else "eval-"
        return sum(1 for s in self.state.get("completed_shards", []) if s.startswith(prefix))
