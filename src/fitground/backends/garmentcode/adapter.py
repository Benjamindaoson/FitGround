"""Subprocess adapter from FitGround contracts to the flux GarmentCode worker.

This module never copies intended_delta_cm into realized_delta_cm. Realized
values only appear if the worker measured them.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

from fitground.correction.schema import (
    CandidateCorrection,
    PredictedFitOutcome,
    SUPPORTED_ACTION_FAMILIES,
)

ROOT = Path(__file__).resolve().parents[4]
WORKER = ROOT / "scripts" / "gpu" / "garmentcode_worker.py"
FLUX_PYTHON = Path("/root/workspace/conda/envs/flux/bin/python")
GC_ROOT = Path("/root/workspace/external/FitVTON-source-tree/GarmentCodeV2")


def garmentcode_available() -> bool:
    return WORKER.exists() and FLUX_PYTHON.exists() and GC_ROOT.exists()


def execute_garmentcode_action(
    action_family: str,
    intended_delta_cm: float,
    output_dir: Path,
    tag: str,
    physics: bool = False,
    render: bool = False,
    seed: int = 0,
    max_sim_steps: int = 400,
) -> dict[str, Any]:
    if action_family not in SUPPORTED_ACTION_FAMILIES:
        return {
            "error_code": "NOT_SUPPORTED",
            "action_family": action_family,
            "simulation_status": "NOT_RUN",
            "render_status": "NOT_RUN",
            "realized_delta_cm": None,
            "verification_status": "NOT_VERIFIED",
        }
    if action_family != "bust_circumference_delta_cm":
        return {
            "error_code": "ACTION_NOT_CALIBRATED",
            "action_family": action_family,
            "message": "Only bust_circumference_delta_cm has a measured GarmentCode mapping in v0.1.",
            "simulation_status": "NOT_RUN",
            "render_status": "NOT_RUN",
            "realized_delta_cm": None,
            "verification_status": "NOT_VERIFIED",
        }
    if not garmentcode_available():
        return {
            "error_code": "SIMULATION_BACKEND_NOT_CONFIGURED",
            "simulation_status": "NOT_RUN",
            "render_status": "NOT_RUN",
            "realized_delta_cm": None,
            "verification_status": "NOT_VERIFIED",
        }
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        str(FLUX_PYTHON),
        str(WORKER),
        "--action-family",
        action_family,
        "--intended-delta-cm",
        str(intended_delta_cm),
        "--output-dir",
        str(output_dir),
        "--tag",
        tag,
        "--seed",
        str(seed),
        "--max-sim-steps",
        str(max_sim_steps),
    ]
    if physics:
        cmd.append("--physics")
    if render:
        cmd.append("--render")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(GC_ROOT) + ":" + env.get("PYTHONPATH", "")
    env["PYOPENGL_PLATFORM"] = env.get("PYOPENGL_PLATFORM", "egl")
    env["CONDA_PREFIX"] = "/root/workspace/conda/envs/flux"
    env["CUDA_HOME"] = env["CONDA_PREFIX"]
    env["PATH"] = str(Path(env["CONDA_PREFIX"]) / "bin") + ":" + env.get("PATH", "")
    proc = subprocess.run(cmd, cwd="/tmp", env=env, capture_output=True, text=True)
    artifact = output_dir / f"{tag}.json"
    if artifact.exists():
        payload = json.loads(artifact.read_text(encoding="utf-8"))
    else:
        payload = {"error": "worker produced no artifact", "stderr": proc.stderr[-4000:]}
    payload["subprocess_returncode"] = proc.returncode
    payload.setdefault("realized_delta_cm", None)
    return payload


def outcome_from_worker(candidate: CandidateCorrection, worker: dict[str, Any]) -> PredictedFitOutcome:
    before = worker.get("garment_measurement_before") or {}
    after = worker.get("garment_measurement_after")
    sim = worker.get("simulation_status") or "NOT_RUN"
    if sim not in ("NOT_RUN", "SIMULATED", "FAILED"):
        sim = "NOT_RUN"
    render = worker.get("render_status") or "NOT_RUN"
    if render not in ("NOT_RUN", "RENDERED", "FAILED", "NOT_APPLICABLE"):
        render = "NOT_RUN"
    side_effects = []
    for region, key in (
        ("waist", "waist_delta_cm"),
        ("shoulder", "shoulder_delta_cm"),
        ("sleeve", "sleeve_delta_cm"),
        ("length", "length_delta_cm"),
    ):
        val = worker.get(key)
        if val is not None:
            side_effects.append({"region": region, "delta_cm": val})
    region_before = {"chest_bust_cm": before.get("bust_circumference_cm")}
    region_after = None
    if after is not None:
        region_after = {"chest_bust_cm": after.get("bust_circumference_cm")}
    if sim == "NOT_RUN" and after is not None:
        # Pattern measurement is not a physics simulation.
        region_after = None
    hashes = {}
    if after and after.get("spec_sha256"):
        hashes["mutated_spec_sha256"] = after["spec_sha256"]
    if before.get("spec_sha256"):
        hashes["baseline_spec_sha256"] = before["spec_sha256"]
    return PredictedFitOutcome(
        candidate_id=candidate.candidate_id or tag_fallback(candidate),
        region_before=region_before,
        region_after=region_after if sim == "SIMULATED" else None,
        direction="increase" if (worker.get("realized_delta_cm") or 0) > 0 else "decrease",
        magnitude=worker.get("realized_delta_cm") if sim == "SIMULATED" else None,
        side_effects=side_effects if sim == "SIMULATED" else [],
        confidence=1.0 if worker.get("realized_delta_cm") is not None else None,
        simulation_status=sim,
        render_status=render if sim != "NOT_RUN" else "NOT_RUN",
        reproducibility={"status": sim, "seed": worker.get("seed")},
        hashes=hashes,
        provenance={
            "source": "garmentcode_backend",
            "parameter": worker.get("parameter_name"),
            "pattern_realized_delta_cm": worker.get("realized_delta_cm"),
            "verification_status": worker.get("verification_status"),
        },
    )


def tag_fallback(candidate: CandidateCorrection) -> str:
    return f"{candidate.action_family}_{candidate.intended_delta_cm}"
