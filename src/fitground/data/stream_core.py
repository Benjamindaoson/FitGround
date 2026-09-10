"""Core bounded-memory shard streaming (shared by train/eval)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from fitground.config import SOURCE_DATASET
from fitground.data.features import compute_relational_features
from fitground.data.identity import make_image_identity, make_sample_id, shard_id_from_filename
from fitground.data.images import audit_image_bytes, image_ref
from fitground.data.measurements import normalize_measurements
from fitground.data.memory import MemoryTracker, release_memory
from fitground.data.quality import classify_quality
from fitground.data.schema import (
    CANONICAL_BODY_FIELDS,
    CANONICAL_GARMENT_FIELDS,
    CANONICAL_RELATIONAL_FIELDS,
    RAW_TO_CANONICAL,
)

MEASUREMENT_COLUMNS = tuple(RAW_TO_CANONICAL.keys())
IMAGE_COLUMNS = ("person", "cloth", "target")
DEFAULT_BATCH_SIZE = 8
MAX_BATCH_SIZE = 16


def load_shard_measurements(shard_path: Path, shard_id: str) -> dict[int, dict[str, float | None]]:
    """Load measurement columns for one shard only (~250 rows)."""
    pf = pq.ParquetFile(shard_path)
    table = pf.read(columns=list(MEASUREMENT_COLUMNS), use_threads=False)
    store: dict[int, dict[str, float | None]] = {}
    for row_id in range(table.num_rows):
        row = {col: table[col][row_id].as_py() for col in MEASUREMENT_COLUMNS}
        m = normalize_measurements(row)
        r = compute_relational_features(m)
        store[row_id] = {**m, **r}
    del table
    release_memory()
    return store


def _struct_field(struct_val: Any, field: str) -> Any:
    if isinstance(struct_val, dict):
        return struct_val.get(field)
    return None


def build_manifest_row(
    split: str,
    shard_id: str,
    row_id: int,
    person_audit: Any,
    garment_audit: Any,
    target_audit: Any,
    feat: dict[str, float | None],
) -> dict[str, Any]:
    measurements = {k: feat[k] for k in CANONICAL_BODY_FIELDS + CANONICAL_GARMENT_FIELDS}
    relational = {k: feat[k] for k in CANONICAL_RELATIONAL_FIELDS}
    quality_status, quality_flags = classify_quality(
        measurements, person_audit, garment_audit, target_audit, relational
    )
    return {
        "sample_id": make_sample_id(split, shard_id, row_id),
        "source_dataset": SOURCE_DATASET,
        "source_split": split,
        "source_shard_id": shard_id,
        "source_row_id": row_id,
        "person_image_ref": image_ref(split, shard_id, row_id, "person", person_audit.path),
        "garment_image_ref": image_ref(split, shard_id, row_id, "cloth", garment_audit.path),
        "target_image_ref": image_ref(split, shard_id, row_id, "target", target_audit.path),
        "person_image_identity": make_image_identity("person", person_audit.sha256 or ""),
        "garment_image_identity": make_image_identity("cloth", garment_audit.sha256 or ""),
        "target_image_identity": make_image_identity("target", target_audit.sha256 or ""),
        "person_sha256": person_audit.sha256,
        "garment_sha256": garment_audit.sha256,
        "target_sha256": target_audit.sha256,
        "person_phash": person_audit.phash,
        "garment_phash": garment_audit.phash,
        "target_phash": target_audit.phash,
        "person_format": person_audit.format,
        "garment_format": garment_audit.format,
        "target_format": target_audit.format,
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
        "duplicate_person_sha256": False,
        "duplicate_garment_sha256": False,
        "duplicate_target_sha256": False,
        "duplicate_person_garment_pair": False,
        "duplicate_record_exact": False,
        "leakage_train_eval_person": False,
        "leakage_train_eval_garment": False,
        "leakage_train_eval_target": False,
        "leakage_train_eval_pair": False,
        "usable_for_fitground": quality_status != "INVALID",
    }


def process_shard_streaming(
    shard_path: Path,
    split: str,
    measurements: dict[int, dict[str, float | None]],
    *,
    batch_size: int = DEFAULT_BATCH_SIZE,
    max_rows: int | None = None,
    tracker: MemoryTracker | None = None,
) -> list[dict[str, Any]]:
    batch_size = min(max(1, batch_size), MAX_BATCH_SIZE)
    shard_id = shard_id_from_filename(shard_path.name)
    pf = pq.ParquetFile(shard_path)
    rows: list[dict[str, Any]] = []
    row_offset = 0

    for batch in pf.iter_batches(batch_size=batch_size, columns=list(IMAGE_COLUMNS), use_threads=False):
        if tracker:
            tracker.check_limit(shard_id)
        n = batch.num_rows
        limit = n
        if max_rows is not None:
            remaining = max_rows - row_offset
            if remaining <= 0:
                break
            limit = min(n, remaining)

        for i in range(limit):
            row_id = row_offset + i
            feat = measurements[row_id]
            person_struct = batch.column("person")[i].as_py()
            cloth_struct = batch.column("cloth")[i].as_py()
            target_struct = batch.column("target")[i].as_py()

            pb = _struct_field(person_struct, "bytes")
            person_audit = audit_image_bytes(
                bytes(pb) if pb else None, _struct_field(person_struct, "path")
            )
            del pb, person_struct

            gb = _struct_field(cloth_struct, "bytes")
            garment_audit = audit_image_bytes(
                bytes(gb) if gb else None, _struct_field(cloth_struct, "path")
            )
            del gb, cloth_struct

            tb = _struct_field(target_struct, "bytes")
            target_audit = audit_image_bytes(
                bytes(tb) if tb else None, _struct_field(target_struct, "path")
            )
            del tb, target_struct

            rows.append(
                build_manifest_row(
                    split, shard_id, row_id, person_audit, garment_audit, target_audit, feat
                )
            )
            del person_audit, garment_audit, target_audit

        row_offset += limit
        del batch
        release_memory()
        if tracker:
            tracker.sample(shard_id)
        if max_rows is not None and row_offset >= max_rows:
            break

    return rows
