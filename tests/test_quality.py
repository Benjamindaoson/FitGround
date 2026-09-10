"""Tests for quality classification."""

from fitground.data.images import ImageAuditResult
from fitground.data.quality import classify_quality


def _good_image() -> ImageAuditResult:
    return ImageAuditResult(
        present=True, decodable=True, width=768, height=1024,
        mode="RGB", format="PNG", sha256="abc", phash="0000000000000000",
        path="000000.png", error=None,
    )


def test_valid_sample() -> None:
    measurements = {
        "body_height_cm": 170.0, "body_bust_cm": 90.0,
        "body_waist_cm": 70.0, "body_hips_cm": 95.0,
        "garment_bust_cm": 100.0, "garment_length_cm": 60.0,
        "garment_sleeve_cm": 25.0,
    }
    relational = {"bust_ease_cm": 10.0, "bust_ease_ratio": 0.11}
    status, flags = classify_quality(
        measurements, _good_image(), _good_image(), _good_image(), relational
    )
    assert status == "VALID"
    assert flags == []


def test_invalid_missing_image() -> None:
    bad = ImageAuditResult(
        present=False, decodable=False, width=None, height=None,
        mode=None, format=None, sha256=None, phash=None, path=None,
        error="missing_bytes",
    )
    measurements = {
        "body_height_cm": 170.0, "body_bust_cm": 90.0,
        "body_waist_cm": 70.0, "body_hips_cm": 95.0,
        "garment_bust_cm": 100.0, "garment_length_cm": 60.0,
        "garment_sleeve_cm": 0.0,
    }
    status, flags = classify_quality(
        measurements, bad, _good_image(), _good_image(), {}
    )
    assert status == "INVALID"
    assert any("missing_person_image" in f for f in flags)


def test_sleeveless_not_invalid() -> None:
    measurements = {
        "body_height_cm": 170.0, "body_bust_cm": 90.0,
        "body_waist_cm": 70.0, "body_hips_cm": 95.0,
        "garment_bust_cm": 100.0, "garment_length_cm": 60.0,
        "garment_sleeve_cm": 0.0,
    }
    relational = {"bust_ease_cm": 10.0, "bust_ease_ratio": 0.11}
    status, flags = classify_quality(
        measurements, _good_image(), _good_image(), _good_image(), relational
    )
    assert status == "VALID"
    assert "sleeveless_garment" in flags


def test_suspicious_extreme_ease() -> None:
    measurements = {
        "body_height_cm": 170.0, "body_bust_cm": 90.0,
        "body_waist_cm": 70.0, "body_hips_cm": 95.0,
        "garment_bust_cm": 200.0, "garment_length_cm": 60.0,
        "garment_sleeve_cm": 0.0,
    }
    relational = {"bust_ease_cm": 110.0, "bust_ease_ratio": 1.22}
    status, flags = classify_quality(
        measurements, _good_image(), _good_image(), _good_image(), relational
    )
    assert status == "SUSPICIOUS"
