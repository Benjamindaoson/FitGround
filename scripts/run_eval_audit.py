#!/usr/bin/env python3
"""Run bounded-memory eval-only FIT audit (no downloads)."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fitground.data.eval_checkpoint import EvalCheckpointManager
from fitground.data.eval_pipeline import finalize_manifest, run_eval_pipeline
from fitground.data.memory import MemoryTracker, current_rss_bytes


def main() -> None:
    parser = argparse.ArgumentParser(description="Bounded-memory FIT eval audit")
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--shard-limit", type=int, default=None)
    parser.add_argument("--max-rows-per-shard", type=int, default=None)
    parser.add_argument("--resume", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--process-only", action="store_true", help="Checkpoint shards only")
    parser.add_argument("--finalize-only", action="store_true", help="Assemble from checkpoints")
    parser.add_argument("--memory-test", action="store_true", help="1 shard, 8 rows, batch=4")
    args = parser.parse_args()

    if args.memory_test:
        args.shard_limit = 1
        args.max_rows_per_shard = 8
        args.batch_size = 4
        args.process_only = True

    if args.finalize_only:
        ckpt = EvalCheckpointManager()
        tracker = MemoryTracker()
        result = finalize_manifest(ckpt, tracker)
    else:
        result = run_eval_pipeline(
            batch_size=args.batch_size,
            shard_limit=args.shard_limit,
            max_rows_per_shard=args.max_rows_per_shard,
            resume=args.resume,
            finalize=not args.process_only,
            process_only=args.process_only,
        )

    result["rss_bytes_at_exit"] = current_rss_bytes()
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
