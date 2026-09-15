#!/usr/bin/env python3
"""Build an unrun correction lattice from a current-state JSON payload."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fitground.correction import (
    CurrentFitState,
    apply_correction,
    build_correction_lattice,
)


def _parse_action(value: str) -> tuple[str, float]:
    action_family, delta = value.rsplit(":", 1)
    return action_family, float(delta)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a FitGround V0.1 correction lattice")
    parser.add_argument("--state", type=Path, required=True, help="CurrentFitState JSON")
    parser.add_argument("--action", action="append", required=True, help="action_family:intended_delta_cm")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    state = CurrentFitState.from_dict(json.loads(args.state.read_text(encoding="utf-8")))
    candidates = [apply_correction(state.garment, *_parse_action(action)) for action in args.action]
    lattice = build_correction_lattice(state, candidates)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(lattice.to_dict(), indent=2), encoding="utf-8")
    print(json.dumps({"lattice_id": lattice.lattice_id, "status": "NOT_RUN", "output": str(args.output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
