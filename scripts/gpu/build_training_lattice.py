#!/usr/bin/env python3
"""Build a measured (s, a, s') lattice + pattern PNGs for training.

Every realized_delta_cm is after-minus-before panel geometry. Intended values
are never copied into realized fields.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path("/root/workspace/projects/FitGround")
if not ROOT.exists():
    ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fitground.training.geometry import rasterize_specification, realized_delta, utility_chest_case

GC_ROOT = Path("/root/workspace/external/FitVTON-source-tree/GarmentCodeV2")
WORKER_DIR = ROOT / "scripts" / "gpu"
if str(WORKER_DIR) not in sys.path:
    sys.path.insert(0, str(WORKER_DIR))

import garmentcode_worker as gcw  # noqa: E402


BODIES = {
    "mean_all": GC_ROOT / "assets/bodies/mean_all.yaml",
    "mean_female": GC_ROOT / "assets/bodies/mean_female.yaml",
}

VISION_WIDTHS = [1.00, 1.02, 1.04, 1.06, 1.08, 1.12, 1.16, 1.22]
VISION_LENGTHS = [0.9, 1.1, 1.3, 1.6]
VISION_SLEEVES = [0.15, 0.30, 0.55]

STATE_WIDTHS = [1.05, 1.08, 1.12, 1.18]
STATE_LENGTH = 1.2
STATE_SLEEVE = 0.3
BUST_DELTAS = [-3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0]
SLEEVE_STARTS = [0.20, 0.30, 0.50]
SLEEVE_DELTAS = [-2.0, -1.0, 1.0, 2.0]
LENGTH_STARTS = [1.00, 1.20, 1.50]
LENGTH_DELTAS = [-2.0, -1.0, 1.0, 2.0]
DECISION_TARGET_EASE = [1.0, 2.0, 3.0]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def state_id(body_name: str, width: float, length: float, sleeve: float) -> str:
    return f"{body_name}_w{width:.2f}_l{length:.2f}_s{sleeve:.2f}"


class PatternCache:
    def __init__(self, tmp_root: Path, png_root: Path):
        self.tmp_root = tmp_root
        self.png_root = png_root
        self.png_root.mkdir(parents=True, exist_ok=True)
        self.tmp_root.mkdir(parents=True, exist_ok=True)
        self.store: dict[tuple, dict] = {}
        self.hits = 0
        self.misses = 0

    def get(self, body_name: str, body_path: Path, width: float, length: float, sleeve: float) -> dict:
        key = (body_name, round(float(width), 5), round(float(length), 5), round(float(sleeve), 5))
        if key in self.store:
            self.hits += 1
            return self.store[key]
        self.misses += 1
        print(f"GENERATE {body_name} w={width:.5f} l={length:.5f} s={sleeve:.5f} miss={self.misses}", flush=True)
        tag = f"{body_name}_{key[1]:.5f}_{key[2]:.5f}_{key[3]:.5f}".replace(".", "p")
        raw = gcw.generate_pattern(
            width,
            self.tmp_root / tag,
            tag,
            body_path=str(body_path),
            extra_params={"shirt.length": float(length), "sleeve.length": float(sleeve)},
        )
        png_name = f"{tag}.png"
        png_path = self.png_root / png_name
        rasterize_specification(raw["specification"], png_path, size=128)
        compact = {
            "body_name": body_name,
            "body_path": str(body_path),
            "body_bust_cm": raw["body_bust_cm"],
            "body_waist_cm": raw.get("body_waist_cm"),
            "body_shoulder_w_cm": raw.get("body_shoulder_w_cm"),
            "params": {
                "shirt.width": float(width),
                "shirt.length": float(length),
                "sleeve.length": float(sleeve),
            },
            "named_pattern_parameters": raw["named_pattern_parameters_after"],
            "measurements": raw["measurements"],
            "self_intersecting": raw["self_intersecting"],
            "png": str(png_path),
            "png_sha256": sha256_file(png_path),
            "spec_sha256": raw["measurements"]["spec_sha256"],
            "state_id": state_id(body_name, width, length, sleeve),
        }
        folder = Path(raw["folder"])
        if folder.exists():
            shutil.rmtree(folder, ignore_errors=True)
        parent = self.tmp_root / tag
        if parent.exists():
            shutil.rmtree(parent, ignore_errors=True)
        self.store[key] = compact
        return compact


def probe_scale(cache: PatternCache, body_name: str, body_path: Path, param: str, v0: float, v1: float, measure_key: str) -> dict:
    width, length, sleeve = 1.05, 1.2, 0.3
    if param == "sleeve.length":
        g0 = cache.get(body_name, body_path, width, length, v0)
        g1 = cache.get(body_name, body_path, width, length, v1)
    elif param == "shirt.length":
        g0 = cache.get(body_name, body_path, width, v0, sleeve)
        g1 = cache.get(body_name, body_path, width, v1, sleeve)
    elif param == "shirt.width":
        g0 = cache.get(body_name, body_path, v0, length, sleeve)
        g1 = cache.get(body_name, body_path, v1, length, sleeve)
    else:
        raise ValueError(param)
    dcm = realized_delta(g0["measurements"][measure_key], g1["measurements"][measure_key])
    dv = float(v1) - float(v0)
    scale = None if dcm is None or abs(dv) < 1e-12 else float(dcm) / dv
    return {
        "parameter": param,
        "measure_key": measure_key,
        "v0": v0,
        "v1": v1,
        "before_cm": g0["measurements"][measure_key],
        "after_cm": g1["measurements"][measure_key],
        "realized_delta_cm": dcm,
        "cm_per_unit": scale,
        "body_name": body_name,
    }


def transition_row(before: dict, after: dict, action_family: str, intended: float, parameter_name: str, measure_key: str) -> dict:
    before_m = before["measurements"]
    after_m = after["measurements"]
    realized = realized_delta(before_m[measure_key], after_m[measure_key])
    row = {
        "state_id": before["state_id"],
        "action_id": f"{before['state_id']}__{action_family}__{intended:+.2f}",
        "action_family": action_family,
        "intended_delta_cm": float(intended),
        "realized_delta_cm": realized,
        "realized_source": "panel_geometry_after_minus_before",
        "realized_measurement_key": measure_key,
        "parameter_name": parameter_name,
        "body_name": before["body_name"],
        "body_bust_cm": before["body_bust_cm"],
        "body_waist_cm": before.get("body_waist_cm"),
        "named_pattern_parameters_before": before["named_pattern_parameters"],
        "named_pattern_parameters_after": after["named_pattern_parameters"],
        "garment_measurement_before": before_m,
        "garment_measurement_after": after_m,
        "png_before": before["png"],
        "png_after": after["png"],
        "self_intersecting": bool(before["self_intersecting"] or after["self_intersecting"]),
        "waist_delta_cm": realized_delta(before_m.get("waist_cm"), after_m.get("waist_cm")),
        "shoulder_delta_cm": realized_delta(before_m.get("shoulder_width_cm"), after_m.get("shoulder_width_cm")),
        "sleeve_delta_cm": realized_delta(before_m.get("sleeve_length_cm"), after_m.get("sleeve_length_cm")),
        "length_delta_cm": realized_delta(before_m.get("length_cm"), after_m.get("length_cm")),
        "bust_delta_cm": realized_delta(before_m.get("bust_circumference_cm"), after_m.get("bust_circumference_cm")),
        "calibration_error_cm": None if realized is None else abs(realized - float(intended)),
        "verification_status": "VERIFIED" if realized is not None else "NOT_VERIFIED",
        "simulation_status": "NOT_RUN",
        "render_status": "NOT_RUN",
    }
    return row


def build_decision_cases(transitions: list[dict]) -> list[dict]:
    by_state: dict[str, list[dict]] = {}
    for row in transitions:
        if row["action_family"] != "bust_circumference_delta_cm":
            continue
        by_state.setdefault(row["state_id"], []).append(row)
    cases = []
    for sid, rows in sorted(by_state.items()):
        base = rows[0]
        before_bust = base["garment_measurement_before"]["bust_circumference_cm"]
        for ease in DECISION_TARGET_EASE:
            target = before_bust + ease
            scored = []
            for row in rows:
                after_bust = row["garment_measurement_after"]["bust_circumference_cm"]
                target_error = after_bust - target
                util = utility_chest_case(
                    target_error_cm=target_error,
                    intended_delta_cm=row["intended_delta_cm"],
                    sleeve_side_effect_cm=row.get("sleeve_delta_cm") or 0.0,
                    length_side_effect_cm=row.get("length_delta_cm") or 0.0,
                )
                scored.append({**row, "target_error_cm": target_error, "utility": util, "target_garment_bust_cm": target})
            scored.sort(key=lambda r: r["utility"], reverse=True)
            oracle = scored[0]
            cases.append(
                {
                    "case_id": f"{sid}__target_plus_{ease:.0f}cm",
                    "state_id": sid,
                    "body_bust_cm": base["body_bust_cm"],
                    "garment_bust_cm": before_bust,
                    "garment_length_cm": base["garment_measurement_before"]["length_cm"],
                    "garment_sleeve_cm": base["garment_measurement_before"]["sleeve_length_cm"],
                    "png": base["png_before"],
                    "target_garment_bust_cm": target,
                    "target_definition": f"increase measured garment bust by {ease} cm vs this state's baseline",
                    "oracle_action_id": oracle["action_id"],
                    "oracle_action_family": oracle["action_family"],
                    "oracle_intended_delta_cm": oracle["intended_delta_cm"],
                    "oracle_utility": oracle["utility"],
                    "ranking": [r["action_id"] for r in scored],
                    "candidates": [
                        {
                            "action_id": r["action_id"],
                            "intended_delta_cm": r["intended_delta_cm"],
                            "realized_delta_cm": r["realized_delta_cm"],
                            "after_bust_cm": r["garment_measurement_after"]["bust_circumference_cm"],
                            "target_error_cm": r["target_error_cm"],
                            "utility": r["utility"],
                        }
                        for r in scored
                    ],
                    "verification_status": "VERIFIED",
                }
            )
    return cases


def vision_rows(cache: PatternCache) -> list[dict]:
    rows = []
    for body_name, body_path in BODIES.items():
        if not body_path.exists():
            continue
        for w in VISION_WIDTHS:
            for length in VISION_LENGTHS:
                for sleeve in VISION_SLEEVES:
                    g = cache.get(body_name, body_path, w, length, sleeve)
                    m = g["measurements"]
                    rows.append(
                        {
                            "sample_id": g["state_id"],
                            "state_id": g["state_id"],
                            "body_name": body_name,
                            "body_bust_cm": g["body_bust_cm"],
                            "body_waist_cm": g.get("body_waist_cm"),
                            "body_shoulder_w_cm": g.get("body_shoulder_w_cm"),
                            "png": g["png"],
                            "png_sha256": g["png_sha256"],
                            "garment_bust_cm": m["bust_circumference_cm"],
                            "garment_waist_cm": m["waist_cm"],
                            "garment_length_cm": m["length_cm"],
                            "garment_sleeve_cm": m["sleeve_length_cm"],
                            "params": g["params"],
                            "source": "generated_garmentcode_pattern_png",
                            "note": "Not FIT-100K. Pattern drawing rasterized from measured specification.",
                        }
                    )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=ROOT / "artifacts" / "training")
    parser.add_argument("--limit-vision", type=int, default=0, help="debug cap on vision samples")
    args = parser.parse_args()
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    cache = PatternCache(out / "_pattern_tmp", out / "pattern_pngs")
    t0 = time.time()
    probes = []
    for body_name, body_path in BODIES.items():
        if not body_path.exists():
            continue
        probes.append(probe_scale(cache, body_name, body_path, "shirt.width", 1.05, 1.05 + 3.0 / 99.8407, "bust_circumference_cm"))
        probes.append(probe_scale(cache, body_name, body_path, "sleeve.length", 0.30, 0.40, "sleeve_length_cm"))
        probes.append(probe_scale(cache, body_name, body_path, "shirt.length", 1.20, 1.40, "length_cm"))

    scale_by = {}
    for p in probes:
        scale_by[(p["body_name"], p["parameter"])] = p["cm_per_unit"]

    transitions = []
    for body_name, body_path in BODIES.items():
        if not body_path.exists():
            continue
        body_bust = cache.get(body_name, body_path, 1.05, STATE_LENGTH, STATE_SLEEVE)["body_bust_cm"]
        for w in STATE_WIDTHS:
            before = cache.get(body_name, body_path, w, STATE_LENGTH, STATE_SLEEVE)
            for intended in BUST_DELTAS:
                param_delta = float(intended) / float(body_bust)
                new_w = w + param_delta
                if new_w < 1.0 or new_w > 1.3:
                    continue
                after = cache.get(body_name, body_path, new_w, STATE_LENGTH, STATE_SLEEVE)
                transitions.append(
                    transition_row(
                        before,
                        after,
                        "bust_circumference_delta_cm",
                        intended,
                        "shirt.width.v",
                        "bust_circumference_cm",
                    )
                )
        sleeve_scale = scale_by.get((body_name, "sleeve.length"))
        if sleeve_scale and abs(sleeve_scale) > 0.05:
            for sleeve0 in SLEEVE_STARTS:
                before = cache.get(body_name, body_path, 1.05, STATE_LENGTH, sleeve0)
                for intended in SLEEVE_DELTAS:
                    dv = float(intended) / sleeve_scale
                    new_s = sleeve0 + dv
                    if new_s < 0.1 or new_s > 1.15:
                        continue
                    after = cache.get(body_name, body_path, 1.05, STATE_LENGTH, new_s)
                    transitions.append(
                        transition_row(
                            before,
                            after,
                            "sleeve_length_delta_cm",
                            intended,
                            "sleeve.length.v",
                            "sleeve_length_cm",
                        )
                    )
        length_scale = scale_by.get((body_name, "shirt.length"))
        if length_scale and abs(length_scale) > 0.05:
            for length0 in LENGTH_STARTS:
                before = cache.get(body_name, body_path, 1.05, length0, STATE_SLEEVE)
                for intended in LENGTH_DELTAS:
                    dv = float(intended) / length_scale
                    new_l = length0 + dv
                    if new_l < 0.5 or new_l > 3.5:
                        continue
                    after = cache.get(body_name, body_path, 1.05, new_l, STATE_SLEEVE)
                    transitions.append(
                        transition_row(
                            before,
                            after,
                            "shirt_length_delta_cm",
                            intended,
                            "shirt.length.v",
                            "length_cm",
                        )
                    )

    vision = vision_rows(cache)
    if args.limit_vision:
        vision = vision[: args.limit_vision]
    decisions = build_decision_cases(transitions)

    trans_path = out / "transition_lattice.jsonl"
    with trans_path.open("w", encoding="utf-8") as fh:
        for row in transitions:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    vis_path = out / "vision_pattern_samples.jsonl"
    with vis_path.open("w", encoding="utf-8") as fh:
        for row in vision:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    dec_path = out / "decision_cases.json"
    dec_path.write_text(json.dumps(decisions, indent=2), encoding="utf-8")

    max_bust_err = max(
        (r["calibration_error_cm"] for r in transitions if r["action_family"] == "bust_circumference_delta_cm" and r["calibration_error_cm"] is not None),
        default=None,
    )
    summary = {
        "task": "measured_training_lattice",
        "n_transitions": len(transitions),
        "n_vision_samples": len(vision),
        "n_decision_cases": len(decisions),
        "n_unique_patterns_generated": cache.misses,
        "cache_hits": cache.hits,
        "families": sorted({r["action_family"] for r in transitions}),
        "probes": probes,
        "max_bust_calibration_error_cm": max_bust_err,
        "realized_source": "panel_geometry_after_minus_before",
        "note": "FIT-100K images were not downloaded. Vision samples are GarmentCode pattern drawings.",
        "paths": {
            "transitions": str(trans_path),
            "vision": str(vis_path),
            "decisions": str(dec_path),
            "png_dir": str(out / "pattern_pngs"),
        },
        "runtime_s": time.time() - t0,
    }
    (out / "lattice_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
