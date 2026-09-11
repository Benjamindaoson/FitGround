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
| Counterfactual readiness (released FIT-100K observational pairs) | **PARTIAL** | Phase 2 freeze: TIER A=0; TIER C appearance co-varies with measurements |
| Released FIT-100K alone cannot identify measurement-grounded counterfactual effects without garment appearance confounding | **VERIFIED** | Phase 2: TIER A=0; same-cloth measurement inconsistency=0; 1574/1731 multivariable; TIER C visual-measurement co-variation |
| Official FIT generator can conceptually hold body+design and change size via cross-drape | **VERIFIED_FROM_DOCS** | FIT paper §3.2 / Appendix B; not a runnable official repo |
| Official FIT layflat image is size-isolated | **REJECTED** | Paper §3.5: VLM try-off from sized I_try-on |
| Official FIT generation code publicly released | **NOT VERIFIED** | Not found 2026-09-11; project page promises future release |
| Controlled Fit Ladder / GPU E0 Stage 1 design | **INTERPRETED** | Experimental Contract v0.2; executable substrate is public GarmentCode |
| Pixel-level fit change (released images) | **NOT VERIFIED** | Phase 2 freeze; GPU E0 human contact sheets are the first audit |
| Memory RSS stability | **INTERPRETED** | POSSIBLE_ALLOCATOR_RETENTION — see memory trend |
