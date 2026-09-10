# Near-Duplicate Algorithm Complexity Audit

**Date:** 2026-09-10  
**Scope:** `run_closure_audit.py`, `fit_stream_pipeline.py`, `duplicates.py`

## Exact SHA256 Duplicate Detection (USED in production path)

**Implementation:** `annotate_duplicates_and_leakage()` in `fit_stream_pipeline.py`

| Step | Complexity |
|------|------------|
| `value_counts()` per modality | O(N) |
| Set of duplicated hashes | O(unique hashes) |
| `isin()` flag assignment | O(N) |
| Train ∩ eval overlap (set intersection) | O(N_train + N_eval) |

**Verdict:** Scalable for 105K. **No O(N²) pairwise comparison.**

## Cross-Split Leakage (USED)

Same set-intersection pattern on SHA256 columns and person|garment pair keys.  
**Complexity:** O(N). **Policy:** annotate only — official eval split preserved.

## Near-Image Duplicate (pHash) — NOT in closure path

**Legacy implementation:** `near_duplicate_phash_groups()` in `duplicates.py`

```python
for i, h1 in enumerate(hash_list):
    for h2 in hash_list[i + 1:]:
        if hamming(h1, h2) <= threshold: ...
```

**Complexity:** O(U²) where U = unique pHash values per modality (~≤ N).  
For 105K samples this is **naive O(N²)** and **NOT used** by:

- `scripts/run_fit_stream.py` / `fit_stream_pipeline.py`
- `scripts/run_closure_audit.py` / `closure/audit.py`

**Closure audit status field:** `near_duplicate_status: DEFERRED_TO_LOCAL_GPU_SPLIT_DESIGN_STAGE`

## Required Scalable Approaches (future local/GPU stage)

| Method | Expected complexity |
|--------|---------------------|
| Hash bucketing (pHash prefix) | O(N) candidate generation + O(bucket) |
| BK-tree | O(N log N) build, O(log N) query |
| LSH | O(N) index build |

## Evidence Grades

| Claim | Status |
|-------|--------|
| NEAR-IMAGE DUPLICATION audit complete | **PARTIAL / DEFERRED** |
| SEMANTIC IDENTITY LEAKAGE | **NOT VERIFIED** |
| Exact image duplicate (SHA256) | **IMPLEMENTED** O(N) |
| Train↔eval exact-image leakage | **IMPLEMENTED** O(N) |

## Recommendation

Do **not** claim exhaustive near-duplicate detection in Data Engineering v0.1.  
pHash values are stored in manifest for downstream scalable indexing on Windows/GPU.
