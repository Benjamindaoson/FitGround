"""V0.1 correction contracts; no local simulation backend is implied."""

from fitground.correction.api import apply_correction
from fitground.correction.lattice import build_correction_lattice
from fitground.correction.schema import (
    SUPPORTED_ACTION_FAMILIES,
    CandidateCorrection,
    CauseHypothesis,
    ContractValidationError,
    CorrectionLattice,
    CurrentFitState,
    PredictedFitOutcome,
)
from fitground.correction.validation import validate_lattice

__all__ = [
    "SUPPORTED_ACTION_FAMILIES",
    "CandidateCorrection",
    "CauseHypothesis",
    "ContractValidationError",
    "CorrectionLattice",
    "CurrentFitState",
    "PredictedFitOutcome",
    "apply_correction",
    "build_correction_lattice",
    "validate_lattice",
]
