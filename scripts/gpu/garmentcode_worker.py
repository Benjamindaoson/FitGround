#!/usr/bin/env python3
"""Flux-env GarmentCode worker: pattern mutation, measurement, optional Warp sim."""
import argparse
import copy
import hashlib
import json
import os
import shutil
import sys
import time
import traceback
from pathlib import Path

import numpy as np
import yaml

GC_ROOT = Path("/root/workspace/external/FitVTON-source-tree/GarmentCodeV2")
os.chdir(GC_ROOT)
sys.path.insert(0, str(GC_ROOT))

from assets.bodies.body_params import BodyParameters
from assets.garment_programs.meta_garment import MetaGarment


DESIGN_PATH = GC_ROOT / "assets/design_params/t-shirt.yaml"
BODY_PATH = GC_ROOT / "assets/bodies/mean_all.yaml"
SIM_PROPS = GC_ROOT / "assets/Sim_props/default_sim_props.yaml"

TORSO_PANELS = ("left_ftorso", "right_ftorso", "left_btorso", "right_btorso")
SLEEVE_PANELS = ("left_sleeve_f", "left_sleeve_b", "right_sleeve_f", "right_sleeve_b")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_design():
    design = yaml.safe_load(DESIGN_PATH.read_text())["design"]
    design.setdefault("shirt", {})
    design["shirt"].setdefault("tucked_in", {"v": False})
    design["shirt"].setdefault("openfront", {"v": False})
    return design


def panel_span(panel):
    verts = np.asarray(panel["vertices"], dtype=float)
    dx = float(verts[:, 0].max() - verts[:, 0].min())
    dy = float(verts[:, 1].max() - verts[:, 1].min())
    return dx, dy


def measure_specification(spec_path):
    spec = json.loads(Path(spec_path).read_text())
    panels = spec["pattern"]["panels"]
    torso_dx = []
    torso_dy = []
    missing = [name for name in TORSO_PANELS if name not in panels]
    for name in TORSO_PANELS:
        if name not in panels:
            continue
        dx, dy = panel_span(panels[name])
        torso_dx.append(dx)
        torso_dy.append(dy)
    sleeve_dy = []
    sleeve_dx = []
    for name in SLEEVE_PANELS:
        if name not in panels:
            continue
        dx, dy = panel_span(panels[name])
        sleeve_dx.append(dx)
        sleeve_dy.append(dy)
    bust = float(sum(torso_dx)) if torso_dx else None
    waist = bust
    length = float(np.mean(torso_dy)) if torso_dy else None
    # Sleeve length is constructed along panel X in GarmentCode sleeves.py, not Y.
    sleeve_length = float(np.mean(sleeve_dx)) if sleeve_dx else None
    # Shoulder seam proxy: top (max-y) edge span of front torso panels, doubled.
    shoulder = None
    top_spans = []
    for name in ("left_ftorso", "right_ftorso"):
        if name not in panels:
            continue
        verts = np.asarray(panels[name]["vertices"], dtype=float)
        ymax = verts[:, 1].max()
        top = verts[np.abs(verts[:, 1] - ymax) < 1e-6]
        if len(top) >= 2:
            top_spans.append(float(top[:, 0].max() - top[:, 0].min()))
        else:
            top_spans.append(float(verts[:, 0].max() - verts[:, 0].min()))
    if top_spans:
        shoulder = float(sum(top_spans))
    return {
        "bust_circumference_cm": bust,
        "waist_cm": waist,
        "length_cm": length,
        "sleeve_length_cm": sleeve_length,
        "shoulder_width_cm": shoulder,
        "torso_panel_dx": {n: panel_span(panels[n])[0] for n in TORSO_PANELS if n in panels},
        "torso_panel_dy": {n: panel_span(panels[n])[1] for n in TORSO_PANELS if n in panels},
        "sleeve_panel_dy": {n: panel_span(panels[n])[1] for n in SLEEVE_PANELS if n in panels},
        "panel_names": list(panels),
        "missing_torso_panels": missing,
        "spec_sha256": sha256_file(spec_path),
    }


def set_design_param(design, dotted_name, value):
    """Set design['shirt']['width']['v'] from a name like 'shirt.width'."""
    cur = design
    parts = dotted_name.split(".")
    for part in parts:
        cur = cur[part]
    cur["v"] = value


def generate_pattern(width_v, out_dir, tag, body_path=None, extra_params=None):
    body = BodyParameters(str(body_path or BODY_PATH))
    design = load_design()
    before = copy.deepcopy(design)
    design["shirt"]["width"]["v"] = float(width_v)
    if extra_params:
        for name, value in extra_params.items():
            if name in ("shirt.width", "width"):
                continue
            set_design_param(design, name, value)
    piece = MetaGarment("t-shirt", body, design)
    pattern = piece.assembly()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    folder = pattern.serialize(
        out_dir,
        tag="_" + tag,
        to_subfolder=True,
        with_3d=False,
        with_text=False,
        view_ids=False,
        with_printable=False,
    )
    folder = Path(folder)
    specs = list(folder.glob("*_specification.json"))
    if not specs:
        raise FileNotFoundError("pattern serialize produced no specification json")
    spec = specs[0]
    meas = measure_specification(spec)
    named = {
        "shirt.width.v": design["shirt"]["width"]["v"],
        "shirt.length.v": design["shirt"]["length"]["v"],
        "shirt.flare.v": design["shirt"]["flare"]["v"],
        "sleeve.length.v": design.get("sleeve", {}).get("length", {}).get("v"),
    }
    named_before = {
        "shirt.width.v": before["shirt"]["width"]["v"],
        "shirt.length.v": before["shirt"]["length"]["v"],
        "shirt.flare.v": before["shirt"]["flare"]["v"],
        "sleeve.length.v": before.get("sleeve", {}).get("length", {}).get("v"),
    }
    return {
        "folder": str(folder),
        "specification": str(spec),
        "self_intersecting": bool(piece.is_self_intersecting()),
        "body_bust_cm": float(body["bust"]),
        "body_waist_cm": float(body["waist"]),
        "body_shoulder_w_cm": float(body["shoulder_w"]),
        "named_pattern_parameters_before": named_before,
        "named_pattern_parameters_after": named,
        "measurements": meas,
        "design_path": str(DESIGN_PATH),
        "body_path": str(BODY_PATH),
    }


def run_physics(spec_path, out_dir, tag, max_steps=400, do_render=False, body_name="mean_all", sim_props_path=None):
    from pygarment.meshgen.boxmeshgen import BoxMesh
    from pygarment.meshgen.simulation import run_sim
    import pygarment.data_config as data_config
    from pygarment.meshgen.sim_config import PathCofig

    t0 = time.time()
    props = data_config.Properties(str(sim_props_path or SIM_PROPS))
    props["sim"]["config"]["max_sim_steps"] = int(max_steps)
    props["sim"]["config"]["optimize_storage"] = True
    props.set_section_stats(
        "sim",
        fails={},
        sim_time={},
        spf={},
        fin_frame={},
        body_collisions={},
        self_collisions={},
    )
    props.set_section_stats("render", render_time={})
    spec_path = Path(spec_path)
    garment_name, _, _ = spec_path.stem.rpartition("_")
    sys_props = data_config.Properties("./system.json")
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    paths = PathCofig(
        in_element_path=spec_path.parent,
        out_path=str(out_path),
        in_name=garment_name,
        out_name=tag,
        body_name=body_name,
        smpl_body=False,
        add_timestamp=False,
        system_path="./system.json",
    )
    garment_box_mesh = BoxMesh(paths.in_g_spec, props["sim"]["config"]["resolution_scale"])
    garment_box_mesh.load()
    garment_box_mesh.serialize(paths, store_panels=True, uv_config=props["render"]["config"]["uv_texture"])
    props.serialize(paths.element_sim_props)
    render_error = None
    sim_error = None
    try:
        run_sim(
            garment_box_mesh.name,
            props,
            paths,
            save_v_norms=False,
            store_usd=False,
            optimize_storage=False,
            verbose=True,
        )
    except Exception as exc:
        sim_error = f"{type(exc).__name__}: {exc}"
    render_status = "NOT_RUN"
    render_files = []
    if do_render and sim_error is None:
        try:
            from pygarment.meshgen.render.pythonrender import render_images
            render_images(paths, None, None, props["render"]["config"])
            render_status = "RENDERED"
        except Exception as exc:
            render_error = f"{type(exc).__name__}: {exc}"
            render_status = "FAILED"
    sim_obj = Path(paths.g_sim)
    box_obj = Path(paths.g_box_mesh)
    renders = list(Path(paths.out_el).glob("*render*.png"))
    render_files = [str(p) for p in renders]
    if renders and render_status == "NOT_RUN":
        render_status = "RENDERED"
    status = "SIMULATED" if sim_obj.exists() and sim_error is None else "FAILED"
    result = {
        "simulation_status": status,
        "render_status": render_status,
        "sim_error": sim_error,
        "render_error": render_error,
        "runtime_s": time.time() - t0,
        "max_sim_steps": int(max_steps),
        "output_dir": str(paths.out_el),
        "sim_mesh": str(sim_obj) if sim_obj.exists() else None,
        "box_mesh": str(box_obj) if box_obj.exists() else None,
        "render_files": render_files,
        "sim_mesh_sha256": sha256_file(sim_obj) if sim_obj.exists() else None,
        "box_mesh_sha256": sha256_file(box_obj) if box_obj.exists() else None,
    }
    if sim_error:
        result["traceback"] = traceback.format_exc()
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--action-family", default="bust_circumference_delta_cm")
    parser.add_argument("--intended-delta-cm", type=float, required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--physics", action="store_true")
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--max-sim-steps", type=int, default=400)
    parser.add_argument("--baseline-width", type=float, default=None)
    args = parser.parse_args()
    np.random.seed(args.seed)
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    payload = {
        "action_family": args.action_family,
        "intended_delta_cm": args.intended_delta_cm,
        "verification_status": "NOT_VERIFIED",
        "error": None,
    }
    try:
        if args.action_family != "bust_circumference_delta_cm":
            raise ValueError("worker currently implements bust_circumference_delta_cm only")
        body = BodyParameters(str(BODY_PATH))
        body_bust = float(body["bust"])
        design = load_design()
        baseline_width = args.baseline_width if args.baseline_width is not None else float(design["shirt"]["width"]["v"])
        # width.v is a multiplier of body bust; +1 cm garment bust => +1/body_bust in parameter
        param_delta = float(args.intended_delta_cm) / body_bust
        width_v = baseline_width + param_delta
        base = generate_pattern(baseline_width, out / "patterns", args.tag + "_base")
        mut = generate_pattern(width_v, out / "patterns", args.tag + "_mut")
        realized = mut["measurements"]["bust_circumference_cm"] - base["measurements"]["bust_circumference_cm"]
        payload.update(
            {
                "state_id": "tshirt_mean_all_baseline",
                "action_id": args.tag,
                "parameter_name": "shirt.width.v",
                "baseline_width_v": baseline_width,
                "mutated_width_v": width_v,
                "parameter_delta": param_delta,
                "body_bust_cm": body_bust,
                "named_pattern_parameters_before": base["named_pattern_parameters_after"],
                "named_pattern_parameters_after": mut["named_pattern_parameters_after"],
                "garment_measurement_before": base["measurements"],
                "garment_measurement_after": mut["measurements"],
                "realized_delta_cm": realized,
                "calibration_error_cm": abs(realized - args.intended_delta_cm) if realized is not None else None,
                "waist_delta_cm": (
                    mut["measurements"]["waist_cm"] - base["measurements"]["waist_cm"]
                    if mut["measurements"]["waist_cm"] is not None
                    else None
                ),
                "shoulder_delta_cm": (
                    mut["measurements"]["shoulder_width_cm"] - base["measurements"]["shoulder_width_cm"]
                    if mut["measurements"]["shoulder_width_cm"] is not None
                    else None
                ),
                "sleeve_delta_cm": (
                    mut["measurements"]["sleeve_length_cm"] - base["measurements"]["sleeve_length_cm"]
                    if mut["measurements"]["sleeve_length_cm"] is not None
                    else None
                ),
                "length_delta_cm": (
                    mut["measurements"]["length_cm"] - base["measurements"]["length_cm"]
                    if mut["measurements"]["length_cm"] is not None
                    else None
                ),
                "baseline_folder": base["folder"],
                "mutated_folder": mut["folder"],
                "baseline_spec": base["specification"],
                "mutated_spec": mut["specification"],
                "self_intersecting": mut["self_intersecting"],
                "simulation_status": "NOT_RUN",
                "render_status": "NOT_RUN",
            }
        )
        if args.physics:
            phys = run_physics(
                mut["specification"],
                out / "sim",
                args.tag,
                max_steps=args.max_sim_steps,
                do_render=args.render,
            )
            payload["physics"] = phys
            payload["simulation_status"] = phys["simulation_status"]
            payload["render_status"] = phys["render_status"]
            payload["mesh"] = phys.get("sim_mesh")
            payload["render"] = phys.get("render_files")
        payload["verification_status"] = (
            "VERIFIED" if payload["realized_delta_cm"] is not None else "NOT_VERIFIED"
        )
        if payload["simulation_status"] == "FAILED":
            payload["verification_status"] = "FAILED"
    except Exception as exc:
        payload["error"] = f"{type(exc).__name__}: {exc}"
        payload["traceback"] = traceback.format_exc()
        payload["verification_status"] = "FAILED"
    payload["runtime_s"] = time.time() - t0
    payload["seed"] = args.seed
    payload["source_hashes"] = {
        "t-shirt.yaml": sha256_file(DESIGN_PATH),
        "mean_all.yaml": sha256_file(BODY_PATH),
        "worker.py": sha256_file(Path(__file__)),
    }
    out_json = out / f"{args.tag}.json"
    out_json.write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload, indent=2))
    return 0 if payload.get("error") is None else 1


if __name__ == "__main__":
    raise SystemExit(main())
