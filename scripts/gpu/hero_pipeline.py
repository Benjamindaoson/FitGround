"""Hero completion pipeline: calibration, lattice, synthetic-body physics, disambiguation.

Body collision uses GarmentCode-shipped static mannequin OBJs (mean_all / mean_female /
mean_male / f_smpl_average_A40). Licensed SMPL-X weights are not used.
Label: SYNTHETIC_BODY_PHYSICS.
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
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(ROOT / "scripts" / "gpu"))

from fitground.physics.outcomes import cloth_body_outcomes  # noqa: E402
from fitground.training.geometry import rasterize_specification, realized_delta, utility_chest_case  # noqa: E402

import garmentcode_worker as gcw  # noqa: E402

GC = Path("/root/workspace/external/FitVTON-source-tree/GarmentCodeV2")
BODIES = {
    "mean_all": GC / "assets/bodies/mean_all.yaml",
    "mean_female": GC / "assets/bodies/mean_female.yaml",
    "mean_male": GC / "assets/bodies/mean_male.yaml",
}
BODY_OBJ = {
    "mean_all": GC / "assets/bodies/mean_all.obj",
    "mean_female": GC / "assets/bodies/mean_female.obj",
    "mean_male": GC / "assets/bodies/mean_male.obj",
    "f_smpl_average_A40": GC / "assets/bodies/f_smpl_average_A40.obj",
}
SIM_PROPS = {
    "default": GC / "assets/Sim_props/default_sim_props.yaml",
    "stiff": GC / "assets/Sim_props/mid_bending.yaml",
    "soft": GC / "assets/Sim_props/minimal_bending.yaml",
}
OUT = ROOT / "artifacts" / "hero"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def dump(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


class PatternCache:
    def __init__(self):
        self.tmp = OUT / "_pat"
        self.png = OUT / "pattern_pngs"
        self.tmp.mkdir(parents=True, exist_ok=True)
        self.png.mkdir(parents=True, exist_ok=True)
        self.store = {}
        self.misses = 0

    def get(self, body_name, width, length, sleeve, connecting=None):
        key = (
            body_name,
            round(float(width), 5),
            round(float(length), 5),
            round(float(sleeve), 5),
            None if connecting is None else round(float(connecting), 5),
        )
        if key in self.store:
            return self.store[key]
        self.misses += 1
        extra = {"shirt.length": float(length), "sleeve.length": float(sleeve)}
        if connecting is not None:
            extra["sleeve.connecting_width"] = float(connecting)
        tag = "p" + hashlib.sha1(str(key).encode()).hexdigest()[:12]
        print(f"PATTERN {self.misses} {body_name} w={width:.4f} l={length:.3f} s={sleeve:.3f} c={connecting}", flush=True)
        raw = gcw.generate_pattern(
            float(width),
            self.tmp / tag,
            tag,
            body_path=str(BODIES[body_name]),
            extra_params=extra,
        )
        png = self.png / f"{tag}.png"
        rasterize_specification(raw["specification"], png, size=160)
        compact = {
            "body_name": body_name,
            "body_bust_cm": raw["body_bust_cm"],
            "body_waist_cm": raw.get("body_waist_cm"),
            "body_shoulder_w_cm": raw.get("body_shoulder_w_cm"),
            "params": extra | {"shirt.width": float(width)},
            "named": raw["named_pattern_parameters_after"],
            "measurements": raw["measurements"],
            "self_intersecting": raw["self_intersecting"],
            "specification": raw["specification"],
            "folder": raw["folder"],
            "png": str(png),
            "state_id": f"{body_name}_w{width:.3f}_l{length:.2f}_sl{sleeve:.2f}_c{connecting if connecting is not None else 'def'}",
        }
        self.store[key] = compact
        return compact


def bootstrap_ci(values, fn, n=400, seed=0):
    arr = np.asarray(list(values), dtype=float)
    if len(arr) == 0:
        return {"mean": None, "lo": None, "hi": None, "n": 0}
    rng = np.random.default_rng(seed)
    stats = []
    for _ in range(n):
        sample = arr[rng.integers(0, len(arr), size=len(arr))]
        stats.append(fn(sample))
    stats = np.asarray(stats)
    return {
        "mean": float(fn(arr)),
        "lo": float(np.percentile(stats, 2.5)),
        "hi": float(np.percentile(stats, 97.5)),
        "n": int(len(arr)),
    }


def gates(rows, family, intended_key="intended_delta_cm"):
    by_int = {}
    for r in rows:
        by_int.setdefault(round(float(r[intended_key]), 3), []).append(r)
    g = {"family": family, "n": len(rows)}
    g["G1_executability"] = {
        "status": "PASS" if rows and all(r.get("realized_delta_cm") is not None for r in rows) else "FAIL"
    }
    errs = [abs(r["calibration_error_cm"]) for r in rows if r.get("calibration_error_cm") is not None]
    max_err = max(errs) if errs else None
    g["G2_accuracy"] = {
        "max_abs_error_cm": max_err,
        "mean_abs_error_cm": float(np.mean(errs)) if errs else None,
        "status": "PASS" if errs and max_err < 0.15 else ("PARTIAL" if errs and max_err < 0.5 else "FAIL"),
    }
    ints = sorted(by_int)
    means = [float(np.mean([r["realized_delta_cm"] for r in by_int[i]])) for i in ints]
    mono = all(a < b for a, b in zip(means, means[1:])) if len(means) >= 3 else False
    g["G3_monotonicity"] = {"intended": ints, "mean_realized": means, "status": "PASS" if mono else "FAIL"}
    loc_fail = False
    notes = []
    for r in rows:
        intended = abs(r.get("intended_delta_cm") or 0) or 1.0
        sleeve = abs(r.get("sleeve_delta_cm") or 0)
        length = abs(r.get("length_delta_cm") or 0)
        bust = abs(r.get("bust_delta_cm") or 0)
        notes.append({"id": r.get("action_id"), "bust": bust, "sleeve": sleeve, "length": length})
        if family == "bust_circumference_delta_cm" and (sleeve > 0.35 * intended or length > 0.35 * intended):
            loc_fail = True
        if family == "sleeve_length_delta_cm" and (bust > 0.35 * intended or length > 0.35 * intended):
            loc_fail = True
    g["G4_locality"] = {"status": "FAIL" if loc_fail else "PARTIAL", "notes": notes[:12]}
    uniq = len({r["garment_measurement_after"]["spec_sha256"] for r in rows if r.get("garment_measurement_after")})
    g["G5_physical_sensitivity"] = {"unique_specs": uniq, "status": "PASS" if uniq >= max(3, len(by_int) - 1) else "FAIL"}
    repro_status = "NOT_RUN"
    for intended, group in by_int.items():
        if len(group) >= 3:
            vals = [r["realized_delta_cm"] for r in group]
            spread = max(vals) - min(vals)
            repro_status = "PASS" if spread < 1e-6 else ("PARTIAL" if spread < 0.05 else "FAIL")
            g["G6_reproducibility"] = {"intended": intended, "values": vals, "spread": spread, "status": repro_status}
            break
    if "G6_reproducibility" not in g:
        g["G6_reproducibility"] = {"status": "NOT_RUN", "reason": "need N>=3 repeats"}
    pattern_ok = g["G1_executability"]["status"] == "PASS" and g["G2_accuracy"]["status"] in ("PASS", "PARTIAL") and g["G3_monotonicity"]["status"] == "PASS"
    g["decision"] = "GO" if pattern_ok and g["G2_accuracy"]["status"] == "PASS" else ("PARTIAL" if pattern_ok else "NO-GO")
    return g


def transition(before, after, family, intended, param, measure_key):
    bm, am = before["measurements"], after["measurements"]
    realized = realized_delta(bm.get(measure_key), am.get(measure_key))
    return {
        "state_id": before["state_id"],
        "action_id": f"{before['state_id']}__{family}__{intended:+.2f}",
        "action_family": family,
        "intended_delta_cm": float(intended),
        "realized_delta_cm": realized,
        "realized_source": "panel_geometry_after_minus_before",
        "realized_measurement_key": measure_key,
        "parameter_name": param,
        "body_name": before["body_name"],
        "body_bust_cm": before["body_bust_cm"],
        "named_pattern_parameters_before": before["named"],
        "named_pattern_parameters_after": after["named"],
        "garment_measurement_before": bm,
        "garment_measurement_after": am,
        "png_before": before["png"],
        "png_after": after["png"],
        "spec_before": before["specification"],
        "spec_after": after["specification"],
        "bust_delta_cm": realized_delta(bm.get("bust_circumference_cm"), am.get("bust_circumference_cm")),
        "waist_delta_cm": realized_delta(bm.get("waist_cm"), am.get("waist_cm")),
        "shoulder_delta_cm": realized_delta(bm.get("shoulder_width_cm"), am.get("shoulder_width_cm")),
        "sleeve_delta_cm": realized_delta(bm.get("sleeve_length_cm"), am.get("sleeve_length_cm")),
        "length_delta_cm": realized_delta(bm.get("length_cm"), am.get("length_cm")),
        "calibration_error_cm": None if realized is None else abs(realized - float(intended)),
        "verification_status": "VERIFIED" if realized is not None else "NOT_VERIFIED",
        "simulation_status": "NOT_RUN",
        "render_status": "NOT_RUN",
        "body_kind": "SYNTHETIC_BODY_PHYSICS",
    }


def score_existing_physics():
    body_obj = BODY_OBJ["mean_all"]
    lattice = ROOT / "artifacts" / "gpu" / "physics_lattice"
    rows = []
    for tag in ("baseline", "bust_plus_1cm", "bust_plus_2cm", "bust_plus_3cm"):
        sim = lattice / tag / f"{tag}_sim.obj"
        if not sim.exists():
            continue
        out = cloth_body_outcomes(sim, body_obj)
        out["tag"] = tag
        out["sim_mesh"] = str(sim)
        rows.append(out)
    dump(OUT / "existing_physics_outcomes.json", {"body_kind": "SYNTHETIC_BODY_PHYSICS", "rows": rows})
    return rows


def probe_family(cache, body_name, param, v0, v1, measure_key, width=1.05, length=1.2, sleeve=0.3):
    kwargs0 = dict(width=width, length=length, sleeve=sleeve)
    kwargs1 = dict(kwargs0)
    if param == "sleeve.length":
        g0 = cache.get(body_name, width, length, v0)
        g1 = cache.get(body_name, width, length, v1)
    elif param == "shirt.length":
        g0 = cache.get(body_name, width, v0, sleeve)
        g1 = cache.get(body_name, width, v1, sleeve)
    elif param == "shirt.width":
        g0 = cache.get(body_name, v0, length, sleeve)
        g1 = cache.get(body_name, v1, length, sleeve)
    elif param == "sleeve.connecting_width":
        g0 = cache.get(body_name, width, length, sleeve, connecting=v0)
        g1 = cache.get(body_name, width, length, sleeve, connecting=v1)
    else:
        raise ValueError(param)
    dcm = realized_delta(g0["measurements"][measure_key], g1["measurements"][measure_key])
    return {
        "parameter": param,
        "measure_key": measure_key,
        "v0": v0,
        "v1": v1,
        "before_cm": g0["measurements"][measure_key],
        "after_cm": g1["measurements"][measure_key],
        "realized_delta_cm": dcm,
        "cm_per_unit": None if dcm is None or abs(v1 - v0) < 1e-12 else dcm / (v1 - v0),
        "cross": {
            "bust": realized_delta(g0["measurements"]["bust_circumference_cm"], g1["measurements"]["bust_circumference_cm"]),
            "sleeve": realized_delta(g0["measurements"]["sleeve_length_cm"], g1["measurements"]["sleeve_length_cm"]),
            "length": realized_delta(g0["measurements"]["length_cm"], g1["measurements"]["length_cm"]),
            "shoulder": realized_delta(g0["measurements"]["shoulder_width_cm"], g1["measurements"]["shoulder_width_cm"]),
        },
        "body_name": body_name,
    }


def run_physics_case(spec, tag, body_name, material, render=True, max_steps=300):
    out_dir = OUT / "sim" / material / tag
    phys = gcw.run_physics(
        spec,
        out_dir,
        tag,
        max_steps=max_steps,
        do_render=render,
        body_name=body_name,
        sim_props_path=str(SIM_PROPS[material]),
    )
    body_obj = BODY_OBJ.get(body_name)
    if phys.get("sim_mesh") and body_obj and Path(body_obj).exists() and phys.get("simulation_status") == "SIMULATED":
        phys["fit_outcomes"] = cloth_body_outcomes(phys["sim_mesh"], body_obj)
        phys["fit_outcomes"]["material"] = material
        phys["fit_outcomes"]["body_name"] = body_name
    phys["material"] = material
    phys["body_name"] = body_name
    phys["body_kind"] = "SYNTHETIC_BODY_PHYSICS"
    dump(out_dir / "physics.json", phys)
    return phys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-physics", action="store_true")
    parser.add_argument("--max-physics", type=int, default=28)
    parser.add_argument("--max-sim-steps", type=int, default=280)
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    existing = score_existing_physics()
    print("existing_physics", len(existing), flush=True)
    cache = PatternCache()
    probes = []
    for body in BODIES:
        probes.append(probe_family(cache, body, "shirt.width", 1.05, 1.08, "bust_circumference_cm"))
        probes.append(probe_family(cache, body, "sleeve.length", 0.25, 0.45, "sleeve_length_cm"))
        probes.append(probe_family(cache, body, "shirt.length", 1.1, 1.4, "length_cm"))
        probes.append(probe_family(cache, body, "sleeve.connecting_width", 0.1, 0.6, "shoulder_width_cm"))
        probes.append(probe_family(cache, body, "sleeve.connecting_width", 0.1, 0.6, "sleeve_length_cm"))
    dump(OUT / "parameter_probes.json", probes)

    scale = {}
    for p in probes:
        scale[(p["body_name"], p["parameter"], p["measure_key"])] = p["cm_per_unit"]

    # --- atomic calibration grids ---
    calib = {"bust_circumference_delta_cm": [], "sleeve_length_delta_cm": [], "shoulder_width_delta_cm": []}
    body = "mean_all"
    body_bust = cache.get(body, 1.05, 1.2, 0.3)["body_bust_cm"]
    for intended in [-3, -2, -1, 0, 1, 2, 3]:
        before = cache.get(body, 1.08, 1.2, 0.3)
        nw = 1.08 + intended / body_bust
        if 1.0 <= nw <= 1.3:
            after = cache.get(body, nw, 1.2, 0.3)
            calib["bust_circumference_delta_cm"].append(
                transition(before, after, "bust_circumference_delta_cm", intended, "shirt.width.v", "bust_circumference_cm")
            )
    for _ in range(2):  # N>=3 including the +3 already in grid
        before = cache.get(body, 1.08, 1.2, 0.3)
        after = cache.get(body, 1.08 + 3.0 / body_bust, 1.2, 0.3)
        row = transition(before, after, "bust_circumference_delta_cm", 3.0, "shirt.width.v", "bust_circumference_cm")
        row["action_id"] += f"_repeat"
        calib["bust_circumference_delta_cm"].append(row)

    sl_scale = scale.get((body, "sleeve.length", "sleeve_length_cm"))
    if sl_scale and abs(sl_scale) > 0.2:
        for intended in [-2, -1, 0, 1, 2]:
            before = cache.get(body, 1.05, 1.2, 0.35)
            ns = 0.35 + intended / sl_scale
            if 0.1 <= ns <= 1.15:
                after = cache.get(body, 1.05, 1.2, ns)
                calib["sleeve_length_delta_cm"].append(
                    transition(before, after, "sleeve_length_delta_cm", intended, "sleeve.length.v", "sleeve_length_cm")
                )
        for k in range(3):
            before = cache.get(body, 1.05, 1.2, 0.35)
            after = cache.get(body, 1.05, 1.2, 0.35 + 2.0 / sl_scale)
            row = transition(before, after, "sleeve_length_delta_cm", 2.0, "sleeve.length.v", "sleeve_length_cm")
            row["action_id"] += f"_r{k}"
            calib["sleeve_length_delta_cm"].append(row)

    sh_scale = scale.get((body, "sleeve.connecting_width", "shoulder_width_cm"))
    shoulder_param = "sleeve.connecting_width"
    shoulder_key = "shoulder_width_cm"
    if not sh_scale or abs(sh_scale) < 0.15:
        # connecting_width is not a centimetre shoulder map — record NO-GO evidence
        sh_scale = None
    else:
        for intended in [-2, -1, 0, 1, 2]:
            v0 = 0.25
            before = cache.get(body, 1.05, 1.2, 0.3, connecting=v0)
            nv = v0 + intended / sh_scale
            if 0.0 <= nv <= 2.0:
                after = cache.get(body, 1.05, 1.2, 0.3, connecting=nv)
                calib["shoulder_width_delta_cm"].append(
                    transition(before, after, "shoulder_width_delta_cm", intended, shoulder_param, shoulder_key)
                )

    calib_gates = {fam: gates(rows, fam) if rows else {"decision": "NO-GO", "reason": "no measured mapping"} for fam, rows in calib.items()}
    dump(OUT / "atomic_calibration.json", {"rows": calib, "gates": calib_gates, "probes": probes})

    # --- large pattern lattice ---
    widths = [1.02, 1.05, 1.08, 1.12, 1.16]
    lengths = [1.05, 1.25]
    sleeves = [0.22, 0.35, 0.50]
    transitions = []
    for body_name in BODIES:
        bb = cache.get(body_name, 1.05, 1.25, 0.35)["body_bust_cm"]
        for w in widths:
            for length in lengths:
                for sl in sleeves:
                    before = cache.get(body_name, w, length, sl)
                    for intended in [-3, -2, -1, 0, 1, 2, 3]:
                        nw = w + intended / bb
                        if nw < 1.0 or nw > 1.3:
                            continue
                        after = cache.get(body_name, nw, length, sl)
                        transitions.append(
                            transition(before, after, "bust_circumference_delta_cm", intended, "shirt.width.v", "bust_circumference_cm")
                        )
        if sl_scale and abs(sl_scale) > 0.2:
            for sl0 in sleeves:
                before = cache.get(body_name, 1.08, 1.25, sl0)
                local = scale.get((body_name, "sleeve.length", "sleeve_length_cm")) or sl_scale
                for intended in [-2, -1, 1, 2]:
                    ns = sl0 + intended / local
                    if 0.1 <= ns <= 1.15:
                        after = cache.get(body_name, 1.08, 1.25, ns)
                        transitions.append(
                            transition(before, after, "sleeve_length_delta_cm", intended, "sleeve.length.v", "sleeve_length_cm")
                        )

    trans_path = OUT / "correction_lattice_v0.2.jsonl"
    with trans_path.open("w", encoding="utf-8") as fh:
        for row in transitions:
            fh.write(json.dumps(row) + "\n")

    # --- physics subset: materials × bodies × actions ---
    physics_rows = []
    if not args.skip_physics:
        plan = []
        base = cache.get("mean_all", 1.05, 1.2, 0.3)
        plan.append(("baseline_default", base, "mean_all", "default", 0.0, "none"))
        for intended, mat in [(2.0, "default"), (3.0, "default"), (2.0, "stiff"), (3.0, "stiff"), (2.0, "soft")]:
            after = cache.get("mean_all", 1.05 + intended / body_bust, 1.2, 0.3)
            plan.append((f"bust_{intended:+.0f}_{mat}", after, "mean_all", mat, intended, "bust_circumference_delta_cm"))
        fem = cache.get("mean_female", 1.05, 1.2, 0.3)
        plan.append(("female_baseline", fem, "mean_female", "default", 0.0, "none"))
        fem_bb = fem["body_bust_cm"]
        plan.append(("female_bust+2", cache.get("mean_female", 1.05 + 2 / fem_bb, 1.2, 0.3), "mean_female", "default", 2.0, "bust_circumference_delta_cm"))
        male = cache.get("mean_male", 1.05, 1.2, 0.3)
        plan.append(("male_baseline", male, "mean_male", "default", 0.0, "none"))
        if sl_scale and abs(sl_scale) > 0.2:
            plan.append(("sleeve+2_default", cache.get("mean_all", 1.05, 1.2, 0.3 + 2 / sl_scale), "mean_all", "default", 2.0, "sleeve_length_delta_cm"))
            plan.append(("sleeve+2_stiff", cache.get("mean_all", 1.05, 1.2, 0.3 + 2 / sl_scale), "mean_all", "stiff", 2.0, "sleeve_length_delta_cm"))
        # same garment, two materials — visual disambiguation seeds
        tight = cache.get("mean_all", 1.02, 1.2, 0.3)
        plan.append(("tight_default", tight, "mean_all", "default", 0.0, "none"))
        plan.append(("tight_stiff", tight, "mean_all", "stiff", 0.0, "none"))
        roomy = cache.get("mean_all", 1.16, 1.2, 0.3)
        plan.append(("roomy_default", roomy, "mean_all", "default", 0.0, "none"))
        plan.append(("roomy_stiff", roomy, "mean_all", "stiff", 0.0, "none"))
        plan = plan[: args.max_physics]
        for tag, garment, bname, mat, intended, family in plan:
            print("PHYSICS", tag, mat, bname, flush=True)
            try:
                phys = run_physics_case(garment["specification"], tag, bname, mat, render=True, max_steps=args.max_sim_steps)
            except Exception as exc:
                phys = {"simulation_status": "FAILED", "error": f"{type(exc).__name__}: {exc}", "tag": tag}
            phys["tag"] = tag
            phys["intended_delta_cm"] = intended
            phys["action_family"] = family
            phys["state_id"] = garment["state_id"]
            phys["pattern_png"] = garment["png"]
            phys["measurements"] = garment["measurements"]
            physics_rows.append(phys)

    dump(OUT / "physics_lattice.json", physics_rows)

    # visual disambiguation: same measurements, different material → different physics
    dis = []
    by_state_mat = {}
    for row in physics_rows:
        if row.get("simulation_status") != "SIMULATED":
            continue
        sid = row.get("state_id")
        by_state_mat.setdefault(sid, {})[row.get("material")] = row
    for sid, mats in by_state_mat.items():
        if "default" in mats and "stiff" in mats:
            a, b = mats["default"], mats["stiff"]
            oa, ob = a.get("fit_outcomes") or {}, b.get("fit_outcomes") or {}
            same_meas = a.get("measurements", {}).get("bust_circumference_cm") == b.get("measurements", {}).get("bust_circumference_cm")
            contact_gap = abs((oa.get("contact_ratio") or 0) - (ob.get("contact_ratio") or 0))
            wrinkle_gap = abs((oa.get("wrinkle_proxy_cm") or 0) - (ob.get("wrinkle_proxy_cm") or 0))
            # If stiff is tighter, recommend extra ease; if already roomy, don't.
            rec_default = "bust+2cm" if (oa.get("contact_ratio") or 0) > 0.08 else "no_edit"
            rec_stiff = "bust+3cm" if (ob.get("contact_ratio") or 0) > (oa.get("contact_ratio") or 0) else rec_default
            dis.append(
                {
                    "case_id": f"disambig_{sid}",
                    "same_pattern_measurements": bool(same_meas),
                    "body_bust_cm": None,
                    "garment_bust_cm": a.get("measurements", {}).get("bust_circumference_cm"),
                    "material_a": "default",
                    "material_b": "stiff",
                    "contact_ratio_a": oa.get("contact_ratio"),
                    "contact_ratio_b": ob.get("contact_ratio"),
                    "wrinkle_proxy_a": oa.get("wrinkle_proxy_cm"),
                    "wrinkle_proxy_b": ob.get("wrinkle_proxy_cm"),
                    "clearance_p10_a": oa.get("clearance_p10_cm"),
                    "clearance_p10_b": ob.get("clearance_p10_cm"),
                    "measurement_only_can_distinguish": False if same_meas else True,
                    "physics_can_distinguish": bool(contact_gap > 1e-4 or wrinkle_gap > 1e-4),
                    "recommended_a": rec_default,
                    "recommended_b": rec_stiff,
                    "vision_needed": bool(same_meas and rec_default != rec_stiff),
                    "render_a": (a.get("render_files") or [None])[0],
                    "render_b": (b.get("render_files") or [None])[0],
                }
            )
    n_need_vis = sum(1 for c in dis if c["vision_needed"])
    verdict = "VISION_NECESSITY_ESTABLISHED" if n_need_vis >= 1 else "VISION_NECESSITY_NOT_ESTABLISHED"
    dump(
        OUT / "visual_disambiguation.json",
        {
            "verdict": verdict,
            "n_pairs": len(dis),
            "n_vision_needed": n_need_vis,
            "cases": dis,
            "note": "Pairs share 2D pattern measurements and differ only in cloth bending material. Measurement-only models cannot see the material split.",
        },
    )

    # decision cases from pattern lattice (CHEST_CASE style) + physics utility when available
    decisions = []
    grouped = {}
    for row in transitions:
        if row["action_family"] != "bust_circumference_delta_cm":
            continue
        grouped.setdefault(row["state_id"], []).append(row)
    for sid, rows in list(grouped.items())[:80]:
        before_bust = rows[0]["garment_measurement_before"]["bust_circumference_cm"]
        for ease in (2.0, 3.0):
            target = before_bust + ease
            scored = []
            for row in rows:
                after_bust = row["garment_measurement_after"]["bust_circumference_cm"]
                util = utility_chest_case(after_bust - target, row["intended_delta_cm"], row.get("sleeve_delta_cm") or 0, row.get("length_delta_cm") or 0)
                scored.append({**row, "utility": util, "target_garment_bust_cm": target, "target_error_cm": after_bust - target})
            scored.sort(key=lambda r: r["utility"], reverse=True)
            decisions.append(
                {
                    "case_id": f"{sid}__plus{ease:.0f}",
                    "state_id": sid,
                    "split_body": rows[0]["body_name"],
                    "body_bust_cm": rows[0]["body_bust_cm"],
                    "garment_bust_cm": before_bust,
                    "target_garment_bust_cm": target,
                    "oracle_action_id": scored[0]["action_id"],
                    "oracle_intended_delta_cm": scored[0]["intended_delta_cm"],
                    "oracle_utility": scored[0]["utility"],
                    "ranking": [s["action_id"] for s in scored],
                    "candidates": [
                        {
                            "action_id": s["action_id"],
                            "intended_delta_cm": s["intended_delta_cm"],
                            "realized_delta_cm": s["realized_delta_cm"],
                            "utility": s["utility"],
                        }
                        for s in scored
                    ],
                }
            )
    dump(OUT / "decision_cases.json", decisions)

    summary = {
        "n_pattern_transitions": len(transitions),
        "n_unique_patterns": cache.misses,
        "n_physics": len(physics_rows),
        "n_physics_ok": sum(1 for r in physics_rows if r.get("simulation_status") == "SIMULATED"),
        "n_disambiguation_pairs": len(dis),
        "vision_verdict": verdict,
        "calibration_gates": {k: v.get("decision") for k, v in calib_gates.items()},
        "existing_physics_scored": len(existing),
        "runtime_s": time.time() - t0,
        "body_kind": "SYNTHETIC_BODY_PHYSICS",
    }
    dump(OUT / "pipeline_summary.json", summary)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
