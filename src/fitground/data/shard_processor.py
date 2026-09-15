"""Process individual parquet shards into manifest rows."""

from __future__ import annotations

from typing import Any, Iterator

import pyarrow.parquet as pq

from fitground.config import SOURCE_DATASET
from fitground.data.features import compute_relational_features
from fitground.data.images import audit_image, image_ref
from fitground.data.measurements import normalize_measurements
from fitground.data.quality import classify_quality


def _image_field_to_dict(val: Any) -> Any:
    if isinstance(val, dict):
        return val
    if hasattr(val, "as_py"):
        return val.as_py()
    return val


def process_shard_rows(
    shard_path: str,
    split: str,
    shard_name: str,
    compute_phash: bool = True,
) -> Iterator[dict[str, Any]]:
    """Yield manifest-ready row dicts from a parquet shard."""
    table = pq.read_table(shard_path)
    shard_stem = shard_name.replace(".parquet", "")

    for row_id in range(table.num_rows):
        row = {col: table[col][row_id].as_py() for col in table.column_names}

        person_field = _image_field_to_dict(row.get("person"))
        cloth_field = _image_field_to_dict(row.get("cloth"))
        target_field = _image_field_to_dict(row.get("target"))

        person_audit = audit_image(person_field, compute_phash=compute_phash)
        garment_audit = audit_image(cloth_field, compute_phash=compute_phash)
        target_audit = audit_image(target_field, compute_phash=compute_phash)

        measurements = normalize_measurements(row)
        relational = compute_relational_features(measurements)
        quality_status, quality_flags = classify_quality(
            measurements, person_audit, garment_audit, target_audit, relational
        )

        sample_id = f"{SOURCE_DATASET}_{split}_{shard_stem}_{row_id:04d}"

        manifest_row: dict[str, Any] = {
            "sample_id": sample_id,
            "source_dataset": SOURCE_DATASET,
            "source_split": split,
            "source_shard": shard_name,
            "source_row_id": row_id,
            "person_image_ref": image_ref(
                split, shard_stem, row_id, "person",
                person_field.get("path") if isinstance(person_field, dict) else None,
            ),
            "garment_image_ref": image_ref(
                split, shard_stem, row_id, "garment",
                cloth_field.get("path") if isinstance(cloth_field, dict) else None,
            ),
            "target_image_ref": image_ref(
                split, shard_stem, row_id, "target",
                target_field.get("path") if isinstance(target_field, dict) else None,
            ),
            "person_md5": person_audit.md5,
            "garment_md5": garment_audit.md5,
            "target_md5": target_audit.md5,
            "person_phash": person_audit.phash,
            "garment_phash": garment_audit.phash,
            "target_phash": target_audit.phash,
            "person_width": person_audit.width,
            "person_height": person_audit.height,
            "garment_width": garment_audit.width,
            "garment_height": garment_audit.height,
            "target_width": target_audit.width,
            "target_height": target_audit.height,
            **measurements,
            **relational,
            "quality_status": quality_status,
            "quality_flags": quality_flags,
            "duplicate_record_exact": False,
            "duplicate_person_md5": False,
            "duplicate_garment_md5": False,
            "duplicate_target_md5": False,
            "duplicate_person_garment_pair": False,
            "leakage_train_eval_person": False,
            "leakage_train_eval_garment": False,
            "leakage_train_eval_target": False,
            "leakage_train_eval_pair": False,
            "usable_for_fitground": quality_status != "INVALID",
        }
        yield manifest_row
