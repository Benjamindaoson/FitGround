"""FIT dataset schema definitions and field mapping."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pyarrow as pa

# Official FIT schema (confirmed from eval audit).
RAW_IMAGE_FIELDS: dict[str, str] = {
    "cloth": "HF Image struct(bytes: binary, path: string) — layflat garment",
    "target": "HF Image struct(bytes: binary, path: string) — person wearing garment",
    "person": "HF Image struct(bytes: binary, path: string) — garment-agnostic person",
}

RAW_MEASUREMENT_FIELDS: dict[str, str] = {
    "body_bust": "float, cm",
    "body_height": "float, cm",
    "body_hips": "float, cm",
    "body_waist": "float, cm",
    "garment_bust": "float, cm",
    "garment_length": "float, cm",
    "garment_sleeve_length": "float, cm",
}

MEASUREMENT_UNIT = "cm"

CANONICAL_BODY_FIELDS = (
    "body_height_cm",
    "body_bust_cm",
    "body_waist_cm",
    "body_hips_cm",
)

CANONICAL_GARMENT_FIELDS = (
    "garment_bust_cm",
    "garment_length_cm",
    "garment_sleeve_cm",
)

CANONICAL_RELATIONAL_FIELDS = (
    "bust_ease_cm",
    "bust_ease_ratio",
    "garment_length_height_ratio",
)

# Raw parquet column → canonical mapping.
RAW_TO_CANONICAL: dict[str, str] = {
    "body_height": "body_height_cm",
    "body_bust": "body_bust_cm",
    "body_waist": "body_waist_cm",
    "body_hips": "body_hips_cm",
    "garment_bust": "garment_bust_cm",
    "garment_length": "garment_length_cm",
    "garment_sleeve_length": "garment_sleeve_cm",
}

IMAGE_FIELDS = ("person", "cloth", "target")
MODALITY_MAP = {"person": "person", "cloth": "cloth", "target": "target"}

RAW_PARQUET_SCHEMA_FIELDS = ("cloth", "target", "person") + tuple(RAW_TO_CANONICAL.keys())


@dataclass(frozen=True)
class ImageAuditResult:
    present: bool
    decodable: bool
    width: int | None
    height: int | None
    mode: str | None
    format: str | None
    sha256: str | None
    phash: str | None
    path: str | None
    error: str | None


def parquet_schema_description() -> dict[str, Any]:
    return {
        "format": "parquet",
        "image_representation": "struct<bytes: binary, path: string>",
        "image_resolution": "768x1024 RGB PNG (typical)",
        "measurement_unit": MEASUREMENT_UNIT,
        "raw_image_fields": RAW_IMAGE_FIELDS,
        "raw_measurement_fields": RAW_MEASUREMENT_FIELDS,
        "canonical_mapping": RAW_TO_CANONICAL,
        "eval_split": {"shards": 20, "expected_rows": 5_000},
    }


def eval_manifest_arrow_schema() -> pa.Schema:
    fields: list[tuple[str, pa.DataType]] = [
        ("sample_id", pa.string()),
        ("source_dataset", pa.string()),
        ("source_split", pa.string()),
        ("source_shard_id", pa.string()),
        ("source_row_id", pa.int32()),
        ("person_image_ref", pa.string()),
        ("garment_image_ref", pa.string()),
        ("target_image_ref", pa.string()),
        ("person_image_identity", pa.string()),
        ("garment_image_identity", pa.string()),
        ("target_image_identity", pa.string()),
        ("person_sha256", pa.string()),
        ("garment_sha256", pa.string()),
        ("target_sha256", pa.string()),
        ("person_phash", pa.string()),
        ("garment_phash", pa.string()),
        ("target_phash", pa.string()),
        ("person_format", pa.string()),
        ("garment_format", pa.string()),
        ("target_format", pa.string()),
        ("person_width", pa.int32()),
        ("person_height", pa.int32()),
        ("garment_width", pa.int32()),
        ("garment_height", pa.int32()),
        ("target_width", pa.int32()),
        ("target_height", pa.int32()),
    ]
    for f in CANONICAL_BODY_FIELDS + CANONICAL_GARMENT_FIELDS + CANONICAL_RELATIONAL_FIELDS:
        fields.append((f, pa.float64()))
    fields.extend(
        [
            ("quality_status", pa.string()),
            ("quality_flags", pa.list_(pa.string())),
            ("duplicate_person_sha256", pa.bool_()),
            ("duplicate_garment_sha256", pa.bool_()),
            ("duplicate_target_sha256", pa.bool_()),
            ("duplicate_person_garment_pair", pa.bool_()),
            ("duplicate_record_exact", pa.bool_()),
            ("leakage_train_eval_person", pa.bool_()),
            ("leakage_train_eval_garment", pa.bool_()),
            ("leakage_train_eval_target", pa.bool_()),
            ("leakage_train_eval_pair", pa.bool_()),
            ("usable_for_fitground", pa.bool_()),
        ]
    )
    return pa.schema(fields)
