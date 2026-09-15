"""Tests for relational feature engineering."""

from fitground.data.features import compute_relational_features


def test_bust_ease() -> None:
    m = {
        "body_bust_cm": 90.0,
        "body_height_cm": 170.0,
        "garment_bust_cm": 100.0,
        "garment_length_cm": 60.0,
    }
    f = compute_relational_features(m)
    assert f["bust_ease_cm"] == 10.0
    assert abs(f["bust_ease_ratio"] - 10.0 / 90.0) < 1e-6
    assert abs(f["garment_length_height_ratio"] - 60.0 / 170.0) < 1e-6
    assert "waist_ease_cm" not in f


def test_missing_propagation() -> None:
    m = {"body_bust_cm": None, "garment_bust_cm": 100.0, "body_height_cm": 170.0}
    f = compute_relational_features(m)
    assert f["bust_ease_cm"] is None
    assert f["bust_ease_ratio"] is None
