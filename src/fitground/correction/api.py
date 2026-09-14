"""Correction planning boundary; no GarmentCode mapping exists locally."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from fitground.correction.schema import CandidateCorrection


def apply_correction(
    garment: Mapping[str, Any],
    action_family: str,
    intended_delta_cm: float,
) -> CandidateCorrection:
    """Plan a supported action without mutating a garment or inventing calibration.

    ``realized_delta_cm`` remains null until a future verified backend measures it.
    """
    source_pattern_parameters = garment.get("source_pattern_parameters", {})
    if not isinstance(source_pattern_parameters, Mapping):
        source_pattern_parameters = {}
    return CandidateCorrection(
        action_family=action_family,
        intended_delta_cm=float(intended_delta_cm),
        realized_delta_cm=None,
        source_pattern_parameters=dict(source_pattern_parameters),
        verification_status="NOT_VERIFIED",
    )
