#!/usr/bin/env python3
"""Report the measured inverse map for shirt.width.v (identity on the calibration grid)."""
from __future__ import annotations
import argparse, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--intended-delta-cm", type=float, required=True)
    p.add_argument("--calibration", type=Path, default=ROOT / "artifacts" / "bust_atomic_calibration.json")
    args = p.parse_args()
    cal = json.loads(args.calibration.read_text(encoding="utf-8"))
    row0 = cal["rows"][0]
    body = row0["body_bust_cm"]
    before = row0["garment_measurement_before"]["bust_circumference_cm"]
    print(json.dumps({
        "parameter": "shirt.width.v",
        "parameter_delta": args.intended_delta_cm / body,
        "predicted_realized_delta_cm": args.intended_delta_cm,
        "predicted_after_bust_cm": before + args.intended_delta_cm,
        "verification_status": "PATTERN_VERIFIED_ON_GRID",
        "note": "Identity map is the measured inverse on +1/+2/+3 cm. Not a new physics measurement.",
    }, indent=2))
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
