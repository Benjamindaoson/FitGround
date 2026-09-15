from __future__ import annotations

import json
from pathlib import Path

import pytest

from fitground.correction import (
    ContractValidationError,
    CorrectionLattice,
    CurrentFitState,
    PredictedFitOutcome,
    apply_correction,
    build_correction_lattice,
    validate_lattice,
)


def _state() -> CurrentFitState:
    return CurrentFitState(
        state_id="case-001",
        body={"bust_cm": 92.0},
        garment={"bust_cm": 94.0, "shoulder_width_cm": 40.0, "sleeve_length_cm": 60.0},
        visual_assets=["target:sha256:abc"],
        material={"stretch": "low"},
        garment_type="structured_blazer",
        fit_intent="regular",
        region_fit_state={"chest": "tight", "shoulder": "regular", "sleeve": "regular"},
        provenance={"source": "unit-test", "input_sha256": "abc"},
    )


def test_current_state_requires_visual_evidence() -> None:
    """Catches a state that would silently degrade to measurement-only input."""
    with pytest.raises(ContractValidationError, match="visual_assets"):
        CurrentFitState(
            state_id="missing-visual",
            body={"bust_cm": 92.0},
            garment={"bust_cm": 94.0},
            visual_assets=[],
            material={"stretch": "low"},
            garment_type="blazer",
            fit_intent="regular",
            region_fit_state={"chest": "tight"},
            provenance={"source": "unit-test"},
        )


def test_candidate_keeps_unverified_realized_delta_null() -> None:
    """Catches accidental copying of intended delta into simulated measurement."""
    candidate = apply_correction(
        _state().garment,
        "bust_circumference_delta_cm",
        3.0,
    )
    assert candidate.intended_delta_cm == 3.0
    assert candidate.realized_delta_cm is None
    assert candidate.verification_status == "NOT_VERIFIED"


def test_unsupported_action_is_rejected() -> None:
    """Catches scope creep into an ambiguous V0.1 action family."""
    with pytest.raises(ContractValidationError, match="NOT_SUPPORTED"):
        apply_correction(_state().garment, "armhole_delta_cm", 1.0)


def test_lattice_ids_are_deterministic_and_candidates_unique() -> None:
    """Catches duplicate candidate rows or non-repeatable resume identifiers."""
    state = _state()
    first = apply_correction(state.garment, "bust_circumference_delta_cm", 1.0)
    second = apply_correction(state.garment, "shoulder_width_delta_cm", 1.0)
    lattice_a = build_correction_lattice(state, [first, second])
    lattice_b = build_correction_lattice(state, [first, second])
    assert lattice_a.lattice_id == lattice_b.lattice_id
    assert lattice_a.candidate_actions[0].candidate_id == lattice_b.candidate_actions[0].candidate_id
    with pytest.raises(ContractValidationError, match="duplicate"):
        build_correction_lattice(state, [first, first])


def test_not_run_outcomes_report_missing_when_complete_required() -> None:
    """Catches a validator that mistakes a planned lattice for simulator evidence."""
    state = _state()
    candidate = apply_correction(state.garment, "sleeve_length_delta_cm", -1.0)
    lattice = build_correction_lattice(state, [candidate])
    result = validate_lattice(lattice, require_complete_outcomes=True)
    assert result["ok"] is False
    assert result["missing_outcome_candidate_ids"] == [lattice.candidate_actions[0].candidate_id]
    assert lattice.oracle_action is None
    assert lattice.outcomes[0].simulation_status == "NOT_RUN"


def test_predicted_outcome_requires_after_state_when_simulated() -> None:
    """Catches a claimed simulation result without an extracted next fit state."""
    with pytest.raises(ContractValidationError, match="region_after"):
        PredictedFitOutcome(
            candidate_id="candidate",
            region_before={"chest": "tight"},
            region_after=None,
            direction=None,
            magnitude=None,
            side_effects=[],
            confidence=None,
            simulation_status="SIMULATED",
            render_status="NOT_RUN",
            reproducibility={"status": "unit-test"},
            hashes={},
            provenance={"source": "unit-test"},
        )


def test_planned_lattice_records_unrun_render_and_evidence_fields() -> None:
    """Catches a planned lattice that omits required verifier evidence fields."""
    lattice = build_correction_lattice(
        _state(), [apply_correction(_state().garment, "bust_circumference_delta_cm", 1.0)]
    )
    outcome = lattice.outcomes[0]
    assert outcome.render_status == "NOT_RUN"
    assert outcome.reproducibility == {"status": "NOT_RUN"}
    assert outcome.hashes == {}
    assert lattice.ranking is None
    assert set(lattice.provenance) >= {
        "git_sha",
        "environment",
        "seed",
        "source_assets",
        "artifact_paths",
    }


def test_lattice_ranking_must_be_a_unique_candidate_permutation() -> None:
    """Catches rankings that silently omit or duplicate a candidate correction."""
    lattice = build_correction_lattice(
        _state(),
        [
            apply_correction(_state().garment, "bust_circumference_delta_cm", 1.0),
            apply_correction(_state().garment, "shoulder_width_delta_cm", 1.0),
        ],
    )
    with pytest.raises(ContractValidationError, match="ranking"):
        CorrectionLattice(
            lattice_id=lattice.lattice_id,
            state_id=lattice.state_id,
            candidate_actions=lattice.candidate_actions,
            outcomes=lattice.outcomes,
            utilities=lattice.utilities,
            oracle_action=None,
            ranking=[lattice.candidate_actions[0].candidate_id or ""],
            verification_status="NOT_VERIFIED",
            provenance=lattice.provenance,
        )


def test_machine_schema_declares_every_v01_contract() -> None:
    """Catches a JSON schema that silently omits one Python contract."""
    schema_path = Path(__file__).resolve().parents[1] / "schemas" / "fit_correction_v0.1.schema.json"
    definitions = json.loads(schema_path.read_text(encoding="utf-8"))["definitions"]
    assert {"CurrentFitState", "CauseHypothesis", "CandidateCorrection", "PredictedFitOutcome", "CorrectionLattice"} <= set(definitions)
    assert {"render_status", "reproducibility", "hashes"} <= set(
        definitions["PredictedFitOutcome"]["properties"]
    )
    assert "ranking" in definitions["CorrectionLattice"]["properties"]
