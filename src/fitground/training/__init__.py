"""Training helpers for measured correction lattices. No fabricated deltas."""

from fitground.training.geometry import (
    realized_delta,
    rasterize_specification,
    utility_chest_case,
    assert_realized_not_copied,
)
from fitground.training.textfmt import format_transition_example, format_decision_example, parse_generated_fields

__all__ = [
    "realized_delta",
    "rasterize_specification",
    "utility_chest_case",
    "assert_realized_not_copied",
    "format_transition_example",
    "format_decision_example",
    "parse_generated_fields",
]
