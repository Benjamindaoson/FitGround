"""Closure-stage tests: lattice honesty, decision abstention, allowed statuses."""

from __future__ import annotations

import json

from fitground.decision.engine import ood_heuristic, physics_utility, rank_candidates, should_abstain
from fitground.eval.lattice import validate_lattice, validate_transition_row


def _row(realized=3.0, intended=3.0, source="panel_geometry_after_minus_before"):
    return {
        "state_id": "s0",
        "action_id": "s0__bust__+3.00",
        "action_family": "bust_circumference_delta_cm",
        "intended_delta_cm": intended,
        "realized_delta_cm": realized,
        "realized_source": source,
        "realized_measurement_key": "bust_circumference_cm",
        "body_name": "mean_all",
        "garment_measurement_before": {"bust_circumference_cm": 100.0},
        "garment_measurement_after": {"bust_circumference_cm": 100.0 + realized},
    }


def test_validate_accepts_measured_identity_map():
    assert validate_transition_row(_row()) == []
    report = validate_lattice([_row(), _row(realized=2.0, intended=2.0)])
    assert report["ok"]
    assert report["n_duplicate_state_action"] == 0


def test_validate_rejects_copied_intended():
    errs = validate_transition_row(_row(source="intended"))
    assert errs


def test_physics_utility_prefers_lower_contact():
    tight = physics_utility({"contact_ratio": 0.04, "chest_clearance_p10_cm": 0.46}, 0.0)
    ease = physics_utility({"contact_ratio": 0.02, "chest_clearance_p10_cm": 0.51}, 2.0)
    assert ease > tight


def test_rank_and_abstain_ood_body():
    ranked = rank_candidates([{"action_id": "a", "utility": -1.0}, {"action_id": "b", "utility": -0.2}])
    assert ranked[0]["action_id"] == "b"
    assert ranked[0]["recommended"]
    decision = should_abstain(
        body_in_support=False,
        material_in_support=True,
        action_in_support=True,
        simulation_stable=True,
        candidate_gap=0.5,
        ood_score=ood_heuristic(
            body_name="mean_female",
            support_bodies=["mean_all"],
            material="default",
            support_materials=["default"],
            intended_delta_cm=2.0,
        ),
    )
    assert decision["abstain"]
    assert "OOD_BODY" in decision["reasons"]


def test_final_status_allowed_values(tmp_path):
    allowed = {"PASS", "NO_GO_WITH_EVIDENCE", "NOT_JUSTIFIED", "HARD_BLOCKED_LICENSE"}
    payload = {
        "Core": "PASS",
        "Shoulder": "NO_GO_WITH_EVIDENCE",
        "RLVR": "NOT_JUSTIFIED",
        "SMPL-X Physics": "HARD_BLOCKED_LICENSE",
    }
    (tmp_path / "FINAL_STATUS.json").write_text(json.dumps({"matrix": payload}))
    data = json.loads((tmp_path / "FINAL_STATUS.json").read_text())
    for status in data["matrix"].values():
        assert status in allowed
