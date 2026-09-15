#!/usr/bin/env python3
"""Rank enumerated CHEST_CASE corrections from the measured lattice artifact."""
from __future__ import annotations
import argparse, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--lattice", type=Path, default=ROOT / "artifacts" / "correction_lattice_chest_case.json")
    args = p.parse_args()
    lat = json.loads(args.lattice.read_text(encoding="utf-8"))
    print(json.dumps({
        "state_id": lat["state_id"],
        "target_garment_bust_cm": lat["target_garment_bust_cm"],
        "oracle_action": lat["oracle_action"],
        "ranking": lat["ranking"],
        "candidates": lat["candidates"],
        "verification_status": lat["verification_status"],
    }, indent=2))
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
