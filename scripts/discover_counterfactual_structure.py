#!/usr/bin/env python3
"""Discover counterfactual grouping structure in FIT-Clean v0.1 (metadata only)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fitground.config import COUNTERFACTUAL_STRUCTURE_PATH, MANIFEST_PATH
from fitground.counterfactual.discovery import run_structure_discovery
from fitground.counterfactual.schema import jsonable


def main() -> None:
    if not MANIFEST_PATH.exists():
        raise SystemExit(f"manifest not found: {MANIFEST_PATH}")
    import pandas as pd

    df = pd.read_parquet(MANIFEST_PATH)
    report = run_structure_discovery(df)
    COUNTERFACTUAL_STRUCTURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    COUNTERFACTUAL_STRUCTURE_PATH.write_text(
        json.dumps(jsonable(report), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    summary = {
        "n_rows": report["n_rows"],
        "n_usable": report["n_usable"],
        "strongest_available_unit": report["strongest_available_unit"],
        "tier_summary": report["tier_summary"],
        "A_groups_gt1": report["A_same_person_same_cloth"]["groups_with_gt1_row"],
        "A_tier_a_groups": report["A_same_person_same_cloth"].get("tier_a_groups"),
        "B_person_groups_gt1": report["B_same_person"]["size"]["n_groups_gt1"],
        "C_cloth_groups_gt1": report["C_same_cloth"]["size"]["n_groups_gt1"],
        "artifact": str(COUNTERFACTUAL_STRUCTURE_PATH),
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
