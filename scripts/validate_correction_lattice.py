#!/usr/bin/env python3
"""Validate a correction lattice without treating NOT_RUN as a simulator result."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fitground.correction import CorrectionLattice, validate_lattice


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a FitGround correction lattice")
    parser.add_argument("--lattice", type=Path, required=True)
    parser.add_argument("--require-complete-outcomes", action="store_true")
    args = parser.parse_args()

    lattice = CorrectionLattice.from_dict(json.loads(args.lattice.read_text(encoding="utf-8")))
    result = validate_lattice(lattice, require_complete_outcomes=args.require_complete_outcomes)
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
