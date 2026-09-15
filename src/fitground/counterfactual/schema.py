"""Canonical measurement vectors, pair schema, and deterministic IDs."""

from __future__ import annotations

import hashlib
from typing import Any

BODY_VECTOR_FIELDS: tuple[str, ...] = (
    "body_height_cm",
    "body_bust_cm",
    "body_waist_cm",
    "body_hips_cm",
)

GARMENT_VECTOR_FIELDS: tuple[str, ...] = (
    "garment_bust_cm",
    "garment_length_cm",
    "garment_sleeve_cm",
)

RELATIONAL_VECTOR_FIELDS: tuple[str, ...] = (
    "bust_ease_cm",
    "bust_ease_ratio",
    "garment_length_height_ratio",
)

# User-facing name in the Phase-2 brief; FIT-Clean column is garment_sha256.
CLOTH_SHA256_FIELD = "garment_sha256"

TIER_A = "A"
TIER_B = "B"
TIER_C = "C"
TIER_D = "D"
VALID_TIERS = (TIER_A, TIER_B, TIER_C, TIER_D)

PAIR_REQUIRED_COLUMNS: tuple[str, ...] = (
    "pair_id",
    "anchor_sample_id",
    "counterfactual_sample_id",
    "pair_tier",
    "same_person_image",
    "same_cloth_image",
    "same_garment_phash",
    "near_garment_phash",
    "garment_phash_hamming",
    "anchor_target_sha256",
    "counterfactual_target_sha256",
    "anchor_person_sha256",
    "counterfactual_person_sha256",
    "anchor_cloth_sha256",
    "counterfactual_cloth_sha256",
    "anchor_body_height_cm",
    "anchor_body_bust_cm",
    "anchor_body_waist_cm",
    "anchor_body_hips_cm",
    "counterfactual_body_height_cm",
    "counterfactual_body_bust_cm",
    "counterfactual_body_waist_cm",
    "counterfactual_body_hips_cm",
    "anchor_garment_bust_cm",
    "anchor_garment_length_cm",
    "anchor_garment_sleeve_cm",
    "counterfactual_garment_bust_cm",
    "counterfactual_garment_length_cm",
    "counterfactual_garment_sleeve_cm",
    "anchor_bust_ease_cm",
    "anchor_bust_ease_ratio",
    "counterfactual_bust_ease_cm",
    "counterfactual_bust_ease_ratio",
    "delta_body_height_cm",
    "delta_body_bust_cm",
    "delta_body_waist_cm",
    "delta_body_hips_cm",
    "delta_garment_bust_cm",
    "delta_garment_length_cm",
    "delta_garment_sleeve_cm",
    "delta_bust_ease_cm",
    "delta_bust_ease_ratio",
    "delta_garment_length_height_ratio",
    "body_measurements_constant",
    "single_variable_garment_change",
    "measurement_intervention_type",
    "different_target",
    "quality_anchor",
    "quality_counterfactual",
    "quality_both_valid",
    "usable_both",
    "duplicate_contamination",
    "leakage_person",
    "leakage_garment",
    "leakage_target",
    "leakage_any",
    "cross_split",
    "pair_split",
    "anchor_split",
    "counterfactual_split",
    "anchor_shard_id",
    "counterfactual_shard_id",
    "control_score",
    "confound_flags",
    "pair_construction_reason",
    "group_key",
)


def cloth_sha256_column() -> str:
    """Map the brief's cloth_sha256 grouping key onto FIT-Clean."""
    return CLOTH_SHA256_FIELD


def canonical_unordered_ids(sample_a: str, sample_b: str) -> tuple[str, str]:
    if sample_a == sample_b:
        raise ValueError("self-pair is not a counterfactual")
    return (sample_a, sample_b) if sample_a < sample_b else (sample_b, sample_a)


def make_pair_id(tier: str, sample_a: str, sample_b: str) -> str:
    """Deterministic unordered pair id. Tier is recorded but does not affect identity."""
    if tier not in VALID_TIERS:
        raise ValueError(f"invalid tier: {tier}")
    lo, hi = canonical_unordered_ids(sample_a, sample_b)
    digest = hashlib.sha256(f"{lo}|{hi}".encode("utf-8")).hexdigest()
    return f"cf_{digest[:24]}"


def unordered_pair_key(sample_a: str, sample_b: str) -> str:
    lo, hi = canonical_unordered_ids(sample_a, sample_b)
    return f"{lo}|{hi}"


def jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if hasattr(value, "item") and callable(value.item):
        try:
            return jsonable(value.item())
        except (ValueError, AttributeError):
            pass
    if isinstance(value, float) and value != value:  # NaN
        return None
    return value
