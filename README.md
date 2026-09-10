# FitGround

**FitGround: Measurement-Grounded Multimodal Garment Fit Understanding**

Research infrastructure for auditing and experimenting on the [FIT 100K](https://huggingface.co/datasets/Yuanhao-Harry-Wang/fitvto-100k) virtual try-on dataset with explicit body–garment measurements, reproducible provenance, and leakage-aware splits.

## Core Research Question

Can a multimodal model use **body–garment measurements** (not visual shortcuts, identity, garment category, or dataset-generation artifacts) to reason about fit?

FitGround builds the **data foundation** required to test that question rigorously.

## FIT-Clean v0.1 — 105,000 Samples

| Split | Shards | Rows |
|-------|--------|------|
| Train | 406 | 100,000 |
| Eval | 20 | 5,000 |
| **Total** | 426 | **105,000** |

**Manifest:** [`data/processed/fit_clean_v0.1.parquet`](data/processed/fit_clean_v0.1.parquet) (~50 MB)  
**SHA256:** `6b998bc4c62b53fe6a4d119cb351a49f140fa1733b432a5d8dd4f1b6a401d177`  
**Upstream revision:** `5563646729edf148ed2b32c4b9c794d51a1bc828`  
**Status:** `FROZEN` — see [`artifacts/data_engineering_v0.1_fingerprint.json`](artifacts/data_engineering_v0.1_fingerprint.json)

Metadata only (SHA256, pHash, measurements, quality flags). No embedded image bytes. Rehydrate samples via [`scripts/materialize_samples.py`](scripts/materialize_samples.py).

## Bounded-Memory Streaming (4 GB RAM / 100 GB Disk)

The full FIT dataset is ~213 GB — larger than our VPS disk budget. We processed it without persisting raw train shards:

1. **Eval** — 20 local shards (~10 GB), fully checkpointed  
2. **Train** — ephemeral Hugging Face download → `iter_batches(8)` → per-shard checkpoint → delete raw  
3. **Resume** — incremental parquet checkpoints + `state.json`  
4. **Finalize** — global duplicate/leakage annotation → single manifest

### OOM → Diagnosis → Redesign → 105K Completion

| Stage | What happened |
|-------|----------------|
| **Failure** | Naive `read_table()` pipeline OOM-killed at ~1.05 GB RSS (pre-redesign) |
| **Diagnosis** | Full-shard image materialization; no incremental release |
| **Redesign** | Bounded-memory streaming, 1.5 GiB RSS guard, disk reserve |
| **Result** | 406/406 train + 20/20 eval; peak shard RSS ~1.06 GB; **0 OOM** post-redesign |

See [`reports/runs/03_oom_failure_and_streaming_redesign.md`](reports/runs/03_oom_failure_and_streaming_redesign.md) and [`reports/memory_trend_analysis.md`](reports/memory_trend_analysis.md).

## Measurement Audit

- 0% missing core measurements on 105K rows  
- Derived features: `bust_ease_cm`, `bust_ease_ratio`, `garment_length_height_ratio`  
- `bust_ease_ratio` shows **observed** discrete structure (11 unique @ 1dp) — hypothesis of preset scaling **not verified** from official docs  
- Full distributions + train/eval shift: [`reports/full_fit_distribution_audit.md`](reports/full_fit_distribution_audit.md)

## Duplicate & Leakage Findings (IMAGE-LEVEL)

| Finding | Count (flagged rows) |
|---------|---------------------|
| Exact person image duplicate (SHA256) | 3,399 |
| Exact cloth image duplicate | 3,225 |
| Cross-split person image leakage | 342 |
| Eval leakage candidates | 316 rows → [`artifacts/eval_leakage_candidates.parquet`](artifacts/eval_leakage_candidates.parquet) |

**Official eval split is preserved.** Leakage is annotated, not deleted.  
**Semantic person-identity leakage: NOT VERIFIED** (no `person_id` in FIT).  
**Near-image duplicates: DEFERRED** to next phase (no O(N²) pHash audit in v0.1).

See [`reports/full_fit_duplicate_leakage_audit.md`](reports/full_fit_duplicate_leakage_audit.md).

## Quality Summary (105K)

| Status | Count |
|--------|-------|
| VALID | 98,252 |
| SUSPICIOUS | 6,747 |
| INVALID | 1 |
| usable_for_fitground | 104,999 |

Rules frozen in [`artifacts/quality_rules_v0.1.yaml`](artifacts/quality_rules_v0.1.yaml). SUSPICIOUS ≠ unusable.

## Evidence Chain

| Run | Topic |
|-----|-------|
| [Run 001](reports/runs/01_environment_and_fit_schema.md) | Environment & FIT schema |
| [Run 002](reports/runs/02_eval_measurement_audit.md) | Eval measurement audit |
| [Run 003](reports/runs/03_oom_failure_and_streaming_redesign.md) | OOM & streaming redesign |
| [Run 004](reports/runs/04_full_fit_stream_progress.md) | Full FIT stream |
| [Run 005](reports/runs/05_data_engineering_closure_final.md) | Finalization & handoff |

Closeout: [`reports/DATA_ENGINEERING_CLOSEOUT.md`](reports/DATA_ENGINEERING_CLOSEOUT.md)  
Evidence matrix: [`reports/evidence_matrix.md`](reports/evidence_matrix.md)

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r artifacts/requirements.lock.txt
pip install -e ".[dev]"

pytest
python scripts/validate_manifest.py
```

Windows handoff: [`docs/LOCAL_WINDOWS_HANDOFF.md`](docs/LOCAL_WINDOWS_HANDOFF.md)

## Next Phase

**Measurement Counterfactual Feasibility & Experimental Contract** — design controlled counterfactual pairs to test whether models use measurements vs shortcuts. Not started in this release.

## License & Attribution

Upstream FIT: CC BY-NC-ND 4.0. See [`docs/DATA_LICENSE_AND_ATTRIBUTION.md`](docs/DATA_LICENSE_AND_ATTRIBUTION.md).  
Raw FIT images are **not** redistributed in this repository.

## Citation

If you use FIT-Clean v0.1, cite the upstream FIT dataset and this repository release tag `data-v0.1`.
