# Full FIT Duplicate & Leakage Audit

## IMAGE-LEVEL EXACT DUPLICATES
- Record exact: 0
- Person image SHA256: 3399
- Cloth image SHA256: 3225
- Target image SHA256: 3278
- Person-cloth pair: 0

## CROSS-SPLIT IMAGE LEAKAGE (train ∩ eval)
- Person: 342
- Cloth: 293
- Target: 297
- Pair: 0

**Semantic person-identity leakage is NOT VERIFIED by SHA256/pHash alone. FIT manifest has no reliable person_id metadata.**

Near-duplicate: DEFERRED_TO_LOCAL_GPU_SPLIT_DESIGN_STAGE