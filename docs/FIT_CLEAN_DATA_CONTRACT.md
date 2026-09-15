# FIT-Clean Data Contract v0.1

**Frozen:** upon Data Engineering closure  
**Manifest:** `data/processed/fit_clean_v0.1.parquet`  
**Machine-readable schema:** `artifacts/fit_clean_schema_v0.1.json`  
**Source:** `Yuanhao-Harry-Wang/fitvto-100k` @ revision `5563646729edf148ed2b32c4b9c794d51a1bc828`

## sample_id Contract

```
sample_id = "{source_split}/{source_shard_id}/{source_row_id:04d}"
```

Example: `eval/eval-00000-of-00020/0000`

**Determinism:** Re-processing the same source row with the same pipeline version must yield the same `sample_id`.

## Image Identity

- Image identity uses `modality:sha256`, never path alone.
- `person_image_identity` = `person:{person_sha256}`
- `garment_image_identity` = `cloth:{garment_sha256}`
- `target_image_identity` = `target:{target_sha256}`

## Column Summary

See `artifacts/fit_clean_schema_v0.1.json` for per-column dtype, nullable, unit, derivation, and quality rules.

### Locators

| Column | Description |
|--------|-------------|
| `source_dataset` | `fitvto-100k` |
| `source_split` | `train` or `eval` |
| `source_shard_id` | e.g. `train-00042-of-00406` |
| `source_row_id` | 0-based index in shard |
| `*_image_ref` | Traceability string to raw parquet location |

**Note:** `source_revision` is pinned in `artifacts/source_manifest.json`, not duplicated per row.

### Measurements (cm)

All body and garment measurements are canonicalized to `*_cm` fields with identity mapping from raw FIT floats (unit: cm).

### Derived Features

| Field | Formula |
|-------|---------|
| `bust_ease_cm` | `garment_bust_cm - body_bust_cm` |
| `bust_ease_ratio` | `bust_ease_cm / body_bust_cm` |
| `garment_length_height_ratio` | `garment_length_cm / body_height_cm` |

### Quality

| `quality_status` | Meaning |
|----------------|---------|
| `VALID` | No integrity issues |
| `SUSPICIOUS` | Flagged (extreme fit, duplicate, leakage) but retained |
| `INVALID` | Integrity failure (missing image, impossible measurement) |

`usable_for_fitground = (quality_status != "INVALID")`

**SUSPICIOUS ≠ unusable** unless explicitly excluded in downstream experiment design.

### Duplicate / Leakage Flags

All duplicate and leakage flags are **IMAGE-LEVEL** (SHA256), not semantic person identity.

## Versioning

Changes to this contract require **v0.2** — no silent edits to v0.1.
