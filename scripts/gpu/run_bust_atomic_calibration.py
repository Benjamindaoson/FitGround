#!/usr/bin/env python3
"""Bust atomic calibration batch: pattern measurements + optional physics."""
import csv
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path("/root/workspace/projects/FitGround")
WORKER = ROOT / "scripts/gpu/garmentcode_worker.py"
OUT = ROOT / "artifacts" / "bust_atomic_calibration"
FIG = ROOT / "reports" / "figures"
GPU_ART = ROOT / "artifacts" / "gpu"


def run_case(tag, delta, physics=False, max_steps=400, render=False, seed=0):
    out_dir = OUT / tag
    cmd = [
        sys.executable,
        str(WORKER),
        "--intended-delta-cm",
        str(delta),
        "--tag",
        tag,
        "--output-dir",
        str(out_dir),
        "--seed",
        str(seed),
    ]
    if physics:
        cmd.append("--physics")
        cmd.extend(["--max-sim-steps", str(max_steps)])
    if render:
        cmd.append("--render")
    env = os.environ.copy()
    env["PYTHONPATH"] = "/root/workspace/external/FitVTON-source-tree/GarmentCodeV2:" + env.get("PYTHONPATH", "")
    env["PYOPENGL_PLATFORM"] = "egl"
    t0 = time.time()
    proc = subprocess.run(cmd, cwd="/tmp", env=env, capture_output=True, text=True)
    payload_path = out_dir / f"{tag}.json"
    payload = {}
    if payload_path.exists():
        payload = json.loads(payload_path.read_text())
    else:
        payload = {"error": "no json", "stdout": proc.stdout[-4000:], "stderr": proc.stderr[-4000:]}
    payload["subprocess_returncode"] = proc.returncode
    payload["wall_s"] = time.time() - t0
    if proc.returncode != 0 and "traceback" not in payload:
        payload["stderr_tail"] = proc.stderr[-4000:]
    return payload


def gates(rows):
    by_tag = {r["action_id"]: r for r in rows if r.get("action_id")}
    g = {}
    needed = ["bust_plus_1cm", "bust_plus_2cm", "bust_plus_3cm", "bust_plus_3cm_repeat"]
    g1_pattern = all(by_tag.get(t, {}).get("realized_delta_cm") is not None for t in needed)
    g1_sim = all(by_tag.get(t, {}).get("simulation_status") == "SIMULATED" for t in needed)
    g1_render = all(by_tag.get(t, {}).get("render_status") == "RENDERED" for t in needed)
    g["G1_executability"] = {
        "pattern": "PASS" if g1_pattern else "FAIL",
        "simulation": "PASS" if g1_sim else ("NOT_RUN" if all(by_tag.get(t, {}).get("simulation_status") == "NOT_RUN" for t in needed) else "FAIL"),
        "render": "PASS" if g1_render else ("NOT_RUN" if all(by_tag.get(t, {}).get("render_status") == "NOT_RUN" for t in needed) else "FAIL"),
    }
    errs = [by_tag[t]["calibration_error_cm"] for t in needed if by_tag.get(t, {}).get("calibration_error_cm") is not None]
    g["G2_measurement_accuracy"] = {
        "max_abs_error_cm": max(errs) if errs else None,
        "mean_abs_error_cm": float(np.mean(errs)) if errs else None,
        "status": "PASS" if errs and max(errs) < 0.15 else ("PARTIAL" if errs and max(errs) < 0.5 else "FAIL"),
    }
    r1 = by_tag.get("bust_plus_1cm", {}).get("realized_delta_cm")
    r2 = by_tag.get("bust_plus_2cm", {}).get("realized_delta_cm")
    r3 = by_tag.get("bust_plus_3cm", {}).get("realized_delta_cm")
    mono = r1 is not None and r2 is not None and r3 is not None and r1 < r2 < r3
    g["G3_monotonicity"] = {"realized": [r1, r2, r3], "status": "PASS" if mono else "FAIL"}
    # locality: sleeve/length vs intended; waist is structurally coupled for flare=1 shirt
    loc_notes = []
    loc_status = "PASS"
    for t, intended in [("bust_plus_1cm", 1), ("bust_plus_2cm", 2), ("bust_plus_3cm", 3)]:
        row = by_tag.get(t, {})
        sleeve = abs(row.get("sleeve_delta_cm") or 0)
        length = abs(row.get("length_delta_cm") or 0)
        waist = abs(row.get("waist_delta_cm") or 0)
        shoulder = abs(row.get("shoulder_delta_cm") or 0)
        loc_notes.append({"tag": t, "waist": waist, "shoulder": shoulder, "sleeve": sleeve, "length": length})
        if sleeve > 0.35 * intended or length > 0.35 * intended:
            loc_status = "FAIL"
    if loc_status != "FAIL":
        # waist coupling expected for Shirt.width; mark PARTIAL not PASS
        loc_status = "PARTIAL"
    g["G4_locality"] = {"status": loc_status, "notes": loc_notes, "reason": "shirt.width.v scales full torso girth; waist tracks bust when flare=1.0"}
    # sensitivity: realized non-zero and visual/pattern change
    hashes = [by_tag.get(t, {}).get("garment_measurement_after", {}).get("spec_sha256") for t in ["bust_plus_1cm", "bust_plus_2cm", "bust_plus_3cm"]]
    unique = len(set(h for h in hashes if h)) == 3
    g["G5_outcome_sensitivity"] = {
        "unique_spec_hashes": unique,
        "status": "PASS" if unique and r3 and r3 > 0.5 else "FAIL",
    }
    a = by_tag.get("bust_plus_3cm", {}).get("realized_delta_cm")
    b = by_tag.get("bust_plus_3cm_repeat", {}).get("realized_delta_cm")
    repro = a is not None and b is not None and abs(a - b) < 1e-6
    g["G6_reproducibility"] = {"plus3": a, "plus3_repeat": b, "abs_diff": None if a is None or b is None else abs(a - b), "status": "PASS" if repro else "FAIL"}
    # overall
    pattern_ok = g["G2_measurement_accuracy"]["status"] == "PASS" and g["G3_monotonicity"]["status"] == "PASS" and g["G5_outcome_sensitivity"]["status"] == "PASS" and g["G6_reproducibility"]["status"] == "PASS" and g["G1_executability"]["pattern"] == "PASS"
    if pattern_ok and g["G1_executability"]["simulation"] == "PASS":
        decision = "GO"
    elif pattern_ok:
        decision = "PARTIAL"
    else:
        decision = "NO-GO"
    g["decision"] = decision
    return g


def figures(rows):
    FIG.mkdir(parents=True, exist_ok=True)
    seq = [r for r in rows if r.get("action_id") in ("bust_plus_1cm", "bust_plus_2cm", "bust_plus_3cm")]
    seq = sorted(seq, key=lambda r: r["intended_delta_cm"])
    if not seq:
        return []
    intended = [r["intended_delta_cm"] for r in seq]
    realized = [r["realized_delta_cm"] for r in seq]
    paths = []
    plt.figure(figsize=(6, 4))
    plt.plot(intended, realized, "o-", label="realized")
    plt.plot(intended, intended, "k--", label="identity")
    plt.xlabel("intended bust delta (cm)")
    plt.ylabel("realized bust delta (cm)")
    plt.title("Bust calibration: intended vs realized (pattern geometry)")
    plt.legend()
    plt.tight_layout()
    p1 = FIG / "bust_intended_vs_realized.png"
    plt.savefig(p1, dpi=140)
    plt.close()
    paths.append(str(p1))
    plt.figure(figsize=(6, 4))
    plt.plot(intended, realized, "o-")
    plt.xlabel("intended bust delta (cm)")
    plt.ylabel("realized bust delta (cm)")
    plt.title("Bust calibration curve (shirt.width.v)")
    plt.tight_layout()
    p2 = FIG / "bust_calibration_curve.png"
    plt.savefig(p2, dpi=140)
    plt.close()
    paths.append(str(p2))
    # side effects
    plt.figure(figsize=(7, 4))
    for key, label in [
        ("waist_delta_cm", "waist"),
        ("shoulder_delta_cm", "shoulder"),
        ("sleeve_delta_cm", "sleeve"),
        ("length_delta_cm", "length"),
    ]:
        plt.plot(intended, [r.get(key) for r in seq], "o-", label=label)
    plt.xlabel("intended bust delta (cm)")
    plt.ylabel("side-effect delta (cm)")
    plt.title("Cross-region side effects of shirt.width.v")
    plt.legend()
    plt.tight_layout()
    p3 = FIG / "bust_side_effects.png"
    plt.savefig(p3, dpi=140)
    plt.close()
    paths.append(str(p3))
    return paths


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cases = [
        ("bust_plus_1cm", 1.0),
        ("bust_plus_2cm", 2.0),
        ("bust_plus_3cm", 3.0),
        ("bust_plus_3cm_repeat", 3.0),
    ]
    rows = []
    for tag, delta in cases:
        print("RUNNING", tag, delta, flush=True)
        row = run_case(tag, delta, physics=False, seed=0)
        rows.append(row)
        print("  realized", row.get("realized_delta_cm"), "err", row.get("calibration_error_cm"), flush=True)
    g = gates(rows)
    figs = figures(rows)
    csv_path = ROOT / "artifacts" / "bust_atomic_calibration.csv"
    fields = [
        "action_id",
        "intended_delta_cm",
        "realized_delta_cm",
        "calibration_error_cm",
        "waist_delta_cm",
        "shoulder_delta_cm",
        "sleeve_delta_cm",
        "length_delta_cm",
        "baseline_width_v",
        "mutated_width_v",
        "simulation_status",
        "render_status",
        "verification_status",
        "runtime_s",
    ]
    with csv_path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k) for k in fields})
    summary = {
        "experiment": "bust_atomic_calibration",
        "garment": "GarmentCodeV2 t-shirt.yaml Shirt on mean_all body",
        "parameter": "shirt.width.v",
        "parameter_unit": "multiplier of body bust",
        "inverse_calibration": "parameter_delta = desired_cm / body_bust_cm",
        "rows": rows,
        "gates": g,
        "figures": figs,
        "csv": str(csv_path),
        "note": "realized_delta_cm is measured from 2D panel geometry, not copied from intended_delta_cm.",
    }
    json_path = ROOT / "artifacts" / "bust_atomic_calibration.json"
    json_path.write_text(json.dumps(summary, indent=2))
    print(json.dumps({"gates": g, "csv": str(csv_path), "json": str(json_path)}, indent=2))
    return 0 if g["decision"] in ("GO", "PARTIAL") else 1


if __name__ == "__main__":
    raise SystemExit(main())
