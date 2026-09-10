"""Tests for schema definitions."""

from fitground.data.schema import RAW_TO_CANONICAL, eval_manifest_arrow_schema, parquet_schema_description


def test_canonical_mapping_complete() -> None:
    assert len(RAW_TO_CANONICAL) == 7
    assert RAW_TO_CANONICAL["body_height"] == "body_height_cm"
    assert RAW_TO_CANONICAL["garment_sleeve_length"] == "garment_sleeve_cm"


def test_manifest_schema_has_required_fields() -> None:
    schema = eval_manifest_arrow_schema()
    names = set(schema.names)
    required = {
        "sample_id", "source_split", "person_image_identity", "person_sha256",
        "body_height_cm", "garment_bust_cm", "bust_ease_cm", "quality_status",
        "usable_for_fitground",
    }
    assert required.issubset(names)


def test_parquet_schema_description() -> None:
    desc = parquet_schema_description()
    assert desc["measurement_unit"] == "cm"
    assert desc["eval_split"]["expected_rows"] == 5_000
