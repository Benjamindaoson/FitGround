#!/usr/bin/env python3
"""Plan correction smoke work; preserve absent-backend failures instead of faking results."""

from __future__ import annotations

import argparse
import json
import sys
from hashlib import sha256
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fitground.correction.schema import canonical_json

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "artifacts" / "fit_correction_smoke_plan_v0.1.yaml"


def _load_plan() -> dict[str, Any]:
    return yaml.safe_load(PLAN_PATH.read_text(encoding="utf-8"))


def _select_actions(case: dict[str, Any], selector: str | None) -> list[dict[str, Any]]:
    actions = list(case["candidates"])
    if selector is None:
        return actions
    family, delta_text = selector.rsplit(":", 1)
    delta = float(delta_text)
    selected = [
        action
        for action in actions
        if action["action_family"] == family and float(action["intended_delta_cm"]) == delta
    ]
    if not selected:
        raise ValueError("requested action is not in the frozen smoke plan")
    return selected


def _artifact_path(output_dir: Path, case_name: str, actions: list[dict[str, Any]]) -> Path:
    digest = sha256(canonical_json({"case": case_name, "actions": actions}).encode("utf-8")).hexdigest()[:16]
    return output_dir / "fit_correction_runs" / case_name / f"{digest}.json"


def _emit(payload: dict[str, Any], code: int) -> int:
    print(json.dumps(payload, indent=2))
    return code


def main() -> int:
    parser = argparse.ArgumentParser(description="FitGround V0.1 GPU correction smoke runner")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--case", required=True, dest="case_name")
    parser.add_argument("--action", help="action_family:intended_delta_cm")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--backend", default="none", choices=["none", "garmentcode"])
    parser.add_argument("--physics", action="store_true")
    args = parser.parse_args()

    plan = _load_plan()
    if args.case_name not in plan["cases"]:
        return _emit({"error_code": "UNKNOWN_SMOKE_CASE", "case": args.case_name}, 2)
    try:
        actions = _select_actions(plan["cases"][args.case_name], args.action)
    except ValueError as error:
        return _emit({"error_code": "UNKNOWN_SMOKE_ACTION", "detail": str(error)}, 2)

    artifact = _artifact_path(args.output_dir, args.case_name, actions)
    if args.resume and artifact.exists():
        existing = json.loads(artifact.read_text(encoding="utf-8"))
        existing["resumed"] = True
        return _emit(existing, 2 if existing.get("error_code") else 0)

    base = {
        "plan_id": plan["plan_id"],
        "case": args.case_name,
        "actions": actions,
        "planned_action_count": len(actions),
        "simulation_status": "NOT_RUN",
        "render_status": "NOT_RUN",
        "backend_status": "NOT_VERIFIED",
        "realized_delta_cm": None,
        "reproducibility": {"status": "NOT_RUN"},
        "hashes": {"smoke_plan_sha256": sha256(PLAN_PATH.read_bytes()).hexdigest()},
        "artifact": str(artifact),
    }
    artifact.parent.mkdir(parents=True, exist_ok=True)
    if args.dry_run:
        artifact.write_text(json.dumps(base, indent=2), encoding="utf-8")
        return _emit(base, 0)

    if args.backend == "none":
        failure = base | {
            "error_code": "SIMULATION_BACKEND_NOT_CONFIGURED",
            "failure_artifact": str(artifact),
            "message": "No verified GarmentCode-to-action mapping or physics backend is configured.",
        }
        artifact.write_text(json.dumps(failure, indent=2), encoding="utf-8")
        return _emit(failure, 2)

    from fitground.backends.garmentcode.adapter import execute_garmentcode_action

    results = []
    for action in actions:
        tag = f"{args.case_name}_{action[action_family]}_{action[intended_delta_cm]}"
        worker = execute_garmentcode_action(
            action["action_family"],
            float(action["intended_delta_cm"]),
            artifact.parent / "backend",
            tag,
            physics=args.physics,
        )
        results.append(worker)
    realized = [r.get("realized_delta_cm") for r in results]
    sim_statuses = [r.get("simulation_status", "NOT_RUN") for r in results]
    payload = base | {
        "backend": "garmentcode",
        "backend_status": "VERIFIED" if any(v is not None for v in realized) else "NOT_VERIFIED",
        "realized_delta_cm": realized,
        "simulation_status": "SIMULATED" if any(s == "SIMULATED" for s in sim_statuses) else (
            "FAILED" if any(s == "FAILED" for s in sim_statuses) else "NOT_RUN"
        ),
        "render_status": results[0].get("render_status", "NOT_RUN") if results else "NOT_RUN",
        "worker_results": results,
        "reproducibility": {"status": "PATTERN_MEASURED", "seed": 0},
    }
    if all(r.get("error_code") == "ACTION_NOT_CALIBRATED" for r in results):
        payload["error_code"] = "ACTION_NOT_CALIBRATED"
        payload["failure_artifact"] = str(artifact)
        artifact.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return _emit(payload, 2)
    artifact.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return _emit(payload, 0)


if __name__ == "__main__":
    raise SystemExit(main())
