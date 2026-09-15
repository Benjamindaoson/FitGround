#!/usr/bin/env python3
"""Unified benchmark entry. Stages resume independently."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> int:
    print("RUN", " ".join(cmd), flush=True)
    return subprocess.call(cmd, cwd=str(ROOT))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--stage", default="all", choices=["all", "tests", "observational", "hero", "status"])
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--device", default="auto")
    p.add_argument("--output-dir", type=Path, default=ROOT / "artifacts" / "benchmark")
    p.add_argument("--resume", action="store_true")
    args = p.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    status = {"seed": args.seed, "device": args.device, "stages": {}}
    if args.stage in ("all", "tests"):
        code = run([sys.executable, "-m", "pytest", "-q"])
        status["stages"]["tests"] = "PASS" if code == 0 else "FAIL"
        if code != 0 and args.stage == "tests":
            return code
    if args.stage in ("all", "observational"):
        script = ROOT / "scripts" / "train" / "train_observational.py"
        if script.exists():
            status["stages"]["observational"] = "RUN"
            run([sys.executable, str(script)])
    if args.stage in ("all", "hero"):
        hero = ROOT / "scripts" / "gpu" / "hero_pipeline.py"
        if hero.exists():
            status["stages"]["hero"] = "DELEGATE_GPU"
    if args.stage in ("all", "status"):
        writer = ROOT / "scripts" / "train" / "write_training_status.py"
        if writer.exists():
            run([sys.executable, str(writer)])
    (args.output_dir / "status.json").write_text(json.dumps(status, indent=2), encoding="utf-8")
    print(json.dumps(status, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
