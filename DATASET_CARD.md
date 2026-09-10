# FIT-Clean v0.1 — FitGround Dataset Card

## Dataset Source

- **Upstream:** [Yuanhao-Harry-Wang/fitvto-100k](https://huggingface.co/datasets/Yuanhao-Harry-Wang/fitvto-100k)
- **Revision:** `5563646729edf148ed2b32c4b9c794d51a1bc828`
- **License:** CC BY-NC-ND 4.0

## Raw Schema (FIT)

Parquet shards with embedded PNG images (`struct<bytes, path>`) plus 7 float measurements (cm).

## Canonical Schema (FIT-Clean)

See `artifacts/fit_clean_schema_v0.1.json` and `docs/FIT_CLEAN_DATA_CONTRACT.md`.

## Splits

| Split | Shards | Expected Rows |
|-------|--------|---------------|
| train | 406 | 100,000 |
| eval | 20 | 5,000 |
| **Total** | 426 | **105,000** |

*Actual row counts must be read from finalized manifest — see `scripts/validate_manifest.py`.*

## Image Representation

- Stored in FIT-Clean as SHA256 + pHash + dimensions (no image bytes)
- Rehydration: `scripts/materialize_samples.py`

## Quality Rules

- VALID / SUSPICIOUS / INVALID tiers
- `garment_sleeve_cm == 0` → sleeveless flag, not invalid
- Extreme fit → SUSPICIOUS, not INVALID

## Derived Features

`bust_ease_cm`, `bust_ease_ratio`, `garment_length_height_ratio`

## Duplicate / Leakage Findings

IMAGE-LEVEL SHA256 exact duplicates and train↔eval image overlap flagged. Semantic person identity leakage **NOT VERIFIED**.

## Known Limitations

- No person_id / garment_id metadata in FIT
- Near-duplicate (embedding) audit deferred to local/GPU stage
- bust_ease_ratio shows discrete concentration (quantization) — hypothesis not verified from official docs

## Storage Strategy

- Eval raw persistent (~9.9 GB)
- Train ephemeral shard download + checkpoint metadata only

## Rehydration Strategy

`materialize_samples.py` — on-demand shard fetch by locator

## Reproducibility

- Pinned HF revision in `artifacts/source_manifest.json`
- Deterministic `sample_id` contract
- Resume/checkpoint pipeline — see `reports/reproducibility_validation.md`

## Intended Use

Measurement-grounded fit research, counterfactual pair construction, leakage-controlled evaluation.

## Not Intended Use

Redistributing raw FIT images; claiming semantic identity from SHA256 alone.
