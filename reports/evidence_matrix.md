# Evidence Matrix

| Claim | Level | Evidence |
|-------|-------|----------|
| FIT schema is Parquet + embedded PNG | **VERIFIED** | Run 001, `fit_schema_audit.md` |
| Measurements in cm | **VERIFIED** | Run 001, README |
| Full measurement completeness | **VERIFIED** | 105K manifest: 0% missing core fields |
| Full image integrity | **VERIFIED** | 1 missing / 105K; 0 corrupt (`closure_audit.json`) |
| bust_ease variation | **OBSERVED** | -14.9 to +86.7 cm flagged extremes |
| bust_ease_ratio quantization | **OBSERVED** | 11 unique @ 1dp; ~20% on 0.05 grid |
| Preset garment scaling levels | **HYPOTHESIZED** | NOT verified from official docs |
| Exact image duplicates | **VERIFIED** | SHA256 group/join O(N) on 105K |
| Near-image duplicates | **NOT VERIFIED** | DEFERRED — no scalable index in v0.1 |
| Train/eval exact-image leakage | **VERIFIED** | 342 person-image cross-split flags |
| Semantic person identity leakage | **NOT VERIFIED** | No person_id in FIT |
| Bounded-memory viability | **VERIFIED** | Peak 1.11 GB, 0 OOM post-redesign |
| Full 105K completion | **VERIFIED** | 406/406 + finalize + validation PASS |
| Reproducibility (sample_id, finalize) | **VERIFIED** | `test_determinism.py`, fingerprint FROZEN |
| Counterfactual readiness | **NOT VERIFIED** | Next research phase |
| Memory RSS stability | **INTERPRETED** | POSSIBLE_ALLOCATOR_RETENTION — see memory trend |
