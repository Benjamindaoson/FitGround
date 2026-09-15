# Windows / Local Handoff

## 1. Clone

```bash
git clone <your-repo-url> FitGround
cd FitGround
```

## 2. Python

- Python **3.11+** (tested on 3.12.3)
- Create venv:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r artifacts/requirements.lock.txt
pip install -e ".[dev]"
```

**Reproducible lock:** `artifacts/requirements.lock.txt` (pip freeze from VPS, Python 3.12.3).  
SHA256 recorded in `artifacts/data_engineering_v0.1_fingerprint.json`.

## 3. Manifest Location

After VPS finalize completes, copy (or sync) to local:

```
data/processed/fit_clean_v0.1.parquet
artifacts/source_manifest.json
artifacts/fit_clean_schema_v0.1.json
```

**Do not copy** `data/raw/`, `data/cache/`, `data/interim/` unless needed.

## 4. Materialize Samples (no 213GB download)

```bash
python scripts/materialize_samples.py \
  --sample-id "eval/eval-00000-of-00020/0000" \
  --output-dir data/materialized/
```

## 5. Run Tests

```bash
pytest
```

## 6. Verify Manifest

```bash
python scripts/validate_manifest.py
python scripts/run_closure_audit.py   # after full 105K finalize
```

## 7. Next Research Phase

**Measurement Counterfactual Feasibility & Experimental Contract**

Question: Can FIT support controlled counterfactual pairs that test whether a multimodal model uses body–garment measurements rather than visual, identity, garment-category, or dataset-generation shortcuts?

**First local command:**

```bash
# After manifest is available locally
python scripts/validate_manifest.py
```

Then design counterfactual pair construction from `fit_clean_v0.1.parquet` — do not start VLM training on VPS.

## Path Portability

All core paths use `fitground.config.PROJECT_ROOT` (derived from package location). No hardcoded `/workspace/FitGround`.
