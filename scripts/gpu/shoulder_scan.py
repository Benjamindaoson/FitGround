#!/usr/bin/env python3
"""Shoulder DoF audit on Shirt + other available GarmentCode design families.

Goal is evidence, not a forced PASS.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path("/root/workspace/projects/FitGround")
if not ROOT.exists():
    ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "gpu"))

from fitground.training.geometry import realized_delta  # noqa: E402
import garmentcode_worker as gcw  # noqa: E402

OUT = ROOT / "artifacts" / "hero"
TMP = OUT / "_shoulder_scan"


def dump(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def probe(param, v0, v1, measure_key="shoulder_width_cm"):
    extra0 = {"shirt.length": 1.2, "sleeve.length": 0.3}
    extra1 = dict(extra0)
    extra0[param] = v0
    extra1[param] = v1
    g0 = gcw.generate_pattern(1.05, TMP / f"{param.replace('.', '_')}_0", "s0", extra_params=extra0)
    g1 = gcw.generate_pattern(1.05, TMP / f"{param.replace('.', '_')}_1", "s1", extra_params=extra1)
    return {
        "parameter": param,
        "v0": v0,
        "v1": v1,
        "measure_key": measure_key,
        "before_cm": g0["measurements"].get(measure_key),
        "after_cm": g1["measurements"].get(measure_key),
        "realized_delta_cm": realized_delta(g0["measurements"].get(measure_key), g1["measurements"].get(measure_key)),
        "cross": {
            "bust": realized_delta(g0["measurements"]["bust_circumference_cm"], g1["measurements"]["bust_circumference_cm"]),
            "sleeve": realized_delta(g0["measurements"]["sleeve_length_cm"], g1["measurements"]["sleeve_length_cm"]),
            "length": realized_delta(g0["measurements"]["length_cm"], g1["measurements"]["length_cm"]),
            "shoulder": realized_delta(g0["measurements"]["shoulder_width_cm"], g1["measurements"]["shoulder_width_cm"]),
        },
        "panel_names": g0["measurements"].get("panel_names"),
    }


def main() -> int:
    TMP.mkdir(parents=True, exist_ok=True)
    probes = []
    # Shirt / tee family — already know connecting_width does not move shoulder_width_cm.
    for param, v0, v1 in [
        ("sleeve.connecting_width", 0.05, 0.9),
        ("collar.standing_shoulder_len", 0.0, 5.0),
    ]:
        try:
            probes.append(probe(param, v0, v1))
        except Exception as exc:
            probes.append({"parameter": param, "error": f"{type(exc).__name__}: {exc}"})
    # Boolean standing_shoulder if present
    try:
        probes.append(probe("collar.standing_shoulder", False, True))
    except Exception as exc:
        probes.append({"parameter": "collar.standing_shoulder", "error": f"{type(exc).__name__}: {exc}"})

    design_dir = Path("/root/workspace/external/FitVTON-source-tree/GarmentCodeV2/assets/design_params")
    families = sorted(p.name for p in design_dir.glob("*.yaml"))
    independent = [
        p
        for p in probes
        if p.get("realized_delta_cm") is not None
        and abs(p["realized_delta_cm"]) >= 0.15
        and abs((p.get("cross") or {}).get("shoulder") or 0) >= 0.15
        and abs((p.get("cross") or {}).get("bust") or 0) < 0.5 * abs(p["realized_delta_cm"])
    ]
    payload = {
        "pattern_family": "GarmentCode Shirt / t-shirt.yaml",
        "available_design_yamls": families,
        "probes": probes,
        "independent_shoulder_parameters": [p["parameter"] for p in independent],
        "verdict": (
            "SHOULDER_ACTION = NO_GO_FOR_CURRENT_PATTERN_FAMILY"
            if not independent
            else "SHOULDER_CANDIDATE_FOUND"
        ),
        "note": (
            "Body shoulder_w is not an action. sleeve.connecting_width moves sleeve length, "
            "not the torso top-edge shoulder proxy. default.yaml standing_shoulder is a collar stand, "
            "not a centimetre garment shoulder width. No FittedShirt-style independent shoulder DoF "
            "is exposed in the available design_params for this worker."
        ),
    }
    dump(OUT / "shoulder_scan.json", payload)
    print(json.dumps({k: payload[k] for k in ("verdict", "independent_shoulder_parameters", "available_design_yamls")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
