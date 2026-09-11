"""Control scores and confound flags for counterfactual pairs."""

from __future__ import annotations

from typing import Any

import numpy as np

from fitground.config import MEANINGFUL_GARMENT_DELTA_CM, MEASUREMENT_EQUAL_ATOL
from fitground.counterfactual.schema import BODY_VECTOR_FIELDS, GARMENT_VECTOR_FIELDS

BODY = BODY_VECTOR_FIELDS
GARMENT = GARMENT_VECTOR_FIELDS


def measurements_constant(a: dict[str, Any], b: dict[str, Any], fields: tuple[str, ...]) -> bool:
    for f in fields:
        va, vb = a[f], b[f]
        if va is None or vb is None or (isinstance(va, float) and np.isnan(va)):
            return False
        if abs(float(va) - float(vb)) > MEASUREMENT_EQUAL_ATOL:
            return False
    return True


def varying_garment_fields(a: dict[str, Any], b: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for f in GARMENT:
        if abs(float(a[f]) - float(b[f])) > MEANINGFUL_GARMENT_DELTA_CM:
            out.append(f)
    return out


def intervention_type(varying: list[str]) -> str:
    if not varying:
        return "none"
    names = [f.replace("garment_", "").replace("_cm", "") for f in varying]
    if names == ["bust"]:
        return "garment_bust_only"
    if names == ["length"]:
        return "garment_length_only"
    if names == ["sleeve"]:
        return "garment_sleeve_only"
    return "garment_" + "_and_".join(names)


def flag_list(*flags: str | None) -> list[str]:
    return [f for f in flags if f]


def confound_flags(record: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    if not record.get("same_person_image"):
        flags.append("person_image_differs")
    if not record.get("same_cloth_image"):
        flags.append("cloth_image_differs")
    if not record.get("body_measurements_constant"):
        flags.append("body_measurement_not_constant")
    if not record.get("different_target"):
        flags.append("same_target_image")
    if not record.get("single_variable_garment_change"):
        if record.get("measurement_intervention_type") == "none":
            flags.append("no_garment_measurement_change")
        else:
            flags.append("multi_variable_garment_change")
    if record.get("cross_split"):
        flags.append("cross_split_pair")
    if record.get("leakage_any"):
        flags.append("exact_image_train_eval_overlap")
    if record.get("duplicate_contamination"):
        flags.append("duplicate_image_flag")
    if record.get("pair_tier") in {"B", "C"}:
        flags.append("person_reuse_expected")
    if not record.get("quality_both_valid"):
        flags.append("non_valid_quality")
    if not record.get("usable_both"):
        flags.append("unusable_member")
    if record.get("pair_tier") == "C":
        flags.append("garment_appearance_confound")
    if record.get("pair_tier") == "D":
        flags.append("nearest_neighbor_residual_confound")
    if record.get("near_garment_phash") and not record.get("same_garment_phash"):
        flags.append("garment_family_is_near_duplicate_not_exact")
    return flags


def control_score(record: dict[str, Any]) -> float:
    """Higher is better controlled. Bounded to [0, 1]."""
    score = 0.0
    if record.get("same_person_image"):
        score += 0.34
    if record.get("same_cloth_image"):
        score += 0.34
    elif record.get("same_garment_phash"):
        score += 0.20
    elif record.get("near_garment_phash"):
        score += 0.10
    if record.get("body_measurements_constant"):
        score += 0.14
    if record.get("single_variable_garment_change"):
        score += 0.10
    elif record.get("measurement_intervention_type") not in {None, "none"}:
        score += 0.04
    if record.get("different_target"):
        score += 0.08
    if record.get("leakage_any"):
        score -= 0.12
    if record.get("duplicate_contamination"):
        score -= 0.06
    if not record.get("quality_both_valid"):
        score -= 0.04
    if record.get("cross_split"):
        score -= 0.04
    if not record.get("same_cloth_image") and record.get("pair_tier") == "C":
        score -= 0.08
    return float(max(0.0, min(1.0, score)))


def construction_reason(record: dict[str, Any]) -> str:
    tier = record.get("pair_tier")
    intervention = record.get("measurement_intervention_type")
    d_bust = record.get("delta_garment_bust_cm")
    d_ease = record.get("delta_bust_ease_cm")
    parts = [
        f"TIER {tier} candidate",
        "same person image" if record.get("same_person_image") else "different person image",
        "same cloth image" if record.get("same_cloth_image") else "different cloth image",
    ]
    if record.get("same_garment_phash"):
        parts.append("same garment pHash family")
    elif record.get("near_garment_phash"):
        parts.append(f"near garment pHash (hamming={record.get('garment_phash_hamming')})")
    parts.append("body measurements constant" if record.get("body_measurements_constant") else "body measurements differ")
    parts.append(f"intervention={intervention}")
    parts.append(f"delta_garment_bust_cm={d_bust}")
    parts.append(f"delta_bust_ease_cm={d_ease}")
    parts.append("targets differ" if record.get("different_target") else "targets identical")
    parts.append(
        "This pair is a legal measurement-counterfactual candidate because the "
        "independent variable is a garment/fit measurement change while the listed "
        "controls hold; residual confounds are recorded in confound_flags."
    )
    return "; ".join(str(p) for p in parts)
