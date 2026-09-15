"""Deterministic text serialization for small causal-LM SFT."""

from __future__ import annotations

import re
from typing import Any, Mapping

FIELD_RE = re.compile(r"([A-Z_]+)=([^\s]+)")


def _fmt(value: Any) -> str:
    if value is None:
        return "NA"
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def format_transition_example(row: Mapping[str, Any], include_target: bool = True) -> str:
    prompt = (
        f"BODY_BUST={_fmt(row.get('body_bust_cm'))} "
        f"GARMENT_BUST={_fmt((row.get('garment_measurement_before') or {}).get('bust_circumference_cm'))} "
        f"GARMENT_WAIST={_fmt((row.get('garment_measurement_before') or {}).get('waist_cm'))} "
        f"GARMENT_LENGTH={_fmt((row.get('garment_measurement_before') or {}).get('length_cm'))} "
        f"GARMENT_SLEEVE={_fmt((row.get('garment_measurement_before') or {}).get('sleeve_length_cm'))} "
        f"ACTION={row.get('action_family')} "
        f"INTENDED={_fmt(row.get('intended_delta_cm'))}"
    )
    if not include_target:
        return prompt + " ->"
    after = row.get("garment_measurement_after") or {}
    target = (
        f" REALIZED={_fmt(row.get('realized_delta_cm'))} "
        f"AFTER_BUST={_fmt(after.get('bust_circumference_cm'))} "
        f"AFTER_WAIST={_fmt(after.get('waist_cm'))} "
        f"AFTER_LENGTH={_fmt(after.get('length_cm'))} "
        f"AFTER_SLEEVE={_fmt(after.get('sleeve_length_cm'))}"
    )
    return prompt + " ->" + target


def format_decision_example(row: Mapping[str, Any], include_target: bool = True) -> str:
    prompt = (
        f"BODY_BUST={_fmt(row.get('body_bust_cm'))} "
        f"GARMENT_BUST={_fmt(row.get('garment_bust_cm'))} "
        f"TARGET_BUST={_fmt(row.get('target_garment_bust_cm'))} "
        f"GARMENT_LENGTH={_fmt(row.get('garment_length_cm'))} "
        f"GARMENT_SLEEVE={_fmt(row.get('garment_sleeve_cm'))}"
    )
    if not include_target:
        return prompt + " ->"
    target = (
        f" ACTION_ID={row.get('oracle_action_id')} "
        f"INTENDED={_fmt(row.get('oracle_intended_delta_cm'))} "
        f"FAMILY={row.get('oracle_action_family')}"
    )
    return prompt + " ->" + target


def parse_generated_fields(text: str) -> dict[str, str]:
    """Parse KEY=value tokens from a prompt, continuation, or full example."""
    return {k: v for k, v in FIELD_RE.findall(text)}
