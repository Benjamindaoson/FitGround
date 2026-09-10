# Public Release Safety Check

**Date:** 2026-09-10  
**Status:** PRE-GITHUB (awaiting user instruction to upload)

## Secrets Scan

| Pattern | Found in committed/staged code? |
|---------|--------------------------------|
| HF_TOKEN | No |
| API keys | No |
| Passwords | No |
| `.env` with secrets | No |

## Must NOT Commit to GitHub

- `data/raw/` — FIT eval parquet (~9.9 GB)
- `data/cache/` — HF hub cache
- `data/interim/` — checkpoints, ephemeral shards
- `data/processed/fit_clean_v0.1.parquet` — TBD by size + license (eval manifest ~2.6 MB may be OK)
- `.venv/`
- Extracted images under `data/materialized/`
- `reports/evidence_samples/*.png` (if any created locally)

## Safe to Commit

- `src/`, `tests/`, `scripts/`
- `docs/`, `DATASET_CARD.md`
- `artifacts/fit_clean_schema_v0.1.json`, `artifacts/source_manifest.json`
- `data/samples/fit_clean_demo.parquet` (50 rows, no images)
- `reports/runs/`, `reports/evidence_ledger.md`, audit markdown/json
- `reports/figures/` — distribution plots (no raw images)

## License Constraints

See `docs/DATA_LICENSE_AND_ATTRIBUTION.md` — CC BY-NC-ND 4.0: raw images must not be redistributed.

## Path Hygiene

Core code uses `PROJECT_ROOT` via `fitground.config` — no hardcoded `/workspace/FitGround` in pipeline modules.

Historical run reports may reference absolute paths for evidence preservation.

## .gitignore

Covers: `.venv/`, `data/raw/`, `data/interim/`, `data/processed/`, `data/cache/`, `reports/figures/`
