# Run 006 — Local Windows Handoff Validation

**Run ID:** `run_006`  
**Stage:** Phase 0 — Local Environment  
**Recorded:** 2026-09-11  
**Machine:** Windows 10, CPU only, Python 3.12.10  
**Git:** `10960f0` `merge: replace GitHub placeholder README with FitGround v0.1 release` (branch `main`, clean)

## Question

Can this Windows machine take over FIT-Clean v0.1 for Measurement Counterfactual Feasibility without downloading the 213GB FIT raw dump?

## Input

- Repo `D:\研究\FitGround`
- Manifest `data/processed/fit_clean_v0.1.parquet`
- Expected SHA256 `6b998bc4c62b53fe6a4d119cb351a49f140fa1733b432a5d8dd4f1b6a401d177`
- Source revision `5563646729edf148ed2b32c4b9c794d51a1bc828`
- Lockfile `artifacts/requirements.lock.txt` (editable Linux path stripped)
- D: free space at handoff: **181.64 GB**

## Execution

1. `git status` / `git log -1 --oneline` — clean `main`.
2. Recomputed SHA256 with Python `hashlib` and PowerShell `Get-FileHash`.
3. Created `.venv` with Python 3.12.10; installed lockfile (minus `-e /workspace/FitGround`) then `pip install -e ".[dev]"`.
4. `python scripts/validate_manifest.py`
5. `pytest`
6. Windows portability fixes (RSS via `GetProcessMemoryInfo`; disk guard defaulted to `PROJECT_ROOT` instead of `/workspace`; eval-shard tests skip when raw shards are absent). **Old tests were not deleted.**

## Results

| Check | Result |
|-------|--------|
| Manifest SHA256 | **MATCH** `6b998bc4c62b53fe6a4d119cb351a49f140fa1733b432a5d8dd4f1b6a401d177` |
| Rows | train 100000 / eval 5000 / total 105000 |
| `duplicate_sample_id` | 0 |
| `validate_manifest.py` | **PASS** |
| pytest after portability fixes | **28 passed, 2 skipped** (eval raw shards not materialized — by design) |
| FIT-Clean v0.1 modified? | **No** |

## Interpretation

**VERIFIED:** the frozen manifest is bit-identical to the VPS closeout hash. Metadata-only Phase 2 can proceed.

**OBSERVED:** two tests skip because `data/raw/fit` is empty. That is required by the 213GB download ban.

## Decision

**GO to Phase 2 structure discovery.** Do not download full FIT. Do not train.

## Artifacts

- `reports/runs/06_local_handoff_validation.md` (this file)
- `.venv/` (local, gitignored)

## Verification

Re-run: `python scripts/validate_manifest.py` must print `"status": "PASS"` and SHA256 must match.

## What We Learned

Windows RSS and `/workspace` paths were VPS-hardcoded. Handoff machines need OS-portable guards or tests skip when raw shards are absent.

## Next

Counterfactual structure discovery on the 105K metadata table.
