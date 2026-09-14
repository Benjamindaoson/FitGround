"""Validation for correction lattices and evidence completeness."""

from __future__ import annotations

from typing import Any

from fitground.correction.schema import CorrectionLattice


def validate_lattice(
    lattice: CorrectionLattice,
    *,
    require_complete_outcomes: bool = False,
) -> dict[str, Any]:
    """Return evidence completeness without upgrading a planned outcome to a result."""
    candidate_ids = [candidate.candidate_id for candidate in lattice.candidate_actions]
    outcome_by_id = {outcome.candidate_id: outcome for outcome in lattice.outcomes}
    missing = [
        candidate_id
        for candidate_id in candidate_ids
        if candidate_id not in outcome_by_id
        or outcome_by_id[candidate_id].simulation_status != "SIMULATED"
    ]
    unknown_outcomes = sorted(set(outcome_by_id) - set(candidate_ids))
    ok = not unknown_outcomes and (not require_complete_outcomes or not missing)
    return {
        "ok": ok,
        "lattice_id": lattice.lattice_id,
        "candidate_count": len(candidate_ids),
        "outcome_count": len(lattice.outcomes),
        "missing_outcome_candidate_ids": missing,
        "unknown_outcome_candidate_ids": unknown_outcomes,
        "verification_status": lattice.verification_status,
    }
