"""Relational fit feature engineering."""

from __future__ import annotations

from typing import Any


def _safe_ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator


def compute_relational_features(measurements: dict[str, float | None]) -> dict[str, float | None]:
    """
    Compute canonical relational features.

    Missing propagation: if any operand is None (or denominator is 0), result is None.
    """
    body_bust = measurements.get("body_bust_cm")
    body_height = measurements.get("body_height_cm")
    garment_bust = measurements.get("garment_bust_cm")
    garment_length = measurements.get("garment_length_cm")

    bust_ease = None
    if garment_bust is not None and body_bust is not None:
        bust_ease = garment_bust - body_bust

    return {
        "bust_ease_cm": bust_ease,
        "bust_ease_ratio": _safe_ratio(bust_ease, body_bust),
        "garment_length_height_ratio": _safe_ratio(garment_length, body_height),
    }
