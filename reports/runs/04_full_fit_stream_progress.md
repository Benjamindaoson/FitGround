# Run 004 — Full FIT Train Streaming (In Progress)

**Run ID:** `run_004`  
**Stage:** Train Shard Streaming → Global FIT-Clean  
**Recorded:** 2026-09-10T16:56 UTC (live snapshot)  
**Status:** PARTIAL (in progress)

---

## 1. What This Stage Does

**Research question:** Can we audit all 100K FIT train samples on a 100 GB / 3.8 GB RAM VPS without persisting raw train data, producing a unified FIT-Clean manifest with hashes, quality flags, and relational features?

**Why:** FitGround requires full-dataset duplicate/leakage audit and train distribution — eval alone is insufficient.

**Position:** Core data engineering stage between eval validation and counterfactual feasibility.

**If this fails:** Global FIT-Clean, train/eval leakage quantification, and 100K EDA remain blocked.

---

## 2. Input / Preconditions

| Item | Value |
|------|-------|
| Command | `.venv/bin/python scripts/run_fit_stream.py --no-eval --batch-size 8 --resume` |
| PID | 309342 |
| Started | ~2026-09-10 16:19 UTC (from `ps` elapsed at capture) |
| batch_size | 8 |
| workers | 1 |
| Eval raw | Local, not re-downloaded |
| Train strategy | Ephemeral HF download per shard (~500 MB) → delete after checkpoint |
| HF cache | `data/cache/huggingface/` |
| Git HEAD | NO_COMMIT |
| Python | 3.12.3 |

### Resources at capture (2026-09-10T16:56 UTC)

| Resource | Value |
|----------|-------|
| RAM total | 3.8 GiB |
| RAM available | ~2.1 GiB |
| Swap used | 1.8 / 11 GiB |
| Disk free | 59 GB |
| data/interim | ~980 MB |
| data/raw/fit | ~9.9 GB |

---

## 3. What Is Actually Happening

1. Eval checkpoints: pre-completed (20/20), skipped via `--no-eval`.
2. Train loop: for each shard 0–405, download if not local → `iter_batches(8)` → checkpoint → delete ephemeral raw.
3. Resume: skips shards in `data/interim/fit_checkpoint/state.json`.
4. No second pipeline instance.
5. No finalize invoked (correct — train incomplete).

### Log state

```
Warning: You are sending unauthenticated requests to the HF Hub...
```

No traceback, no 429, no fatal error in `reports/fit_stream_run.log`.

---

## 4. Results — Live Snapshot

| Metric | Value |
|--------|-------|
| **Process running** | YES (PID 309342) |
| **Elapsed** | 37:02 |
| **CPU** | 66.2% |
| **Process RSS** | 522,308 KB (~510 MB) |
| **Eval checkpoints** | 20 / 20 |
| **Train checkpoints** | 57 / 406 |
| **Latest train shard** | `train-00056-of-00406.parquet` |
| **Samples in checkpoints (approx)** | 20×250 + 57×~246 ≈ 19,042 (exact row counts per shard vary; NOT individually verified at this snapshot) |
| **OOM since stream start** | 0 (last dmesg OOM: 13:54 UTC, before stream) |
| **HF errors** | None fatal (unauthenticated warning only) |
| **Disk anomaly** | None (59 GB free stable) |

### Throughput estimate (NOT RECORDED precisely — approximate)

~57 shards in ~37 min ≈ 1.5 shards/min → ETA for remaining 349 shards ≈ **~3.9 hours** (rough; network variance unknown).

---

## 5. Interpretation

**Observation:** RSS stable ~510 MB at 37 min, well below 1.5 GB limit and prior OOM threshold.

**Interpretation:** Bounded-memory architecture is holding under sustained train load.

**Implication:** No code intervention needed while metrics remain stable.

**Observation:** 57/406 train shards in ~37 min.

**Interpretation:** Full train pass is multi-hour batch job — checkpoint/resume design is essential.

**Implication:** Do not finalize until 406/406; interruption can resume safely.

---

## 6. Decision

**DECISION:** Do not stop, restart, or modify running pipeline.

**WHY:** Healthy progress, stable RSS, no errors, checkpoints accumulating.

**DECISION:** Do not run `--finalize-only` until train 406/406 + eval 20/20.

**WHY:** Premature finalize would produce incomplete FIT-Clean.

---

## 7. Failure Evidence

None during current run (Run 004). Prior OOM documented in Run 003.

---

## 8. Artifacts (current)

| Artifact | Path |
|----------|------|
| Stream log | `reports/fit_stream_run.log` |
| Checkpoint state | `data/interim/fit_checkpoint/state.json` |
| Train checkpoints | `data/interim/fit_checkpoint/train-*.parquet` (57 files) |
| Eval checkpoints | `data/interim/fit_checkpoint/eval-*.parquet` (20 files) |
| Plan | `reports/fit_stream_plan.md` |
| Code | `scripts/run_fit_stream.py`, `src/fitground/data/fit_stream_pipeline.py` |

**Not yet generated:**

- `data/processed/fit_clean_v0.1.parquet` (awaiting 406/406)
- Global EDA figures for full 105K

---

## 9. Verification

| Check | Result |
|-------|--------|
| `pgrep run_fit_stream` | PID 309342 active |
| Checkpoint count increasing | YES (2 → 57 over session) |
| RSS < 1.5 GB | YES (~510 MB) |
| New OOM in dmesg | NO |
| pytest | 22 passed (last run before this snapshot) |

---

## 10. What We Learned (so far)

1. Ephemeral train shard loop works on this VPS without full raw persistence.
2. RSS remains ~500–800 MB — architecture fix from Run 003 is effective at scale.
3. HF unauthenticated access is sufficient for current download rate.
4. ~14% train complete at 37 min — full run is hours, not minutes.
5. Evidence capture must not disturb long-running jobs.

---

## 11. Project State

| Area | Status |
|------|--------|
| Eval audit + manifest | DONE |
| Train streaming | PARTIAL (57/406) |
| Global FIT-Clean | BLOCKED |
| Duplicate/leakage (full) | BLOCKED |
| Counterfactual feasibility | BLOCKED |

**Can prove now:** Eval measurement completeness, fit variation, streaming viability.  
**Cannot prove yet:** Full 100K distributions, global train/eval leakage, 105K duplicate rates.

---

## 12. Next Stage

**WHEN train 406/406:**

```bash
.venv/bin/python scripts/run_fit_stream.py --finalize-only
```

**THEN:** Global duplicate/leakage audit, FIT-Clean manifest, EDA, readiness decision (GO/PARTIAL/NO-GO).

**AFTER FIT-Clean:** Measurement Counterfactual Feasibility Study.
