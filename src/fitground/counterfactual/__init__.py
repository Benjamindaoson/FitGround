"""Measurement-counterfactual discovery, matching, and validation."""

from fitground.counterfactual.schema import (
    BODY_VECTOR_FIELDS,
    GARMENT_VECTOR_FIELDS,
    PAIR_REQUIRED_COLUMNS,
    RELATIONAL_VECTOR_FIELDS,
    TIER_A,
    TIER_B,
    TIER_C,
    TIER_D,
    cloth_sha256_column,
    make_pair_id,
)

__all__ = [
    "BODY_VECTOR_FIELDS",
    "GARMENT_VECTOR_FIELDS",
    "RELATIONAL_VECTOR_FIELDS",
    "PAIR_REQUIRED_COLUMNS",
    "TIER_A",
    "TIER_B",
    "TIER_C",
    "TIER_D",
    "cloth_sha256_column",
    "make_pair_id",
]
