# Reproducibility Validation

**Status:** VERIFIED (105K finalize complete)

## 1. Same Shard Twice

**Test:** `tests/test_determinism.py` — PASS

## 2. Checkpoint Resume

Verified during Run 004: `--resume` skips completed shards.

## 3. Interrupted State

`stopped_reason` on MemoryLimitError/DiskSpaceError. OOM post-redesign: 0.

## 4. Finalize Determinism

**VERIFIED:** `fit_clean_v0.1.parquet` — 105,000 rows, 0 duplicate sample_id, validation PASS.

Note: eval/train checkpoint schemas differed (leakage cols); `assemble_manifest()` unifies to target schema before concat.

## 5. Duplicate Annotation Determinism

**Test:** `tests/test_eval_pipeline.py::test_duplicate_annotation` — PASS

## sample_id Contract

`{source_split}/{source_shard_id}/{source_row_id:04d}` — frozen in v0.1 artifacts.

## Source Revision

`5563646729edf148ed2b32c4b9c794d51a1bc828` in `artifacts/source_manifest.json`
