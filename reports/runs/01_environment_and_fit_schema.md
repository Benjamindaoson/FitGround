# Run 001 — Environment & FIT Schema Audit

**Run ID:** `run_001`  
**Stage:** Environment Audit + FIT Schema Discovery  
**Recorded:** 2026-09-10 (retroactive evidence capture)  
**Status:** DONE

---

## 1. What This Stage Does

**Stage name:** Environment & Schema Audit (Phase 0–1)

**Research question:** Can we access FIT (`Yuanhao-Harry-Wang/fitvto-100k`) on this VPS, understand its true schema, and determine whether full local persistence is feasible?

**Why needed:** FitGround requires measurement-grounded audit of person/garment/try-on triplets. All downstream cleaning, feature engineering, leakage control, and counterfactual construction depend on knowing the *actual* repository layout — not paper assumptions.

**Position in FitGround:** Foundation layer. Failure here blocks all data engineering.

**If this fails:** Cannot proceed to integrity audit, FIT-Clean manifest, or any model baseline.

---

## 2. Input / Preconditions

| Item | Value |
|------|-------|
| Dataset | `Yuanhao-Harry-Wang/fitvto-100k` (Hugging Face) |
| Host | Ubuntu 24.04.4 LTS, kernel 6.8.0-138-generic |
| Python | 3.12.3 |
| RAM | 3.8 GiB (later expanded swap to ~12 GiB — see Run 003) |
| Disk total | ~99 GB (`/dev/vda1`) |
| Disk free (initial audit) | ~84.9 GB (`84896509952` bytes, `reports/environment_audit.json`) |
| Git HEAD | NO_COMMIT (repo initialized, not yet committed) |
| HF repo accessible | Yes (ping + `dataset_info` succeeded) |

**Storage constraint (from `reports/storage_audit.json`):**

| Metric | Bytes | GB |
|--------|-------|-----|
| Full dataset required | 212,586,373,905 | ~212.6 |
| Train required | 202,588,693,900 | ~202.6 |
| Eval required | 9,997,680,005 | ~10.0 |
| Available at audit | 84,894,900,224 | ~84.9 |
| Shortfall (full) | 127,691,473,681 | ~127.7 |

**Decision precondition:** `can_download_full: false`, `can_download_eval: true`, strategy `eval_persistent_train_ephemeral`.

---

## 3. What Was Actually Done

1. Inspected HF repository via `huggingface_hub.dataset_info()` — 426 parquet siblings (406 train + 20 eval).
2. Streamed one train sample via `datasets.load_dataset(..., streaming=True)` to confirm field names and types.
3. Downloaded one train shard (`train-00000-of-00406.parquet`, ~504 MB) to measure bytes/row.
4. Downloaded README.md for official documentation cross-check.
5. Wrote `reports/fit_schema_audit.md`, `reports/storage_audit.json`, `reports/environment_audit.json`.

**No full dataset download attempted** after shortfall calculation.

---

## 4. Results — Real Data

### Repository layout

- **Format:** Parquet shards with embedded PNG images
- **Train:** 406 shards, expected 100,000 rows
- **Eval:** 20 shards, expected 5,000 rows
- **Single shard sample:** `train-00000-of-00406.parquet` = 504,216,699 bytes, 247 rows → ~2.04 MB/row

### Confirmed schema (from streaming sample + shard read)

| Field | Type | Unit |
|-------|------|------|
| `cloth` | HF Image `struct(bytes, path)` | 768×1024 RGB PNG |
| `target` | HF Image `struct(bytes, path)` | 768×1024 RGB PNG |
| `person` | HF Image `struct(bytes, path)` | 768×1024 RGB PNG |
| `body_bust` | float32 | cm |
| `body_height` | float32 | cm |
| `body_hips` | float32 | cm |
| `body_waist` | float32 | cm |
| `garment_bust` | float32 | cm |
| `garment_length` | float32 | cm |
| `garment_sleeve_length` | float32 | cm |

**Note:** README describes folder layout (`cloth/`, `target/`, `metadata.jsonl`); actual HF distribution uses embedded-image Parquet only.

### Eval local persistence (later confirmed)

- 20 eval shards on disk: `data/raw/fit/data/eval-*.parquet`
- Raw size: **~9.9 GB**

---

## 5. Interpretation

**Observation:** Full FIT requires ~213 GB; VPS has ~99 GB total and ~59–85 GB free depending on time.

**Interpretation:** Complete local mirror of FIT 100K is infeasible on this machine without external storage.

**Implication:** Train must use ephemeral shard download or streaming; eval can persist locally (~10 GB).

**Observation:** Schema uses embedded images, not separate image folders.

**Interpretation:** Audit pipeline must decode from Parquet struct bytes per row/batch — cannot assume filesystem image paths as primary identity.

---

## 6. Decision

**DECISION:** Eval persistent locally; train ephemeral shard-by-shard processing.

**WHY:** Storage shortfall ~128 GB for full dataset; eval fits within budget and provides official 5K holdout.

**DECISION:** Canonical measurement unit = cm (identity mapping, no silent conversion).

**WHY:** README + value inspection (e.g. body_height ≈ 176) confirm cm.

---

## 7. Failure Evidence

None at this stage. Storage constraint identified *before* attempting full download (intentional gate).

---

## 8. Artifacts

| Artifact | Path |
|----------|------|
| Environment audit | `reports/environment_audit.json` |
| Storage audit | `reports/storage_audit.json` |
| Schema audit | `reports/fit_schema_audit.md` |
| Raw eval shards | `data/raw/fit/data/eval-*.parquet` |
| Schema code | `src/fitground/data/schema.py` |
| Config | `src/fitground/config.py` |

---

## 9. Verification

- HF repository reachable: YES
- Schema confirmed from live sample: YES
- Storage math documented: YES
- Full download avoided when infeasible: YES

---

## 10. What We Learned

1. FIT on HF is Parquet+embedded PNG, not folder-based images.
2. Full 100K local copy is impossible on 100 GB VPS (~128 GB short).
3. Eval (~10 GB) is the only split that can be kept raw locally.
4. Measurement fields are flat floats in cm — suitable for canonical schema mapping.
5. Per-row storage ~2 MB implies strict bounded-memory processing is mandatory.

---

## 11. Project State

| Area | Status |
|------|--------|
| Environment documented | DONE |
| Schema confirmed | DONE |
| Full raw FIT local | BLOCKED (storage) |
| Eval raw local | DONE |
| Train raw local | NOT PLANNED |

**Can prove:** FIT schema, units, storage constraints, eval accessibility.  
**Cannot prove yet:** Full 100K audit, global leakage, train distribution.

---

## 12. Next Stage

**NEXT:** Eval-only measurement & integrity audit (Run 002)  
**QUESTION:** Is official eval measurement-complete and fit-varied enough to validate pipeline?  
**INPUT:** 20 local eval shards  
**OUTPUT:** `fit_eval_clean_v0.1.parquet`, audit reports  
**WHY NOW:** Eval fits on disk and provides ground-truth holdout before scaling to 100K train via streaming.
