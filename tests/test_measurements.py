"""Tests for measurement normalization."""

from fitground.data.measurements import (
    CONVERSION_RULE,
    RAW_UNIT,
    is_impossible_measurement,
    normalize_measurements,
)


def test_normalize_measurements_identity() -> None:
    row = {
        "body_height": 175.0,
        "body_bust": 90.0,
        "body_waist": 70.0,
        "body_hips": 95.0,
        "garment_bust": 100.0,
        "garment_length": 60.0,
        "garment_sleeve_length": 25.0,
    }
    result = normalize_measurements(row)
    assert result["body_height_cm"] == 175.0
    assert result["garment_sleeve_cm"] == 25.0
    assert RAW_UNIT == "cm"
    assert "identity" in CONVERSION_RULE


def test_impossible_measurement() -> None:
    assert is_impossible_measurement("body_height_cm", 50.0)
    assert not is_impossible_measurement("body_height_cm", 170.0)


def test_missing_measurement() -> None:
    result = normalize_measurements({"body_height": None})
    assert result["body_height_cm"] is None
