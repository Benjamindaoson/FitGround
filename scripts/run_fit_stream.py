#!/usr/bin/env python3
"""Streaming FIT data engineering — no full dataset in RAM or on disk."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fitground.data.fit_checkpoint import FitCheckpointManager
from fitground.data.fit_stream_pipeline import finalize_fit_clean, run_fit_stream
from fitground.data.memory import current_rss_bytes


def main() -> None:
    parser = argparse.ArgumentParser(description="FIT streaming pipeline")
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--resume", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--no-train", action="store_true")
    parser.add_argument("--no-eval", action="store_true")
    parser.add_argument("--train-shard-limit", type=int, default=None)
    parser.add_argument("--finalize", action="store_true")
    parser.add_argument("--finalize-only", action="store_true")
    parser.add_argument("--smoke", action="store_true", help="1 train shard only")
    args = parser.parse_args()

    if args.smoke:
        args.train_shard_limit = 1
        args.no_eval = True

    if args.finalize_only:
        ckpt = FitCheckpointManager()
        result = finalize_fit_clean(ckpt)
    else:
        result = run_fit_stream(
            batch_size=args.batch_size,
            resume=args.resume,
            process_train=not args.no_train,
            process_eval=not args.no_eval,
            train_shard_limit=args.train_shard_limit,
            finalize=args.finalize,
        )

    result["rss_bytes_at_exit"] = current_rss_bytes()
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
