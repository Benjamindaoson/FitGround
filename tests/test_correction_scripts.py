from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ | {"PYTHONPATH": str(ROOT / "src")}
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script), *args],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def test_calibration_dry_run_has_no_realized_measurement(tmp_path: Path) -> None:
    """Catches a calibration scaffold that pretends an intended delta was measured."""
    result = _run(
        "calibrate_correction_action.py",
        "--dry-run",
        "--action-family",
        "bust_circumference_delta_cm",
        "--intended-delta-cm",
        "3",
        "--output",
        str(tmp_path / "calibration.json"),
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads((tmp_path / "calibration.json").read_text(encoding="utf-8"))
    assert payload["intended_delta_cm"] == 3.0
    assert payload["realized_delta_cm"] is None
    assert payload["status"] == "NOT_RUN"


def test_smoke_runner_dry_run_never_claims_simulation(tmp_path: Path) -> None:
    """Catches a dry-run that accidentally reports fabricated simulation output."""
    result = _run(
        "run_fit_correction_smoke.py",
        "--dry-run",
        "--case",
        "CHEST_CASE",
        "--output-dir",
        str(tmp_path),
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["simulation_status"] == "NOT_RUN"
    assert payload["backend_status"] == "NOT_VERIFIED"
    assert payload["planned_action_count"] == 5
    assert payload["render_status"] == "NOT_RUN"
    assert payload["reproducibility"] == {"status": "NOT_RUN"}
    assert len(payload["hashes"]["smoke_plan_sha256"]) == 64


def test_smoke_runner_preserves_and_resumes_backend_failure(tmp_path: Path) -> None:
    """Catches overwrite or disappearance of a non-dry-run backend failure."""
    first = _run(
        "run_fit_correction_smoke.py",
        "--case",
        "SLEEVE_CASE",
        "--action",
        "sleeve_length_delta_cm:-1",
        "--output-dir",
        str(tmp_path),
    )
    assert first.returncode == 2
    failure = json.loads(first.stdout)
    assert failure["error_code"] == "SIMULATION_BACKEND_NOT_CONFIGURED"
    artifact = Path(failure["failure_artifact"])
    original = artifact.read_text(encoding="utf-8")

    resumed = _run(
        "run_fit_correction_smoke.py",
        "--resume",
        "--case",
        "SLEEVE_CASE",
        "--action",
        "sleeve_length_delta_cm:-1",
        "--output-dir",
        str(tmp_path),
    )
    assert resumed.returncode == 2
    assert json.loads(resumed.stdout)["resumed"] is True
    assert artifact.read_text(encoding="utf-8") == original
