"""Construct planned correction lattices without a simulated after-state."""

from __future__ import annotations

from fitground.correction.schema import (
    CandidateCorrection,
    ContractValidationError,
    CorrectionLattice,
    CurrentFitState,
    PredictedFitOutcome,
    stable_id,
)


def build_correction_lattice(
    state: CurrentFitState,
    candidates: list[CandidateCorrection],
) -> CorrectionLattice:
    """Create deterministic, explicitly unrun candidate entries for one state."""
    identified = [candidate.identified_for(state.state_id) for candidate in candidates]
    candidate_ids = [candidate.candidate_id for candidate in identified]
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ContractValidationError("duplicate candidate action in lattice")
    outcomes = [
        PredictedFitOutcome(
            candidate_id=candidate.candidate_id or "",
            region_before=dict(state.region_fit_state),
            region_after=None,
            direction=None,
            magnitude=None,
            side_effects=[],
            confidence=None,
            simulation_status="NOT_RUN",
            render_status="NOT_RUN",
            reproducibility={"status": "NOT_RUN"},
            hashes={},
            provenance={"source": "lattice_builder", "state_id": state.state_id},
        )
        for candidate in identified
    ]
    lattice_id = stable_id(
        "lattice",
        {"state_id": state.state_id, "candidate_ids": sorted(candidate_ids)},
    )
    return CorrectionLattice(
        lattice_id=lattice_id,
        state_id=state.state_id,
        candidate_actions=identified,
        outcomes=outcomes,
        utilities={candidate_id: None for candidate_id in candidate_ids if candidate_id is not None},
        oracle_action=None,
        ranking=None,
        verification_status="NOT_VERIFIED",
        provenance={
            "source": "lattice_builder",
            "current_state_provenance": dict(state.provenance),
            "simulation_backend": "NOT_CONFIGURED",
            "git_sha": state.provenance.get("git_sha", "UNAVAILABLE_AT_CHECKOUT"),
            "environment": state.provenance.get("environment", "NOT_RUN"),
            "seed": state.provenance.get("seed"),
            "source_assets": list(state.visual_assets),
            "artifact_paths": [],
        },
    )
