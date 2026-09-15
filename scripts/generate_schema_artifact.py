#!/usr/bin/env python3
"""Generate artifacts/fit_clean_schema_v0.1.json from code contract."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fitground.config import ARTIFACTS_DIR, HF_REPO_ID, HF_SOURCE_REVISION
from fitground.data.identity import make_sample_id

COLUMNS = [
    {"name": "sample_id", "dtype": "string", "nullable": False,
     "meaning": "Deterministic ID: {split}/{shard_id}/{row_id:04d}",
     "derivation": "make_sample_id(source_split, source_shard_id, source_row_id)",
     "example": make_sample_id("eval", "eval-00000-of-00020", 0), "required_downstream": True},
    {"name": "source_dataset", "dtype": "string", "nullable": False,
     "meaning": "HF dataset slug", "example": "fitvto-100k", "required_downstream": True},
    {"name": "source_split", "dtype": "string", "nullable": False,
     "meaning": "train or eval", "required_downstream": True},
    {"name": "source_shard_id", "dtype": "string", "nullable": False,
     "meaning": "Parquet shard stem without extension", "required_downstream": True},
    {"name": "source_row_id", "dtype": "int32", "nullable": False,
     "meaning": "0-based row index within shard", "required_downstream": True},
    {"name": "person_image_ref", "dtype": "string", "nullable": False,
     "meaning": "Traceability ref to raw parquet person image", "required_downstream": True},
    {"name": "garment_image_ref", "dtype": "string", "nullable": False,
     "meaning": "Traceability ref to cloth image (garment)", "required_downstream": True},
    {"name": "target_image_ref", "dtype": "string", "nullable": False,
     "meaning": "Traceability ref to try-on target image", "required_downstream": True},
    {"name": "person_image_identity", "dtype": "string", "nullable": False,
     "meaning": "person:{sha256}", "required_downstream": True},
    {"name": "garment_image_identity", "dtype": "string", "nullable": False,
     "meaning": "cloth:{sha256}", "required_downstream": True},
    {"name": "target_image_identity", "dtype": "string", "nullable": False,
     "meaning": "target:{sha256}", "required_downstream": True},
    {"name": "person_sha256", "dtype": "string", "nullable": True,
     "meaning": "SHA256 of embedded person PNG bytes", "required_downstream": True},
    {"name": "garment_sha256", "dtype": "string", "nullable": True,
     "meaning": "SHA256 of embedded cloth PNG bytes", "required_downstream": True},
    {"name": "target_sha256", "dtype": "string", "nullable": True,
     "meaning": "SHA256 of embedded target PNG bytes", "required_downstream": True},
    {"name": "person_phash", "dtype": "string", "nullable": True,
     "meaning": "Perceptual hash (pHash) of person image", "required_downstream": False},
    {"name": "garment_phash", "dtype": "string", "nullable": True,
     "meaning": "pHash of cloth image", "required_downstream": False},
    {"name": "target_phash", "dtype": "string", "nullable": True,
     "meaning": "pHash of target image", "required_downstream": False},
    {"name": "body_height_cm", "dtype": "float64", "nullable": True, "unit": "cm",
     "source_field": "body_height", "required_downstream": True},
    {"name": "body_bust_cm", "dtype": "float64", "nullable": True, "unit": "cm",
     "source_field": "body_bust", "required_downstream": True},
    {"name": "body_waist_cm", "dtype": "float64", "nullable": True, "unit": "cm",
     "source_field": "body_waist", "required_downstream": True},
    {"name": "body_hips_cm", "dtype": "float64", "nullable": True, "unit": "cm",
     "source_field": "body_hips", "required_downstream": True},
    {"name": "garment_bust_cm", "dtype": "float64", "nullable": True, "unit": "cm",
     "source_field": "garment_bust", "required_downstream": True},
    {"name": "garment_length_cm", "dtype": "float64", "nullable": True, "unit": "cm",
     "source_field": "garment_length", "required_downstream": True},
    {"name": "garment_sleeve_cm", "dtype": "float64", "nullable": True, "unit": "cm",
     "source_field": "garment_sleeve_length",
     "quality_rule": "0.0 = sleeveless (flag only, not invalid)", "required_downstream": True},
    {"name": "bust_ease_cm", "dtype": "float64", "nullable": True, "unit": "cm",
     "derivation": "garment_bust_cm - body_bust_cm", "required_downstream": True},
    {"name": "bust_ease_ratio", "dtype": "float64", "nullable": True,
     "derivation": "bust_ease_cm / body_bust_cm", "required_downstream": True},
    {"name": "garment_length_height_ratio", "dtype": "float64", "nullable": True,
     "derivation": "garment_length_cm / body_height_cm", "required_downstream": True},
    {"name": "quality_status", "dtype": "string", "nullable": False,
     "meaning": "VALID | SUSPICIOUS | INVALID", "required_downstream": True},
    {"name": "quality_flags", "dtype": "list<string>", "nullable": True,
     "meaning": "Non-fatal flags e.g. sleeveless_garment, possible_duplicate", "required_downstream": True},
    {"name": "duplicate_person_sha256", "dtype": "bool", "nullable": False,
     "meaning": "IMAGE-LEVEL exact SHA256 duplicate", "required_downstream": True},
    {"name": "duplicate_garment_sha256", "dtype": "bool", "nullable": False,
     "meaning": "IMAGE-LEVEL cloth SHA256 duplicate", "required_downstream": True},
    {"name": "duplicate_target_sha256", "dtype": "bool", "nullable": False,
     "meaning": "IMAGE-LEVEL target SHA256 duplicate", "required_downstream": True},
    {"name": "duplicate_person_garment_pair", "dtype": "bool", "nullable": False,
     "meaning": "Same person+cloth SHA256 pair appears >1", "required_downstream": True},
    {"name": "duplicate_record_exact", "dtype": "bool", "nullable": False,
     "meaning": "Exact person+cloth+target SHA256 triple duplicate", "required_downstream": True},
    {"name": "leakage_train_eval_person", "dtype": "bool", "nullable": False,
     "meaning": "Same person IMAGE SHA256 in train and eval", "required_downstream": True},
    {"name": "leakage_train_eval_garment", "dtype": "bool", "nullable": False,
     "meaning": "Same cloth IMAGE SHA256 in train and eval", "required_downstream": True},
    {"name": "leakage_train_eval_target", "dtype": "bool", "nullable": False,
     "meaning": "Same target IMAGE SHA256 in train and eval", "required_downstream": True},
    {"name": "leakage_train_eval_pair", "dtype": "bool", "nullable": False,
     "meaning": "Same person+cloth pair across splits", "required_downstream": True},
    {"name": "usable_for_fitground", "dtype": "bool", "nullable": False,
     "meaning": "True iff quality_status != INVALID", "required_downstream": True},
]

schema = {
    "version": "v0.1",
    "dataset_source": HF_REPO_ID,
    "dataset_revision": HF_SOURCE_REVISION,
    "sample_id_contract": "{source_split}/{source_shard_id}/{source_row_id:04d}",
    "columns": COLUMNS,
}

ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
out = ARTIFACTS_DIR / "fit_clean_schema_v0.1.json"
out.write_text(json.dumps(schema, indent=2))
print(f"Wrote {out}")
