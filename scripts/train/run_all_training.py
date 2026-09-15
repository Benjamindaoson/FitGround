#!/usr/bin/env python3
"""Run the remaining training stages after the measured lattice exists."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run(script: str, extra: list[str] | None = None) -> None:
    cmd = [sys.executable, str(ROOT / "scripts" / "train" / script), *(extra or [])]
    print("RUN", " ".join(cmd), flush=True)
    proc = subprocess.run(cmd, cwd=str(ROOT))
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-observational", action="store_true")
    parser.add_argument("--mlp-epochs", type=int, default=400)
    parser.add_argument("--lm-epochs", type=int, default=80)
    parser.add_argument("--cnn-epochs", type=int, default=40)
    parser.add_argument("--rlvr-steps", type=int, default=300)
    args = parser.parse_args()
    if not args.skip_observational:
        run("train_observational.py", ["--epochs", str(args.cnn_epochs)])
    run("train_transition_sft.py", ["--mlp-epochs", str(args.mlp_epochs), "--lm-epochs", str(args.lm_epochs)])
    run("train_decision_sft.py", ["--mlp-epochs", str(args.mlp_epochs), "--lm-epochs", str(args.lm_epochs)])
    run("train_rlvr.py", ["--steps", str(args.rlvr_steps)])
    run("write_training_status.py")
    summary = {
        "observational": str(ROOT / "artifacts" / "training" / "observational_and_vision_baselines.json"),
        "transition_sft": str(ROOT / "artifacts" / "training" / "transition_sft.json"),
        "decision_sft": str(ROOT / "artifacts" / "training" / "decision_sft.json"),
        "rlvr": str(ROOT / "artifacts" / "training" / "rlvr.json"),
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
