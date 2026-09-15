# Run 003 — OOM Failure & Bounded-Memory Streaming Redesign

**Run ID:** `run_003`  
**Stage:** Failure Analysis + Architecture Fix  
**Recorded:** 2026-09-10 (retroactive)  
**Status:** DONE (fix verified by smoke + eval re-run)

---

## 1. What This Stage Does

**Research question:** Why did the first FIT processing pipeline fail on this VPS, and what architecture is required to audit 100K without OOM or full-disk persistence?

**Why:** Without fixing root cause, any full-dataset attempt will repeat OOM or exhaust disk.

**Position:** Engineering gate between "eval works" and "100K train streaming".

---

## 2. Input / Preconditions

| Item | Value |
|------|-------|
| RAM | 3.8 GiB physical |
| Swap | Expanded to ~12 GiB (user-confirmed; exact size at expansion: NOT RECORDED in artifacts) |
| Failing approach | `pq.read_table(shard_path)` per shard + accumulate rows |
| dmesg timestamps | 2026-09-10 13:53–13:54 UTC |

---

## 3. What Was Actually Done

### Failure (old pipeline)

1. `eval_pipeline.process_eval_shards()` called `pq.read_table()` on full ~500 MB shards.
2. Processed all rows in memory before checkpoint.
3. Python process killed by OOM killer.

### Evidence from dmesg

```
[Thu Sep 10 13:53:40 2026] Out of memory: Killed process 289779 (cursor) ...
[Thu Sep 10 13:54:36 2026] Out of memory: Killed process 298204 (python)
  total-vm:5880432kB, anon-rss:1076568kB (~1.05 GB)
```

Cursor GUI also killed — indicates system-wide memory pressure on 3.8 GB RAM.

### Fix implemented

| Component | Path | Change |
|-----------|------|--------|
| Stream core | `src/fitground/data/stream_core.py` | `iter_batches(batch_size=8)`, per-image decode→hash→release |
| Memory guard | `src/fitground/data/memory.py` | RSS tracking, 1.5 GiB hard stop |
| Images | `src/fitground/data/images.py` | `audit_image_bytes()` with immediate PIL close/del |
| Eval checkpoint | `src/fitground/data/eval_checkpoint.py` | Per-shard parquet checkpoint + resume |
| Fit checkpoint | `src/fitground/data/fit_checkpoint.py` | Unified train+eval checkpoints |
| Disk guard | `src/fitground/data/disk_guard.py` | 20 GiB reserve |
| HF cache | `src/fitground/data/hf_env.py` | Pin to `data/cache/huggingface/`, ~2 GiB cap |
| Train streaming | `src/fitground/data/fit_stream_pipeline.py` | Ephemeral download → process → delete |
| CLI | `scripts/run_fit_stream.py` | `--resume`, `--smoke`, `--finalize-only` |

### Constraints enforced

- batch_size ≤ 8 (default), max 16
- workers = 1
- No `read_table()` on image columns
- Per-shard measurement load only (~250 rows)
- `gc.collect()` after each batch
- Incremental checkpoint per shard
- Resume from `data/interim/fit_checkpoint/state.json`

---

## 4. Results — Real Data

### Before fix

| Metric | Value |
|--------|-------|
| Python anon RSS at kill | ~1,076,568 KB (~1.05 GB) |
| Outcome | Process killed, audit incomplete |

### After fix (smoke test, 1 train shard)

| Metric | Value |
|--------|-------|
| RSS peak | 806,744,064 bytes (~770 MB) |
| batch_size | 4 |
| Outcome | SUCCESS |

### After fix (full eval re-run, 5000 samples)

| Metric | Value |
|--------|-------|
| RSS peak | 844,488,704 bytes (~805 MB) |
| Shards | 20 / 20 |
| Outcome | SUCCESS |

### After fix (ongoing train stream — snapshot at Run 004)

| Metric | Value |
|--------|-------|
| RSS (process) | ~522,308 KB (~510 MB) at 37 min elapsed |
| No new OOM since pipeline restart | YES (last dmesg OOM: 13:54, stream started ~16:19) |

---

## 5. Interpretation

**Observation:** Old pipeline materialized full shard tables (~500 MB) plus Python object overhead exceeded safe memory on 3.8 GB RAM.

**Interpretation:** Whole-shard image materialization violates bounded-memory requirement — not a tuning issue, an architecture issue.

**Implication:** 100K FIT *must* use shard/batch incremental processing; no shortcut via `load_dataset()` without streaming.

**Observation:** Fixed pipeline peaks ~800 MB vs 1.5 GB limit.

**Interpretation:** ~2× safety margin on current hardware — viable with swap as buffer.

---

## 6. Decision

**DECISION:** Adopt shard-by-shard streaming with ephemeral train downloads.

**WHY:** 200GB+ dataset vs 100GB disk; OOM proven on whole-shard read.

**DECISION:** RSS hard stop at 1.5 GiB with resume.

**WHY:** Prior OOM at ~1.05 GB anon; need headroom for OS + swap churn.

**DECISION:** Do not stop running pipeline for HF unauthenticated warning.

**WHY:** Warning is informational; downloads proceed successfully.

---

## 7. Failure Evidence

| Event | Evidence | Fix | Verified |
|-------|----------|-----|----------|
| Python OOM | dmesg pid 298204, anon-rss 1076568kB | `iter_batches` + immediate release | YES (eval 5K + smoke) |
| Cursor OOM | dmesg pid 289779 | Not in scope; swap expanded | PARTIAL |
| `quality_flags` numpy truthiness bug on finalize | traceback on finalize | Explicit `len()` check | YES |

---

## 8. Artifacts

| Artifact | Path |
|----------|------|
| Stream core | `src/fitground/data/stream_core.py` |
| Memory module | `src/fitground/data/memory.py` |
| Fit stream pipeline | `src/fitground/data/fit_stream_pipeline.py` |
| Tests | `tests/test_memory.py`, `tests/test_eval_streaming.py` |
| Plan doc | `reports/fit_stream_plan.md` |

---

## 9. Verification

```
pytest: 22 passed (post-redesign)
smoke test RSS: ~770 MB < 1.5 GB limit
eval re-audit: 5000 rows, peak ~805 MB
no OOM in dmesg after 16:19 UTC stream start: confirmed at Run 004 capture
```

---

## 10. What We Learned

1. `read_table()` on image-heavy parquet is fatal on 3.8 GB RAM.
2. Batch size 8 + immediate release keeps RSS ~500–800 MB.
3. Checkpoints + resume are mandatory for 406-shard train (hours-long run).
4. Swap expansion helps survival but is not a substitute for bounded memory.
5. Failures must be preserved in evidence — they justify architecture choices.

---

## 11. Project State

| Area | Status |
|------|--------|
| OOM root cause identified | DONE |
| Streaming architecture | DONE |
| Eval re-validated | DONE |
| Train streaming | IN PROGRESS (Run 004) |

---

## 12. Next Stage

**NEXT:** Full FIT train streaming (Run 004)  
**WHY NOW:** Architecture verified on eval; train requires ephemeral 406-shard loop.
