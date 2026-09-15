#!/usr/bin/env python3
"""Resume-only physics expansion for visual disambiguation. Does not regenerate lattice rows."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path("/root/workspace/projects/FitGround")
if not ROOT.exists():
    ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "gpu"))

from fitground.physics.outcomes import cloth_body_outcomes  # noqa: E402
from fitground.decision.engine import physics_utility  # noqa: E402
import garmentcode_worker as gcw  # noqa: E402

GC = Path("/root/workspace/external/FitVTON-source-tree/GarmentCodeV2")
BODY_OBJ = {
    "mean_all": GC / "assets/bodies/mean_all.obj",
    "mean_female": GC / "assets/bodies/mean_female.obj",
    "mean_male": GC / "assets/bodies/mean_male.obj",
}
SIM_PROPS = {
    "default": GC / "assets/Sim_props/default_sim_props.yaml",
    "stiff": GC / "assets/Sim_props/mid_bending.yaml",
    "soft": GC / "assets/Sim_props/minimal_bending.yaml",
}
OUT = ROOT / "artifacts" / "hero"


def dump(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def load_jsonl(path: Path):
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def spec_exists(path) -> bool:
    return isinstance(path, str) and Path(path).exists()


def short_tag(*parts) -> str:
    raw = "|".join(str(p) for p in parts)
    return "vd" + hashlib.sha1(raw.encode()).hexdigest()[:14]


def run_one(spec, tag, body_name, material, max_steps, do_render):
    out_dir = OUT / "sim_vd" / material / tag
    marker = out_dir / "physics.json"
    if marker.exists():
        prev = json.loads(marker.read_text(encoding="utf-8"))
        if prev.get("simulation_status") == "SIMULATED" and prev.get("fit_outcomes"):
            return prev, True
    phys = gcw.run_physics(
        spec,
        out_dir,
        tag,
        max_steps=max_steps,
        do_render=do_render,
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
    phys["tag"] = tag
    dump(marker, phys)
    return phys, False


def select_states(transitions, n_states: int):
    """Diverse (body, garment measurements) states that have a +2 cm bust after-spec."""
    by_state = {}
    for row in transitions:
        if row.get("action_family") != "bust_circumference_delta_cm":
            continue
        sid = row["state_id"]
        by_state.setdefault(sid, {"before": row, "plus2": None, "plus3": None})
        intended = round(float(row["intended_delta_cm"]), 2)
        if intended == 2.0:
            by_state[sid]["plus2"] = row
        if intended == 3.0:
            by_state[sid]["plus3"] = row
    candidates = []
    for sid, pack in by_state.items():
        if pack["plus2"] is None:
            continue
        before = pack["before"]
        if not spec_exists(before.get("spec_before")):
            continue
        if not spec_exists(pack["plus2"].get("spec_after")):
            continue
        gb = before["garment_measurement_before"]["bust_circumference_cm"]
        candidates.append(
            {
                "state_id": sid,
                "body_name": before["body_name"],
                "garment_bust_cm": gb,
                "body_bust_cm": before["body_bust_cm"],
                "spec_now": before["spec_before"],
                "spec_plus2": pack["plus2"]["spec_after"],
                "spec_plus3": (pack["plus3"] or {}).get("spec_after") if pack["plus3"] else None,
                "png": before.get("png_before"),
                "sleeve_delta_plus2": pack["plus2"].get("sleeve_delta_cm") or 0.0,
                "length_delta_plus2": pack["plus2"].get("length_delta_cm") or 0.0,
                "waist_delta_plus2": pack["plus2"].get("waist_delta_cm") or 0.0,
            }
        )
    # spread across bodies and bust bins
    candidates.sort(key=lambda c: (c["body_name"], c["garment_bust_cm"], c["state_id"]))
    picked = []
    used_bins = set()
    for c in candidates:
        bin_id = (c["body_name"], round(c["garment_bust_cm"] / 2.0) * 2)
        if bin_id in used_bins and len(picked) < n_states:
            continue
        used_bins.add(bin_id)
        picked.append(c)
        if len(picked) >= n_states:
            break
    if len(picked) < n_states:
        for c in candidates:
            if c in picked:
                continue
            picked.append(c)
            if len(picked) >= n_states:
                break
    return picked


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-states", type=int, default=28)
    parser.add_argument("--max-sim-steps", type=int, default=220)
    parser.add_argument("--materials", default="default,stiff")
    parser.add_argument("--render-first", type=int, default=16)
    args = parser.parse_args()
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    lattice_path = OUT / "correction_lattice_v0.2.jsonl"
    transitions = load_jsonl(lattice_path)
    states = select_states(transitions, args.max_states)
    materials = [m.strip() for m in args.materials.split(",") if m.strip()]
    plan = []
    for i, st in enumerate(states):
        for mat in materials:
            plan.append((st, mat, 0.0, st["spec_now"], "now"))
            plan.append((st, mat, 2.0, st["spec_plus2"], "plus2"))
    print(f"PLAN n_states={len(states)} n_sims={len(plan)}", flush=True)
    rows = []
    n_resume = 0
    n_fail = 0
    n_new = 0
    for i, (st, mat, edit, spec, edit_name) in enumerate(plan):
        tag = short_tag(st["state_id"], mat, edit_name)
        do_render = (edit_name == "now") or (i < args.render_first)
        print(f"PHYSICS {i+1}/{len(plan)} {tag} {st['body_name']} {mat} edit={edit}", flush=True)
        try:
            phys, resumed = run_one(spec, tag, st["body_name"], mat, args.max_sim_steps, do_render)
        except Exception as exc:
            phys = {
                "simulation_status": "FAILED",
                "error": f"{type(exc).__name__}: {exc}",
                "tag": tag,
                "material": mat,
                "body_name": st["body_name"],
            }
            resumed = False
            n_fail += 1
        if resumed:
            n_resume += 1
        elif phys.get("simulation_status") == "SIMULATED":
            n_new += 1
        elif phys.get("simulation_status") != "SIMULATED":
            n_fail += 1
        phys["state_id"] = st["state_id"]
        phys["intended_delta_cm"] = edit
        phys["edit_name"] = edit_name
        phys["garment_bust_cm"] = st["garment_bust_cm"]
        phys["body_bust_cm"] = st["body_bust_cm"]
        phys["pattern_png"] = st["png"]
        phys["side_effect_cm"] = abs(st["sleeve_delta_plus2"]) + abs(st["length_delta_plus2"]) if edit else 0.0
        fo = phys.get("fit_outcomes")
        phys["utility"] = physics_utility(fo, edit, side_effect_cm=phys["side_effect_cm"]) if fo else None
        rows.append(phys)
        if (i + 1) % 4 == 0:
            dump(OUT / "physics_vd_partial.json", {"n": len(rows), "rows": rows})
    dump(OUT / "physics_vd.json", rows)
    summary = {
        "n_states": len(states),
        "n_plan": len(plan),
        "n_rows": len(rows),
        "n_ok": sum(1 for r in rows if r.get("simulation_status") == "SIMULATED"),
        "n_failed": n_fail,
        "n_resumed": n_resume,
        "n_new": n_new,
        "runtime_s": time.time() - t0,
        "body_kind": "SYNTHETIC_BODY_PHYSICS",
    }
    dump(OUT / "physics_vd_summary.json", summary)
    print(json.dumps(summary, indent=2), flush=True)
    return 0 if summary["n_ok"] > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
