# Run 005 — Data Engineering Finalization & Handoff

**Run ID:** `run_005`  
**Status:** **FINAL / DONE**  
**Recorded:** 2026-09-10T22:48 UTC  
**Prior snapshots:** `05_data_engineering_closure_partial.md` (89/406), `05_data_engineering_closure_status.md`

## 1. Final Data Processed

| Split | Shards | Rows (actual) |
|-------|--------|---------------|
| Train | 406/406 | 100,000 |
| Eval | 20/20 | 5,000 |
| **Total** | 426 | **105,000** |

Manifest: `data/processed/fit_clean_v0.1.parquet` (50 MB)  
SHA256: `6b998bc4c62b53fe6a4d119cb351a49f140fa1733b432a5d8dd4f1b6a401d177`

## 2. Final Quality

| Split | VALID | SUSPICIOUS | INVALID | usable |
|-------|-------|------------|---------|--------|
| ALL | 98,252 | 6,747 | 1 | 104,999 |
| train | 93,579 | 6,421 | 0 | 100,000 |
| eval | 4,673 | 326 | 1 | 4,999 |

## 3. Leakage / Duplicate

- Exact person image dup (SHA256): 3,399 flagged rows
- Cross-split person leakage: 342 rows (316 eval candidates in `artifacts/eval_leakage_candidates.parquet`)
- Near-image duplication: **DEFERRED** (no O(N²) audit in closure path)
- Semantic identity leakage: **NOT VERIFIED**

## 4. Distribution Shift

Max KS ~0.017 (body_waist_cm); all fields show small train/eval shift. See `reports/full_fit_distribution_audit.md`.

## 5. Quantization

`bust_ease_ratio`: 11 unique @ 1dp on 105K; ~20% on 0.05 grid. **HYPOTHESIS** not verified from official docs.

## 6. Pipeline Reliability

- Peak shard RSS: 1.11 GB (< 1.5 GiB guard)
- Memory trend: **POSSIBLE_ALLOCATOR_RETENTION** (see `reports/memory_trend_analysis.md`)
- OOM post-redesign: 0

## 7. Reproducibility

- sample_id contract verified
- finalize deterministic at 105K rows
- pytest: 30/30 passed
- Fingerprint: `artifacts/data_engineering_v0.1_fingerprint.json` → **FROZEN**

## 8. What This Stage Proved

Bounded-memory audit of 213 GB FIT without persisting raw train; reproducible FIT-Clean v0.1 metadata manifest; exact-image duplicate/leakage annotation; measurement completeness.

## 9. What This Stage Cannot Prove

Semantic person identity; exhaustive near-duplicate detection; counterfactual feasibility.

## 10. Why Data Engineering Can End

All gates passed: 406/406 + finalize + validation + closure audit + fingerprint FROZEN.

**DATA ENGINEERING STATUS: FROZEN AT FIT-CLEAN v0.1**

## 11. Next Phase

Measurement Counterfactual Feasibility & Experimental Contract (Windows local). First command: `python scripts/validate_manifest.py`
