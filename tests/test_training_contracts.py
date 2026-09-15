"""Training-contract tests that do not require GPU or GarmentCode."""

from __future__ import annotations

import json

import numpy as np
from PIL import Image

from fitground.training.geometry import (
    assert_realized_not_copied,
    grouped_state_split,
    rasterize_specification,
    realized_delta,
    utility_chest_case,
)
from fitground.training.textfmt import format_transition_example, parse_generated_fields


def test_realized_delta_is_after_minus_before_not_intended() -> None:
    assert realized_delta(100.0, 103.0) == 3.0
    assert realized_delta(None, 103.0) is None
    intended = 3.0
    # A non-identity measurement must survive: this is the honesty invariant.
    assert realized_delta(10.0, 11.5) != intended


def test_assert_realized_rejects_missing_provenance() -> None:
    row = {
        "realized_delta_cm": 3.0,
        "intended_delta_cm": 3.0,
        "realized_source": "copied_from_intended",
        "realized_measurement_key": "bust_circumference_cm",
        "garment_measurement_before": {"bust_circumference_cm": 100.0},
        "garment_measurement_after": {"bust_circumference_cm": 103.0},
    }
    try:
        assert_realized_not_copied(row)
        raise AssertionError("should have rejected copied provenance")
    except ValueError:
        pass
    row["realized_source"] = "panel_geometry_after_minus_before"
    assert_realized_not_copied(row)


def test_utility_prefers_on_target_smaller_edit() -> None:
    on_target = utility_chest_case(0.0, 3.0, 0.2, 0.1)
    miss = utility_chest_case(2.0, 1.0, 0.05, 0.05)
    assert on_target > miss


def test_rasterize_fake_specification(tmp_path) -> None:
    spec = {
        "pattern": {
            "panels": {
                "left_ftorso": {"vertices": [[0, 0], [10, 0], [10, 20], [0, 20]]},
                "right_ftorso": {"vertices": [[10, 0], [20, 0], [20, 20], [10, 20]]},
                "left_btorso": {"vertices": [[20, 0], [30, 0], [30, 20], [20, 20]]},
                "right_btorso": {"vertices": [[30, 0], [40, 0], [40, 20], [30, 20]]},
            }
        }
    }
    path = tmp_path / "pat.png"
    img = rasterize_specification(spec, path, size=64)
    assert path.exists()
    assert img.size == (64, 64)
    arr = np.asarray(Image.open(path))
    assert arr.max() > 0


def test_text_roundtrip_parse() -> None:
    row = {
        "body_bust_cm": 99.84,
        "action_family": "bust_circumference_delta_cm",
        "intended_delta_cm": 3.0,
        "realized_delta_cm": 3.0,
        "garment_measurement_before": {
            "bust_circumference_cm": 104.8,
            "waist_cm": 104.8,
            "length_cm": 40.0,
            "sleeve_length_cm": 20.0,
        },
        "garment_measurement_after": {
            "bust_circumference_cm": 107.8,
            "waist_cm": 107.8,
            "length_cm": 40.1,
            "sleeve_length_cm": 20.2,
        },
    }
    text = format_transition_example(row)
    fields = parse_generated_fields(text)
    assert fields["INTENDED"].startswith("3")
    assert fields["REALIZED"].startswith("3")
    assert "AFTER_BUST" in fields


def test_grouped_state_split_is_deterministic() -> None:
    ids = [f"s{i}" for i in range(10)] * 3
    a = grouped_state_split(ids, seed=0)
    b = grouped_state_split(ids, seed=0)
    assert a == b
    assert set(a.values()) <= {"train", "val", "test"}
    assert "train" in a.values()
