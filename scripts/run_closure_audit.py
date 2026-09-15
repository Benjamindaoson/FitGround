#!/usr/bin/env python3
"""Run full closure audits after FIT-Clean finalize."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fitground.closure.audit import run_full_closure
from fitground.config import EVAL_SHARD_COUNT, FIT_CHECKPOINT_DIR, MANIFEST_PATH, TRAIN_SHARD_COUNT


def _checkpoint_counts() -> tuple[int, int]:
    ckpt = FIT_CHECKPOINT_DIR
    train = len(list(ckpt.glob("train-*.parquet")))
    eval_ = len(list(ckpt.glob("eval-*.parquet")))
    return train, eval_


def main() -> None:
    train, eval_ = _checkpoint_counts()
    if train < TRAIN_SHARD_COUNT or eval_ < EVAL_SHARD_COUNT:
        print(json.dumps({
            "status": "blocked",
            "reason": "checkpoints incomplete",
            "train_shards": train,
            "train_required": TRAIN_SHARD_COUNT,
            "eval_shards": eval_,
            "eval_required": EVAL_SHARD_COUNT,
        }, indent=2))
        sys.exit(1)
    if not MANIFEST_PATH.exists():
        print(json.dumps({"status": "blocked", "reason": f"missing {MANIFEST_PATH}"}, indent=2))
        sys.exit(1)
    result = run_full_closure(MANIFEST_PATH)
    print(json.dumps({"status": "ok", "validation": result["validation"]}, indent=2))


if __name__ == "__main__":
    main()
