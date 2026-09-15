#!/bin/bash
source /root/workspace/projects/FitGround/scripts/gpu/flux_env.sh
cd /root/workspace/external/FitVTON-source-tree/GarmentCodeV2
python - << 'PY'
import json, hashlib, time, traceback
from pathlib import Path
from pygarment.meshgen.boxmeshgen import BoxMesh
from pygarment.meshgen.simulation import run_sim
import pygarment.data_config as data_config
from pygarment.meshgen.sim_config import PathCofig

cases = {
  "bust_plus_1cm": Path("/root/workspace/projects/FitGround/artifacts/bust_atomic_calibration/bust_plus_1cm/patterns/t-shirt__bust_plus_1cm_mut/t-shirt__bust_plus_1cm_mut_specification.json"),
  "bust_plus_3cm": Path("/root/workspace/projects/FitGround/artifacts/bust_atomic_calibration/bust_plus_3cm/patterns/t-shirt__bust_plus_3cm_mut/t-shirt__bust_plus_3cm_mut_specification.json"),
  "baseline": Path("/root/workspace/projects/FitGround/artifacts/bust_atomic_calibration/bust_plus_1cm/patterns/t-shirt__bust_plus_1cm_base/t-shirt__bust_plus_1cm_base_specification.json"),
}
out_root = Path("/root/workspace/projects/FitGround/artifacts/gpu/physics_lattice")
out_root.mkdir(parents=True, exist_ok=True)
results = {}
for tag, spec in cases.items():
    print("PHYS", tag, spec.exists(), flush=True)
    t0 = time.time()
    rec = {"tag": tag, "spec": str(spec), "status": "FAIL"}
    try:
        props = data_config.Properties("./assets/Sim_props/default_sim_props.yaml")
        props["sim"]["config"]["max_sim_steps"] = 300
        props.set_section_stats("sim", fails={}, sim_time={}, spf={}, fin_frame={}, body_collisions={}, self_collisions={})
        props.set_section_stats("render", render_time={})
        garment_name, _, _ = spec.stem.rpartition("_")
        paths = PathCofig(
            in_element_path=spec.parent,
            out_path=str(out_root),
            in_name=garment_name,
            out_name=tag,
            body_name="mean_all",
            smpl_body=False,
            add_timestamp=False,
            system_path="./system.json",
        )
        mesh = BoxMesh(paths.in_g_spec, props["sim"]["config"]["resolution_scale"])
        mesh.load()
        mesh.serialize(paths, store_panels=False, uv_config=props["render"]["config"]["uv_texture"])
        run_sim(mesh.name, props, paths, save_v_norms=False, store_usd=False, optimize_storage=False, verbose=False)
        sim = Path(paths.g_sim)
        renders = list(Path(paths.out_el).glob("*render*.png"))
        rec.update({
            "status": "PASS" if sim.exists() else "FAIL",
            "simulation_status": "SIMULATED" if sim.exists() else "FAILED",
            "render_status": "RENDERED" if renders else "FAILED",
            "sim_mesh": str(sim) if sim.exists() else None,
            "renders": [str(p) for p in renders],
            "output_dir": str(paths.out_el),
        })
        if sim.exists():
            rec["sim_sha256"] = hashlib.sha256(sim.read_bytes()).hexdigest()
    except Exception as e:
        rec["error"] = f"{type(e).__name__}: {e}"
        rec["traceback"] = traceback.format_exc()
    rec["runtime_s"] = time.time() - t0
    results[tag] = rec
    print("DONE", tag, rec["status"], rec["runtime_s"], flush=True)
Path("/root/workspace/projects/FitGround/artifacts/gpu/physics_lattice/results.json").write_text(json.dumps(results, indent=2))
print("ALL_DONE")
PY
