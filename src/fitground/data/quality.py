"""Quality classification: VALID / SUSPICIOUS / INVALID."""

from __future__ import annotations

from fitground.config import (
    BUST_EASE_CM_SUSPICIOUS_HIGH,
    BUST_EASE_CM_SUSPICIOUS_LOW,
    BUST_EASE_RATIO_SUSPICIOUS_HIGH,
    BUST_EASE_RATIO_SUSPICIOUS_LOW,
    EXPECTED_IMAGE_HEIGHT,
    EXPECTED_IMAGE_WIDTH,
)
from fitground.data.images import ImageAuditResult
from fitground.data.measurements import is_impossible_measurement
CORE_MEASUREMENT_FIELDS = (
    "body_height_cm",
    "body_bust_cm",
    "body_waist_cm",
    "body_hips_cm",
    "garment_bust_cm",
    "garment_length_cm",
    "garment_sleeve_cm",
)


def classify_quality(
    measurements: dict[str, float | None],
    person_audit: ImageAuditResult,
    garment_audit: ImageAuditResult,
    target_audit: ImageAuditResult,
    relational: dict[str, float | None],
) -> tuple[str, list[str]]:
    flags: list[str] = []
    invalid_reasons: list[str] = []

    for role, audit in (
        ("person", person_audit),
        ("garment", garment_audit),
        ("target", target_audit),
    ):
        if not audit.present:
            invalid_reasons.append(f"missing_{role}_image")
        elif not audit.decodable:
            invalid_reasons.append(f"corrupt_{role}_image")
        elif audit.width != EXPECTED_IMAGE_WIDTH or audit.height != EXPECTED_IMAGE_HEIGHT:
            flags.append(f"unusual_{role}_dimensions_{audit.width}x{audit.height}")

    for field in CORE_MEASUREMENT_FIELDS:
        val = measurements.get(field)
        if val is None:
            invalid_reasons.append(f"missing_{field}")
        elif is_impossible_measurement(field, val):
            invalid_reasons.append(f"impossible_{field}_{val}")

    informational: list[str] = []
    suspicious: list[str] = []

    # garment_sleeve_cm == 0 is valid (sleeveless) — informational flag only.
    sleeve = measurements.get("garment_sleeve_cm")
    if sleeve is not None and sleeve == 0.0:
        informational.append("sleeveless_garment")

    if invalid_reasons:
        return "INVALID", invalid_reasons + flags + informational

    bust_ease = relational.get("bust_ease_cm")
    if bust_ease is not None:
        if bust_ease < BUST_EASE_CM_SUSPICIOUS_LOW or bust_ease > BUST_EASE_CM_SUSPICIOUS_HIGH:
            suspicious.append(f"extreme_bust_ease_{bust_ease:.1f}cm")

    bust_ease_ratio = relational.get("bust_ease_ratio")
    if bust_ease_ratio is not None:
        if (
            bust_ease_ratio < BUST_EASE_RATIO_SUSPICIOUS_LOW
            or bust_ease_ratio > BUST_EASE_RATIO_SUSPICIOUS_HIGH
        ):
            suspicious.append(f"extreme_bust_ease_ratio_{bust_ease_ratio:.3f}")

    all_flags = flags + suspicious + informational
    if suspicious or flags:
        return "SUSPICIOUS", all_flags
    return "VALID", all_flags
