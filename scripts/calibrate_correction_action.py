#!/usr/bin/env python3
"""Plan future action calibration without claiming a GarmentCode mapping exists."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fitground.correction import ContractValidationError, apply_correction


def main() -> int:
    parser = argparse.ArgumentParser(description="FitGround V0.1 correction calibration framework")
    parser.add_argument("--action-family", required=True)
    parser.add_argument("--intended-delta-cm", required=True, type=float)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    try:
        candidate = apply_correction({}, args.action_family, args.intended_delta_cm)
    except ContractValidationError as error:
        print(json.dumps({"error": str(error), "status": "NOT_SUPPORTED"}, indent=2))
        return 2

    payload = {
        "framework": "fitground_correction_calibration_v0.1",
        "action_family": candidate.action_family,
        "intended_delta_cm": candidate.intended_delta_cm,
        "realized_delta_cm": None,
        "error_cm": None,
        "cross_region_effects": None,
        "status": "NOT_RUN" if args.dry_run else "NOT_VERIFIED",
        "backend": "NOT_CONFIGURED",
        "required_future_steps": [
            "map action to a named pattern parameter",
            "apply pattern change",
            "extract realized garment measurements",
            "record cross-region effects",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if args.dry_run else 2


if __name__ == "__main__":
    raise SystemExit(main())
