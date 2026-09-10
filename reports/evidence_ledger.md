# FitGround Evidence Ledger

Project-wide provenance index. **Append-only — do not overwrite history.**

| Date | Run ID | Stage | Question | Input | Main Result | Decision | Artifacts | Status | Next |
|------|--------|-------|----------|-------|-------------|----------|-----------|--------|------|
| 2026-09-10 | run_001 | Environment & FIT Schema | Can we access FIT and is full local download feasible? | HF `fitvto-100k`, VPS 99GB disk | Schema confirmed (Parquet+embedded PNG, cm); full download shortfall ~128GB | Eval persistent, train ephemeral | `reports/runs/01_environment_and_fit_schema.md`, `reports/storage_audit.json` | DONE | Eval audit |
| 2026-09-10 | run_002 | Eval Measurement Audit | Is eval 5K measurement-complete and fit-varied? | 20 eval shards, 5000 samples | 0% meas missing; bust_ease -14.9→+61.7cm; VALID 4987/5000 | sleeve=0 is sleeveless not invalid; modality:sha256 identity | `reports/runs/02_eval_measurement_audit.md`, `data/processed/fit_eval_clean_v0.1.parquet` | DONE | Fix OOM, stream train |
| 2026-09-10 | run_003 | OOM Failure & Streaming Redesign | Why OOM and how to fix? | dmesg: python anon-rss 1.05GB killed | `iter_batches(8)` + checkpoint; peak RSS ~805MB | Shard streaming mandatory; RSS limit 1.5GB | `reports/runs/03_oom_failure_and_streaming_redesign.md`, `stream_core.py` | DONE | Full train stream |
| 2026-09-10 | run_004 | Full FIT Train Streaming | Audit 100K train without raw persistence? | Ephemeral train shards, batch=8, PID 309342 | **57/406 train** (live); eval 20/20; RSS ~510MB; no new OOM | Do not stop/restart running pipeline | `reports/runs/04_full_fit_stream_progress.md`, `data/interim/fit_checkpoint/` | PARTIAL | Finalize at 406/406 |
| 2026-09-10 | run_005 | Data Engineering Closure (partial) | Close DE with evidence pack? | 89/406 train, eval done | Contracts, materialize tool, 30 tests pass | Do not stop pipeline | `reports/runs/05_data_engineering_closure_partial.md` | PARTIAL | Finalize at 406/406 |
| — | run_006 | Global FIT-Clean + EDA | Full 105K quality, leakage, distributions? | All checkpoints | NOT STARTED | — | `data/processed/fit_clean_v0.1.parquet` | BLOCKED | Counterfactual feasibility |
| — | run_006 | Counterfactual Feasibility | Sufficient controlled measurement variation? | FIT-Clean manifest | NOT STARTED | — | TBD | BLOCKED | ML/VLM baselines |

---

## Evidence Chain (current)

```
Research Question: Do VLMs learn measurement-grounded fit?
    ↓
Run 001: Schema + storage constraints identified
    ↓
Run 002: Eval 5K audited — measurements complete, fit variation confirmed
    ↓
Run 003: OOM → bounded-memory architecture
    ↓
Run 004: Train streaming in progress (57/406)
    ↓
Run 005: [PENDING] Global FIT-Clean + leakage + EDA
    ↓
Run 006: [PENDING] Counterfactual pair feasibility
```

---

## Rules (Evidence-First Development)

1. Every meaningful run → independent Markdown report in `reports/runs/`.
2. Naming: `YYYYMMDD_HHMM_<stage>_<run_id>.md` for future runs; historical runs use numbered `01_`–`04_` prefix.
3. No overwriting prior reports.
4. Failures are evidence — document, don't hide.
5. Code ≠ completion; require execution evidence.
