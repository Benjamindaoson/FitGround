# Data Engineering Closeout

**Status:** **GO — FROZEN AT FIT-CLEAN v0.1**  
**Snapshot:** 2026-09-10T22:48 UTC

## Problem

Build measurement-grounded audit infrastructure for FIT 100K on a 4 GB RAM / 100 GB disk VPS without persisting 213 GB raw train data.

## Final Dataset

| Split | Shards | Rows |
|-------|--------|------|
| eval | 20/20 | 5,000 |
| train | 406/406 | 100,000 |
| **Total** | 426 | **105,000** |

`data/processed/fit_clean_v0.1.parquet` — **50 MB**, SHA256 `6b998bc4…0177`

## Quality (105K)

| | VALID | SUSPICIOUS | INVALID | usable |
|---|-------|------------|---------|--------|
| ALL | 98,252 | 6,747 | 1 | 104,999 |

SUSPICIOUS ≠ unusable. See `artifacts/quality_rules_v0.1.yaml`.

## Image Integrity

1 missing person hash / 105,000; 0 corrupt; 768×1024 RGB PNG compliant. See `reports/full_fit_image_integrity.md`.

## Duplicate & Leakage

IMAGE-LEVEL exact SHA256 only. Cross-split leakage annotated (342 person-image rows); eval candidates in `artifacts/eval_leakage_candidates.parquet`. Official eval split preserved.

Semantic person-identity leakage: **NOT VERIFIED**.

## Distribution & Quantization

Small train/eval shift (KS ≤ 0.017). `bust_ease_ratio` shows discrete structure — OBSERVED, not verified as preset scaling.

## Memory & Performance

Ephemeral shard streaming; peak RSS 1.11 GB; trend **POSSIBLE_ALLOCATOR_RETENTION**. See `reports/memory_trend_analysis.md`, `reports/data_pipeline_performance.md`.

## Reproducibility

Fingerprint `artifacts/data_engineering_v0.1_fingerprint.json` — **FROZEN**. pytest 30/30.

## Known Limitations

- Near-image pHash duplicate: DEFERRED to local/GPU
- Semantic identity: no person_id in FIT
- NC-ND license: raw images not redistributable

## Handoff

- `docs/LOCAL_WINDOWS_HANDOFF.md`
- `scripts/materialize_samples.py`
- `artifacts/source_manifest.json`

## Next Phase

Measurement Counterfactual Feasibility & Experimental Contract (Windows).

---

**DATA ENGINEERING STATUS: FROZEN AT FIT-CLEAN v0.1**
