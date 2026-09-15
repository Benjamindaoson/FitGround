"""Measurement parsing and normalization."""

from __future__ import annotations

import math
from typing import Any

from fitground.config import (
    BODY_BUST_CM_MAX,
    BODY_BUST_CM_MIN,
    BODY_HEIGHT_CM_MAX,
    BODY_HEIGHT_CM_MIN,
    BODY_HIPS_CM_MAX,
    BODY_HIPS_CM_MIN,
    BODY_WAIST_CM_MAX,
    BODY_WAIST_CM_MIN,
    GARMENT_BUST_CM_MAX,
    GARMENT_BUST_CM_MIN,
    GARMENT_LENGTH_CM_MAX,
    GARMENT_LENGTH_CM_MIN,
    GARMENT_SLEEVE_CM_MAX,
    GARMENT_SLEEVE_CM_MIN,
)
from fitground.data.schema import RAW_TO_CANONICAL

RAW_UNIT = "cm"
CONVERSION_RULE = "identity: raw values already in cm per dataset README"


def _parse_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_measurements(row: dict[str, Any]) -> dict[str, float | None]:
    """Map raw parquet fields to canonical cm fields."""
    out: dict[str, float | None] = {}
    for raw_key, canonical_key in RAW_TO_CANONICAL.items():
        out[canonical_key] = _parse_float(row.get(raw_key))
    return out


def measurement_bounds() -> dict[str, tuple[float, float]]:
    return {
        "body_height_cm": (BODY_HEIGHT_CM_MIN, BODY_HEIGHT_CM_MAX),
        "body_bust_cm": (BODY_BUST_CM_MIN, BODY_BUST_CM_MAX),
        "body_waist_cm": (BODY_WAIST_CM_MIN, BODY_WAIST_CM_MAX),
        "body_hips_cm": (BODY_HIPS_CM_MIN, BODY_HIPS_CM_MAX),
        "garment_bust_cm": (GARMENT_BUST_CM_MIN, GARMENT_BUST_CM_MAX),
        "garment_length_cm": (GARMENT_LENGTH_CM_MIN, GARMENT_LENGTH_CM_MAX),
        "garment_sleeve_cm": (GARMENT_SLEEVE_CM_MIN, GARMENT_SLEEVE_CM_MAX),
    }


def is_impossible_measurement(field: str, value: float | None) -> bool:
    if value is None:
        return False
    bounds = measurement_bounds()
    if field not in bounds:
        return False
    lo, hi = bounds[field]
    return value < lo or value > hi
