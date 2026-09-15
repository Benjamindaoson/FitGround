"""Tests for eval pipeline helpers."""

import pandas as pd

from fitground.data.eval_pipeline import analyze_bust_ease_ratio_quantization, annotate_eval_duplicates


def test_duplicate_annotation() -> None:
    df = pd.DataFrame({
        "person_sha256": ["a", "a", "b"],
        "garment_sha256": ["x", "x", "y"],
        "target_sha256": ["t1", "t2", "t3"],
        "quality_status": ["VALID", "VALID", "VALID"],
        "quality_flags": [[], [], []],
    })
    out = annotate_eval_duplicates(df)
    assert out["duplicate_person_sha256"].sum() == 2
    assert out.loc[0, "quality_status"] == "SUSPICIOUS"
    assert "possible_duplicate" in list(out.loc[0, "quality_flags"])


def test_quantization_analysis() -> None:
    df = pd.DataFrame({
        "bust_ease_ratio": [0.05, 0.10, 0.10, 0.15, 0.20],
        "bust_ease_cm": [1.0, 2.0, 2.0, 3.0, 4.0],
        "garment_sleeve_cm": [0.0, 10.0, 10.0, 10.0, 10.0],
    })
    result = analyze_bust_ease_ratio_quantization(df)
    assert result["n_samples"] == 5
    assert "verdict" in result
    assert result["sleeveless_count"] == 1
